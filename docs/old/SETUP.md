# 🚀 Setup Guide

## Step-by-Step Installation

### 1. Prerequisites Check
Ensure you have Python 3.14 or higher installed:
```bash
python --version
```

### 2. Install Dependencies
Install the required Python packages:
```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install google-adk python-dotenv
```

### 3. Configure Authentication

You can run the project in one of two modes:

#### Option A (recommended): Vertex AI (ADC)

1. Authenticate locally via ADC:
```bash
gcloud auth application-default login
```

2. Set these environment variables (e.g. in `.env`):
```
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your_gcp_project_id
GOOGLE_CLOUD_LOCATION=us-central1
```

#### Option B: Google AI Studio (API key)

1. Get an API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Set these environment variables (e.g. in `.env`):
```
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_actual_api_key_here
```

### 4. Configure Environment Variables

Create your `.env` file:
```bash
cp .env.example .env
```

Edit the `.env` file and configure authentication (Vertex AI ADC or AI Studio API key).

**Important**: Never commit the `.env` file to version control!

### 5. Verify Setup

Run the verification script to ensure everything is configured correctly:
```bash
python verify_setup.py
```

You should see:
```
✅ Python version: 3.x.x
✅ python-dotenv installed
✅ google-adk installed
✅ .env file exists
✅ Authentication is configured
✅ ALL CHECKS PASSED! You're ready to run main.py
```

### 6. Run the Application

Start the application:
```bash
python main.py
```

Enter your search details when prompted:
```
📍 Enter city name: Paris
❤️  What do you like? (e.g., coffee, museums, parks): art museums and cafes
```

## 🐛 Troubleshooting

### Issue: Module not found
```
ModuleNotFoundError: No module named 'google.adk'
```
**Solution**: Install dependencies with `pip install -r requirements.txt`

### Issue: Authentication Error
```
❌ No valid authentication configuration found.
```
**Solution**:
1. Vertex AI (recommended): run `gcloud auth application-default login` and set `GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION`
2. AI Studio: set `GOOGLE_API_KEY`

### Issue: Rate Limit Errors
```
429 Too Many Requests
```
**Solution**: 
- The app has built-in retry logic that handles this automatically
- If it persists, wait a few minutes before trying again
- Check your API quota at [Google AI Studio](https://aistudio.google.com/)

### Issue: Import Errors After Installation
**Solution**: 
1. Make sure you're using the correct Python environment
2. Try reinstalling: `pip uninstall google-adk python-dotenv && pip install google-adk python-dotenv`

## 🔧 Advanced Configuration

### Using a Virtual Environment (Recommended)

Create and activate a virtual environment:

**macOS/Linux**:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows**:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Customizing the AI Agent

You can modify the agent configuration in `main.py`:

**Change the AI Model**:
```python
model=Gemini(
    model="gemini-2.0-flash-exp",  # Try: gemini-pro, gemini-2.5-flash-lite
    retry_options=retry_config
)
```

**Adjust Retry Behavior**:
```python
retry_config = types.HttpRetryOptions(
    attempts=5,        # Increase for more retries
    exp_base=7,        # Higher = longer delays between retries
    initial_delay=1,   # Starting delay in seconds
)
```

**Customize Agent Instructions**:
```python
instruction=(
    "Your custom instructions here..."
)
```

## 📝 Next Steps

Once setup is complete:
1. Run the application with `python main.py`
2. Try different cities and preferences
3. Check out `PROJECT_README.md` for features and development ideas
4. Extend the project with multiple agents or additional tools

## 🆘 Still Having Issues?

1. Run `python verify_setup.py` to diagnose problems
2. Check that your API key is valid at [Google AI Studio](https://aistudio.google.com/)
3. Ensure you have an active internet connection
4. Review the error messages carefully - they usually indicate the problem

---

Happy searching! 🎉
