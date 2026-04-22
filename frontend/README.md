---
title: MapMe Search
emoji: 🗺️
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 6.12.0
python_version: 3.13
app_file: hf_app.py
pinned: false
license: mit
---

# AI-Powered Places Search

Thin trusted relay frontend deployed to Hugging Face Spaces.
Collects user input and Cloudflare Turnstile token, then forwards
requests server-side to the Cloud Run Agent API.

## Environment Variables

Set these in the HF Space settings:

| Name | Type | Description |
|------|------|-------------|
| `AGENT_API_URL` | Secret | Cloud Run service URL |
| `PROXY_AUTH_TOKEN` | Secret | Shared secret for X-Proxy-Auth header |
| `TURNSTILE_SITE_KEY` | Variable | Cloudflare Turnstile public site key |

## Architecture

```
 Browser
 │ Turnstile challenge
 ▼
┌─────────────────┐  X-Proxy-Auth   ┌──────────────────┐
│  Hugging Face   │ ──────────────▶ │  Cloud Run       │
│  (This Relay)   │ ◀────────────── │  Agent API       │
└─────────────────┘  JSON result    └──────────────────┘
```

This frontend is a trusted relay — it does not contain agent logic or Google secrets.
