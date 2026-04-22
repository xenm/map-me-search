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
from google.adk.sessions import InMemorySessionService
from google.adk.tools import AgentTool, FunctionTool, google_search
from google.genai import types

from .scoring_tools import calculate_distance_score, get_place_category_boost

try:
    from google.genai import errors as genai_errors
except ImportError:  # pragma: no cover
    genai_errors = None


def is_transient_model_error(exc: BaseException) -> bool:
    if genai_errors is not None and isinstance(
        exc, getattr(genai_errors, "ServerError", ())
    ):
        status_code = getattr(exc, "status_code", None)
        if status_code == 503:
            return True

    msg = str(exc).lower()
    if "503" in msg and ("overloaded" in msg or "unavailable" in msg):
        return True
    if "the model is overloaded" in msg:
        return True
    if "429" in msg and ("resource_exhausted" in msg or "quota" in msg):
        return True
    return False


def is_quota_exhausted_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    if "429" in msg and ("resource_exhausted" in msg or "quota" in msg):
        return True
    return False


def get_model_candidates() -> list[str]:
    primary = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
    fallback = os.environ.get("GEMINI_FALLBACK_MODEL", "gemini-2.5-flash-lite").strip()
    candidates = [primary] if primary else ["gemini-2.5-flash"]
    if fallback and fallback not in candidates:
        candidates.append(fallback)
    return candidates


async def run_runner_collect_final_text(
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
            if is_quota_exhausted_error(e):
                raise
            if not is_transient_model_error(e) or attempt >= max_attempts:
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
        announce(
            "\n🔧 Initializing Enhanced Multi-Agent System with Sessions & Memory..."
        )

    model_name = (
        model_name or os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"
    ).strip()

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
You are a specialized research agent. Your ONLY job is to use the `google_search` tool
to find real, currently-operating places that match the user's city and preferences.

Inputs in the user prompt:
- `City` and `Preferences` — the primary intent; always drives the search.
- Optional `Taste hints` — phrases from earlier searches on the same Topic.
  They are only preference phrases, not past places or past cities. Use them
  as soft signals (style, vibe, diet, price range) only when they fit the
  current Preferences; otherwise ignore them.

**Hard requirements:**
- Perform real `google_search` queries. Do not invent places from memory.
- Return exactly 5–7 distinct, real places.
- Prefer specific venues over generic neighborhoods.
- No duplicates, no closed/permanently-shut venues if you can tell.

**Output format (strict):** A plain-text structured list, one block per place,
blocks separated by a single blank line. Each block MUST contain exactly these
labeled fields, one per line:

Name: <official place name>
Type: <restaurant | cafe | museum | gallery | park | bar | shop | viewpoint | ...>
Neighborhood: <area or district, or "unknown">
DistanceKm: <approximate km from city center as a number, or "unknown">
Description: <1–2 sentence factual description>
WhyMatch: <1 sentence tying it to the user's preferences / taste signals>

Do not add commentary before or after the list. The next agent will parse these
fields, so stay on-format.""",
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
You are a filtering and ranking specialist. The previous agent produced a structured
list of candidate places (fields: Name, Type, Neighborhood, DistanceKm, Description,
WhyMatch). Parse it and rank them.

Procedure:
1. For each place, call `get_place_category_boost(category=Type, preferences=...)`
   to get a category-match boost.
2. If `DistanceKm` is a number, call `calculate_distance_score(distance_km=...)`
   for a location score. If it is "unknown", skip distance and note it.
3. Use the `CalculationAgent` to produce Python code that combines the available
   scores into a final rating on a **1–10 scale** (weight category heavier than
   distance; if distance is unknown, use category boost + relevance to preferences).
4. Always check the `"status"` field in tool responses; skip or warn on errors.
5. Select the top **5** places and sort by final score descending.

**Output format (strict)** — the formatter will parse it. One block per place,
blocks separated by a single blank line. No prose outside the blocks:

Name: <name>
Type: <type>
Neighborhood: <area or "unknown">
DistanceKm: <number or "unknown">
Score: <final 1–10 rating, one decimal allowed>
ScoreBreakdown: category=<n>, distance=<n or "n/a">
Description: <keep the factual sentence from research>
WhyMatch: <refined one-sentence reason this place suits the user>""",
        "tools": [
            FunctionTool(func=calculate_distance_score),
            FunctionTool(func=get_place_category_boost),
            AgentTool(agent=calculation_agent),
        ],
        "output_key": "filtered_results",
    }
    if after_agent_callback is not None:
        filter_agent_kwargs["after_agent_callback"] = after_agent_callback

    filter_agent = LlmAgent(**filter_agent_kwargs)
    if announce is not None:
        announce(
            "✅ FilterAgent created (with custom FunctionTools + AgentTool + Memory)"
        )

    formatter_agent = LlmAgent(
        name="FormatterAgent",
        model=Gemini(
            model=model_name,
            retry_options=retry_config,
        ),
        instruction="""
You are the presentation specialist. You receive the ranked, structured list from
the FilterAgent and turn it into the final user-facing answer.

**Output contract (must follow exactly):**

1. Output **valid GitHub-Flavored Markdown ONLY** — no HTML, no code fences around
   the whole response, no leading/trailing commentary like "Here is your guide:".
2. The output will be rendered inside a narrow centered card. Keep lines short,
   avoid wide tables, and rely on headings + bullets for rhythm.
3. Use a Markdown horizontal rule (`---`) on its own line as the separator
   between places. Horizontal rules are the ONLY reliable visual separator in
   the target UI — blank lines alone will be collapsed.
4. Emojis are encouraged but used sparingly: one in the H3 heading, optionally
   one inline per bullet. Never more than ~2 emojis per place.

**Exact structure to produce:**

    ## ✨ Top Picks in <City>

    *A short, warm one-sentence intro tied to the user's preferences.*

    ---

    ### 📍 1. <Place Name> — *<Type>*

    **⭐ Score:** <score>/10 &nbsp;·&nbsp; **📍 Area:** <neighborhood>
    <when distance is known, append> &nbsp;·&nbsp; **🚶 ~<n> km from center**

    <Description sentence(s) — plain prose, 2–3 sentences max.>

    **Why you'll like it:** <one sentence tying to user's preferences>

    ---

    ### 📍 2. <Place Name> — *<Type>*
    ... (same block) ...

    ---

    ### 📍 3. <Place Name> — *<Type>*
    ... etc. for all 5 places ...

    ---

    ### 🎯 In short

    One or two friendly sentences summarizing the picks (e.g. "Start with X for
    the vibe, then head to Y for…").

**Strict rules:**
- Always include a `---` line BEFORE the first place, BETWEEN every pair of
  places, and BEFORE the closing "In short" section.
- Never place two `###` headings back-to-back without a `---` in between.
- If the filter provided a `ScoreBreakdown`, you may append it as small italic
  text on its own line under the score line, e.g. *category 3 · distance 8*.
- If a field is "unknown", omit that fragment entirely rather than printing
  "unknown".
- Do not invent facts not present in the filtered input.""",
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
        announce(
            "📋 Pipeline: ResearchAgent → FilterAgent (with tools) → FormatterAgent"
        )
        announce("🔧 Custom Tools: calculate_distance_score, get_place_category_boost")
        announce("🤖 Agent Tools: CalculationAgent (code executor)")

    return root_agent


def initialize_services() -> Tuple[Any, Any]:
    """Return in-memory session and memory services.

    Topic persistence is managed externally via the topic_preferences module.
    """
    return InMemorySessionService(), InMemoryMemoryService()


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


def generate_session_id() -> str:
    """Return a unique session ID for a single request."""
    return str(uuid.uuid4())


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
            raise RuntimeError(
                f"Failed to create or retrieve session: {retrieve_error}"
            )
