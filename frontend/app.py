"""
Mini Frontend for Places Search Agent
Deployed to Hugging Face Spaces with Gradio UI

Features:
- Topic selection for categorized memory (DatabaseSessionService when topic provided)
- Transient mode when topic is empty (InMemorySessionService)
- Clean, modern UI with emoji support
"""

import os
import asyncio
import logging
from typing import Optional

import gradio as gr
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for required environment variables
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    logger.warning("⚠️ GOOGLE_API_KEY not found. Set it in .env or environment variables.")

# Try to import the agent module
try:
    import sys
    # Add parent directory to path if running locally
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from agent.agent import search_places, initialize_services, initialize_multi_agent_system
    AGENT_AVAILABLE = True
    logger.info("✅ Agent module loaded successfully")
except ImportError as e:
    AGENT_AVAILABLE = False
    logger.warning(f"⚠️ Agent module not available: {e}")
    logger.info("Running in demo mode - agent calls will be simulated")


# ============================================================================
# Backend Functions
# ============================================================================

async def search_with_topic(
    city: str,
    preferences: str,
    topic: str,
    user_id: str = "hf_user"
) -> str:
    """
    Execute search with optional topic for memory categorization.
    
    Args:
        city: City name to search in
        preferences: User preferences (e.g., "coffee, museums")
        topic: Topic/category for session. Empty = transient (InMemorySessionService)
        user_id: User identifier
    
    Returns:
        Search results as formatted string
    """
    if not city or not preferences:
        return "❌ Please enter both a city name and your preferences."
    
    # Determine session mode
    topic_cleaned = topic.strip() if topic else None
    
    if topic_cleaned:
        sanitized_topic = topic_cleaned.replace('\n', '').replace('\r', '')
        logger.info(f"🗄️ Using DatabaseSessionService for topic: '{sanitized_topic}'")
    else:
        logger.info("🚀 Using InMemorySessionService (transient mode)")
    
    if AGENT_AVAILABLE:
        try:
            result = await search_places(
                city_name=city,
                preferences=preferences,
                topic=topic_cleaned,
                user_id=user_id
            )
            return result
        except (ValueError, RuntimeError, ConnectionError, ImportError) as e:
            logger.error(f"Search error: {e}")
            return f"❌ Error during search: {str(e)}"
    else:
        # Demo mode response
        return f"""
🎯 **Demo Mode Response**

Since the agent module is not available, here's a simulated response:

📍 **City**: {city}
❤️ **Preferences**: {preferences}
🏷️ **Topic**: {topic_cleaned or "None (transient session)"}

---

**Memory Mode**: {"DatabaseSessionService (persistent)" if topic_cleaned else "InMemorySessionService (transient)"}

In production, this would call the Vertex AI Agent Engine to get real recommendations!

---

To enable full functionality:
1. Set `GOOGLE_API_KEY` environment variable
2. Ensure the agent module is properly installed
"""


def sync_search(city: str, preferences: str, topic: str) -> str:
    """Synchronous wrapper for the async search function."""
    return asyncio.run(search_with_topic(city, preferences, topic))


# ============================================================================
# Gradio UI
# ============================================================================

# Custom CSS for better styling
custom_css = """
.gradio-container {
    max-width: 900px !important;
    margin: auto;
}

.topic-info {
    background-color: #f0f7ff;
    border-left: 4px solid #2196f3;
    padding: 10px 15px;
    margin: 10px 0;
    border-radius: 4px;
}

.memory-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 16px;
    font-size: 12px;
    font-weight: 600;
}

.badge-persistent {
    background-color: #e8f5e9;
    color: #2e7d32;
}

.badge-transient {
    background-color: #fff3e0;
    color: #ef6c00;
}
"""

# Build the Gradio interface
with gr.Blocks(
    title="🗺️ AI Places Search",
    theme=gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="slate",
    ),
    css=custom_css
) as demo:
    
    gr.Markdown("""
    # 🗺️ AI-Powered Places Search
    
    Find personalized place recommendations powered by Google's Gemini AI.
    
    ---
    """)
    
    with gr.Row():
        with gr.Column(scale=2):
            # Input fields
            city_input = gr.Textbox(
                label="📍 City Name",
                placeholder="e.g., Paris, Tokyo, New York",
                info="Enter the city you want to explore"
            )
            
            preferences_input = gr.Textbox(
                label="❤️ Your Preferences",
                placeholder="e.g., coffee shops, museums, outdoor activities",
                info="What do you like? We'll find places matching your interests."
            )
            
            topic_input = gr.Textbox(
                label="🏷️ Topic (Optional)",
                placeholder="e.g., travel-2024, food-exploration, work-trips",
                info="Leave empty for transient session, or enter a topic to save search history"
            )
            
            # Info box about memory modes
            gr.Markdown("""
            <div class="topic-info">
            <strong>💡 Memory Modes:</strong><br>
            • <strong>Empty topic</strong> → Uses <code>InMemorySessionService</code> (no history saved)<br>
            • <strong>With topic</strong> → Uses <code>DatabaseSessionService</code> (history persists for this topic)
            </div>
            """)
            
            search_btn = gr.Button("🔍 Search Places", variant="primary", size="lg")
        
        with gr.Column(scale=1):
            # Memory status indicator
            memory_status = gr.Markdown(
                value="**Current Mode**: Transient (InMemory)",
                label="Session Status"
            )
            
            # Quick topic suggestions
            gr.Markdown("### 💡 Topic Ideas")
            gr.Markdown("""
            - `travel-europe-2024`
            - `date-night-spots`
            - `family-friendly`
            - `solo-adventures`
            - `foodie-finds`
            - `art-culture`
            """)
    
    # Output area
    gr.Markdown("---")
    output = gr.Markdown(
        label="🎯 Recommendations",
        value="*Enter a city and your preferences, then click Search!*"
    )
    
    # Update memory status based on topic input
    def update_memory_status(topic: str) -> str:
        if topic and topic.strip():
            return f"""
            **Current Mode**: Persistent (Database)
            
            🏷️ **Topic**: `{topic.strip()}`
            
            ✅ Your search history will be saved under this topic.
            """
        else:
            return """
            **Current Mode**: Transient (InMemory)
            
            ⚡ Quick search mode - no history will be saved.
            """
    
    topic_input.change(
        fn=update_memory_status,
        inputs=[topic_input],
        outputs=[memory_status]
    )
    
    # Search button click handler
    search_btn.click(
        fn=sync_search,
        inputs=[city_input, preferences_input, topic_input],
        outputs=[output]
    )
    
    # Examples
    gr.Markdown("---")
    gr.Markdown("### 📝 Examples")
    gr.Examples(
        examples=[
            ["Paris", "coffee shops, art museums", "travel-2024"],
            ["Tokyo", "ramen, anime, nightlife", "japan-trip"],
            ["New York", "jazz clubs, pizza, rooftop bars", ""],
            ["Barcelona", "tapas, beaches, architecture", "summer-vacation"],
        ],
        inputs=[city_input, preferences_input, topic_input],
    )
    
    # Footer
    gr.Markdown("""
    ---
    
    <center>
    
    Made with ❤️ using [Google ADK](https://ai.google.dev/adk) & [Gradio](https://gradio.app)
    
    **Note**: This frontend calls the AI agent deployed on Vertex AI.
    
    </center>
    """)


# ============================================================================
# Launch
# ============================================================================

if __name__ == "__main__":
    # For local development
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
