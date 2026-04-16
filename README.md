# AI-Powered Nearby Places Search Agent

An intelligent multi-agent system that searches for personalized nearby places using Google's Gemini AI and Agent Development Kit (ADK).

## Security Architecture (DevSecOps)

This project treats security as a first-class design constraint, not an afterthought. The architecture assumes **public source code** and enforces **zero trust at every boundary**.

```
 Browser
 │  Cloudflare Turnstile challenge (bot/abuse mitigation)
 ▼
┌──────────────────────┐  X-Proxy-Auth   ┌──────────────────────┐
│  Hugging Face Space  │ ──────────────▶ │  Google Cloud Run    │
│  (Thin Trusted Relay)│ ◀────────────── │  (Agent API)         │
│                      │   JSON result   │                      │
│  • Gradio UI         │                 │  • FastAPI + Uvicorn │
│  • No GCP secrets    │                 │  • Multi-agent pipeline│
│  • No agent logic    │                 │  • Gemini LLM calls  │
│  • httpx relay only  │                 │  • Secret Manager    │
└──────────────────────┘                 └──────────────────────┘
```

### Why this is the most secure architecture

| Principle | Implementation |
|---|---|
| **Zero GCP secrets in GitHub** | GitHub stores only non-sensitive identifiers (`vars.*`). Runtime secrets (`PROXY_AUTH_TOKEN`, `TURNSTILE_SECRET_KEY`) live in Google Secret Manager and are injected into Cloud Run at deploy time. |
| **Workload Identity Federation** | GitHub Actions authenticates to GCP via OIDC federation — no JSON service account keys anywhere. |
| **Least-privilege service accounts** | `map-me-search-deploy@` can only push images and deploy one service. `map-me-search-run@` can only read its own secrets. Neither has project-wide admin roles. |
| **Immutable container images** | Docker images are tagged with the Git SHA. Artifact Registry enforces immutable tags, vulnerability scanning, and cleanup policies. |
| **Non-root container** | The Dockerfile creates and runs as `appuser` — no root process in production. |
| **Minimal frontend dependencies** | The HF Space installs only `gradio`, `httpx`, and `python-dotenv`. No GCP SDK, no agent code, no AI model access. A compromised Space cannot reach Google APIs. |
| **App-layer authentication** | Cloud Run is public at the network level (required because the caller is HF, not a Google identity), but every request must pass two checks: a shared secret (`X-Proxy-Auth` verified with constant-time comparison) and a Cloudflare Turnstile token (verified server-side against Cloudflare's API). |
| **Fail-closed on misconfiguration** | If `PROXY_AUTH_TOKEN` or `TURNSTILE_SECRET_KEY` is missing, the API rejects all requests (HTTP 500), never falls open. |
| **Deny-by-default GitHub Actions** | Top-level `permissions: {}` in workflows; only the deploy job gets `contents: read` + `id-token: write`. |
| **SHA-pinned Actions** | All third-party Actions are pinned to commit SHA, not mutable tags. Dependabot monitors for updates. |

### Security model summary

- **Browser ↔ HF Space**: Turnstile widget proves the user is human
- **HF Space ↔ Cloud Run**: shared secret header proves the caller is the trusted relay
- **Cloud Run ↔ Cloudflare**: server-side Turnstile verification proves the token is valid, single-use, and not expired
- **GitHub ↔ GCP**: WIF + OIDC proves the caller is this repo's main branch
- **Cloud Run ↔ Secret Manager**: runtime SA proves the container is authorized to read secrets

---

## Quick Start (Local Development)

See [docs/QUICKSTART.md](docs/QUICKSTART.md) for full setup instructions.

```bash
# Agent API (terminal 1)
cp agent/.env.example agent/.env   # edit GCP project + auth
uvicorn agent.agent_api:app --port 8080

# Frontend (terminal 2)
cp frontend/.env.example frontend/.env
python frontend/hf_app.py
```

## Architecture

### Deployment

| Component | Runtime | Entry point | Deployment |
|---|---|---|---|
| Agent API | Google Cloud Run | `agent/agent_api.py` | `deploy-agent-api.yaml` |
| Frontend | Hugging Face Spaces | `frontend/hf_app.py` | `deploy-hf-app.yaml` |

### Agent Pipeline

The API runs a **sequential multi-agent pipeline** via Google ADK:

1. **ResearchAgent** — searches for places using Google Search
2. **FilterAgent** — scores and ranks results using custom tools:
   - `calculate_distance_score()` — proximity scoring
   - `get_place_category_boost()` — category matching
   - `save_user_preferences()` / `retrieve_user_preferences()` — session state
   - **CalculationAgent** — mathematical scoring via code execution (AgentTool)
3. **FormatterAgent** — presents user-friendly recommendations

### Infrastructure

- **Session management**: `DatabaseSessionService` (persistent) or `InMemorySessionService` (transient), selected by optional topic field
- **Memory**: `InMemoryMemoryService` with auto-save callbacks
- **Context compaction**: `EventsCompactionConfig` (every 4 turns)
- **Observability**: `LoggingPlugin` for tracing
- **Model fallback**: Gemini 2.5 Flash → Gemini 2.5 Flash Lite on 503/429

## Tech Stack

- **AI Framework**: Google Agent Development Kit (ADK)
- **AI Model**: Gemini 2.5 Flash (with automatic fallback)
- **API**: FastAPI + Uvicorn
- **Frontend**: Gradio
- **Language**: Python 3.14
- **Container**: Docker (python:3.14-slim, non-root)
- **CI/CD**: GitHub Actions (SHA-pinned, WIF auth)
- **Secrets**: Google Secret Manager
- **Registry**: Google Artifact Registry (immutable tags, vulnerability scanning)
- **Bot protection**: Cloudflare Turnstile
- **Testing**: pytest

## Repository Structure

```
├── agent/
│   ├── agent_api.py          # FastAPI app (Cloud Run entry point)
│   ├── requirements.txt
│   ├── .env.example
│   ├── __init__.py
│   └── utils/
│       ├── places_agent_core.py   # Multi-agent pipeline logic
│       └── scoring_tools.py       # Distance/category scoring
├── frontend/
│   ├── hf_app.py             # Gradio relay app (HF Space entry point)
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md             # HF Space metadata (YAML frontmatter)
├── tests/
│   └── test_tools.py         # Unit tests for scoring tools
├── .github/
│   ├── workflows/
│   │   ├── deploy-agent-api.yaml
│   │   ├── deploy-hf-app.yaml
│   │   └── qodana_code_quality.yml
│   ├── dependabot.yml
│   └── FUNDING.yml
├── Dockerfile                # Cloud Run container (non-root, 3.14-slim)
├── .dockerignore
├── SECURITY.md
└── LICENSE
```

## Testing

```bash
python3 -m pytest tests/ -v
```

## Environment Variables

### Agent API (Cloud Run — injected via Secret Manager)

| Variable | Source | Note |
|---|---|---|
| `GOOGLE_API_KEY` | Secret Manager | Gemini API key |
| `PROXY_AUTH_TOKEN` | Secret Manager | Shared secret for relay auth |
| `TURNSTILE_SECRET_KEY` | Secret Manager | Cloudflare Turnstile server-side secret |

### Frontend (HF Space — set in Space settings)

| Variable | Type | Description |
|---|---|---|
| `AGENT_API_URL` | Secret | Cloud Run service URL |
| `PROXY_AUTH_TOKEN` | Secret | Shared secret for relay |
| `TURNSTILE_SITE_KEY` | Variable | Cloudflare Turnstile public key |

### Optional model override

```bash
GEMINI_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODEL=gemini-2.5-flash-lite
```

## License

See [LICENSE](LICENSE) file for details.

---

**Built with [Google ADK](https://ai.google.dev/adk), [FastAPI](https://fastapi.tiangolo.com), and [Gradio](https://gradio.app)**
