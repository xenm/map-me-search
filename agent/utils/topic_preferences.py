"""Persistent preference store for named search topics.

Schema
------
    topic_preferences(topic TEXT PK, preferences TEXT, version INTEGER)

Lifecycle per request (when topic is set)
-----------------------------------------
  1. get_preferences(topic)            -> inject into LLM prompt as past-context
  2. Agent pipeline runs               -> ResearchAgent -> FilterAgent -> FormatterAgent
  3. append_and_maybe_summarize(...)   -> appends new bullet; summarizes every 10th version
"""

import asyncio
import os
from typing import Optional

from sqlalchemy import Column, Integer, String, func, select, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import StaticPool

_SUMMARIZE_PROMPT = """\
You are condensing a user's accumulated search preferences for a named topic.

Current list:
{preferences}

Rules:
- Return ONLY bullet points, one per line, each starting with "- " (dash space)
- Merge duplicates and similar items into a single bullet
- Keep the most specific and useful preferences
- No intro sentence, no conclusion, no blank lines between bullets
"""


class _Base(DeclarativeBase):
    pass


class TopicPreference(_Base):
    __tablename__ = "topic_preferences"

    topic = Column(String, primary_key=True, nullable=False)
    preferences = Column(String, nullable=False, default="")
    version = Column(Integer, nullable=False, default=0)


_engine: Optional[AsyncEngine] = None
_session_factory: Optional[sessionmaker] = None
_init_lock = asyncio.Lock()


def _get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("Topic preferences engine is not initialized")
    return _engine


def _get_session_factory() -> sessionmaker:
    if _session_factory is None:
        raise RuntimeError("Topic preferences session factory is not initialized")
    return _session_factory


def _build_db_url() -> str:
    """Return the PostgreSQL connection string from ``DATABASE_URL``.

    Raises:
        RuntimeError: when ``DATABASE_URL`` is not set. There is no SQLite /
            in-memory fallback — the app requires PostgreSQL (local Docker
            container for dev, Cloud SQL in production).
    """
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Start the local Postgres container "
            "(`docker compose up -d postgres`) and set DATABASE_URL in "
            "agent/.env — see agent/.env.example."
        )
    return url


def _build_engine_kwargs(db_url: str) -> dict:
    """Return extra SQLAlchemy engine kwargs.

    PostgreSQL over TCP requires SSL for production (Cloud SQL, etc).
    Unix sockets (Cloud SQL Auth Proxy) and localhost Docker do not.
    Non-postgresql URLs are only used by the ``_init_with_url`` test helper.
    """
    if not db_url.startswith("postgresql"):
        return {}
    is_unix = "host=/cloudsql/" in db_url or db_url.split("@", 1)[-1].startswith("/")
    # Skip SSL for localhost Docker connections
    is_localhost = "localhost" in db_url or "127.0.0.1" in db_url
    return {} if (is_unix or is_localhost) else {"connect_args": {"ssl": "require"}}


async def _ensure_initialized() -> None:
    global _engine, _session_factory
    if _engine is not None:
        return
    async with _init_lock:
        if _engine is not None:
            return
        db_url = _build_db_url()
        kwargs = _build_engine_kwargs(db_url)
        if db_url.startswith("postgresql"):
            kwargs.setdefault("pool_pre_ping", True)
        engine = create_async_engine(db_url, **kwargs)
        async with engine.begin() as conn:
            await conn.run_sync(_Base.metadata.create_all)
        _session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        _engine = engine


async def _reset_for_testing() -> None:
    """Dispose the engine and clear the singleton. Tests only."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None


async def _init_with_url(db_url: str) -> None:
    """Initialize with a specific URL, bypassing env var and SSL. Tests only."""
    await _reset_for_testing()
    kwargs: dict = {}
    if ":memory:" in db_url:
        kwargs["connect_args"] = {"check_same_thread": False}
        kwargs["poolclass"] = StaticPool
    engine = create_async_engine(db_url, **kwargs)
    async with engine.begin() as conn:
        await conn.run_sync(_Base.metadata.create_all)
    global _engine, _session_factory
    _session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    _engine = engine


async def get_preferences(topic: str) -> str:
    """Return accumulated bullet-point preferences for *topic*, or "" if none."""
    await _ensure_initialized()
    session_factory = _get_session_factory()
    async with session_factory() as session:
        result = await session.execute(
            select(TopicPreference).where(
                func.lower(TopicPreference.topic) == topic.lower()
            )
        )
        row = result.scalar_one_or_none()
        return row.preferences if row is not None else ""


async def _summarize(preferences: str, model_name: str) -> str:
    from google import genai

    client = genai.Client()
    response = await client.aio.models.generate_content(
        model=model_name,
        contents=_SUMMARIZE_PROMPT.format(preferences=preferences),
    )
    summary = (response.text or "").strip()
    return summary if summary else preferences


async def append_and_maybe_summarize(
    topic: str, new_preference: str, model_name: str
) -> None:
    """Append *new_preference* as a bullet; summarize every 10th version.

    Reads and writes are case-insensitive. If a row already exists under a
    different case (legacy entry), it is updated in-place. New rows are keyed
    with a lowercase topic string.
    """
    await _ensure_initialized()
    session_factory = _get_session_factory()
    engine = _get_engine()
    async with session_factory() as session:
        async with session.begin():
            stmt = select(TopicPreference).where(
                func.lower(TopicPreference.topic) == topic.lower()
            )
            if engine.dialect.name == "postgresql":
                stmt = stmt.with_for_update()
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()

            if row is None:
                preferences = f"- {new_preference}"
                version = 1
                topic_key = topic.lower()
            else:
                sep = "\n" if row.preferences else ""
                preferences = f"{row.preferences}{sep}- {new_preference}"
                version = row.version + 1
                topic_key = row.topic

            if version % 10 == 0:
                preferences = await _summarize(preferences, model_name)

            await session.execute(
                text(
                    "INSERT INTO topic_preferences (topic, preferences, version) "
                    "VALUES (:topic, :preferences, :version) "
                    "ON CONFLICT (topic) DO UPDATE SET "
                    "preferences = EXCLUDED.preferences, "
                    "version = EXCLUDED.version"
                ),
                {"topic": topic_key, "preferences": preferences, "version": version},
            )
