"""
Multi-Agent Pattern Examples
Demonstrates Sequential, Parallel, and Loop patterns using Google ADK
"""

import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent
from google.adk.models.google_llm import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.tools import google_search, FunctionTool
from google.genai import types


def setup_retry_config():
    """Configure retry options for API calls"""
    return types.HttpRetryOptions(
        attempts=5,
        exp_base=7,
        initial_delay=1,
        http_status_codes=[429, 500, 503, 504],
    )


# ============================================================================
# Example 1: Sequential Pattern (Current Implementation)
# ============================================================================

def create_sequential_pipeline():
    """
    Sequential Pattern: Research → Filter → Format
    Use when: Order matters, each step builds on previous
    """
    retry_config = setup_retry_config()
    
    # Agent 1: Research
    research_agent = Agent(
        name="ResearchAgent",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        instruction="Search for 5-7 places matching the city and preferences.",
        tools=[google_search],
        output_key="research_findings",
    )
    
    # Agent 2: Filter
    filter_agent = Agent(
        name="FilterAgent",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        instruction="""
Review the research findings: {research_findings}
Rate and select top 5 matches. Output curated list.""",
        output_key="filtered_results",
    )
    
    # Agent 3: Format
    formatter_agent = Agent(
        name="FormatterAgent",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        instruction="""
Format these results beautifully: {filtered_results}
Create engaging recommendations with emojis and structure.""",
        output_key="final_output",
    )
    
    # Create Sequential Pipeline
    pipeline = SequentialAgent(
        name="PlacesSearchPipeline",
        sub_agents=[research_agent, filter_agent, formatter_agent],
    )
    
    return pipeline


# ============================================================================
# Example 2: Parallel Pattern (Advanced)
# ============================================================================

def create_parallel_research_system():
    """
    Parallel Pattern: Multiple researchers work simultaneously
    Use when: Tasks are independent, speed matters
    
    Example: Research restaurants, attractions, and hotels simultaneously
    """
    retry_config = setup_retry_config()
    
    # Three independent researchers
    restaurant_researcher = Agent(
        name="RestaurantResearcher",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        instruction="Research top restaurants in the city. Focus on local favorites.",
        tools=[google_search],
        output_key="restaurant_findings",
    )
    
    attraction_researcher = Agent(
        name="AttractionResearcher",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        instruction="Research top tourist attractions and activities.",
        tools=[google_search],
        output_key="attraction_findings",
    )
    
    hotel_researcher = Agent(
        name="HotelResearcher",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        instruction="Research highly-rated hotels and accommodations.",
        tools=[google_search],
        output_key="hotel_findings",
    )
    
    # Aggregator combines parallel results
    aggregator = Agent(
        name="TravelAggregator",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        instruction="""
Combine these findings into a comprehensive travel guide:
- Restaurants: {restaurant_findings}
- Attractions: {attraction_findings}
- Hotels: {hotel_findings}

Create a day-by-day itinerary with dining, activities, and accommodation.""",
        output_key="travel_guide",
    )
    
    # Note: ParallelAgent would be used here if available
    # For now, this demonstrates the pattern structure
    # parallel_team = ParallelAgent(
    #     name="ParallelResearchTeam",
    #     sub_agents=[restaurant_researcher, attraction_researcher, hotel_researcher],
    # )
    
    # Combined pipeline: Parallel Research → Aggregator
    # root = SequentialAgent(
    #     name="TravelPlanningSystem",
    #     sub_agents=[parallel_team, aggregator],
    # )
    
    print("✅ Parallel pattern example created (structure only)")
    return None  # Return None since ParallelAgent may not be available


# ============================================================================
# Example 3: Loop Pattern (Advanced)
# ============================================================================

def create_refinement_loop():
    """
    Loop Pattern: Iterative improvement cycle
    Use when: Quality refinement needed, feedback loops
    
    Example: Writer → Critic → Refiner (loop until approved)
    """
    retry_config = setup_retry_config()
    
    # Initial writer
    initial_writer = Agent(
        name="InitialWriter",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        instruction="Write a draft recommendation guide for the places found.",
        output_key="current_draft",
    )
    
    # Critic reviews the draft
    critic_agent = Agent(
        name="CriticAgent",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        instruction="""
Review this draft: {current_draft}

If excellent, respond with exactly: "APPROVED"
Otherwise, provide 2-3 specific improvements needed.""",
        output_key="critique",
    )
    
    # Exit function for loop termination
    def exit_refinement_loop():
        """Called when critique is APPROVED"""
        return {"status": "approved", "message": "Draft approved"}
    
    # Refiner improves or exits
    refiner_agent = Agent(
        name="RefinerAgent",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        instruction="""
Current draft: {current_draft}
Critique: {critique}

IF critique is "APPROVED", call exit_refinement_loop function.
OTHERWISE, rewrite the draft incorporating all feedback.""",
        tools=[FunctionTool(exit_refinement_loop)],
        output_key="current_draft",  # Overwrites draft
    )
    
    # Note: LoopAgent would be used here if available
    # refinement_loop = LoopAgent(
    #     name="RefinementLoop",
    #     sub_agents=[critic_agent, refiner_agent],
    #     max_iterations=3,
    # )
    
    # root = SequentialAgent(
    #     name="WritingPipeline",
    #     sub_agents=[initial_writer, refinement_loop],
    # )
    
    print("✅ Loop pattern example created (structure only)")
    return None  # Return None since LoopAgent may not be available


# ============================================================================
# Example 4: Hybrid Pattern (Advanced)
# ============================================================================

def create_hybrid_system():
    """
    Hybrid Pattern: Combines multiple patterns
    
    Structure:
    1. Parallel research (multiple cities)
    2. Sequential processing per city
    3. Loop refinement on final output
    
    This demonstrates how patterns can be nested and combined.
    """
    print("""
    Hybrid Pattern Example:
    
    [Parallel]
      ├─ City1: Sequential(Research → Filter → Format)
      ├─ City2: Sequential(Research → Filter → Format)
      └─ City3: Sequential(Research → Filter → Format)
    
    Then:
    
    [Aggregator] → [Loop(Critic → Refiner)]
    
    This creates a powerful multi-city comparison system
    with quality refinement.
    """)
    return None


# ============================================================================
# Example 5: LLM-Based Coordination
# ============================================================================

def create_llm_coordinator():
    """
    LLM-Based Coordination: Root agent decides workflow
    
    Use when: Dynamic orchestration needed, LLM should decide
    
    The root agent uses sub-agents as tools and decides
    which to call and in what order based on the user's request.
    """
    retry_config = setup_retry_config()
    
    # Specialized sub-agents
    research_agent = Agent(
        name="ResearchAgent",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        instruction="Research places using google_search.",
        tools=[google_search],
        output_key="research_data",
    )
    
    price_agent = Agent(
        name="PriceAgent",
        model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
        instruction="Analyze and compare prices from research data: {research_data}",
        output_key="price_analysis",
    )
    
    # Note: Would use AgentTool to wrap sub-agents
    # from google.adk.tools import AgentTool
    
    # root = Agent(
    #     name="Coordinator",
    #     model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
    #     instruction="""
    #     You coordinate the workflow:
    #     1. Call ResearchAgent to find places
    #     2. If user asks about prices, call PriceAgent
    #     3. Present final results
    #     """,
    #     tools=[AgentTool(research_agent), AgentTool(price_agent)],
    # )
    
    print("✅ LLM-based coordinator example created (structure only)")
    return None


# ============================================================================
# Demo Runner
# ============================================================================

async def demo_sequential():
    """Demo the sequential pattern (currently implemented)"""
    load_dotenv()
    
    if not os.environ.get("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not found. Set it in .env file.")
        return
    
    print("\n" + "="*60)
    print("🔄 SEQUENTIAL PATTERN DEMO")
    print("="*60)
    
    pipeline = create_sequential_pipeline()
    runner = InMemoryRunner(agent=pipeline)
    
    prompt = "Find coffee shops in San Francisco for remote workers"
    print(f"\n📝 Query: {prompt}\n")
    
    response = await runner.run_debug(prompt)
    
    print("\n" + "="*60)
    print("✅ SEQUENTIAL DEMO COMPLETE")
    print("="*60)


def main():
    """Show all pattern examples"""
    print("\n" + "="*70)
    print("🤖 MULTI-AGENT PATTERN EXAMPLES")
    print("="*70)
    
    print("\n1️⃣  Sequential Pattern (Implemented)")
    create_sequential_pipeline()
    
    print("\n2️⃣  Parallel Pattern (Advanced)")
    create_parallel_research_system()
    
    print("\n3️⃣  Loop Pattern (Advanced)")
    create_refinement_loop()
    
    print("\n4️⃣  Hybrid Pattern (Advanced)")
    create_hybrid_system()
    
    print("\n5️⃣  LLM-Based Coordination (Advanced)")
    create_llm_coordinator()
    
    print("\n" + "="*70)
    print("📚 PATTERN SELECTION GUIDE")
    print("="*70)
    print("""
    ✅ Sequential: Order matters, linear pipeline (CURRENT)
    🏃 Parallel: Independent tasks, need speed
    🔄 Loop: Iterative refinement, quality cycles
    🧠 LLM-Coordinator: Dynamic decisions, complex workflows
    🔀 Hybrid: Combine multiple patterns for complex systems
    """)
    
    print("\n💡 To run the sequential demo:")
    print("   python examples/multi_agent_examples.py --demo")


if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        asyncio.run(demo_sequential())
    else:
        main()
