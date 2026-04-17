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

from sqlalchemy import Column, Integer, String, select, text
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
- Maximum 8 bullet points
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


def _build_db_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    return url if url else "sqlite+aiosqlite:///topic_preferences.db"


def _build_engine_kwargs(db_url: str) -> dict:
    """Return extra SQLAlchemy engine kwargs.

    PostgreSQL over TCP requires SSL. Cloud SQL Auth Proxy (Unix socket) does not.
    """
    if not db_url.startswith("postgresql"):
        return {}
    is_unix = "host=/cloudsql/" in db_url or db_url.split("@", 1)[-1].startswith("/")
    return {} if is_unix else {"connect_args": {"ssl": "require"}}


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
    async with _session_factory() as session:
        result = await session.execute(
            select(TopicPreference).where(TopicPreference.topic == topic)
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
    """Append *new_preference* as a bullet; summarize every 10th version."""
    await _ensure_initialized()
    async with _session_factory() as session:
        async with session.begin():
            stmt = select(TopicPreference).where(TopicPreference.topic == topic)
            if _engine.dialect.name == "postgresql":
                stmt = stmt.with_for_update()
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()

            if row is None:
                preferences = f"- {new_preference}"
                version = 1
            else:
                sep = "\n" if row.preferences else ""
                preferences = f"{row.preferences}{sep}- {new_preference}"
                version = row.version + 1

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
                {"topic": topic, "preferences": preferences, "version": version},
            )
