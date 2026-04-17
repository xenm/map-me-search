# QUICKSTART (Local Development)

Run both components locally with the fewest possible steps.

## Requirements

- Python 3.14+
- Docker (for the required local PostgreSQL container)
- Gemini API key (get one from [Google AI Studio](https://aistudio.google.com/app/apikey)) — **optional for local dev**; keep the default `test-api-key-returns-dummy-response` to use the built-in dummy LLM stub that still exercises the full DB → prompt → persistence flow

## 1) Start PostgreSQL (required)

The app no longer ships an in-memory / SQLite fallback — every run reads and writes `topic_preferences` in Postgres.

```bash
docker compose up -d postgres
```

This brings up `postgres:16-alpine` on `localhost:5432` (user/password/db all `mapme`). Tear it down with `docker compose down` (add `-v` to wipe the volume).

## 2) Agent API

```bash
# Install dependencies
pip install -r agent/requirements.txt

# Create .env from template (includes a ready-to-use DATABASE_URL pointing at
# the docker compose container, and a dummy Gemini key for offline dev)
cp agent/.env.example agent/.env
# Optional: edit agent/.env → set GOOGLE_API_KEY=your_real_key for live results

# Start the API server
uvicorn agent.agent_api:app --port 8080
```

The API is now running at `http://localhost:8080`. Verify with:

```bash
curl http://localhost:8080/health
```

## 3) Frontend

In a second terminal:

```bash
# Install dependencies
pip install -r frontend/requirements.txt

# Create .env from template (defaults to localhost:8080 + Turnstile test keys)
cp frontend/.env.example frontend/.env

# Start Gradio
python frontend/hf_app.py
```

Open `http://localhost:7860` in your browser.

## Optional: model selection

By default the agent uses `gemini-2.5-flash` and falls back to `gemini-2.5-flash-lite` on transient 503/429 errors.

Override in your shell:

```bash
export GEMINI_MODEL=gemini-2.5-flash
export GEMINI_FALLBACK_MODEL=gemini-2.5-flash-lite
```

## Running tests

```bash
python3 -m pytest tests/ -v
```
