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
    
    if sys.version_info < (3, 10):
        logging.warning(
            f"⚠️ Python {python_version} detected. Python 3.10+ recommended for full compatibility."
        )
        logging.warning("⚠️ Some features (like DatabaseSessionService) may not work correctly.")
        print(f"⚠️ Warning: Python {python_version} detected")
        print("⚠️ Python 3.10+ is recommended for full compatibility")
        print("⚠️ The app will work with limited features (sessions won't persist)\n")


def load_environment():
    """Load environment variables from .env file"""
    load_dotenv()
    api_key = os.environ.get("GOOGLE_API_KEY")
    
    if not api_key:
        raise ValueError(
            "❌ GOOGLE_API_KEY not found in environment variables.\n"
            "Please create a .env file with your API key.\n"
            "See .env.example for reference."
        )
    
    print("✅ Environment variables loaded successfully.")
    return api_key


# Custom Function Tools - Following ADK Best Practices

def calculate_distance_score(distance_km: float) -> dict:
    """Calculates a relevance score based on distance from city center.
    
    Args:
        distance_km: Distance in kilometers from city center
        
    Returns:
        Dictionary with status and score.
        Success: {"status": "success", "score": 10}
        Error: {"status": "error", "error_message": "Invalid distance"}
    """
    if distance_km < 0:
        return {
            "status": "error",
            "error_message": "Distance cannot be negative"
        }
    
    # Closer = higher score (10 points max)
    if distance_km <= 1:
        score = 10
    elif distance_km <= 3:
        score = 8
    elif distance_km <= 5:
        score = 6
    elif distance_km <= 10:
        score = 4
    else:
        score = 2
    
    return {
        "status": "success",
        "score": score,
        "distance_km": distance_km
    }


def get_place_category_boost(category: str, preferences: str) -> dict:
    """Calculates a boost score based on how well a category matches preferences.
    
    Args:
        category: Category of the place (e.g., "restaurant", "museum")
        preferences: User's stated preferences
        
    Returns:
        Dictionary with status and boost score.
        Success: {"status": "success", "boost": 2}
        Error: {"status": "error", "error_message": "..."}
    """
    category = category.lower()
    preferences = preferences.lower()
    
    # Direct match gives highest boost
    if category in preferences or preferences in category:
        return {"status": "success", "boost": 3, "reason": "Direct match"}
    
    # Related categories get medium boost
    food_related = ["restaurant", "cafe", "coffee", "bar", "food"]
    culture_related = ["museum", "gallery", "theater", "art"]
    outdoor_related = ["park", "garden", "hiking", "beach"]
    
    if category in food_related and any(term in preferences for term in food_related):
        return {"status": "success", "boost": 2, "reason": "Food-related match"}
    if category in culture_related and any(term in preferences for term in culture_related):
        return {"status": "success", "boost": 2, "reason": "Culture-related match"}
    if category in outdoor_related and any(term in preferences for term in outdoor_related):
        return {"status": "success", "boost": 2, "reason": "Outdoor-related match"}
    
    return {"status": "success", "boost": 0, "reason": "No special match"}


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
    tool_context.state["user:last_city"] = city
    tool_context.state["user:last_preferences"] = preferences
    return {"status": "success", "message": f"Saved preferences for {city}"}


def retrieve_user_preferences(tool_context: ToolContext) -> Dict[str, Any]:
    """Retrieve user's previously saved city and preferences from session state.
    
    Args:
        tool_context: Context providing access to session state
        
    Returns:
        Dictionary with status and data.
        Success: {"status": "success", "city": "...", "preferences": "..."}
    """
    city = tool_context.state.get("user:last_city", "Not set")
    preferences = tool_context.state.get("user:last_preferences", "Not set")
    
    return {
        "status": "success",
        "city": city,
        "preferences": preferences
    }


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


def initialize_multi_agent_system():
    """Initialize and configure the enhanced multi-agent system with Sessions and Memory"""
    print("\n🔧 Initializing Enhanced Multi-Agent System with Sessions & Memory...")
    
    # Configure retry options for API calls
    retry_config = types.HttpRetryOptions(
        attempts=5,
        exp_base=7,
        initial_delay=1,
        http_status_codes=[429, 500, 503, 504],
    )
    
    # Agent 1: Research Agent - Searches for places using Google Search
    research_agent = LlmAgent(
        name="ResearchAgent",
        model=Gemini(
            model="gemini-2.5-flash",
            retry_options=retry_config
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
    print("✅ ResearchAgent created (with google_search tool)")
    
    # Agent 2: Calculation Agent - Uses code execution for precise scoring
    calculation_agent = LlmAgent(
        name="CalculationAgent",
        model=Gemini(
            model="gemini-2.5-flash",
            retry_options=retry_config
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
    print("✅ CalculationAgent created (with BuiltInCodeExecutor)")
    
    # Agent 3: Filter Agent - Uses custom tools and calculation agent
    filter_agent = LlmAgent(
        name="FilterAgent",
        model=Gemini(
            model="gemini-2.5-flash",
            retry_options=retry_config
        ),
        instruction="""
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
        tools=[
            FunctionTool(func=calculate_distance_score),
            FunctionTool(func=get_place_category_boost),
            FunctionTool(func=save_user_preferences),
            FunctionTool(func=retrieve_user_preferences),
            AgentTool(agent=calculation_agent),  # Using agent as a tool!
            preload_memory,  # Memory retrieval tool
        ],
        output_key="filtered_results",
        after_agent_callback=auto_save_to_memory,  # Auto-save to memory
    )
    print("✅ FilterAgent created (with custom FunctionTools + AgentTool + Memory)")
    
    # Agent 4: Formatter Agent - Creates beautiful final recommendations
    formatter_agent = LlmAgent(
        name="FormatterAgent",
        model=Gemini(
            model="gemini-2.5-flash",
            retry_options=retry_config
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
    print("✅ FormatterAgent created")
    
    # Create Sequential Agent - Enhanced pipeline with calculation agent
    root_agent = SequentialAgent(
        name="EnhancedPlacesSearchPipeline",
        sub_agents=[research_agent, filter_agent, formatter_agent],
    )
    
    print("\n✅ Enhanced Multi-Agent Pipeline created")
    print("📋 Pipeline: ResearchAgent → FilterAgent (with tools) → FormatterAgent")
    print("🔧 Custom Tools: calculate_distance_score, get_place_category_boost")
    print("🤖 Agent Tools: CalculationAgent (code executor)")
    print("💾 Session State: save_user_preferences, retrieve_user_preferences")
    print("🧠 Memory: preload_memory for long-term recall")
    return root_agent


def initialize_services(topic: Optional[str] = None):
    """Initialize Session and Memory services based on topic.
    
    Args:
        topic: If provided, use DatabaseSessionService for persistence.
               If None/empty, use InMemorySessionService for transient session.
    
    Returns:
        Tuple of (session_service, memory_service)
    """
    print("\n🗄️ Initializing Services...")
    
    if topic:
        # PERSISTENT: Use database for topic-based sessions
        db_url = "sqlite:///places_search_sessions.db"
        try:
            session_service = DatabaseSessionService(db_url=db_url)
            print(f"✅ DatabaseSessionService initialized for topic '{topic}': {db_url}")
            logging.info(f"DatabaseSessionService initialized for topic '{topic}': {db_url}")
        except Exception as e:
            # Fallback to InMemorySessionService if database fails
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            logging.warning(
                f"⚠️ DatabaseSessionService failed (Python {python_version}): {e}"
            )
            logging.warning("⚠️ Falling back to InMemorySessionService (sessions won't persist)")
            print(f"⚠️ DatabaseSessionService failed: {e}")
            print(f"💡 Tip: Upgrade to Python 3.10+ (currently using Python {python_version})")
            
            session_service = InMemorySessionService()
            print("✅ InMemorySessionService initialized (fallback mode)")
            logging.info("InMemorySessionService initialized as fallback")
    else:
        # TRANSIENT: Use in-memory for one-off searches (no topic)
        session_service = InMemorySessionService()
        print("🚀 Transient Mode: Using InMemorySessionService (No DB write)")
        logging.info("InMemorySessionService initialized (transient mode - no topic)")
    
    # InMemoryMemoryService - Long-term knowledge storage
    memory_service = InMemoryMemoryService()
    print("✅ InMemoryMemoryService initialized")
    
    return session_service, memory_service


def create_app_with_compaction(root_agent, plugins=None):
    """Create App with Events Compaction for context optimization.
    
    Args:
        root_agent: The root agent for the app
        plugins: List of plugins to add to the app (Day 4a)
    """
    print("\n📦 Creating App with Context Compaction...")
    
    app = App(
        name="PlacesSearchApp",
        root_agent=root_agent,
        # Context Compaction: Automatically summarize conversation history
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=4,  # Compact every 4 turns
            overlap_size=1,  # Keep 1 turn for context
        ),
        plugins=plugins or [],  # Day 4a: Add plugins to App, not Runner
    )
    
    print("✅ App created with EventsCompactionConfig")
    print("   - Compaction interval: 4 turns")
    print("   - Overlap size: 1 turn")
    if plugins:
        print(f"   - Plugins: {len(plugins)} enabled")
    
    return app


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
    
    # Initialize multi-agent system
    agent = initialize_multi_agent_system()
    
    # Initialize Session and Memory services based on topic
    session_service, memory_service = initialize_services(topic)
    
    # Create plugins list for observability (Day 4a)
    plugins = []
    
    if enable_logging_plugin:
        plugins.append(LoggingPlugin())
        logging.info("🔌 LoggingPlugin enabled for comprehensive observability")
    
    if enable_metrics_plugin and METRICS_PLUGIN_AVAILABLE:
        _metrics_plugin_instance = MetricsTrackingPlugin()
        plugins.append(_metrics_plugin_instance)
        logging.info("🔌 MetricsTrackingPlugin enabled for performance metrics")
    
    # Create App with context compaction and plugins (Day 4a: plugins go in App, not Runner)
    app = create_app_with_compaction(agent, plugins=plugins)
    
    # Create Runner with all services (plugins are in the App)
    runner = Runner(
        app=app,
        session_service=session_service,
        memory_service=memory_service
    )
    
    # Generate session ID based on topic
    # If topic provided: stable ID for persistence
    # If no topic: random UUID for transient session
    if topic:
        session_id = f"{user_id}::{topic}"
    else:
        session_id = f"{user_id}::temp::{uuid.uuid4()}"
    
    print(f"\n📱 Session ID: {session_id}")
    
    # Create or retrieve session
    try:
        session = await session_service.create_session(
            app_name=app.name,
            user_id=user_id,
            session_id=session_id
        )
        print("✅ New session created")
    except:
        session = await session_service.get_session(
            app_name=app.name,
            user_id=user_id,
            session_id=session_id
        )
        print("✅ Existing session retrieved")
    
    # Create a search prompt
    prompt = (
        f"Find nearby places in {city_name} for someone who likes {preferences}. "
        f"Provide specific recommendations with names, brief descriptions, and why they would enjoy them."
    )
    
    print(f"\n📝 Prompt: {prompt}\n")
    print("🤖 AI Agent is working...\n")
    
    # Convert to ADK Content format
    query_content = types.Content(role="user", parts=[types.Part(text=prompt)])
    
    # Run the agent asynchronously and collect response
    final_text = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=query_content
    ):
        if event.is_final_response() and event.content and event.content.parts:
            text = event.content.parts[0].text
            if text and text != "None":
                final_text = text
    
    # Save session to memory for long-term recall (only if topic is provided)
    if topic:
        try:
            await memory_service.add_session_to_memory(session)
            print(f"\n💾 Session saved to memory for topic '{topic}'")
        except Exception as e:
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
        
        logging.info(f"📍 User query: city={city_name}, preferences={preferences}, topic={topic or 'transient'}")
        
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
    except Exception as e:
        logging.exception(f"❌ Unexpected error: {e}")
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
