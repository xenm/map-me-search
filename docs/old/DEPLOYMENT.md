# Deployment Guide

This guide covers deploying the AI Places Search agent to **Vertex AI** and the mini frontend to **Hugging Face Spaces** via **GitHub Actions**.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                        │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────────────┐ │
│  │   agent/    │    │  frontend/  │    │ .github/workflows/   │ │
│  │  (Brain)    │    │   (Face)    │    │    deploy.yaml       │ │
│  └──────┬──────┘    └──────┬──────┘    └──────────┬───────────┘ │
└─────────┼──────────────────┼──────────────────────┼─────────────┘
          │                  │                      │
          │    GitHub Actions (CI/CD)               │
          │                  │                      │
          ▼                  ▼                      │
┌─────────────────┐  ┌─────────────────┐           │
│   Vertex AI     │  │  Hugging Face   │◀──────────┘
│  Agent Engine   │  │    Spaces       │
│    (Brain)      │  │     (Face)      │
└────────┬────────┘  └────────┬────────┘
         │                    │
         │   API Requests     │
         │◀───────────────────┘
         │
    ┌────┴────┐
    │ Memory  │
    │  Bank   │
    └─────────┘
```

## Prerequisites

### 1. Google Cloud Setup

```bash
# Set your project ID
export PROJECT_ID="your-project-id"

# Create Service Account for GitHub Actions
gcloud iam service-accounts create github-deployer \
    --display-name="GitHub Actions Deployer"

# Grant required permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-deployer@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/logging.logWriter"

# Generate Service Account Key (for GitHub Secrets)
gcloud iam service-accounts keys create key.json \
    --iam-account=github-deployer@$PROJECT_ID.iam.gserviceaccount.com
```

### 2. Hugging Face Setup

1. Create a Hugging Face account at [huggingface.co](https://huggingface.co)
2. Create a new Space: `New Space` → Select `Gradio` as SDK
3. Generate an access token: `Settings` → `Access Tokens` → `New token`

### 3. GitHub Secrets

Go to your repository: `Settings` → `Secrets and variables` → `Actions`

Add these secrets:

| Secret Name | Description |
|-------------|-------------|
| `GCP_CREDENTIALS` | Content of the `key.json` file |
| `GCP_PROJECT_ID` | Your Google Cloud project ID |
| `HF_TOKEN` | Hugging Face access token |
| `HF_USERNAME` | Your Hugging Face username |
| `HF_SPACE_NAME` | Name of your Hugging Face Space |

## Directory Structure

```
map-me-search/
├── .github/
│   └── workflows/
│       └── deploy.yaml          # CI/CD workflow
├── agent/                       # Deployed to Vertex AI
│   ├── __init__.py
│   ├── agent.py                 # Core agent logic
│   ├── requirements.txt
│   └── .agent_engine_config.json
├── frontend/                    # Deployed to Hugging Face
│   ├── app.py                   # Gradio UI
│   ├── requirements.txt
│   └── README.md                # HF Space metadata
├── main.py                      # Local development entry point
└── requirements.txt             # Root dependencies
```

## Topic-Based Memory System

The system uses topic-based session management:

| Topic Field | Session Service | Behavior |
|-------------|-----------------|----------|
| Empty/None | `InMemorySessionService` | Transient - no history saved |
| Any string | `DatabaseSessionService` | Persistent - history saved under topic |

### How it works:

1. **User enters topic** (e.g., "travel-2024"):
   - Session ID: `{user_id}::travel-2024`
   - Uses `DatabaseSessionService`
   - History persists across sessions

2. **User leaves topic empty**:
   - Session ID: `{user_id}::temp::{uuid}`
   - Uses `InMemorySessionService`
   - History discarded after search

## Deployment Triggers

The workflow triggers on:

1. **Push to main** with changes in:
   - `agent/**`
   - `frontend/**`
   - `.github/workflows/deploy.yaml`

2. **Manual dispatch** via GitHub Actions UI:
   - Can selectively deploy to Vertex AI or Hugging Face

## Local Development

### Run the CLI locally:
```bash
# Install dependencies
pip install -r requirements.txt

# Run the CLI
python main.py
```

### Run the frontend locally:
```bash
# Install frontend dependencies
pip install -r frontend/requirements.txt

# Run Gradio app
python frontend/app.py
```

## Post-Deployment

### Vertex AI
- Access via Google Cloud Console → Vertex AI → Reasoning Engines
- No public URL - accessed via API or frontend

### Hugging Face
- Public URL: `https://huggingface.co/spaces/{username}/{space-name}`
- Can be embedded in other websites

## Troubleshooting

### Common Issues

1. **ADK deployment fails**
   - Check service account permissions
   - Verify GitHub Actions auth (WIF/service account) is configured correctly
   - Check region availability for Agent Engine

2. **Hugging Face deployment fails**
   - Verify `HF_TOKEN` has write access
   - Check Space name matches exactly
   - Ensure `README.md` has valid YAML frontmatter

3. **Memory not persisting**
   - In Vertex AI, SQLite doesn't persist (ephemeral storage)
   - For production, use `FirestoreSessionService` or `VertexAiMemoryBankService`

### Logs

- **GitHub Actions**: Check the Actions tab in your repository
- **Vertex AI**: Cloud Logging in Google Cloud Console
- **Hugging Face**: Space logs in the Space's "Logs" tab
