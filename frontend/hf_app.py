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
import time
import concurrent.futures

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
    logger.warning(
        "PROXY_AUTH_TOKEN not set — relay requests will be rejected by the API"
    )
if not TURNSTILE_SITE_KEY:
    logger.warning("TURNSTILE_SITE_KEY not set — Turnstile widget will not render")


# ============================================================================
# Relay Function
# ============================================================================


async def _relay_search(
    city: str,
    preferences: str,
    topic: str,
    token: str,
) -> str:
    """Forward search request server-side to the Cloud Run Agent API."""
    if not city or not preferences:
        return "Please enter both a city name and your preferences."

    if not token:
        return "Please complete the security verification before searching."

    payload = {
        "city": city,
        "preferences": preferences,
        "topic": topic.strip() or None,
        "turnstile_token": token,
    }
    headers = {"X-Proxy-Auth": PROXY_AUTH_TOKEN}

    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
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
    token: str,
) -> str:
    """Synchronous wrapper for the async relay function."""
    logger.debug("relay called: city=%s, token_present=%s", city, bool(token))
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(
                asyncio.run, _relay_search(city, preferences, topic, token)
            ).result()
    return asyncio.run(_relay_search(city, preferences, topic, token))


# ============================================================================
# Gradio UI
# ============================================================================

custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@300;400;500;600;700&display=swap');

:root {
    color-scheme: dark !important;
    --bg-primary: #07090f;
    --bg-secondary: #0b1220;
    --panel-bg: linear-gradient(180deg, rgba(8,18,33,0.92) 0%, rgba(10,23,43,0.88) 100%);
    --panel-border: rgba(74, 208, 255, 0.20);
    --text-primary: #e8f7ff;
    --text-secondary: rgba(213, 239, 255, 0.78);
    --text-muted: rgba(173, 220, 246, 0.48);
    --accent: #5de4ff;
    --accent-strong: #1fc8ff;
    --accent-soft: rgba(93, 228, 255, 0.18);
    --divider: rgba(93, 228, 255, 0.14);
    --button-bg: linear-gradient(135deg, #00a9d6 0%, #33d6ff 100%);
    --button-hover: linear-gradient(135deg, #10b7df 0%, #5de4ff 100%);
    --field-border: rgba(93, 228, 255, 0.22);
    --field-focus: #5de4ff;
    --page-glow: radial-gradient(circle at top center, rgba(31, 200, 255, 0.18), transparent 38%);
}

body, .gradio-container, .gradio-container * {
    font-family: 'Exo 2', sans-serif !important;
}

html,
body,
#root {
    background:
        var(--page-glow),
        radial-gradient(circle at 20% 18%, rgba(93, 228, 255, 0.08), transparent 22%),
        linear-gradient(180deg, var(--bg-secondary) 0%, var(--bg-primary) 100%) !important;
    color: var(--text-primary) !important;
}

html,
body,
#root {
    min-height: 100vh !important;
}

.app,
.wrap,
.contain,
.main,
footer {
    background: transparent !important;
    background-color: transparent !important;
}

.gradio-container {
    background-image: none !important;
}

.gradio-container::before,
.gradio-container::after,
.app::before,
.app::after,
.main::before,
.main::after {
    background: transparent !important;
}

.gradio-container {
    max-width: 860px !important;
    margin: auto !important;
    background: linear-gradient(180deg, rgba(6, 12, 22, 0.78) 0%, rgba(7, 10, 16, 0.80) 100%) !important;
    border: 1px solid rgba(93, 228, 255, 0.14) !important;
    border-radius: 14px !important;
    box-shadow: 0 14px 48px rgba(0,0,0,0.40), 0 0 24px rgba(31,200,255,0.10) !important;
    padding: 8px 20px 18px 20px !important;
}

.md-title-simple {
    font-size: 2.55rem !important;
    font-weight: 300 !important;
    letter-spacing: 0.14em !important;
    color: #e9f9ff !important;
    margin: 0 !important;
    text-transform: uppercase !important;
    line-height: 0.96 !important;
    text-shadow:
        0 0 10px rgba(255, 255, 255, 0.20),
        0 0 20px rgba(93, 228, 255, 0.14),
        0 1px 0 rgba(8, 20, 34, 0.44);
}

.md-title-frame {
    position: relative;
    margin: 24px 0 20px 0;
    padding: 10px 0 12px 0;
    display: block;
    width: 100%;
    text-align: center;
}

.md-title-frame::before,
.md-title-frame::after {
    content: "";
    position: absolute;
    left: 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg, transparent 0%, rgba(93, 228, 255, 0.42) 12%, rgba(93, 228, 255, 0.95) 50%, rgba(93, 228, 255, 0.42) 88%, transparent 100%);
    box-shadow: 0 0 10px rgba(93, 228, 255, 0.20);
}

.md-title-frame .md-title-simple {
    display: inline-block;
}

.md-title-frame::before {
    top: 0;
}

.md-title-frame::after {
    bottom: 0;
}

.md-card,
.md-output {
    position: relative;
}

.md-card {
    overflow: hidden;
}

.md-output {
    overflow: visible;
}

.md-card::before,
.md-output::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        linear-gradient(90deg, transparent 0%, rgba(93, 228, 255, 0.04) 48%, transparent 100%),
        linear-gradient(0deg, transparent 0%, rgba(93, 228, 255, 0.03) 48%, transparent 100%);
    background-size: 160px 160px;
    pointer-events: none;
}

/* === Form Card === */
.md-card {
    background: var(--panel-bg) !important;
    border-radius: 10px !important;
    border: 1px solid var(--panel-border) !important;
    box-shadow: 0 10px 36px rgba(0,0,0,0.30), 0 0 28px rgba(31,200,255,0.10) !important;
    backdrop-filter: blur(12px);
    padding: 24px 32px 32px 32px !important;
}

/* === Text Fields === */
.md-card .form,
.md-card .block,
.md-card .block.padded,
.md-card label.container {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    border-color: transparent !important;
    box-shadow: none !important;
    outline: none !important;
}

.md-card label.container.show_textbox_border {
    background: transparent !important;
    background-color: transparent !important;
    border: 1px solid rgba(93, 228, 255, 0.24) !important;
    border-radius: 8px !important;
    padding: 10px 12px 8px 12px !important;
    box-shadow: none !important;
}

.md-card label.container.show_textbox_border .input-container {
    background: transparent !important;
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    border-radius: 6px !important;
    padding: 6px 10px 4px 10px !important;
}

.gradio-container input,
.gradio-container textarea {
    border: none !important;
    border-bottom: 1px solid var(--field-border) !important;
    border-radius: 0 !important;
    background-color: transparent !important;
    padding: 8px 0 6px 0 !important;
    font-size: 1rem !important;
    font-weight: 400 !important;
    color: var(--text-primary) !important;
    caret-color: var(--accent) !important;
    transition: border-color 0.18s ease, box-shadow 0.18s ease !important;
    box-shadow: none !important;
    outline: none !important;
}

.gradio-container input::placeholder,
.gradio-container textarea::placeholder {
    color: var(--text-muted) !important;
}

.gradio-container span[data-testid="block-info"] {
    color: rgba(207, 241, 255, 0.96) !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
}

.gradio-container input:focus,
.gradio-container textarea:focus {
    border-bottom: 2px solid var(--field-focus) !important;
    box-shadow: 0 1px 0 0 var(--field-focus), 0 10px 18px -18px var(--field-focus) !important;
    outline: none !important;
}

.gradio-container textarea {
    resize: none !important;
    overflow-y: hidden !important;
}

/* === Block containers === */
.gradio-container .block {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 8px 0 !important;
}

/* === Material Button (brand) === */
.gradio-container button.lg.primary {
    background: var(--button-bg) !important;
    color: #03111a !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 999px !important;
    font-size: 0.86rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    height: 40px !important;
    padding: 0 24px !important;
    box-shadow: 0 8px 24px rgba(31,200,255,0.20), 0 3px 10px rgba(0,0,0,0.18) !important;
    transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease !important;
    margin-top: 16px !important;
}

.gradio-container button.lg.primary:hover:not(:disabled) {
    background: var(--button-hover) !important;
    transform: translateY(-1px);
    box-shadow: 0 10px 30px rgba(31,200,255,0.26), 0 5px 14px rgba(0,0,0,0.20) !important;
}

.gradio-container button.lg.primary:disabled {
    background: rgba(255,255,255,0.10) !important;
    color: rgba(255,255,255,0.35) !important;
    box-shadow: none !important;
}

/* === Output card === */
.md-output {
    background: var(--panel-bg) !important;
    border-radius: 10px !important;
    border: 1px solid rgba(93, 228, 255, 0.14) !important;
    box-shadow: 0 8px 28px rgba(0,0,0,0.20), 0 0 24px rgba(31,200,255,0.06) !important;
    padding: 24px !important;
    min-height: 110px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
}

.md-output [data-testid="status-tracker"] {
    position: static !important;
    display: block !important;
    width: 100% !important;
    min-height: 34px !important;
    margin: 0 auto !important;
    padding: 0 !important;
    text-align: center !important;
}

.md-output [data-testid="status-tracker"] > * {
    display: block !important;
    text-align: center !important;
    width: 100% !important;
}

.md-output [data-testid="status-tracker"] * {
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    color: rgba(228, 246, 255, 0.92) !important;
    opacity: 1 !important;
    font-size: 1rem !important;
    line-height: 1.35 !important;
}

.md-output [data-testid="status-tracker"] svg,
.md-output [data-testid="status-tracker"] img {
    width: 1.1rem !important;
    height: 1.1rem !important;
    max-width: none !important;
    display: inline-block !important;
    vertical-align: middle !important;
    margin: 0 0.35rem !important;
}

.md-output p,
.md-output li,
.md-output span,
.md-output em,
.md-output strong {
    color: var(--text-secondary) !important;
    font-size: 1rem !important;
    line-height: 1.6 !important;
    text-align: center !important;
    margin: 0 auto !important;
}

.md-output .prose,
.md-output .gr-markdown,
.md-output .gr-markdown > div {
    width: 100% !important;
    text-align: center !important;
}

.md-output .gr-markdown {
    margin: 0 !important;
}

/* === Divider === */
.md-divider {
    border: none;
    border-top: 1px solid var(--divider);
    margin: 24px 0;
}

/* === Examples table === */
.gr-samples-table td {
    font-size: 0.875rem !important;
    color: var(--text-secondary) !important;
    padding: 8px 12px !important;
    border-color: var(--divider) !important;
    background: transparent !important;
}

.gr-samples-table th {
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: var(--accent-strong) !important;
    padding: 8px 12px !important;
    border-bottom: 1px solid var(--divider) !important;
    background: transparent !important;
}

/* === Toggle switch (Topic) === */
.md-toggle {
    margin: 10px 0 4px 0 !important;
}

.md-toggle .block,
.md-toggle .form,
.md-toggle .wrap {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
}

.md-toggle label {
    display: inline-flex !important;
    align-items: center !important;
    gap: 12px !important;
    cursor: pointer !important;
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    letter-spacing: 0.01em !important;
}

.md-toggle label > span,
.md-toggle label .ml-2 {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    margin: 0 !important;
    padding: 0 !important;
}

.md-toggle label svg,
.md-toggle label .checkmark,
.md-toggle label [data-testid="checkbox-icon"] {
    display: none !important;
}

.md-toggle input[type="checkbox"] {
    appearance: none !important;
    -webkit-appearance: none !important;
    -moz-appearance: none !important;
    position: relative !important;
    width: 42px !important;
    height: 22px !important;
    min-width: 42px !important;
    max-width: 42px !important;
    border-radius: 999px !important;
    background: rgba(93, 228, 255, 0.10) !important;
    border: 1px solid rgba(93, 228, 255, 0.28) !important;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.35) !important;
    transition: background 0.22s ease, border-color 0.22s ease, box-shadow 0.22s ease !important;
    cursor: pointer !important;
    margin: 0 !important;
    padding: 0 !important;
    flex-shrink: 0 !important;
    vertical-align: middle !important;
}

.md-toggle input[type="checkbox"]::before {
    content: "" !important;
    position: absolute !important;
    top: 50% !important;
    left: 2px !important;
    width: 16px !important;
    height: 16px !important;
    border-radius: 50% !important;
    background: #cfeeff !important;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.45), 0 0 6px rgba(93, 228, 255, 0.25) !important;
    transform: translateY(-50%) !important;
    transition: left 0.22s ease, background 0.22s ease, box-shadow 0.22s ease !important;
}

.md-toggle input[type="checkbox"]:hover {
    border-color: rgba(93, 228, 255, 0.48) !important;
}

.md-toggle input[type="checkbox"]:checked {
    background: linear-gradient(135deg, #00a9d6 0%, #33d6ff 100%) !important;
    border-color: rgba(93, 228, 255, 0.65) !important;
    box-shadow: 0 0 10px rgba(31, 200, 255, 0.35), inset 0 1px 2px rgba(0, 0, 0, 0.25) !important;
}

.md-toggle input[type="checkbox"]:checked::before {
    left: 22px !important;
    background: #ffffff !important;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.45), 0 0 8px rgba(255, 255, 255, 0.5) !important;
}

.md-toggle input[type="checkbox"]:focus-visible {
    outline: 2px solid var(--accent) !important;
    outline-offset: 2px !important;
}

.md-toggle .info,
.md-toggle span[data-testid="block-info"] + *,
.md-toggle .wrap > span:not(.ml-2) {
    color: var(--text-muted) !important;
    font-size: 0.82rem !important;
    font-weight: 400 !important;
    letter-spacing: 0 !important;
    margin-top: 6px !important;
    display: block !important;
}

/* === Turnstile === */
.turnstile-box {
    margin: 12px 0 2px 0;
}

.turnstile-hidden {
    position: absolute !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
    opacity: 0 !important;
}

footer,
.built-with,
.settings,
[data-testid="footer"],
[data-testid="gradio-footer"],
.gradio-container > footer {
    display: none !important;
}
"""

# Build the Gradio interface
with gr.Blocks(
    title="AI Places Search",
    theme=gr.themes.Base(),
    css=custom_css,
    head=f"""
    <meta name="color-scheme" content="dark">
    <script>
    // Force dark mode regardless of device preference (iPhones in light mode would
    // otherwise render Gradio's light theme variables and look wrong).
    (function forceDarkMode() {{
        try {{
            document.documentElement.classList.add('dark');
            document.documentElement.style.colorScheme = 'dark';
        }} catch (e) {{}}
    }})();
    </script>
    <script src="https://challenges.cloudflare.com/turnstile/v0/api.js" async defer></script>
    <script>
    // Keep forcing the dark class in case Gradio removes it after hydration.
    function enforceDarkMode() {{
        if (!document.documentElement.classList.contains('dark')) {{
            document.documentElement.classList.add('dark');
        }}
        document.documentElement.style.colorScheme = 'dark';
    }}

    function applyTextareaAutoGrow() {{
        var textareas = document.querySelectorAll('textarea[data-testid="textbox"]');
        textareas.forEach(function(el) {{
            if (el.closest('#turnstile-token')) return;
            el.style.setProperty('resize', 'none', 'important');
            el.style.setProperty('overflow-y', 'hidden', 'important');
            el.style.height = 'auto';
            var next = Math.max(42, el.scrollHeight);
            el.style.height = next + 'px';
        }});
    }}

    function applyMapMeShellTheme() {{
        var bg = 'radial-gradient(circle at top center, rgba(31, 200, 255, 0.18), transparent 38%), radial-gradient(circle at 20% 18%, rgba(93, 228, 255, 0.08), transparent 22%), linear-gradient(180deg, #0b1220 0%, #07090f 100%)';
        var selectors = ['html', 'body', '#root'];
        selectors.forEach(function(selector) {{
            document.querySelectorAll(selector).forEach(function(el) {{
                el.style.setProperty('background', bg, 'important');
                el.style.setProperty('background-color', '#07090f', 'important');
                el.style.setProperty('color', '#e4f6ff', 'important');
                el.style.setProperty('min-height', '100vh', 'important');
            }});
        }});
        document.querySelectorAll('.wrap, .contain, .main, .app').forEach(function(el) {{
            el.style.setProperty('background', 'transparent', 'important');
            el.style.setProperty('background-color', 'transparent', 'important');
        }});
    }}

    document.addEventListener('DOMContentLoaded', function() {{
        enforceDarkMode();
        applyMapMeShellTheme();
        applyTextareaAutoGrow();
        setTimeout(enforceDarkMode, 50);
        setTimeout(enforceDarkMode, 250);
        setTimeout(enforceDarkMode, 1000);
        setTimeout(applyMapMeShellTheme, 50);
        setTimeout(applyMapMeShellTheme, 250);
        setTimeout(applyMapMeShellTheme, 1000);
        setTimeout(applyTextareaAutoGrow, 50);
        setTimeout(applyTextareaAutoGrow, 250);
        setTimeout(applyTextareaAutoGrow, 1000);

        // Watch <html> to reassert dark mode if Gradio or the runtime strips it.
        var htmlObserver = new MutationObserver(enforceDarkMode);
        htmlObserver.observe(document.documentElement, {{
            attributes: true,
            attributeFilter: ['class', 'style']
        }});

        document.addEventListener('input', function(e) {{
            if (e.target && e.target.matches('textarea[data-testid="textbox"]')) {{
                applyTextareaAutoGrow();
            }}
        }});

        var mo = new MutationObserver(function() {{
            applyTextareaAutoGrow();
        }});
        mo.observe(document.body, {{ childList: true, subtree: true }});
    }});

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

    window.addEventListener('load', function() {{
        enforceDarkMode();
        applyMapMeShellTheme();
    }});
    </script>
    """,  # noqa: F541
) as demo:
    gr.HTML(
        "<div class='md-title-frame'><h1 class='md-title-simple'>MapMe Search</h1></div>"
    )

    with gr.Column(elem_classes=["md-card"]):
        city_input = gr.Textbox(
            label="Place",
            placeholder="Enter a location",
        )

        preferences_input = gr.Textbox(
            label="Preferences",
            placeholder="Describe what you want to explore",
        )

        topic_toggle = gr.Checkbox(
            label="Remember search context",
            value=False,
            info="This topic acts as a memory key. All past preferences saved under this exact topic will be added to your search.",
            elem_classes=["md-toggle"],
        )

        topic_input = gr.Textbox(
            label="Topic Key",
            placeholder="Type a common word or unique string",
            interactive=False,
            visible=False,
        )

        topic_help = gr.Markdown(
            value=(
                "<div style='font-size:0.82rem;line-height:1.6;color:var(--text-secondary);"
                "border-left:2px solid var(--accent-soft);padding:10px 14px;margin-top:4px;"
                "background:rgba(93,228,255,0.04);border-radius:0 6px 6px 0;text-align:left;'>"
                "<div style='color:var(--accent-strong);font-weight:600;letter-spacing:0.04em;"
                "text-transform:uppercase;font-size:0.72rem;margin-bottom:6px;'>How this topic key works</div>"
                "<b>Empty</b>: Fully anonymous. No past context is used or saved.<br>"
                "<b>Common word</b> (e.g. <i>food</i>): Shared pool. You use and add to the preferences of everyone who used this key.<br>"
                "<b>Unique string</b> (e.g. <i>xk9-mytrip</i>): Private session. If no one else guesses it, only your own history is used."
                "</div>"
            ),
            visible=False,
        )

        def _toggle_topic(enabled: bool):
            return (
                gr.update(interactive=enabled, visible=enabled),
                gr.update(visible=enabled),
            )

        topic_toggle.change(
            fn=_toggle_topic,
            inputs=[topic_toggle],
            outputs=[topic_input, topic_help],
            show_progress="hidden",
        )

        # Hidden Turnstile token (populated by JS callback)
        turnstile_token = gr.Textbox(
            elem_id="turnstile-token",
            label="",
            container=False,
            elem_classes=["turnstile-hidden"],
        )

        search_btn = gr.Button("Search Places", variant="primary", size="lg")

    gr.HTML('<hr class="md-divider">')
    with gr.Column(elem_classes=["md-output"]):
        output = gr.Markdown(
            label="Recommendations",
            value="*Enter a place and your preferences, then click Search*",
        )

    # Search button with loading state — disable while running
    def _start_search():
        return (
            gr.update(value="⠋ **Searching places**\n\nRunning for 0.0s"),
            gr.update(interactive=False, value="Searching…"),
        )

    def _do_search(city, preferences, topic, topic_enabled, token):
        effective_topic = topic if topic_enabled else ""
        started = time.perf_counter()
        spinner_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        frame_index = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(
                sync_relay_search, city, preferences, effective_topic, token
            )
            while not future.done():
                elapsed = time.perf_counter() - started
                frame = spinner_frames[frame_index % len(spinner_frames)]
                frame_index += 1
                yield (
                    f"{frame} **Searching places**\n\nRunning for {elapsed:.1f}s",
                    gr.update(interactive=False, value="Searching…"),
                )
                time.sleep(0.2)

            try:
                result = future.result()
            except (RuntimeError, concurrent.futures.CancelledError):
                logger.exception("Search execution failed")
                result = "Could not complete the search. Please try again."

        yield result, gr.update(interactive=True, value="Search Places")

    search_btn.click(
        fn=_start_search,
        outputs=[output, search_btn],
        show_progress="hidden",
    ).then(
        fn=_do_search,
        inputs=[city_input, preferences_input, topic_input, topic_toggle, turnstile_token],
        outputs=[output, search_btn],
        show_progress="hidden",
    ).then(
        fn=lambda: gr.update(value=""),
        outputs=[turnstile_token],
        js="() => { try { if (window.turnstile) { window.turnstile.reset(); } } catch (e) { console.error('[Turnstile] reset failed', e); } return []; }",
        show_progress="hidden",
    )

    gr.HTML('<hr class="md-divider">')
    gr.HTML(
        f"""
        <div class="turnstile-box">
          <div class="cf-turnstile"
               data-sitekey="{TURNSTILE_SITE_KEY}"
               data-callback="onTurnstileSuccess"
               data-theme="dark"></div>
        </div>
        """
    )

    gr.HTML(
        "<div style='font-size:0.76rem;color:var(--text-muted);text-align:center;padding:10px 0 10px 0;'>"
        "Made with <a href='https://ai.google.dev/gemini-api' target='_blank' rel='noopener noreferrer' style='color:var(--accent-strong);'>Gemini</a>"
        " &amp; <a href='https://gradio.app' target='_blank' rel='noopener noreferrer' style='color:var(--accent-strong);'>Gradio</a> · "
        "Explore the code on "
        "<a href='https://github.com/xenm/map-me-search' target='_blank' rel='noopener noreferrer' style='color:var(--accent-strong);font-weight:600;'>"
        "GitHub ↗</a></div>"
    )


# ============================================================================
# Launch
# ============================================================================

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )
