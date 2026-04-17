"""
Tests for topic_preferences — the persistent preference store for named topics.

Unit tests use an in-process SQLite database (no Docker needed).
Integration tests spin up a postgres:16-alpine container via testcontainers and
verify the full lifecycle against real PostgreSQL.

Requires Docker for integration tests only.
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

_SQLITE_URL = "sqlite+aiosqlite:///:memory:"
_PG_IMAGE = "postgres:16-alpine"


@pytest_asyncio.fixture
async def sqlite_db():
    """Fresh in-memory SQLite DB for each unit test."""
    await _init_with_url(_SQLITE_URL)
    yield
    await _reset_for_testing()


@pytest.fixture(scope="module")
def postgres_asyncpg_url():
    """Spin up a postgres:16-alpine container and yield an asyncpg-compatible URL."""
    PostgresContainer = pytest.importorskip(
        "testcontainers.postgres", reason="testcontainers not installed"
    ).PostgresContainer
    with PostgresContainer(_PG_IMAGE) as pg:
        url = pg.get_connection_url()
        asyncpg_url = url.replace(
            "postgresql+psycopg2://", "postgresql+asyncpg://", 1
        ).replace("postgresql://", "postgresql+asyncpg://", 1)
        yield asyncpg_url


# ============================================================================
# Unit tests — _build_db_url and _build_engine_kwargs (no DB needed)
# ============================================================================


class TestBuildDbUrl:
    def test_falls_back_to_sqlite_when_no_env(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        url = _build_db_url()
        assert url.startswith("sqlite+aiosqlite://")

    def test_returns_database_url_when_set(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://user:pass@host/db")
        url = _build_db_url()
        assert url == "postgresql+asyncpg://user:pass@host/db"


class TestBuildEngineKwargs:
    def test_sqlite_returns_empty(self):
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
# Unit tests — get_preferences and append_and_maybe_summarize (SQLite)
# ============================================================================


class TestGetPreferences:
    @pytest.mark.asyncio
    async def test_returns_empty_string_for_unknown_topic(self, sqlite_db):
        result = await get_preferences("nonexistent-topic")
        assert result == ""

    @pytest.mark.asyncio
    async def test_returns_stored_preferences(self, sqlite_db):
        with patch(
            "agent.utils.topic_preferences._summarize", new_callable=AsyncMock
        ) as mock_summarize:
            mock_summarize.return_value = "- mocked summary"
            await append_and_maybe_summarize(
                "food-2024", "sushi restaurants", "gemini-test"
            )
        result = await get_preferences("food-2024")
        assert "sushi restaurants" in result


class TestAppendPreferences:
    @pytest.mark.asyncio
    async def test_first_append_creates_bullet(self, sqlite_db):
        await append_and_maybe_summarize("trip-a", "coffee shops", "gemini-test")
        prefs = await get_preferences("trip-a")
        assert prefs == "- coffee shops"

    @pytest.mark.asyncio
    async def test_second_append_adds_bullet(self, sqlite_db):
        await append_and_maybe_summarize("trip-b", "museums", "gemini-test")
        await append_and_maybe_summarize("trip-b", "parks", "gemini-test")
        prefs = await get_preferences("trip-b")
        assert prefs == "- museums\n- parks"

    @pytest.mark.asyncio
    async def test_version_increments(self, sqlite_db):
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
    async def test_summarize_called_at_version_10(self, sqlite_db):
        with patch(
            "agent.utils.topic_preferences._summarize", new_callable=AsyncMock
        ) as mock_summarize:
            mock_summarize.return_value = "- condensed preferences"
            for i in range(10):
                await append_and_maybe_summarize(
                    "trip-d", f"preference {i}", "gemini-test"
                )
            mock_summarize.assert_called_once()
        prefs = await get_preferences("trip-d")
        assert prefs == "- condensed preferences"

    @pytest.mark.asyncio
    async def test_summarize_not_called_before_version_10(self, sqlite_db):
        with patch(
            "agent.utils.topic_preferences._summarize", new_callable=AsyncMock
        ) as mock_summarize:
            for i in range(9):
                await append_and_maybe_summarize(
                    "trip-e", f"preference {i}", "gemini-test"
                )
            mock_summarize.assert_not_called()

    @pytest.mark.asyncio
    async def test_topics_are_isolated(self, sqlite_db):
        await append_and_maybe_summarize("iso-x", "hiking", "gemini-test")
        await append_and_maybe_summarize("iso-y", "beaches", "gemini-test")
        assert "hiking" in await get_preferences("iso-x")
        assert "beaches" in await get_preferences("iso-y")
        assert "beaches" not in await get_preferences("iso-x")


# ============================================================================
# Integration tests — real PostgreSQL container
# ============================================================================


class TestTopicPreferencesIntegration:
    """Full lifecycle tests against a real postgres:16-alpine container."""

    @pytest_asyncio.fixture(autouse=True)
    async def pg_db(self, postgres_asyncpg_url):
        await _init_with_url(postgres_asyncpg_url)
        yield
        await _reset_for_testing()

    @pytest.mark.asyncio
    async def test_preference_persists_across_engine_instances(
        self, postgres_asyncpg_url
    ):
        """Write via one engine, read via a fresh engine — confirms real DB write."""
        await append_and_maybe_summarize("persist-test", "rooftop bars", "gemini-test")
        await _reset_for_testing()
        await _init_with_url(postgres_asyncpg_url)
        result = await get_preferences("persist-test")
        assert "rooftop bars" in result

    @pytest.mark.asyncio
    async def test_summarization_at_version_10(self, postgres_asyncpg_url):
        with patch(
            "agent.utils.topic_preferences._summarize", new_callable=AsyncMock
        ) as mock_summarize:
            mock_summarize.return_value = "- summarized on postgres"
            for i in range(10):
                await append_and_maybe_summarize(
                    "pg-summarize", f"pref {i}", "gemini-test"
                )
            mock_summarize.assert_called_once()
        assert await get_preferences("pg-summarize") == "- summarized on postgres"
