"""
AI-Powered Nearby Places Search
Uses Google Agent Development Kit (ADK) to search for places based on user preferences
"""

import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search, AgentTool, FunctionTool
from google.adk.code_executors import BuiltInCodeExecutor
from google.genai import types


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


def initialize_multi_agent_system():
    """Initialize and configure the enhanced multi-agent system with custom tools"""
    print("\n🔧 Initializing Enhanced Multi-Agent System...")
    
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
You are a filtering and ranking specialist. Review the research findings: {research_findings}

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
            AgentTool(agent=calculation_agent),  # Using agent as a tool!
        ],
        output_key="filtered_results",
    )
    print("✅ FilterAgent created (with custom FunctionTools + AgentTool)")
    
    # Agent 4: Formatter Agent - Creates beautiful final recommendations
    formatter_agent = LlmAgent(
        name="FormatterAgent",
        model=Gemini(
            model="gemini-2.5-flash",
            retry_options=retry_config
        ),
        instruction="""
You are a presentation specialist. Take the filtered results: {filtered_results}

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
    return root_agent


async def search_places(city_name: str, preferences: str):
    """
    Search for nearby places based on city and preferences
    
    Args:
        city_name: The name of the city to search in
        preferences: What the user likes (e.g., "coffee shops", "museums", "parks")
    """
    print(f"\n🔍 Searching for places in {city_name} based on: '{preferences}'")
    print("=" * 60)
    
    # Initialize multi-agent system
    agent = initialize_multi_agent_system()
    
    # Create runner
    runner = InMemoryRunner(agent=agent)
    print("✅ Runner created.")
    
    # Create a search prompt
    prompt = (
        f"Find nearby places in {city_name} for someone who likes {preferences}. "
        f"Provide specific recommendations with names, brief descriptions, and why they would enjoy them."
    )
    
    print(f"\n📝 Prompt: {prompt}\n")
    print("🤖 AI Agent is working...\n")
    
    # Run the agent
    response = await runner.run_debug(prompt)
    
    return response


def print_response(response):
    """Print the agent's response in a formatted way"""
    print("\n" + "=" * 60)
    print("📍 SEARCH RESULTS")
    print("=" * 60)
    
    if hasattr(response, 'text'):
        print(response.text)
    elif hasattr(response, 'content'):
        print(response.content)
    else:
        print(response)
    
    print("\n" + "=" * 60)


def get_user_input():
    """Get city name and preferences from the user"""
    print("\n" + "=" * 60)
    print("🗺️  AI-POWERED NEARBY PLACES SEARCH")
    print("=" * 60)
    
    city_name = input("\n📍 Enter city name: ").strip()
    preferences = input("❤️  What do you like? (e.g., coffee, museums, parks): ").strip()
    
    if not city_name or not preferences:
        print("❌ Both fields are required!")
        return None, None
    
    return city_name, preferences


async def main():
    """Main application entry point"""
    try:
        # Load environment variables
        load_environment()
        
        # Get user input
        city_name, preferences = get_user_input()
        
        if not city_name or not preferences:
            return
        
        # Search for places
        response = await search_places(city_name, preferences)
        
        # Print results
        print_response(response)
        
        print("\n✅ Search completed successfully!")
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
