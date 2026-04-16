"""
Mini Frontend for Places Search Agent
Deployed to Hugging Face Spaces with Gradio UI

Thin trusted relay — collects user input and Cloudflare Turnstile token,
then forwards the request server-side to the Cloud Run Agent API.
Does not contain agent pipeline logic or Google secrets.
"""

import os
import asyncio
import logging

import gradio as gr
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).resolve().parent / ".env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# Configuration
# ============================================================================

AGENT_API_URL = os.environ.get("AGENT_API_URL", "http://localhost:8080")
PROXY_AUTH_TOKEN = os.environ.get("PROXY_AUTH_TOKEN", "")
TURNSTILE_SITE_KEY = os.environ.get("TURNSTILE_SITE_KEY", "")

if not PROXY_AUTH_TOKEN:
    logger.warning("PROXY_AUTH_TOKEN not set — relay requests will be rejected by the API")
if not TURNSTILE_SITE_KEY:
    logger.warning("TURNSTILE_SITE_KEY not set — Turnstile widget will not render")


# ============================================================================
# Relay Function
# ============================================================================

async def _relay_search(
    city: str,
    preferences: str,
    topic: str,
    turnstile_token: str,
) -> str:
    """Forward search request server-side to the Cloud Run Agent API."""
    if not city or not preferences:
        return "Please enter both a city name and your preferences."

    if not turnstile_token:
        return "Please complete the security verification before searching."

    payload = {
        "city": city,
        "preferences": preferences,
        "topic": topic.strip() or None,
        "turnstile_token": turnstile_token,
    }
    headers = {"X-Proxy-Auth": PROXY_AUTH_TOKEN}

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                f"{AGENT_API_URL}/search",
                json=payload,
                headers=headers,
            )
        if resp.status_code == 200:
            return resp.json().get("result", "No results returned.")
        logger.error("Agent API returned HTTP %s: %s", resp.status_code, resp.text)
        return f"The search service returned an error (HTTP {resp.status_code}). Please try again."
    except httpx.TimeoutException:
        logger.error("Agent API request timed out")
        return "The search is taking too long. Please try again later."
    except httpx.HTTPError as exc:
        logger.exception("Agent API request failed: %s", exc)
        return "Could not reach the search service. Please try again later."


def sync_relay_search(
    city: str,
    preferences: str,
    topic: str,
    turnstile_token: str,
) -> str:
    """Synchronous wrapper for the async relay function."""
    logger.debug("relay called: city=%s, token_present=%s", city, bool(turnstile_token))
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, _relay_search(city, preferences, topic, turnstile_token)).result()
    return asyncio.run(_relay_search(city, preferences, topic, turnstile_token))


# ============================================================================
# Gradio UI
# ============================================================================

custom_css = """
.gradio-container {
    max-width: 900px !important;
    margin: auto;
}

.turnstile-box {
    margin: 12px 0;
}

.turnstile-hidden {
    position: absolute !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    opacity: 0 !important;
}
"""

# Build the Gradio interface
with gr.Blocks(
    title="AI Places Search",
    head=f"""
    <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
    <script>
    function onTurnstileSuccess(token) {{
        var el = document.querySelector('#turnstile-token textarea')
              || document.querySelector('#turnstile-token input')
              || document.querySelector('#turnstile-token-wrapper textarea')
              || document.querySelector('#turnstile-token-wrapper input');
        if (el) {{
            var proto = el.tagName === 'TEXTAREA'
                ? window.HTMLTextAreaElement.prototype
                : window.HTMLInputElement.prototype;
            var nset = Object.getOwnPropertyDescriptor(proto, 'value').set;
            nset.call(el, token);
            el.dispatchEvent(new Event('input', {{bubbles: true}}));
        }} else {{
            console.error('[Turnstile] could not find token input element');
        }}
    }}
    </script>
    """,
) as demo:

    gr.Markdown("""
    # MapMe Search

    Find personalized place recommendations powered by Google's Gemini AI.

    ---
    """)

    with gr.Row():
        with gr.Column(scale=2):
            city_input = gr.Textbox(
                label="City Name",
                placeholder="e.g., Paris, Tokyo, New York",
                info="Enter the city you want to explore",
            )

            preferences_input = gr.Textbox(
                label="Your Preferences",
                placeholder="e.g., coffee shops, museums, outdoor activities",
                info="What do you like? We'll find places matching your interests.",
            )

            topic_input = gr.Textbox(
                label="Topic (Optional)",
                placeholder="e.g., travel-2024, food-exploration, work-trips",
                info="Leave empty for a one-off search, or enter a topic to keep history",
            )

            # Turnstile widget and hidden token
            turnstile_token = gr.Textbox(
                elem_id="turnstile-token",
                label="",
                container=False,
                elem_classes=["turnstile-hidden"],
            )
            gr.HTML(
                f"""
                <div class="turnstile-box">
                  <div class="cf-turnstile"
                       data-sitekey="{TURNSTILE_SITE_KEY}"
                       data-callback="onTurnstileSuccess"
                       data-theme="light"></div>
                </div>
                """
            )

            search_btn = gr.Button("Search Places", variant="primary", size="lg")


    gr.Markdown("---")
    output = gr.Markdown(
        label="Recommendations",
        value="*Enter a city and your preferences, then click Search!*",
    )

    # Search button with loading state — disable while running
    def _start_search():
        return (
            gr.update(value="*🔍 Searching — this may take up to 60 seconds…*"),
            gr.update(interactive=False, value="Searching…"),
        )

    def _do_search(city, preferences, topic, token):
        result = sync_relay_search(city, preferences, topic, token)
        return result, gr.update(interactive=True, value="Search Places")

    search_btn.click(
        fn=_start_search,
        outputs=[output, search_btn],
    ).then(
        fn=_do_search,
        inputs=[city_input, preferences_input, topic_input, turnstile_token],
        outputs=[output, search_btn],
    )

    gr.Markdown("---")
    gr.Markdown("### Examples")
    gr.Examples(
        examples=[
            ["Paris", "coffee shops, art museums", "travel-2024"],
            ["Tokyo", "ramen, anime, nightlife", "japan-trip"],
            ["New York", "jazz clubs, pizza, rooftop bars", ""],
            ["Barcelona", "tapas, beaches, architecture", "summer-vacation"],
        ],
        inputs=[city_input, preferences_input, topic_input],
    )

    gr.Markdown("""
    ---

    <center>

    Made with [Google ADK](https://ai.google.dev/adk) & [Gradio](https://gradio.app)

    </center>
    """)


# ============================================================================
# Launch
# ============================================================================

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="slate",
        ),
        css=custom_css,
    )
