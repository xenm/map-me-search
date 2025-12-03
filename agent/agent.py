"""
AI-Powered Nearby Places Search Agent
Adapted for Vertex AI Agent Engine deployment

This module contains the core agent logic that can be imported by the deployment entry point.
"""

import os
import sys
import logging
import uuid
from dotenv import load_dotenv
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService, InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.adk.tools import google_search, AgentTool, FunctionTool, preload_memory
from google.adk.tools.tool_context import ToolContext
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.plugins.logging_plugin import LoggingPlugin
from google.genai import types
from typing import Any, Dict, Optional

# Load environment variables
load_dotenv()

# Configure logging for cloud environment
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Custom Function Tools
# ============================================================================

def calculate_distance_score(distance_km: float) -> dict:
    """Calculates a relevance score based on distance from city center.
    
    Args:
        distance_km: Distance in kilometers from city center
        
    Returns:
        Dictionary with status and score.
    """
    if distance_km < 0:
        return {"status": "error", "error_message": "Distance cannot be negative"}
    
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
    
    return {"status": "success", "score": score, "distance_km": distance_km}


def get_place_category_boost(category: str, preferences: str) -> dict:
    """Calculates a boost score based on how well a category matches preferences.
    
    Args:
        category: Category of the place
        preferences: User's stated preferences
        
    Returns:
        Dictionary with status and boost score.
    """
    category = category.lower()
    preferences = preferences.lower()
    
    if category in preferences or preferences in category:
        return {"status": "success", "boost": 3, "reason": "Direct match"}
    
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


def save_user_preferences(tool_context: ToolContext, city: str, preferences: str) -> Dict[str, Any]:
    """Save user's city and preferences to session state."""
    tool_context.state["user:last_city"] = city
    tool_context.state["user:last_preferences"] = preferences
    return {"status": "success", "message": f"Saved preferences for {city}"}


def retrieve_user_preferences(tool_context: ToolContext) -> Dict[str, Any]:
    """Retrieve user's previously saved preferences from session state."""
    city = tool_context.state.get("user:last_city", "Not set")
    preferences = tool_context.state.get("user:last_preferences", "Not set")
    return {"status": "success", "city": city, "preferences": preferences}


# ============================================================================
# Agent System Initialization
# ============================================================================

def initialize_multi_agent_system():
    """Initialize the multi-agent system for places search."""
    logger.info("Initializing Multi-Agent System...")
    
    retry_config = types.HttpRetryOptions(
        attempts=5,
        exp_base=7,
        initial_delay=1,
        http_status_codes=[429, 500, 503, 504],
    )
    
    # Research Agent
    research_agent = LlmAgent(
        name="ResearchAgent",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
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
    
    # Calculation Agent
    calculation_agent = LlmAgent(
        name="CalculationAgent",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
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
    
    # Filter Agent
    filter_agent = LlmAgent(
        name="FilterAgent",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
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
            AgentTool(agent=calculation_agent),
            preload_memory,
        ],
        output_key="filtered_results",
    )
    
    # Formatter Agent
    formatter_agent = LlmAgent(
        name="FormatterAgent",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
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
    
    # Sequential Pipeline
    root_agent = SequentialAgent(
        name="EnhancedPlacesSearchPipeline",
        sub_agents=[research_agent, filter_agent, formatter_agent],
    )
    
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
    topic_str = topic if topic is not None else 'None (transient)'
    topic_str = topic_str.replace('\r', '').replace('\n', '')
    logger.info(f"Initializing services with topic: {topic_str}")
    
    if topic:
        # PERSISTENT: Use database for topic-based sessions
        try:
            db_url = "sqlite:///places_search_sessions.db"
            session_service = DatabaseSessionService(db_url=db_url)
            topic_sanitized = topic.replace('\r', '').replace('\n', '')
            logger.info(f"DatabaseSessionService initialized for topic '{topic_sanitized}'")
        except Exception as e:
            logger.warning(f"DatabaseSessionService failed: {e}, falling back to InMemory")
            session_service = InMemorySessionService()
    else:
        # TRANSIENT: Use in-memory for one-off searches
        session_service = InMemorySessionService()
        logger.info("InMemorySessionService initialized (transient mode)")
    
    memory_service = InMemoryMemoryService()
    logger.info("InMemoryMemoryService initialized")
    
    return session_service, memory_service


def create_app(root_agent, plugins=None):
    """Create App with Events Compaction for context optimization."""
    app = App(
        name="PlacesSearchApp",
        root_agent=root_agent,
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=4,
            overlap_size=1,
        ),
        plugins=plugins or [],
    )
    logger.info("App created with EventsCompactionConfig")
    return app


async def search_places(
    city_name: str,
    preferences: str,
    topic: Optional[str] = None,
    user_id: str = "default_user"
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
    logger.info(f"Searching in {city_name} for '{preferences}' (topic: {topic or 'transient'})")
    
    # Initialize agent and services
    agent = initialize_multi_agent_system()
    session_service, memory_service = initialize_services(topic)
    
    # Generate session ID based on topic
    if topic:
        session_id = f"{user_id}::{topic}"
    else:
        session_id = f"{user_id}::temp::{uuid.uuid4()}"
    
    # Create app and runner
    app = create_app(agent, plugins=[LoggingPlugin()])
    runner = Runner(
        app=app,
        session_service=session_service,
        memory_service=memory_service
    )
    
    # Create or retrieve session
    try:
        session = await session_service.create_session(
            app_name=app.name,
            user_id=user_id,
            session_id=session_id
        )
    except:
        session = await session_service.get_session(
            app_name=app.name,
            user_id=user_id,
            session_id=session_id
        )
    
    # Create prompt
    prompt = (
        f"Find nearby places in {city_name} for someone who likes {preferences}. "
        f"Provide specific recommendations with names, brief descriptions, and why they would enjoy them."
    )
    
    query_content = types.Content(role="user", parts=[types.Part(text=prompt)])
    
    # Run agent and collect response
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
    
    # Save to memory if topic is provided
    if topic:
        try:
            await memory_service.add_session_to_memory(session)
            logger.info("Session saved to memory")
        except Exception as e:
            logger.warning(f"Memory save failed: {e}")
    
    return final_text


# Export the root agent for Vertex AI deployment
root_agent = initialize_multi_agent_system()
app = create_app(root_agent)
