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
from google.adk.tools.tool_context import ToolContext  # noqa: E402
from google.genai import types  # noqa: E402
from typing import Any, Dict, Optional  # noqa: E402
import hmac  # noqa: E402

import httpx  # noqa: E402
from fastapi import FastAPI, Request, HTTPException  # noqa: E402
from pydantic import BaseModel  # noqa: E402

try:
    from .utils import places_agent_core
except ImportError:
    from utils import places_agent_core

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
    return places_agent_core._is_transient_model_error(exc)


def _is_quota_exhausted_error(exc: BaseException) -> bool:
    return places_agent_core._is_quota_exhausted_error(exc)


def _get_model_candidates() -> list[str]:
    return places_agent_core._get_model_candidates()


async def _run_runner_collect_final_text(
    runner: Runner,
    user_id: str,
    session_id: str,
    query_content: types.Content,
    max_attempts: int,
    initial_delay_s: float,
    backoff_factor: float,
) -> str:
    def _on_retry(attempt: int, max_attempts: int, delay: float) -> None:
        logger.warning(
            f"Model temporarily unavailable (503). Retrying in {delay:.1f}s... ({attempt}/{max_attempts})"
        )

    return await places_agent_core._run_runner_collect_final_text(
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
# Custom Function Tools
# ============================================================================
# NOTE: calculate_distance_score and get_place_category_boost are now imported from utils.scoring_tools


def save_user_preferences(
    tool_context: ToolContext, city: str, preferences: str
) -> Dict[str, Any]:
    """Save user's city and preferences to session state."""
    return places_agent_core.save_user_preferences(
        tool_context=tool_context,
        city=city,
        preferences=preferences,
    )


def retrieve_user_preferences(tool_context: ToolContext) -> Dict[str, Any]:
    """Retrieve user's previously saved preferences from session state."""
    return places_agent_core.retrieve_user_preferences(tool_context=tool_context)


# ============================================================================
# Agent System Initialization
# ============================================================================


def initialize_multi_agent_system(model_name: Optional[str] = None):
    """Initialize the multi-agent system for places search."""
    logger.info("Initializing Multi-Agent System...")

    root_agent = places_agent_core.initialize_multi_agent_system(model_name=model_name)

    logger.info("Multi-Agent Pipeline initialized successfully")
    return root_agent


def initialize_services(topic: Optional[str] = None):
    """
    Initialize Session and Memory services based on topic.

    Args:
        topic: If provided, use DatabaseSessionService for persistence.
               If None/empty, use InMemorySessionService for transient session.

    Returns:
        Tuple of (session_service, memory_service)
    """
    topic_str = topic if topic is not None else "None (transient)"
    topic_str = topic_str.replace("\r", "").replace("\n", "")
    logger.info(f"Initializing services with topic: {topic_str}")

    session_service, memory_service, using_database, db_error = (
        places_agent_core.initialize_services(topic)
    )

    if topic:
        if using_database:
            topic_sanitized = topic.replace("\r", "").replace("\n", "")
            logger.info(
                f"DatabaseSessionService initialized for topic '{topic_sanitized}'"
            )
        else:
            logger.warning(
                f"DatabaseSessionService failed: {db_error}, falling back to InMemory"
            )
    else:
        logger.info("InMemorySessionService initialized (transient mode)")

    logger.info("InMemoryMemoryService initialized")
    return session_service, memory_service


def create_app(root_agent, plugins=None):
    """Create App with Events Compaction for context optimization."""
    app = places_agent_core.create_app(
        root_agent=root_agent,
        plugins=plugins,
        compaction_interval=4,
        overlap_size=1,
    )
    logger.info("App created with EventsCompactionConfig")
    return app


# Sanitize strings before logging to prevent log injection
def _sanitize_log_str(s):
    if s is None:
        return ""
    return str(s).replace("\r", "").replace("\n", "")


async def search_places(
    city_name: str,
    preferences: str,
    topic: Optional[str] = None,
    user_id: str = "default_user",
) -> str:
    """
    Search for nearby places based on city and preferences.

    Args:
        city_name: The name of the city to search in
        preferences: What the user likes
        topic: Optional topic for session persistence. If None, uses transient session.
        user_id: User identifier for session management

    Returns:
        String with formatted recommendations
    """
    city_name_clean = _sanitize_log_str(city_name)
    preferences_clean = _sanitize_log_str(preferences)
    topic_clean = _sanitize_log_str(topic) if topic is not None else "transient"
    logger.info(
        f"Searching in {city_name_clean} for '{preferences_clean}' (topic: {topic_clean})"
    )

    # Dev stub — return canned response without calling LLM
    if os.environ.get("GOOGLE_API_KEY") == _DEV_DUMMY_KEY:
        await asyncio.sleep(5)
        return (
            f"## Dev Stub Results for {city_name}\n\n"
            f"**Preferences:** {preferences}\n\n"
            "1. **The Golden Cafe** — Cozy spot with great espresso and pastries. "
            "Perfect for a relaxed morning.\n"
            "2. **Riverside Park** — Beautiful walking trails along the river. "
            "Great for outdoor activities.\n"
            "3. **The Art Quarter** — Vibrant neighborhood with street art, "
            "galleries, and independent boutiques.\n\n"
            "*This is a dev stub response. Set a real `GOOGLE_API_KEY` in "
            "`agent/.env` for live results.*"
        )

    # Initialize services
    session_service, memory_service = initialize_services(topic)

    # Generate session ID based on topic
    session_id = places_agent_core.generate_session_id(user_id=user_id, topic=topic)

    model_candidates = _get_model_candidates()

    # Create or retrieve session
    app_name = "PlacesSearchApp"
    session, _created_new = await places_agent_core.create_or_retrieve_session(
        session_service=session_service,
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )

    # Create prompt
    prompt = (
        f"Find nearby places in {city_name} for someone who likes {preferences}. "
        f"Provide specific recommendations with names, brief descriptions, and why they would enjoy them."
    )

    query_content = types.Content(role="user", parts=[types.Part(text=prompt)])

    final_text = ""
    last_error: Optional[BaseException] = None
    for idx, model_name in enumerate(model_candidates, start=1):
        try:
            if idx > 1:
                safe_model_name = (
                    model_name.replace("\r", "").replace("\n", "")
                    if isinstance(model_name, str)
                    else str(model_name).replace("\r", "").replace("\n", "")
                )
                logger.info(f"Switching model to '{safe_model_name}' and retrying")

            agent = initialize_multi_agent_system(model_name=model_name)
            app = create_app(agent, plugins=[LoggingPlugin()])
            runner = Runner(
                app=app,
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

    # Save to memory if topic is provided
    if topic:
        try:
            await memory_service.add_session_to_memory(session)
            logger.info("Session saved to memory")
        except (ValueError, RuntimeError, ConnectionError) as e:
            logger.warning(f"Memory save failed: {e}")

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
