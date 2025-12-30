"""
AI-Powered Nearby Places Search
Uses Google Agent Development Kit (ADK) to search for places based on user preferences

Day 4 Enhancement: Added Observability (Logging, Traces, Metrics) and Evaluation
"""

import os
import sys
import asyncio
import logging
import uuid
from typing import Any, Dict, Optional
from dotenv import load_dotenv

try:
    from google.genai import errors as genai_errors
except ImportError:  # pragma: no cover
    genai_errors = None

def sanitize_for_log(s: Optional[str]) -> str:
    """Remove newlines and carriage returns from user input for safe logging."""
    if s is None:
        return ""
    return s.replace('\r\n', '').replace('\n', '').replace('\r', '')
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService, InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.tools import google_search, AgentTool, FunctionTool, load_memory, preload_memory
from google.adk.tools.tool_context import ToolContext
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.genai import types
from agent.utils.scoring_tools import calculate_distance_score, get_place_category_boost
from agent.utils import places_agent_core

# Day 4a: Custom observability plugin (optional)
try:
    from observability_plugin import MetricsTrackingPlugin
    METRICS_PLUGIN_AVAILABLE = True
except ImportError:
    METRICS_PLUGIN_AVAILABLE = False
    logging.warning("⚠️ MetricsTrackingPlugin not available")

# Global metrics plugin instance for summary retrieval
_metrics_plugin_instance = None


def configure_logging(log_level=logging.INFO, log_file="places_search.log"):
    """
    Configure logging for observability (Day 4a)
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file
    """
    # Clean up old log file
    if os.path.exists(log_file):
        os.remove(log_file)
        print(f"🧹 Cleaned up old log file: {log_file}")
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(filename)s:%(lineno)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Also print to console
        ]
    )
    
    print(f"✅ Logging configured: Level={logging.getLevelName(log_level)}, File={log_file}")
    return log_file


def check_python_version():
    """Check Python version and warn if outdated."""
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    
    if sys.version_info < (3, 14):
        logging.warning(
            f"⚠️ Python {python_version} detected. Python 3.14+ recommended for full compatibility."
        )
        logging.warning("⚠️ Some features (like DatabaseSessionService) may not work correctly.")
        print(f"⚠️ Warning: Python {python_version} detected")
        print("⚠️ Python 3.14+ is recommended for full compatibility")
        print("⚠️ The app will work with limited features (sessions won't persist)\n")


def load_environment():
    """Load environment variables from .env file"""
    load_dotenv()
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION")
    api_key = os.environ.get("GOOGLE_API_KEY")

    if api_key:
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "FALSE"
        print("✅ Using Google AI Studio authentication (API key).")
        return api_key

    if project and location:
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
        print("✅ Using Vertex AI authentication (ADC).")
        return None

    raise ValueError(
        "❌ No valid authentication configuration found.\n"
        "Configure one of the following:\n"
        "1) Vertex AI (recommended): GOOGLE_CLOUD_PROJECT + GOOGLE_CLOUD_LOCATION and authenticate via ADC (e.g. `gcloud auth application-default login`)\n"
        "2) Google AI Studio: GOOGLE_API_KEY\n"
    )


# Custom Function Tools - Following ADK Best Practices
# NOTE: calculate_distance_score and get_place_category_boost are now imported from utils.scoring_tools


# Session State Management Tools (Day 3 - Part 1)

def save_user_preferences(tool_context: ToolContext, city: str, preferences: str) -> Dict[str, Any]:
    """Save user's city and preferences to session state for reuse across conversation.
    
    Args:
        tool_context: Context providing access to session state
        city: City name the user is searching in
        preferences: User's stated preferences
        
    Returns:
        Dictionary with status.
        Success: {"status": "success"}
    """
    return places_agent_core.save_user_preferences(
        tool_context=tool_context,
        city=city,
        preferences=preferences,
    )


def retrieve_user_preferences(tool_context: ToolContext) -> Dict[str, Any]:
    """Retrieve user's previously saved city and preferences from session state.
    
    Args:
        tool_context: Context providing access to session state
        
    Returns:
        Dictionary with status and data.
        Success: {"status": "success", "city": "...", "preferences": "..."}
    """
    return places_agent_core.retrieve_user_preferences(tool_context=tool_context)


# Callback for automatic memory storage (Day 3 - Part 2)
async def auto_save_to_memory(callback_context):
    """Automatically save session to memory after each agent turn."""
    try:
        await callback_context._invocation_context.memory_service.add_session_to_memory(
            callback_context._invocation_context.session
        )
        print("💾 Session automatically saved to memory")
    except Exception as e:
        print(f"⚠️ Memory save failed: {e}")


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
        print(
            f"\n⚠️ Model temporarily unavailable (503). Retrying in {delay:.1f}s... ({attempt}/{max_attempts})"
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


def initialize_multi_agent_system(model_name: Optional[str] = None):
    """Initialize and configure the enhanced multi-agent system with Sessions and Memory"""
    return places_agent_core.initialize_multi_agent_system(
        model_name=model_name,
        after_agent_callback=auto_save_to_memory,
        announce=print,
    )


def initialize_services(topic: Optional[str] = None):
    """Initialize Session and Memory services based on topic.
    
    Args:
        topic: Optional topic for session persistence. If None/empty, uses transient session.
               If None/empty, use InMemorySessionService for transient session.
    
    Returns:
        Tuple of (session_service, memory_service)
    """
    print("\n🗄️ Initializing Services...")

    session_service, memory_service, using_database, db_error = places_agent_core.initialize_services(topic)

    if topic:
        db_url = "sqlite:///places_search_sessions.db"
        if using_database:
            print(f"✅ DatabaseSessionService initialized for topic '{topic}': {db_url}")
            logging.info(f"DatabaseSessionService initialized for topic '{sanitize_for_log(topic)}': {db_url}")
        else:
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            logging.warning(f"⚠️ DatabaseSessionService failed (Python {python_version}): {db_error}")
            logging.warning("⚠️ Falling back to InMemorySessionService (sessions won't persist)")
            print(f"⚠️ DatabaseSessionService failed: {db_error}")
            print(f"💡 Tip: Upgrade to Python 3.14+ (currently using Python {python_version})")
            print("✅ InMemorySessionService initialized (fallback mode)")
            logging.info("InMemorySessionService initialized as fallback")
    else:
        print("🚀 Transient Mode: Using InMemorySessionService (No DB write)")
        logging.info("InMemorySessionService initialized (transient mode - no topic)")

    print("✅ InMemoryMemoryService initialized")
    return session_service, memory_service


def initialize_plugins(
    enable_logging_plugin: bool = True,
    enable_metrics_plugin: bool = True,
):
    """Initialize observability plugins (logging + metrics)."""
    global _metrics_plugin_instance

    plugins = []
    if enable_logging_plugin:
        plugins.append(LoggingPlugin())
        print("✅ LoggingPlugin enabled")
    else:
        print("⚠️ LoggingPlugin disabled")

    _metrics_plugin_instance = None
    if enable_metrics_plugin and METRICS_PLUGIN_AVAILABLE:
        _metrics_plugin_instance = MetricsTrackingPlugin()
        plugins.append(_metrics_plugin_instance)
        print("✅ MetricsTrackingPlugin enabled")
    elif enable_metrics_plugin and not METRICS_PLUGIN_AVAILABLE:
        print("⚠️ MetricsTrackingPlugin requested but not available")
    else:
        print("⚠️ MetricsTrackingPlugin disabled")

    return plugins


def create_app_with_compaction(root_agent, plugins=None):
    """Create App with Events Compaction for context optimization.
    
    Args:
        root_agent: The root agent for the app
        plugins: List of plugins to add to the app (Day 4a)
    """
    print("\n📦 Creating App with Context Compaction...")

    app = places_agent_core.create_app(
        root_agent=root_agent,
        plugins=plugins,
        compaction_interval=4,
        overlap_size=1,
    )
    
    print("✅ App created with EventsCompactionConfig")
    print("   - Compaction interval: 4 turns")
    print("   - Overlap size: 1 turn")
    if plugins:
        print(f"   - Plugins: {len(plugins)} enabled")
    
    return app


def generate_session_id(user_id: str, topic: Optional[str]) -> str:
    """Generate session ID based on topic for persistence or transient use."""
    return places_agent_core.generate_session_id(user_id=user_id, topic=topic)


async def create_or_retrieve_session(session_service, app_name: str, user_id: str, session_id: str):
    """Create new session or retrieve existing one."""
    session, created_new = await places_agent_core.create_or_retrieve_session(
        session_service=session_service,
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )
    print("✅ New session created" if created_new else "✅ Existing session retrieved")
    return session


async def search_places(
    city_name: str, 
    preferences: str, 
    topic: Optional[str] = None,
    user_id: str = "default_user",
    enable_logging_plugin: bool = True,
    enable_metrics_plugin: bool = True
):
    """
    Search for nearby places based on city and preferences with session persistence
    
    Args:
        city_name: The name of the city to search in
        preferences: What the user likes (e.g., "coffee shops", "museums", "parks")
        topic: Optional topic for session persistence. If None/empty, uses transient session.
               - Empty: InMemorySessionService (no history saved)
               - With topic: DatabaseSessionService (history persists for this topic)
        user_id: User identifier for session management
        enable_logging_plugin: Enable LoggingPlugin for observability (Day 4a)
        enable_metrics_plugin: Enable MetricsTrackingPlugin for metrics (Day 4a)
    """
    global _metrics_plugin_instance
    
    # Clean topic (empty string becomes None)
    topic = topic.strip() if topic else None
    
    print(f"\n🔍 Searching for places in {city_name} based on: '{preferences}'")
    print(f"🏷️  Topic: {topic or 'None (transient session)'}")
    print("=" * 60)
    
    # Initialize Session and Memory services based on topic
    session_service, memory_service = initialize_services(topic)
    
    # Create plugins list for observability (Day 4a)
    plugins = initialize_plugins(enable_logging_plugin, enable_metrics_plugin)
    
    # Generate session ID based on topic
    session_id = generate_session_id(user_id, topic)
    
    print(f"\n📱 Session ID: {session_id}")
    
    # Create or retrieve session
    session = await create_or_retrieve_session(session_service, "PlacesSearchApp", user_id, session_id)
    
    # Create a search prompt
    prompt = (
        f"Find nearby places in {city_name} for someone who likes {preferences}. "
        f"Provide specific recommendations with names, brief descriptions, and why they would enjoy them."
    )
    
    print(f"\n📝 Prompt: {prompt}\n")
    print("🤖 AI Agent is working...\n")
    
    # Convert to ADK Content format
    query_content = types.Content(role="user", parts=[types.Part(text=prompt)])

    model_candidates = _get_model_candidates()
    final_text = ""
    last_error: Optional[BaseException] = None
    for idx, model_name in enumerate(model_candidates, start=1):
        try:
            if idx > 1:
                print(f"\n🔁 Switching model to '{model_name}' and retrying...")

            agent = initialize_multi_agent_system(model_name=model_name)
            app = create_app_with_compaction(agent, plugins=plugins)
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
        logging.exception("❌ LLM request failed after retries/model fallback")
        if _is_quota_exhausted_error(last_error):
            return (
                "Gemini API quota is exceeded (HTTP 429 RESOURCE_EXHAUSTED). "
                "This usually means your API key has no free-tier quota for that model or billing is required. "
                "Try setting GEMINI_MODEL/GEMINI_FALLBACK_MODEL to a model with available quota, "
                "or switch to Vertex AI authentication (ADC + GOOGLE_CLOUD_PROJECT/GOOGLE_CLOUD_LOCATION)."
            )
        return (
            "The AI model is temporarily unavailable (HTTP 503). "
            "Please try again in a minute, or set GEMINI_FALLBACK_MODEL in .env to a different model."
        )
    
    # Save session to memory for long-term recall (only if topic is provided)
    if topic:
        try:
            await memory_service.add_session_to_memory(session)
            print(f"\n💾 Session saved to memory for topic '{topic}'")
        except (ValueError, RuntimeError, ConnectionError) as e:
            print(f"\n⚠️ Memory save failed: {e}")
    else:
        print("\n🚀 Transient session - skipping memory save")
    
    # Day 4a: Log metrics summary if MetricsTrackingPlugin is enabled
    if _metrics_plugin_instance:
        _metrics_plugin_instance.log_metrics_summary()
    
    return final_text


def print_response(response):
    """Print the agent's response in a formatted way"""
    print("\n" + "=" * 60)
    print("🎯 FINAL RECOMMENDATIONS")
    print("=" * 60)
    print(response)
    print("=" * 60)


def get_user_input():
    """Get city name, preferences, and optional topic from the user"""
    print("\n" + "=" * 60)
    print("🗺️  AI-POWERED NEARBY PLACES SEARCH")
    print("=" * 60)
    
    city_name = input("\n📍 Enter city name: ").strip()
    preferences = input("❤️  What do you like? (e.g., coffee, museums, parks): ").strip()
    topic = input("🏷️  Topic (leave empty for transient session): ").strip()
    
    if not city_name or not preferences:
        print("❌ City and preferences are required!")
        return None, None, None
    
    return city_name, preferences, topic if topic else None


async def main():
    """Main application entry point with observability (Day 4a)"""
    try:
        # Day 4a: Configure logging first
        log_file = configure_logging(
            log_level=logging.INFO,  # Change to logging.DEBUG for detailed traces
            log_file="places_search.log"
        )
        logging.info("🚀 Application started")
        
        # Check Python version
        check_python_version()
        
        # Load environment variables
        load_environment()
        logging.info("✅ Environment loaded")
        
        # Get user input
        city_name, preferences, topic = get_user_input()
        
        if not city_name or not preferences:
            logging.warning("⚠️ User input incomplete - exiting")
            return
        
        logging.info(
            f"📍 User query: city={sanitize_for_log(city_name)}, preferences={sanitize_for_log(preferences)}, topic={sanitize_for_log(topic) if topic else 'transient'}"
        )
        
        # Search for places with optional topic
        response = await search_places(city_name, preferences, topic=topic)
        
        # Print results
        print_response(response)
        
        logging.info("✅ Search completed successfully")
        print(f"\n✅ Search completed successfully!")
        print(f"📊 Logs saved to: {log_file}")
        
    except ValueError as e:
        logging.error(f"❌ Configuration Error: {e}")
        print(f"\n❌ Configuration Error: {e}")
    except (ImportError, RuntimeError, ConnectionError) as e:
        logging.exception(f"❌ Unexpected error: {e}")
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
