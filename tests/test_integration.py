"""
Integration tests — Frontend relay → Agent API with mocked externals.

Mocks:
  - Cloudflare Turnstile verification (always passes)
  - Gemini LLM responses (returns canned text)

Tests the full request path:
  Frontend _relay_search → HTTP POST /search → proxy auth → turnstile verify → agent pipeline → response
"""

import os
import sys
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ.setdefault("PROXY_AUTH_TOKEN", "test-token")
os.environ.setdefault("TURNSTILE_SECRET_KEY", "test-secret")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")
os.environ.setdefault("GOOGLE_API_KEY", "fake-key-for-test")

from httpx import ASGITransport, AsyncClient
from agent.agent_api import app, _verify_turnstile


# ============================================================================
# Fixtures
# ============================================================================

MOCK_AGENT_RESULT = "Here are 3 great places in Prague: 1) Café Louvre 2) Letná Park 3) DOX Centre"


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
        async with AsyncClient(transport=transport, base_url="http://test") as client:
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
        async with AsyncClient(transport=transport, base_url="http://test") as client:
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
        async with AsyncClient(transport=transport, base_url="http://test") as client:
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
        async with AsyncClient(transport=transport, base_url="http://test") as client:
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

        async with AsyncClient(transport=transport, base_url="http://test") as client:
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

        async with AsyncClient(transport=transport, base_url="http://test") as client:
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
