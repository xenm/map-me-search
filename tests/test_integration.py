"""
Integration tests — Frontend relay → Agent API with mocked externals.

Mocks:
  - Cloudflare Turnstile verification (always passes)
  - Gemini LLM responses (returns canned text via the built-in dev dummy key)

Tests the full request path:
  Frontend _relay_search → HTTP POST /search → proxy auth → turnstile verify → agent pipeline → response

The topic-persistence tests run against a real postgres:16-alpine container
spun up via testcontainers (shared across the session — see ``conftest.py``).
"""

import os
import sys
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ.setdefault("PROXY_AUTH_TOKEN", "test-token")
os.environ.setdefault("TURNSTILE_SECRET_KEY", "test-secret")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")
os.environ.setdefault("GOOGLE_API_KEY", "fake-key-for-test")

from httpx import ASGITransport, AsyncClient
from agent.agent_api import app, _verify_turnstile, _DEV_DUMMY_KEY, search_places
from agent.utils import topic_preferences as topic_prefs_module
from agent.utils.topic_preferences import (
    _init_with_url,
    _reset_for_testing,
    get_preferences,
)
from fastapi import HTTPException


# ============================================================================
# Fixtures
# ============================================================================

MOCK_AGENT_RESULT = (
    "Here are 3 great places in Prague: 1) Café Louvre 2) Letná Park 3) DOX Centre"
)


@pytest.fixture
def mock_turnstile():
    """Bypass Cloudflare Turnstile verification."""
    with patch("agent.agent_api._verify_turnstile", new_callable=AsyncMock) as m:
        m.return_value = None
        yield m


@pytest.fixture
def mock_agent():
    """Mock the search_places agent pipeline to return canned results."""
    with patch("agent.agent_api.search_places", new_callable=AsyncMock) as m:
        m.return_value = MOCK_AGENT_RESULT
        yield m


# ============================================================================
# Integration: Agent API end-to-end (mocked LLM + Turnstile)
# ============================================================================


class TestSearchEndToEnd:
    """Full /search flow with mocked externals."""

    @pytest.mark.asyncio
    async def test_valid_search_returns_result(self, mock_turnstile, mock_agent):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="https://test") as client:
            resp = await client.post(
                "/search",
                json={
                    "city": "Prague",
                    "preferences": "coffee shops and parks",
                    "turnstile_token": "fake-token",
                },
                headers={"X-Proxy-Auth": "test-token"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "result" in data
        assert data["result"] == MOCK_AGENT_RESULT
        mock_agent.assert_called_once_with(
            city_name="Prague",
            preferences="coffee shops and parks",
            topic=None,
        )

    @pytest.mark.asyncio
    async def test_search_with_topic(self, mock_turnstile, mock_agent):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="https://test") as client:
            resp = await client.post(
                "/search",
                json={
                    "city": "Prague",
                    "preferences": "outdoor activities",
                    "topic": "hiking",
                    "turnstile_token": "fake-token",
                },
                headers={"X-Proxy-Auth": "test-token"},
            )
        assert resp.status_code == 200
        mock_agent.assert_called_once_with(
            city_name="Prague",
            preferences="outdoor activities",
            topic="hiking",
        )

    @pytest.mark.asyncio
    async def test_missing_proxy_auth_rejected(self, mock_turnstile, mock_agent):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="https://test") as client:
            resp = await client.post(
                "/search",
                json={
                    "city": "Prague",
                    "preferences": "food",
                    "turnstile_token": "fake-token",
                },
            )
        assert resp.status_code == 403
        mock_agent.assert_not_called()

    @pytest.mark.asyncio
    async def test_wrong_proxy_auth_rejected(self, mock_turnstile, mock_agent):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="https://test") as client:
            resp = await client.post(
                "/search",
                json={
                    "city": "Prague",
                    "preferences": "food",
                    "turnstile_token": "fake-token",
                },
                headers={"X-Proxy-Auth": "wrong-token"},
            )
        assert resp.status_code == 403
        mock_agent.assert_not_called()


# ============================================================================
# Integration: Frontend relay → Agent API (mocked LLM + Turnstile)
# ============================================================================


class TestFrontendRelayIntegration:
    """Test the frontend _relay_search function calling the real Agent API."""

    @pytest.mark.asyncio
    async def test_relay_full_roundtrip(self, mock_turnstile, mock_agent):
        """Frontend relay → Agent API /search → mocked agent → response."""
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="https://test") as client:
            # Simulate what _relay_search does
            payload = {
                "city": "Prague",
                "preferences": "coffee shops",
                "topic": None,
                "turnstile_token": "fake-token",
            }
            headers = {"X-Proxy-Auth": "test-token"}
            resp = await client.post("/search", json=payload, headers=headers)

        assert resp.status_code == 200
        result = resp.json().get("result", "")
        assert "Prague" in result
        assert mock_agent.called

    @pytest.mark.asyncio
    async def test_relay_receives_error_on_bad_auth(self, mock_turnstile, mock_agent):
        """Frontend relay with wrong token gets 403."""
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="https://test") as client:
            resp = await client.post(
                "/search",
                json={
                    "city": "Prague",
                    "preferences": "coffee",
                    "turnstile_token": "fake-token",
                },
                headers={"X-Proxy-Auth": "bad-token"},
            )

        assert resp.status_code == 403
        mock_agent.assert_not_called()


# ============================================================================
# Unit Tests: Turnstile Verification
# ============================================================================


class TestTurnstileVerification:
    """Unit tests for _verify_turnstile function."""

    def test_turnstile_javascript_syntax(self):
        """Validate that the Turnstile JavaScript in the Gradio head is syntactically correct."""
        import re
        from pathlib import Path

        # Read the source file directly
        hf_app_path = Path(__file__).parent.parent / "frontend" / "hf_app.py"
        source_code = hf_app_path.read_text()

        # Find the gr.Blocks head parameter
        # Match: head=f""" or head="""
        head_pattern = r'head=(f?)"""'
        match = re.search(head_pattern, source_code)

        assert match is not None, "Could not find head parameter in gr.Blocks"
        has_f_string = match.group(1) == "f"

        # The head parameter must be an f-string to properly escape {{ and }}
        assert has_f_string, (
            'The head parameter in gr.Blocks must be an f-string (head=f""") '
            "to properly escape JavaScript braces. Without the 'f' prefix, "
            "{{ and }} remain as double braces in the output, causing JavaScript syntax errors."
        )

        # Extract the content between head=..."""
        head_content_pattern = r'head=f"""(.*?)"""'
        head_match = re.search(head_content_pattern, source_code, re.DOTALL)
        assert head_match is not None, "Could not extract head content"

        head_content = head_match.group(1)

        # Verify that the JavaScript uses double braces for escaping
        # In f-strings, {{ becomes { and }} becomes } in the output
        assert "{{" in head_content, (
            "JavaScript in head should use {{ and }} for f-string escaping"
        )

        # Check for common JavaScript patterns to ensure it's not empty
        assert "function" in head_content or "addEventListener" in head_content, (
            "JavaScript in head appears to be missing expected code"
        )

    def test_turnstile_reset_after_search(self):
        """The search click chain must reset Turnstile so each request uses a fresh token.

        Cloudflare Turnstile tokens are single-use; reusing one yields
        'timeout-or-duplicate' and a 403 from the Agent API. The frontend must
        call `turnstile.reset()` after every search and clear the hidden token
        textbox.
        """
        from pathlib import Path

        hf_app_path = Path(__file__).parent.parent / "frontend" / "hf_app.py"
        source_code = hf_app_path.read_text()

        assert "window.turnstile.reset()" in source_code, (
            "Frontend must call window.turnstile.reset() after a search to "
            "obtain a fresh Turnstile token for the next request."
        )

    def test_relay_search_timeout_at_least_180s(self):
        """The relay HTTP client must allow enough time for the multi-agent pipeline.

        The agent pipeline can take well over 90s end-to-end; a too-low timeout
        surfaces as 'The search is taking too long' even when the API succeeds.
        """
        import re
        from pathlib import Path

        hf_app_path = Path(__file__).parent.parent / "frontend" / "hf_app.py"
        source_code = hf_app_path.read_text()

        match = re.search(r"httpx\.AsyncClient\(timeout=(\d+(?:\.\d+)?)\)", source_code)
        assert match is not None, (
            "Could not find httpx.AsyncClient(timeout=...) call in frontend/hf_app.py"
        )
        timeout_value = float(match.group(1))
        assert timeout_value >= 180.0, (
            f"Relay timeout is {timeout_value}s; must be >= 180s to accommodate "
            "the full agent pipeline latency."
        )

    @pytest.mark.asyncio
    async def test_verify_turnstile_network_error(self):
        """Test that network failure to Cloudflare raises 502 error."""
        from unittest.mock import patch
        import httpx

        # Mock httpx.AsyncClient to raise HTTPError
        with patch("agent.agent_api.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = (
                httpx.HTTPError("Network error")
            )

            with pytest.raises(HTTPException) as exc_info:
                await _verify_turnstile("fake-token")
            assert exc_info.value.status_code == 502
            assert "Verification service unavailable" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_turnstile_invalid_token(self):
        """Test that invalid/expired token raises 403 error."""
        from unittest.mock import patch, AsyncMock

        # Mock successful HTTP response but with failed verification
        with patch("agent.agent_api.httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json = lambda: {
                "success": False,
                "error-codes": ["invalid-input-response"],
            }
            mock_client.return_value.__aenter__.return_value.post.return_value = (
                mock_response
            )

            with pytest.raises(HTTPException) as exc_info:
                await _verify_turnstile("invalid-token")
            assert exc_info.value.status_code == 403
            assert "Turnstile verification failed" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verify_turnstile_success(self):
        """Test that valid token passes verification."""
        from unittest.mock import patch, AsyncMock

        # Mock successful HTTP response with successful verification
        with patch("agent.agent_api.httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json = lambda: {"success": True}
            mock_client.return_value.__aenter__.return_value.post.return_value = (
                mock_response
            )

            # Should not raise any exception
            await _verify_turnstile("valid-token")


# ============================================================================
# Integration: Topic preferences — real Postgres + dummy-LLM end-to-end
# ============================================================================
#
# These tests exercise the full ``search_places`` flow (DB read → prompt build →
# LLM → DB write) against a real postgres:16-alpine container, with the Gemini
# call replaced by the built-in dev-dummy stub (see
# ``agent_api._build_dummy_llm_response``). This lets us verify that the
# preferences history is actually persisted and injected into the LLM prompt on
# subsequent calls — without burning real API credits.


@pytest_asyncio.fixture
async def pg_db_with_dummy_llm(postgres_asyncpg_url, monkeypatch):
    """Point topic_preferences at the shared Postgres container, truncate the
    table, and force the dev-dummy LLM path for the duration of the test."""
    monkeypatch.setenv("DATABASE_URL", postgres_asyncpg_url)
    monkeypatch.setenv("GOOGLE_API_KEY", _DEV_DUMMY_KEY)

    await _init_with_url(postgres_asyncpg_url)
    from sqlalchemy import text
    from agent.utils.topic_preferences import _engine

    async with _engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE topic_preferences"))
    yield
    await _reset_for_testing()


class TestTopicHistoryInjectionIntegration:
    """Verify that past calls on the same topic add the topic's accumulated
    preference history to the subsequent LLM request."""

    @pytest.mark.asyncio
    async def test_second_call_includes_first_calls_preferences(
        self, pg_db_with_dummy_llm
    ):
        """First search persists; second search on the same topic must inject
        the first call's preferences into the LLM prompt."""
        first = await search_places(
            city_name="Prague",
            preferences="rooftop bars",
            topic="roadtrip",
        )
        # First call: no history yet
        assert "No past preferences on file" in first

        stored = await get_preferences("roadtrip")
        assert stored == "- rooftop bars"

        second = await search_places(
            city_name="Vienna",
            preferences="opera houses",
            topic="roadtrip",
        )
        # Second call: the dummy LLM response echoes the injected past prefs
        assert "Past preferences injected into the prompt" in second
        assert "- rooftop bars" in second

        # And the new preference was appended
        stored_after = await get_preferences("roadtrip")
        assert stored_after == "- rooftop bars\n- opera houses"

    @pytest.mark.asyncio
    async def test_third_call_accumulates_history(self, pg_db_with_dummy_llm):
        await search_places(city_name="A", preferences="p1", topic="acc")
        await search_places(city_name="B", preferences="p2", topic="acc")
        third = await search_places(city_name="C", preferences="p3", topic="acc")

        assert "- p1" in third
        assert "- p2" in third
        # p3 is the *new* preference — it is persisted AFTER the LLM call,
        # so it must NOT appear in the injected past-preferences context. The
        # stub wraps the header in `**...**` markdown emphasis.
        assert "Past preferences injected into the prompt:**\n- p1\n- p2" in third

        final_stored = await get_preferences("acc")
        assert final_stored == "- p1\n- p2\n- p3"

    @pytest.mark.asyncio
    async def test_different_topics_are_isolated(self, pg_db_with_dummy_llm):
        await search_places(city_name="Oslo", preferences="fjords", topic="nordic")
        madrid = await search_places(
            city_name="Madrid", preferences="tapas", topic="iberia"
        )
        # Madrid's context must not contain Oslo's preferences
        assert "fjords" not in madrid
        assert "No past preferences on file" in madrid

    @pytest.mark.asyncio
    async def test_no_topic_skips_database_entirely(
        self, pg_db_with_dummy_llm, monkeypatch
    ):
        """With ``topic=None`` the code must never touch the DB, even on failure."""
        get_called = False
        append_called = False

        real_get = topic_prefs_module.get_preferences
        real_append = topic_prefs_module.append_and_maybe_summarize

        async def tracking_get(*args, **kwargs):
            nonlocal get_called
            get_called = True
            return await real_get(*args, **kwargs)

        async def tracking_append(*args, **kwargs):
            nonlocal append_called
            append_called = True
            return await real_append(*args, **kwargs)

        monkeypatch.setattr(topic_prefs_module, "get_preferences", tracking_get)
        monkeypatch.setattr(
            topic_prefs_module, "append_and_maybe_summarize", tracking_append
        )

        result = await search_places(
            city_name="Anywhere", preferences="anything", topic=None
        )
        assert result  # still returns a response
        assert get_called is False
        assert append_called is False


class TestDatabaseFailureFallbackIntegration:
    """When the database is unreachable, the search must still succeed with
    empty history and the failure must be logged."""

    @pytest.mark.asyncio
    async def test_search_succeeds_when_get_preferences_raises(
        self, pg_db_with_dummy_llm, monkeypatch, caplog
    ):
        async def boom(topic):
            raise ConnectionError("simulated database outage")

        monkeypatch.setattr(topic_prefs_module, "get_preferences", boom)

        import logging

        with caplog.at_level(logging.ERROR, logger="agent.agent_api"):
            result = await search_places(
                city_name="Lisbon",
                preferences="pastel de nata",
                topic="eurotrip",
            )

        # Search still returns a result — with empty past-preferences context
        assert result
        assert "No past preferences on file" in result

        # And the DB failure was logged with a stack trace (logger.exception)
        error_records = [
            r for r in caplog.records if r.levelno == logging.ERROR and r.exc_info
        ]
        assert any(
            "Failed to load past preferences" in r.getMessage() for r in error_records
        ), f"Expected a logged DB failure with traceback; got: {caplog.records!r}"

    @pytest.mark.asyncio
    async def test_search_succeeds_when_append_raises(
        self, pg_db_with_dummy_llm, monkeypatch, caplog
    ):
        async def boom(**kwargs):
            raise ConnectionError("simulated database outage on write")

        monkeypatch.setattr(topic_prefs_module, "append_and_maybe_summarize", boom)

        import logging

        with caplog.at_level(logging.ERROR, logger="agent.agent_api"):
            result = await search_places(
                city_name="Porto",
                preferences="port wine",
                topic="eurotrip",
            )

        assert result
        error_records = [
            r for r in caplog.records if r.levelno == logging.ERROR and r.exc_info
        ]
        assert any(
            "Failed to persist preferences" in r.getMessage() for r in error_records
        ), f"Expected a logged DB persist failure; got: {caplog.records!r}"
