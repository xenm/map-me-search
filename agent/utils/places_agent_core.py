import os
import uuid
import asyncio
from typing import Any, Callable, Dict, Optional, Tuple

from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.memory import InMemoryMemoryService
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService, InMemorySessionService
from google.adk.tools import AgentTool, FunctionTool, google_search, preload_memory
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from .scoring_tools import calculate_distance_score, get_place_category_boost

try:
    from google.genai import errors as genai_errors
except ImportError:  # pragma: no cover
    genai_errors = None


def save_user_preferences(tool_context: ToolContext, city: str, preferences: str) -> Dict[str, Any]:
    tool_context.state["user:last_city"] = city
    tool_context.state["user:last_preferences"] = preferences
    return {"status": "success", "message": f"Saved preferences for {city}"}


def retrieve_user_preferences(tool_context: ToolContext) -> Dict[str, Any]:
    city = tool_context.state.get("user:last_city", "Not set")
    preferences = tool_context.state.get("user:last_preferences", "Not set")

    return {
        "status": "success",
        "city": city,
        "preferences": preferences,
    }


def _is_transient_model_error(exc: BaseException) -> bool:
    if genai_errors is not None and isinstance(exc, getattr(genai_errors, "ServerError", ())):
        try:
            status_code = getattr(exc, "status_code", None)
            if status_code == 503:
                return True
        except Exception:
            pass

    msg = str(exc).lower()
    if "503" in msg and ("overloaded" in msg or "unavailable" in msg):
        return True
    if "the model is overloaded" in msg:
        return True
    if "429" in msg and ("resource_exhausted" in msg or "quota" in msg):
        return True
    return False


def _is_quota_exhausted_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    if "429" in msg and ("resource_exhausted" in msg or "quota" in msg):
        return True
    return False


def _get_model_candidates() -> list[str]:
    primary = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
    fallback = os.environ.get("GEMINI_FALLBACK_MODEL", "gemini-2.5-flash-lite").strip()
    candidates = [primary] if primary else ["gemini-2.5-flash"]
    if fallback and fallback not in candidates:
        candidates.append(fallback)
    return candidates


async def _run_runner_collect_final_text(
    runner: Runner,
    user_id: str,
    session_id: str,
    query_content: types.Content,
    max_attempts: int,
    initial_delay_s: float,
    backoff_factor: float,
    on_retry: Optional[Callable[[int, int, float], None]] = None,
) -> str:
    attempt = 0
    delay = initial_delay_s
    last_exc: Optional[BaseException] = None

    while attempt < max_attempts:
        attempt += 1
        try:
            final_text = ""
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=query_content,
            ):
                if event.is_final_response() and event.content and event.content.parts:
                    text = event.content.parts[0].text
                    if text and text != "None":
                        final_text = text
            return final_text
        except Exception as e:
            last_exc = e
            if _is_quota_exhausted_error(e):
                raise
            if not _is_transient_model_error(e) or attempt >= max_attempts:
                raise

            if on_retry is not None:
                on_retry(attempt, max_attempts, delay)
            await asyncio.sleep(delay)
            delay *= backoff_factor

    if last_exc:
        raise last_exc
    return ""


def initialize_multi_agent_system(
    model_name: Optional[str] = None,
    after_agent_callback: Optional[Callable[..., Any]] = None,
    announce: Optional[Callable[[str], None]] = None,
):
    if announce is not None:
        announce("\n🔧 Initializing Enhanced Multi-Agent System with Sessions & Memory...")

    model_name = (model_name or os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash").strip()

    retry_config = types.HttpRetryOptions(
        attempts=5,
        exp_base=7,
        initial_delay=1,
        http_status_codes=[500, 503, 504],
    )

    research_agent = LlmAgent(
        name="ResearchAgent",
        model=Gemini(
            model=model_name,
            retry_options=retry_config,
        ),
        instruction="""
You are a specialized research agent. Your only job is to use the google_search tool 
    to find relevant places, attractions, restaurants, and activities.

Search for 5-7 specific places that match the user's interests. For each place, gather:
- Name of the place
- Type (restaurant, museum, park, etc.)
- Brief description
- Approximate distance from city center (if available)
- Why it matches the preferences

Present your findings as structured data with clear details for each place.""",
        tools=[google_search],
        output_key="research_findings",
    )
    if announce is not None:
        announce("✅ ResearchAgent created (with google_search tool)")

    calculation_agent = LlmAgent(
        name="CalculationAgent",
        model=Gemini(
            model=model_name,
            retry_options=retry_config,
        ),
        instruction="""You are a specialized calculator that ONLY responds with Python code.
        
Your task is to take scoring data and calculate final relevance scores.

**RULES:**
1. Your output MUST be ONLY a Python code block
2. Do NOT write any text before or after the code
3. The Python code MUST calculate the result
4. The Python code MUST print the final result to stdout
5. You are PROHIBITED from performing the calculation yourself

Generate Python code that calculates weighted scores based on the provided data.""",
        code_executor=BuiltInCodeExecutor(),
        output_key="calculation_results",
    )
    if announce is not None:
        announce("✅ CalculationAgent created (with BuiltInCodeExecutor)")

    filter_agent_kwargs: Dict[str, Any] = {
        "name": "FilterAgent",
        "model": Gemini(
            model=model_name,
            retry_options=retry_config,
        ),
        "instruction": """
You are a filtering and ranking specialist. Review the research findings from the previous agent.

Your task:
1. For each place, use get_place_category_boost() to calculate category relevance
2. If distance data is available, use calculate_distance_score() for location scoring
3. Use the CalculationAgent to generate Python code that combines scores into a final rating (1-10)
4. Check "status" field in each tool response for errors
5. Select the top 5 highest-scoring places
6. Organize by final score (highest first)

Output a curated list with:
- Place name
- Final score (1-10)
- Score breakdown (category boost, distance score, etc.)
- Reasoning for selection""",
        "tools": [
            FunctionTool(func=calculate_distance_score),
            FunctionTool(func=get_place_category_boost),
            FunctionTool(func=save_user_preferences),
            FunctionTool(func=retrieve_user_preferences),
            AgentTool(agent=calculation_agent),
            preload_memory,
        ],
        "output_key": "filtered_results",
    }
    if after_agent_callback is not None:
        filter_agent_kwargs["after_agent_callback"] = after_agent_callback

    filter_agent = LlmAgent(**filter_agent_kwargs)
    if announce is not None:
        announce("✅ FilterAgent created (with custom FunctionTools + AgentTool + Memory)")

    formatter_agent = LlmAgent(
        name="FormatterAgent",
        model=Gemini(
            model=model_name,
            retry_options=retry_config,
        ),
        instruction="""
You are a presentation specialist. Review the filtered and scored places from the previous agent.

Create a beautifully formatted recommendation guide with:

📍 For each place:
   • Name and type (bold)
   • Final relevance score (⭐ 1-10)
   • Clear description (2-3 sentences)
   • Why it's perfect for the user's preferences
   • Score breakdown (if available)

Make it engaging, easy to read, and helpful. Use emojis strategically. 
End with a friendly summary of the recommendations.""",
        output_key="final_recommendations",
    )
    if announce is not None:
        announce("✅ FormatterAgent created")

    root_agent = SequentialAgent(
        name="EnhancedPlacesSearchPipeline",
        sub_agents=[research_agent, filter_agent, formatter_agent],
    )

    if announce is not None:
        announce("\n✅ Enhanced Multi-Agent Pipeline created")
        announce("📋 Pipeline: ResearchAgent → FilterAgent (with tools) → FormatterAgent")
        announce("🔧 Custom Tools: calculate_distance_score, get_place_category_boost")
        announce("🤖 Agent Tools: CalculationAgent (code executor)")
        announce("💾 Session State: save_user_preferences, retrieve_user_preferences")
        announce("🧠 Memory: preload_memory for long-term recall")

    return root_agent


def initialize_services(
    topic: Optional[str] = None,
    db_url: str = "sqlite:///places_search_sessions.db",
) -> Tuple[Any, Any, bool, Optional[BaseException]]:
    if topic:
        try:
            session_service = DatabaseSessionService(db_url=db_url)
            using_database = True
            db_error: Optional[BaseException] = None
        except Exception as e:
            session_service = InMemorySessionService()
            using_database = False
            db_error = e
    else:
        session_service = InMemorySessionService()
        using_database = False
        db_error = None

    memory_service = InMemoryMemoryService()
    return session_service, memory_service, using_database, db_error


def create_app(
    root_agent,
    plugins=None,
    compaction_interval: int = 4,
    overlap_size: int = 1,
) -> App:
    return App(
        name="PlacesSearchApp",
        root_agent=root_agent,
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=compaction_interval,
            overlap_size=overlap_size,
        ),
        plugins=plugins or [],
    )


def generate_session_id(user_id: str, topic: Optional[str]) -> str:
    if topic:
        return f"{user_id}::{topic}"
    return f"{user_id}::temp::{uuid.uuid4()}"


async def create_or_retrieve_session(
    session_service,
    app_name: str,
    user_id: str,
    session_id: str,
) -> Tuple[Any, bool]:
    try:
        session = await session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
        )
        return session, True
    except (ValueError, RuntimeError, ConnectionError):
        try:
            session = await session_service.get_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
            )
            return session, False
        except (ValueError, RuntimeError, ConnectionError) as retrieve_error:
            raise RuntimeError(f"Failed to create or retrieve session: {retrieve_error}")
