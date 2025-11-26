"""
AI-Powered Nearby Places Search
Uses Google Agent Development Kit (ADK) to search for places based on user preferences
"""

import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent
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


def initialize_multi_agent_system():
    """Initialize and configure the multi-agent system"""
    print("\n🔧 Initializing Multi-Agent System...")
    
    # Configure retry options for API calls
    retry_config = types.HttpRetryOptions(
        attempts=5,  # Maximum retry attempts
        exp_base=7,  # Delay multiplier
        initial_delay=1,
        http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
    )
    
    # Agent 1: Research Agent - Searches for places using Google Search
    research_agent = Agent(
        name="ResearchAgent",
        model=Gemini(
            model="gemini-2.5-flash",
            retry_options=retry_config
        ),
        instruction="""
You are a specialized research agent. Your only job is to use the google_search tool 
to find relevant places, attractions, restaurants, and activities based on the city and preferences provided.

Search for 5-7 specific places that match the user's interests. For each place, gather:
- Name of the place
- Type (restaurant, museum, park, etc.)
- Brief description
- Why it matches the preferences

Present your findings as structured data with clear details for each place.""",
        tools=[google_search],
        output_key="research_findings",  # Output stored in session state
    )
    print("✅ ResearchAgent created.")
    
    # Agent 2: Filter Agent - Analyzes and ranks the findings
    filter_agent = Agent(
        name="FilterAgent",
        model=Gemini(
            model="gemini-2.5-flash",
            retry_options=retry_config
        ),
        instruction="""
You are a filtering and ranking specialist. Review the research findings: {research_findings}

Your task:
1. Analyze each place found by the research agent
2. Rate how well each matches the user's preferences (1-10)
3. Remove any duplicates or irrelevant results
4. Select the top 5 best matches
5. Organize them by relevance (best matches first)

Output a curated list with ratings and reasoning for each selection.""",
        output_key="filtered_results",
    )
    print("✅ FilterAgent created.")
    
    # Agent 3: Formatter Agent - Creates beautiful final recommendations
    formatter_agent = Agent(
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
   • Clear description (2-3 sentences)
   • Why it's perfect for the user's preferences
   • A relevance score or badge (⭐)

Make it engaging, easy to read, and helpful. Use emojis strategically. 
End with a friendly summary of the recommendations.""",
        output_key="final_recommendations",
    )
    print("✅ FormatterAgent created.")
    
    # Create Sequential Agent - Runs agents in order: Research → Filter → Format
    root_agent = SequentialAgent(
        name="PlacesSearchPipeline",
        sub_agents=[research_agent, filter_agent, formatter_agent],
    )
    
    print("✅ Sequential Multi-Agent Pipeline created.")
    print("\n📋 Pipeline: ResearchAgent → FilterAgent → FormatterAgent")
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
