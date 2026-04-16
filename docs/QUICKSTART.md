# QUICKSTART (Local Development)

Run both components locally with the fewest possible steps.

## Requirements

- Python 3.14+
- Gemini API key (get one from [Google AI Studio](https://aistudio.google.com/app/apikey))

## 1) Agent API

```bash
# Install dependencies
pip install -r agent/requirements.txt

# Create .env from template, then add your Gemini API key
cp agent/.env.example agent/.env
# Edit agent/.env → set GOOGLE_API_KEY=your_key

# Start the API server
uvicorn agent.agent_api:app --port 8080
```

The API is now running at `http://localhost:8080`. Verify with:

```bash
curl http://localhost:8080/health
```

## 2) Frontend

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
