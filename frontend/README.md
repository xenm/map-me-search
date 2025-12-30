---
title: AI Places Search
emoji: 🗺️
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.44.0
app_file: app.py
pinned: false
license: mit
---

# 🗺️ AI-Powered Places Search

A mini frontend for the AI Places Search agent, built with Gradio.

## Features

- **Topic-based Memory**: Enter a topic to save search history (uses `DatabaseSessionService`)
- **Transient Mode**: Leave topic empty for quick searches without saving history (uses `InMemorySessionService`)
- **Beautiful UI**: Clean, modern interface with helpful examples

## Memory Modes

| Topic Field | Session Service | Behavior |
|-------------|-----------------|----------|
| Empty | `InMemorySessionService` | Quick search, no history saved |
| Any string | `DatabaseSessionService` | History persists under that topic |

## Environment Variables

Set these in the Space settings or `.env` file:

- `VERTEX_AGENT_RESOURCE_ID`: Vertex AI Agent Engine resource ID
- `VERTEX_PROJECT_ID`: Google Cloud project ID for Vertex AI
- `VERTEX_LOCATION`: Vertex AI region
- `GOOGLE_API_KEY`: (Optional) Google AI Studio API key (only needed if using a local agent against AI Studio)

## Usage

1. Enter a city name
2. Describe your preferences
3. (Optional) Enter a topic to save search history
4. Click "Search Places"

## Architecture

```
┌─────────────────┐     API Calls      ┌──────────────────┐
│  Hugging Face   │ ───────────────────▶│  Vertex AI       │
│  (This Frontend)│ ◀─────────────────── │  Agent Engine    │
└─────────────────┘                     └──────────────────┘
```

This frontend serves as the "Face" while the actual agent logic runs on Vertex AI (the "Brain").
