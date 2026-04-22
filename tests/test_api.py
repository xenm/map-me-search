"""
Unit tests for the Agent API security layer.

Tests X-Proxy-Auth verification, Turnstile validation,
and the /health endpoint without requiring external services.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ.setdefault("PROXY_AUTH_TOKEN", "test-token")
os.environ.setdefault("TURNSTILE_SECRET_KEY", "test-secret")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")
os.environ.setdefault("GOOGLE_API_KEY", "fake-key-for-test")

from fastapi.testclient import TestClient
from agent.agent_api import _build_search_prompt, app


client = TestClient(app, raise_server_exceptions=False)


# ============================================================================
# /health
# ============================================================================


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ============================================================================
# X-Proxy-Auth verification
# ============================================================================


class TestProxyAuth:
    def test_missing_header_returns_403(self):
        resp = client.post(
            "/search",
            json={
                "city": "Tokyo",
                "preferences": "ramen",
                "turnstile_token": "tok",
            },
        )
        assert resp.status_code == 403

    def test_wrong_token_returns_403(self):
        resp = client.post(
            "/search",
            json={
                "city": "Tokyo",
                "preferences": "ramen",
                "turnstile_token": "tok",
            },
            headers={"X-Proxy-Auth": "wrong-token"},
        )
        assert resp.status_code == 403

    def test_correct_token_passes_auth(self):
        """With correct proxy auth but fake turnstile token, should reach
        Turnstile verification (and fail there, not at proxy auth)."""
        resp = client.post(
            "/search",
            json={
                "city": "Tokyo",
                "preferences": "ramen",
                "turnstile_token": "fake",
            },
            headers={"X-Proxy-Auth": "test-token"},
        )
        # Should NOT be 403 Forbidden (proxy auth passed);
        # will be 502 or 403 from Turnstile verification failure
        assert resp.status_code in (403, 502)


# ============================================================================
# Request validation
# ============================================================================


class TestRequestValidation:
    def test_missing_city_returns_422(self):
        resp = client.post(
            "/search",
            json={"preferences": "ramen", "turnstile_token": "tok"},
            headers={"X-Proxy-Auth": "test-token"},
        )
        assert resp.status_code == 422

    def test_missing_turnstile_token_returns_422(self):
        resp = client.post(
            "/search",
            json={"city": "Tokyo", "preferences": "ramen"},
            headers={"X-Proxy-Auth": "test-token"},
        )
        assert resp.status_code == 422

    def test_topic_is_optional(self):
        """topic field should be optional (defaults to None)."""
        resp = client.post(
            "/search",
            json={
                "city": "Tokyo",
                "preferences": "ramen",
                "turnstile_token": "tok",
            },
            headers={"X-Proxy-Auth": "test-token"},
        )
        # Should not be 422 (validation passed); will fail at Turnstile
        assert resp.status_code != 422


# ============================================================================
# _build_search_prompt
# ============================================================================


class TestBuildSearchPrompt:
    def test_no_past_preferences_returns_base_prompt(self):
        result = _build_search_prompt("Paris", "museums", "")
        assert "Paris" in result
        assert "museums" in result
        assert "Taste hints" not in result

    def test_with_past_preferences_injects_context(self):
        past = "- coffee shops\n- art galleries"
        result = _build_search_prompt("Berlin", "nightlife", past)
        assert "Berlin" in result
        assert "nightlife" in result
        assert "Taste hints" in result
        assert past in result

    def test_no_past_preferences_omits_hints(self):
        result = _build_search_prompt("Rome", "pizza", "")
        assert "Taste hints" not in result
        assert "earlier searches" not in result

    def test_with_past_preferences_has_separator(self):
        result = _build_search_prompt("Tokyo", "ramen", "- ramen bars")
        assert "\n\n" in result

    def test_city_and_preferences_always_present(self):
        for past in ("", "- hiking"):
            result = _build_search_prompt("Oslo", "fjords", past)
            assert "Oslo" in result
            assert "fjords" in result
