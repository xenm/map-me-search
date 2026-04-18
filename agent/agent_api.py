"""
AI-Powered Nearby Places Search Agent API
Deployed to Google Cloud Run

Exposes /health and /search endpoints. Requests are authenticated via
X-Proxy-Auth shared secret and Cloudflare Turnstile server-side verification.
"""

import os
import logging
import asyncio

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")  # no-op when absent (Cloud Run)
from google.adk.runners import Runner  # noqa: E402
from google.adk.plugins.logging_plugin import LoggingPlugin  # noqa: E402
from google.genai import types  # noqa: E402
from typing import Optional  # noqa: E402
import hmac  # noqa: E402

import httpx  # noqa: E402
from fastapi import FastAPI, Request, HTTPException  # noqa: E402
from pydantic import BaseModel  # noqa: E402

try:
    from .utils import places_agent_core
    from .utils import topic_preferences
except ImportError:
    from utils import places_agent_core
    from utils import topic_preferences

try:
    from google.genai import errors as genai_errors
except ImportError:  # pragma: no cover
    genai_errors = None

# Load environment variables

# Configure logging for cloud environment
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants


def _is_transient_model_error(exc: BaseException) -> bool:
    return places_agent_core.is_transient_model_error(exc)


def _is_quota_exhausted_error(exc: BaseException) -> bool:
    return places_agent_core.is_quota_exhausted_error(exc)


def _get_model_candidates() -> list[str]:
    return places_agent_core.get_model_candidates()


async def _run_runner_collect_final_text(
    runner: Runner,
    user_id: str,
    session_id: str,
    query_content: types.Content,
    max_attempts: int,
    initial_delay_s: float,
    backoff_factor: float,
) -> str:
    def _on_retry(attempt: int, total_attempts: int, delay: float) -> None:
        logger.warning(
            f"Model temporarily unavailable (503). Retrying in {delay:.1f}s... ({attempt}/{total_attempts})"
        )

    return await places_agent_core.run_runner_collect_final_text(
        runner=runner,
        user_id=user_id,
        session_id=session_id,
        query_content=query_content,
        max_attempts=max_attempts,
        initial_delay_s=initial_delay_s,
        backoff_factor=backoff_factor,
        on_retry=_on_retry,
    )


_DEV_DUMMY_KEY = "test-api-key-returns-dummy-response"


def _configure_genai_auth() -> None:
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set — cannot authenticate to Gemini")
    if api_key == _DEV_DUMMY_KEY:
        logger.info("Dummy API key detected — LLM calls will return stub responses")
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
    logger.info("Gemini authentication configured (API key)")


_configure_genai_auth()


# ============================================================================
# Agent System Initialization
# ============================================================================


def initialize_multi_agent_system(model_name: Optional[str] = None):
    """Initialize the multi-agent system for places search."""
    logger.info("Initializing Multi-Agent System...")

    root_agent = places_agent_core.initialize_multi_agent_system(model_name=model_name)

    logger.info("Multi-Agent Pipeline initialized successfully")
    return root_agent


def _build_search_prompt(city: str, preferences: str, past_preferences: str) -> str:
    """Build the LLM prompt, injecting past preferences as taste context when available."""
    base = (
        f"Find nearby places in {city} for someone who likes: {preferences}. "
        "Provide specific recommendations with names, brief descriptions, "
        "and why they would enjoy each place."
    )
    if past_preferences:
        return (
            f"{base}\n\n"
            "For additional context, here are the user's accumulated preferences "
            f"from previous searches on this topic:\n{past_preferences}"
        )
    return base


def create_app(root_agent, plugins=None):
    """Create App with Events Compaction for context optimization."""
    agent_app = places_agent_core.create_app(
        root_agent=root_agent,
        plugins=plugins,
        compaction_interval=4,
        overlap_size=1,
    )
    logger.info("App created with EventsCompactionConfig")
    return agent_app


# Sanitize strings before logging to prevent log injection
def _sanitize_log_str(s):
    if s is None:
        return ""
    return str(s).replace("\r", "").replace("\n", "")


def _build_dummy_llm_response(
    city_name: str, preferences: str, past_preferences: str
) -> str:
    """Dev stub — canned response that echoes inputs AND any past preferences
    injected from the topic_preferences store. Lets integration tests verify the
    DB → prompt → response flow without spending real Gemini credits."""
    context_block = (
        f"\n\n**Past preferences injected into the prompt:**\n{past_preferences}\n"
        if past_preferences
        else "\n\n*No past preferences on file for this topic.*\n"
    )
    return (
        f"## Dev Stub Results for {city_name}\n\n"
        f"**Preferences:** {preferences}"
        f"{context_block}\n"
        "1. **The Golden Cafe** — Cozy spot with great espresso and pastries.\n"
        "2. **Riverside Park** — Beautiful walking trails along the river.\n"
        "3. **The Art Quarter** — Street art, galleries, and independent boutiques.\n\n"
        "*This is a dev stub response. Set a real `GOOGLE_API_KEY` in "
        "`agent/.env` for live results.*"
    )


async def _invoke_llm_pipeline(
    prompt: str,
    user_id: str,
    model_candidates: list[str],
) -> str:
    """Run the real multi-agent Gemini pipeline against *prompt*.

    Centralised so the dev-stub short-circuit in `search_places` replaces only
    this call, leaving the surrounding DB read/write flow intact for local
    testing without real API credits.
    """
    session_service, memory_service = places_agent_core.initialize_services()
    session_id = places_agent_core.generate_session_id()

    app_name = "PlacesSearchApp"
    session, _created_new = await places_agent_core.create_or_retrieve_session(
        session_service=session_service,
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )

    query_content = types.Content(role="user", parts=[types.Part(text=prompt)])

    final_text = ""
    last_error: Optional[BaseException] = None
    for idx, model_name in enumerate(model_candidates, start=1):
        try:
            if idx > 1:
                safe_model_name = _sanitize_log_str(model_name)
                logger.info(f"Switching model to '{safe_model_name}' and retrying")

            agent = initialize_multi_agent_system(model_name=model_name)
            agent_app = create_app(agent, plugins=[LoggingPlugin()])
            runner = Runner(
                app=agent_app,
                session_service=session_service,
                memory_service=memory_service,
            )

            final_text = await _run_runner_collect_final_text(
                runner=runner,
                user_id=user_id,
                session_id=session.id,
                query_content=query_content,
                max_attempts=3,
                initial_delay_s=2.0,
                backoff_factor=2.0,
            )
            last_error = None
            break
        except Exception as e:
            last_error = e
            if not _is_transient_model_error(e):
                raise
            continue

    if last_error is not None:
        logger.exception("LLM request failed after retries/model fallback")
        if _is_quota_exhausted_error(last_error):
            return (
                "Gemini API quota is exceeded (HTTP 429 RESOURCE_EXHAUSTED). "
                "Try setting GEMINI_MODEL/GEMINI_FALLBACK_MODEL to a model that has available quota."
            )
        return (
            "The AI model is temporarily overloaded (HTTP 503). "
            "Please try again later, or configure GEMINI_MODEL / GEMINI_FALLBACK_MODEL."
        )

    return final_text


async def search_places(
    city_name: str,
    preferences: str,
    topic: Optional[str] = None,
    user_id: str = "default_user",
) -> str:
    """
    Search for nearby places based on city and preferences.

    Flow:
      1. If `topic` is set → read accumulated preferences from Postgres.
         On DB failure, log the error and continue with empty history.
      2. Build the prompt (injecting past preferences when present).
      3. Call the LLM pipeline — mocked when the dev dummy key is configured.
      4. If `topic` is set → append the new preference to Postgres.
         On DB failure, log the error; the user still gets their results.

    When `topic` is None, the database is never touched.
    """
    city_name_clean = _sanitize_log_str(city_name)
    preferences_clean = _sanitize_log_str(preferences)
    topic_clean = _sanitize_log_str(topic) if topic is not None else "transient"
    logger.info(
        f"Searching in {city_name_clean} for '{preferences_clean}' (topic: {topic_clean})"
    )

    # 1) Retrieve persisted preferences for this topic (empty when anonymous/new/DB-down)
    past_preferences = ""
    if topic:
        try:
            past_preferences = await topic_preferences.get_preferences(topic)
        except Exception:
            logger.exception(
                f"Failed to load past preferences for topic '{topic_clean}'; "
                "continuing with empty context"
            )

    # 2) Build prompt — past preferences are injected as taste context when available
    prompt = _build_search_prompt(city_name, preferences, past_preferences)

    # 3) LLM call — mocked when the dev dummy key is set, so the DB flow is still exercised
    model_candidates = _get_model_candidates()
    if os.environ.get("GOOGLE_API_KEY") == _DEV_DUMMY_KEY:
        await asyncio.sleep(0.1)
        final_text = _build_dummy_llm_response(city_name, preferences, past_preferences)
    else:
        final_text = await _invoke_llm_pipeline(
            prompt=prompt,
            user_id=user_id,
            model_candidates=model_candidates,
        )

    # 4) Persist new preference bullet for this topic
    if topic and final_text:
        try:
            await topic_preferences.append_and_maybe_summarize(
                topic=topic,
                new_preference=preferences,
                model_name=model_candidates[0],
            )
        except Exception:
            logger.exception(f"Failed to persist preferences for topic '{topic_clean}'")

    return final_text


# ============================================================================
# FastAPI Application (Cloud Run entry point)
# ============================================================================

_PROXY_AUTH_TOKEN = os.environ.get("PROXY_AUTH_TOKEN", "")
_TURNSTILE_SECRET_KEY = os.environ.get("TURNSTILE_SECRET_KEY", "")
_TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


class SearchRequest(BaseModel):
    city: str
    preferences: str
    topic: Optional[str] = None
    turnstile_token: str


def _verify_proxy_auth(request: Request) -> None:
    """Validate X-Proxy-Auth header. Fail-closed if token is not configured."""
    if not _PROXY_AUTH_TOKEN:
        logger.error("PROXY_AUTH_TOKEN not configured — rejecting request")
        raise HTTPException(status_code=500, detail="Server misconfiguration")
    header_value = request.headers.get("X-Proxy-Auth", "")
    if not hmac.compare_digest(header_value, _PROXY_AUTH_TOKEN):
        raise HTTPException(status_code=403, detail="Forbidden")


async def _verify_turnstile(token: str) -> None:
    """Server-side Cloudflare Turnstile verification. Rejects missing, invalid,
    duplicate, and expired tokens."""
    if not _TURNSTILE_SECRET_KEY:
        logger.error("TURNSTILE_SECRET_KEY not configured — rejecting request")
        raise HTTPException(status_code=500, detail="Server misconfiguration")
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                _TURNSTILE_VERIFY_URL,
                data={"secret": _TURNSTILE_SECRET_KEY, "response": token},
            )
        result = resp.json()
    except httpx.HTTPError:
        logger.exception("Turnstile verification request failed")
        raise HTTPException(status_code=502, detail="Verification service unavailable")
    if not result.get("success"):
        error_codes = result.get("error-codes", [])
        logger.warning("Turnstile verification failed: %s", error_codes)
        raise HTTPException(status_code=403, detail="Turnstile verification failed")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/search")
async def search_endpoint(request: Request, body: SearchRequest) -> dict:
    _verify_proxy_auth(request)
    await _verify_turnstile(body.turnstile_token)
    result = await search_places(
        city_name=body.city,
        preferences=body.preferences,
        topic=body.topic,
    )
    return {"result": result}
