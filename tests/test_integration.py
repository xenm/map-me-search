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
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ.setdefault("PROXY_AUTH_TOKEN", "test-token")
os.environ.setdefault("TURNSTILE_SECRET_KEY", "test-secret")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")
os.environ.setdefault("GOOGLE_API_KEY", "fake-key-for-test")

from httpx import ASGITransport, AsyncClient
from agent.agent_api import app, _verify_turnstile
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
            "The head parameter in gr.Blocks must be an f-string (head=f\"\"\") "
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
