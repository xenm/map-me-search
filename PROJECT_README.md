# 🗺️ AI-Powered Nearby Places Search

An intelligent application that searches for nearby places based on city name and user preferences using Google Agent Development Kit (ADK) and Gemini AI.

## 🌟 Features

- **AI-Powered Search**: Uses Google's Gemini AI model to understand and search for places
- **User Preferences**: Personalized recommendations based on what you like
- **Real-Time Data**: Leverages Google Search for current information
- **Interactive CLI**: Simple command-line interface for easy interaction
- **Robust Error Handling**: Implements retry logic for API calls

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))

### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd map-me-search
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Google API key:
   ```
   GOOGLE_API_KEY=your_actual_api_key_here
   ```

### Usage

Run the application:
```bash
python main.py
```

You'll be prompted to enter:
1. **City Name**: The city you want to search in (e.g., "New York", "London", "Tokyo")
2. **What You Like**: Your preferences (e.g., "coffee shops", "museums", "parks", "Italian restaurants")

### Example

```
🗺️  AI-POWERED NEARBY PLACES SEARCH
============================================================

📍 Enter city name: San Francisco
❤️  What do you like? (e.g., coffee, museums, parks): coffee and books

🔍 Searching for places in San Francisco based on: 'coffee and books'
============================================================
...
📍 SEARCH RESULTS
============================================================
[AI-generated recommendations with specific places, descriptions, and reasons]
============================================================
```

## 🏗️ Project Structure

```
map-me-search/
├── main.py              # Main application script
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .env                 # Your actual API keys (git-ignored)
├── .gitignore          # Git ignore rules
└── PROJECT_README.md   # This file
```

## 🔧 Technical Details

### Architecture

The application uses a single AI agent with the following configuration:

- **Model**: Gemini 2.0 Flash Exp
- **Tools**: Google Search integration
- **Retry Logic**: Automatic retry on rate limits and server errors
- **Runner**: InMemoryRunner for agent execution

### Key Components

1. **Environment Loading**: Securely loads API keys from `.env` file
2. **Agent Initialization**: Configures the AI agent with retry options
3. **Search Function**: Executes the search based on user input
4. **Response Formatting**: Displays results in a user-friendly format

### API Retry Configuration

```python
retry_config = types.HttpRetryOptions(
    attempts=5,                              # Maximum retry attempts
    exp_base=7,                             # Exponential backoff multiplier
    initial_delay=1,                        # Initial delay in seconds
    http_status_codes=[429, 500, 503, 504]  # Retry on these errors
)
```

## 🔐 Security Notes

- **Never commit your `.env` file** - It's already in `.gitignore`
- API keys are loaded from environment variables, not hardcoded
- The `.env.example` file shows the required format without exposing secrets

## 📦 Dependencies

- **google-adk**: Google Agent Development Kit for building AI agents
- **python-dotenv**: Environment variable management

## 🛠️ Development

### Adding More Features

To extend this project, you can:

1. **Add more agents**: Use `SequentialAgent`, `ParallelAgent`, or `LoopAgent` for complex workflows
2. **Add custom tools**: Create `FunctionTool` instances for specialized tasks
3. **Enhance the UI**: Build a web interface using Flask or Streamlit
4. **Add caching**: Implement response caching for repeated searches
5. **Add filters**: Include price range, ratings, or distance filters

### Troubleshooting

**Issue**: `GOOGLE_API_KEY not found`
- **Solution**: Make sure you've created a `.env` file with your API key

**Issue**: Import errors
- **Solution**: Run `pip install -r requirements.txt` to install all dependencies

**Issue**: Rate limit errors
- **Solution**: The retry logic should handle this automatically. If it persists, check your API quota

## 📄 License

This project is for educational and personal use.

## 🤝 Contributing

Feel free to fork this project and add your own enhancements!

## 📞 Support

For issues with:
- **Google ADK**: Check the [official documentation](https://github.com/google/adk)
- **Gemini API**: Visit [Google AI Studio](https://aistudio.google.com/)

---

Made with ❤️ using Google Agent Development Kit
