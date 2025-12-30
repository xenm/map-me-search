# QUICKSTART (Local)

This guide gets you running locally from scratch with the fewest possible steps.

## Requirements

- Python 3.14+

## 1) Install (creates `venv/`, installs deps, creates `.env`)

```bash
chmod +x install.sh
./install.sh
```

## 2) Configure authentication

The installer creates `.env` from `.env.example` (if missing). Edit `.env` and choose one:

### Option A (recommended): Vertex AI via ADC

```bash
gcloud auth application-default login
```

Set in `.env` (or export in your shell):

```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

### Option B (optional): Google AI Studio API key

Set in `.env`:

```bash
GOOGLE_API_KEY=your_api_key
```

## 3) Run

```bash
source venv/bin/activate
python main.py
```

## Optional: model selection / fallback

By default the app uses `gemini-2.5-flash` and will fall back to `gemini-2.5-flash-lite` if the primary model is temporarily overloaded (HTTP 503) or quota-limited (HTTP 429).

You can override this in `.env`:

```bash
GEMINI_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODEL=gemini-2.5-flash-lite
```

## Sanity checks

```bash
source venv/bin/activate
python verify_setup.py
```
