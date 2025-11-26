"""
AI-Powered Nearby Places Search
Uses Google Agent Development Kit (ADK) to search for places based on user preferences
"""

import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search
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


def initialize_agent():
    """Initialize and configure the AI agent"""
    print("\n🔧 Initializing AI Agent...")
    
    # Configure retry options for API calls
    retry_config = types.HttpRetryOptions(
        attempts=5,  # Maximum retry attempts
        exp_base=7,  # Delay multiplier
        initial_delay=1,
        http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
    )
    
    # Create the root agent with search capabilities
    root_agent = Agent(
        name="places_search_assistant",
        model=Gemini(
            model="gemini-2.5-flash",
            retry_options=retry_config
        ),
        description="An AI agent that searches for nearby places based on city and user preferences.",
        instruction=(
            "You are a helpful assistant specialized in finding nearby places. "
            "When given a city name and user preferences (what they like), use Google Search to find "
            "relevant nearby places, attractions, restaurants, or activities. "
            "Provide detailed, helpful recommendations with specific names and brief descriptions. "
            "Always use Google Search for current and accurate information."
        ),
        tools=[google_search],
    )
    
    print("✅ Root Agent defined.")
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
    
    # Initialize agent
    agent = initialize_agent()
    
    # Create runner
    runner = InMemoryRunner(agent=agent)
    print("✅ Runner created.")
    
    # Create search prompt
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
    """Get city name and preferences from user"""
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
