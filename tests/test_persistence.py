"""
Tests for topic_preferences — the persistent preference store for named topics.

The application no longer supports any in-memory / SQLite fallback, so every
runtime-behaviour test spins up a postgres:16-alpine container via
testcontainers and runs against real PostgreSQL.

Unit tests (pure functions) remain DB-free.

Requires Docker for all classes except ``TestBuildDbUrl`` and
``TestBuildEngineKwargs``.
"""

import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ.setdefault("GOOGLE_API_KEY", "test-api-key-returns-dummy-response")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")

from agent.utils.topic_preferences import (
    _build_db_url,
    _build_engine_kwargs,
    _init_with_url,
    _reset_for_testing,
    append_and_maybe_summarize,
    get_preferences,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest_asyncio.fixture
async def pg_db(postgres_asyncpg_url):
    """Initialise topic_preferences against the shared Postgres container and
    truncate between tests so each test starts from an empty table."""
    await _init_with_url(postgres_asyncpg_url)
    from sqlalchemy import text
    from agent.utils.topic_preferences import _engine

    async with _engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE topic_preferences"))
    yield
    await _reset_for_testing()


# ============================================================================
# Unit tests — _build_db_url and _build_engine_kwargs (no DB needed)
# ============================================================================


class TestBuildDbUrl:
    def test_raises_when_no_env(self, monkeypatch):
        """SQLite fallback has been removed — DATABASE_URL is now mandatory."""
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
            _build_db_url()

    def test_raises_when_empty(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "   ")
        with pytest.raises(RuntimeError, match="DATABASE_URL is not set"):
            _build_db_url()

    def test_returns_database_url_when_set(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@host/db")
        url = _build_db_url()
        assert url == "postgresql+asyncpg://user:pass@host/db"


class TestBuildEngineKwargs:
    def test_non_postgresql_returns_empty(self):
        """Non-postgres URLs (only used by the _init_with_url test helper) skip SSL."""
        assert _build_engine_kwargs("sqlite+aiosqlite:///test.db") == {}

    def test_postgresql_tcp_requires_ssl(self):
        kwargs = _build_engine_kwargs(
            "postgresql+asyncpg://user:pass@db.example.com/mydb"
        )
        assert kwargs == {"connect_args": {"ssl": "require"}}

    def test_cloud_sql_unix_socket_skips_ssl(self):
        url = "postgresql+asyncpg://user:pass@/mydb?host=/cloudsql/project:region:instance"
        assert _build_engine_kwargs(url) == {}

    def test_cloud_sql_at_slash_syntax_skips_ssl(self):
        assert _build_engine_kwargs("postgresql+asyncpg://user:pass@/mydb") == {}


# ============================================================================
# Integration tests — real PostgreSQL container (testcontainers)
# ============================================================================


class TestTopicPreferencesIntegration:
    """Full lifecycle tests against a real postgres:16-alpine container."""

    @pytest.mark.asyncio
    async def test_returns_empty_string_for_unknown_topic(self, pg_db):
        assert await get_preferences("nonexistent-topic") == ""

    @pytest.mark.asyncio
    async def test_returns_stored_preferences(self, pg_db):
        await append_and_maybe_summarize(
            "food-2024", "sushi restaurants", "gemini-test"
        )
        assert "sushi restaurants" in await get_preferences("food-2024")

    @pytest.mark.asyncio
    async def test_first_append_creates_bullet(self, pg_db):
        await append_and_maybe_summarize("trip-a", "coffee shops", "gemini-test")
        assert await get_preferences("trip-a") == "- coffee shops"

    @pytest.mark.asyncio
    async def test_second_append_adds_bullet(self, pg_db):
        await append_and_maybe_summarize("trip-b", "museums", "gemini-test")
        await append_and_maybe_summarize("trip-b", "parks", "gemini-test")
        assert await get_preferences("trip-b") == "- museums\n- parks"

    @pytest.mark.asyncio
    async def test_version_increments(self, pg_db):
        from sqlalchemy import select
        from agent.utils.topic_preferences import _session_factory, TopicPreference

        await append_and_maybe_summarize("trip-c", "galleries", "gemini-test")
        await append_and_maybe_summarize("trip-c", "bookshops", "gemini-test")
        await append_and_maybe_summarize("trip-c", "jazz bars", "gemini-test")

        async with _session_factory() as session:
            result = await session.execute(
                select(TopicPreference).where(TopicPreference.topic == "trip-c")
            )
            row = result.scalar_one()
        assert row.version == 3

    @pytest.mark.asyncio
    async def test_summarize_called_at_version_10(self, pg_db):
        with patch(
            "agent.utils.topic_preferences._summarize", new_callable=AsyncMock
        ) as mock_summarize:
            mock_summarize.return_value = "- condensed preferences"
            for i in range(10):
                await append_and_maybe_summarize(
                    "trip-d", f"preference {i}", "gemini-test"
                )
            mock_summarize.assert_called_once()
        assert await get_preferences("trip-d") == "- condensed preferences"

    @pytest.mark.asyncio
    async def test_summarize_not_called_before_version_10(self, pg_db):
        with patch(
            "agent.utils.topic_preferences._summarize", new_callable=AsyncMock
        ) as mock_summarize:
            for i in range(9):
                await append_and_maybe_summarize(
                    "trip-e", f"preference {i}", "gemini-test"
                )
            mock_summarize.assert_not_called()

    @pytest.mark.asyncio
    async def test_topics_are_isolated(self, pg_db):
        await append_and_maybe_summarize("iso-x", "hiking", "gemini-test")
        await append_and_maybe_summarize("iso-y", "beaches", "gemini-test")
        assert "hiking" in await get_preferences("iso-x")
        assert "beaches" in await get_preferences("iso-y")
        assert "beaches" not in await get_preferences("iso-x")

    @pytest.mark.asyncio
    async def test_preference_persists_across_engine_instances(
        self, pg_db, postgres_asyncpg_url
    ):
        """Write via one engine, read via a fresh engine — confirms real DB write."""
        await append_and_maybe_summarize("persist-test", "rooftop bars", "gemini-test")
        await _reset_for_testing()
        await _init_with_url(postgres_asyncpg_url)
        assert "rooftop bars" in await get_preferences("persist-test")

    @pytest.mark.asyncio
    async def test_case_insensitive_read_and_append(self, pg_db):
        """Mixed-case legacy topics are found case-insensitively and updated in-place."""
        from sqlalchemy import select, text
        from agent.utils.topic_preferences import _session_factory, TopicPreference

        # Seed a legacy mixed-case row directly (simulates pre-existing data)
        async with _session_factory() as session:
            await session.execute(
                text(
                    "INSERT INTO topic_preferences (topic, preferences, version) "
                    "VALUES (:topic, :preferences, :version)"
                ),
                {"topic": "Trip-X", "preferences": "- museums", "version": 1},
            )
            await session.commit()

        # Read with different case
        assert "museums" in await get_preferences("trip-x")
        # Append with different case
        await append_and_maybe_summarize("TRIP-X", "parks", "gemini-test")
        stored = await get_preferences("Trip-X")
        assert "museums" in stored
        assert "parks" in stored
        # Original topic case in DB is preserved
        async with _session_factory() as session:
            result = await session.execute(
                select(TopicPreference).where(TopicPreference.topic == "Trip-X")
            )
            row = result.scalar_one()
        assert row.topic == "Trip-X"
        assert row.version == 2

    @pytest.mark.asyncio
    async def test_new_topic_is_lowercased(self, pg_db):
        """New topics are stored as lowercase."""
        await append_and_maybe_summarize("NEW-TOPIC", "cafes", "gemini-test")
        assert "cafes" in await get_preferences("new-topic")
        # Verify the DB row itself is lowercase
        from sqlalchemy import select
        from agent.utils.topic_preferences import _session_factory, TopicPreference

        async with _session_factory() as session:
            result = await session.execute(
                select(TopicPreference).where(TopicPreference.topic == "new-topic")
            )
            row = result.scalar_one()
        assert row.topic == "new-topic"
