# 🏗️ Architecture Documentation

## Overview

This application uses Google's Agent Development Kit (ADK) to create an AI-powered places search assistant. The architecture follows a simple single-agent pattern with Google Search integration.

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER INPUT                            │
│            (City Name + Preferences)                     │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│                  main.py                                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Environment Loading (python-dotenv)            │   │
│  │  - Loads authentication config from .env        │   │
│  └─────────────────────────────────────────────────┘   │
│                    │                                     │
│                    ▼                                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Agent Configuration                            │   │
│  │  - Model: Gemini 2.0 Flash Exp                  │   │
│  │  - Tools: google_search                         │   │
│  │  - Retry Logic: Exponential backoff             │   │
│  └─────────────────────────────────────────────────┘   │
│                    │                                     │
│                    ▼                                     │
│  ┌─────────────────────────────────────────────────┐   │
│  │  InMemoryRunner                                 │   │
│  │  - Executes agent with prompt                   │   │
│  │  - Handles async operations                     │   │
│  └─────────────────────────────────────────────────┘   │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              Google ADK Backend                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Gemini AI Model                                │   │
│  │  - Processes natural language input             │   │
│  │  - Determines search strategy                   │   │
│  │  - Synthesizes results                          │   │
│  └───────────────────┬─────────────────────────────┘   │
│                      │                                   │
│                      ▼                                   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Google Search Tool                             │   │
│  │  - Executes web searches                        │   │
│  │  - Retrieves current information                │   │
│  └─────────────────────────────────────────────────┘   │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              FORMATTED RESPONSE                          │
│        (Places with descriptions & reasons)              │
└─────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Main Application (`main.py`)

**Responsibilities**:
- User interaction (CLI)
- Environment configuration
- Agent initialization
- Response formatting

**Key Functions**:
- `load_environment()`: Loads authentication configuration
- `initialize_agent()`: Configures the AI agent with retry logic
- `search_places()`: Executes the search with user input
- `get_user_input()`: Handles user interaction
- `print_response()`: Formats and displays results

### 2. Agent Configuration

**Single Agent Pattern**:
```python
Agent(
    name="places_search_assistant",
    model=Gemini(...),
    description="Search specialist",
    instruction="Detailed system prompt",
    tools=[google_search]
)
```

**Why Single Agent?**
- Simplicity: Easy to understand and maintain
- Efficiency: No coordination overhead
- Sufficient: Google Search tool provides all needed capabilities
- Scalable: Can be extended to multi-agent later

### 3. Retry Logic

**Configuration**:
```python
HttpRetryOptions(
    attempts=5,                              # Max retries
    exp_base=7,                             # Exponential multiplier
    initial_delay=1,                        # Starting delay (seconds)
    http_status_codes=[429, 500, 503, 504] # Retry triggers
)
```

**Retry Schedule**:
- Attempt 1: Immediate
- Attempt 2: ~1 second delay
- Attempt 3: ~7 seconds delay
- Attempt 4: ~49 seconds delay
- Attempt 5: ~343 seconds delay

### 4. Data Flow

1. **User Input** → City name + preferences
2. **Prompt Construction** → Natural language query
3. **Agent Processing** → Gemini analyzes request
4. **Tool Execution** → Google Search retrieves data
5. **Synthesis** → Gemini formats recommendations
6. **Output** → Formatted response to user

## Technology Stack

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| google-adk | Latest | Agent framework and tools |
| python-dotenv | Latest | Environment variable management |

### Google ADK Components

- **Agents**: `Agent` (single-agent pattern)
- **Models**: `Gemini` (2.0-flash-exp)
- **Runners**: `InMemoryRunner` (local execution)
- **Tools**: `google_search` (web search capability)
- **Types**: `HttpRetryOptions` (error handling)

## Security Architecture

### Authentication
```
.env (git-ignored, optional) → os.environ → Agent
```

**Security Measures**:
- ✅ Supports Vertex AI authentication via ADC (recommended)
- ✅ Supports API-key authentication for Google AI Studio (optional)
- ✅ `.env` file excluded from git via `.gitignore`
- ✅ `.env.example` template with placeholders
- ✅ No hardcoded credentials

### Error Handling
- Environment validation before execution
- Graceful handling of API errors
- User-friendly error messages
- Stack trace logging for debugging

## Extension Points

### Adding More Agents

**Sequential Pattern**:
```python
SequentialAgent(
    agents=[research_agent, filter_agent, formatter_agent]
)
```

**Parallel Pattern**:
```python
ParallelAgent(
    agents=[places_agent, reviews_agent, hours_agent]
)
```

**Loop Pattern**:
```python
LoopAgent(
    agent=search_agent,
    condition=lambda x: x.needs_refinement()
)
```

### Custom Tools

```python
@FunctionTool
def get_place_hours(place_name: str) -> dict:
    """Custom tool to fetch business hours"""
    # Implementation
    return hours_data
```

### Additional Features

1. **Caching**: Store recent searches
2. **Filtering**: Price, rating, distance filters
3. **Mapping**: Integration with Maps API
4. **Reviews**: Aggregate review data
5. **Favorites**: User preference storage

## Performance Considerations

### Current Performance
- **Latency**: 2-5 seconds per search (network dependent)
- **Rate Limits**: Handled by retry logic
- **Memory**: Minimal (InMemoryRunner)
- **Scalability**: Suitable for single-user CLI

### Optimization Opportunities
1. **Caching**: Reduce redundant API calls
2. **Batching**: Multiple searches in one session
3. **Async**: Parallel tool execution
4. **Streaming**: Real-time response updates

## Testing Strategy

### Verification Levels

1. **Import Tests** (`test_imports.py`)
   - Validates all dependencies are installed
   - Checks import paths

2. **Setup Verification** (`verify_setup.py`)
   - Python version check
   - Dependency presence
   - Environment configuration

3. **Manual Testing**
   - Run application with sample inputs
   - Verify response quality
   - Test error handling

### Future Testing
- Unit tests for individual functions
- Integration tests with mock API
- End-to-end tests with real API calls

## Deployment Options

### Local Development (Current)
```bash
python main.py
```

### Future Deployment Options

1. **Web Application**
   - Flask/FastAPI backend
   - React/Streamlit frontend
   - Deploy to Vercel/Heroku

2. **API Service**
   - REST API endpoints
   - Docker containerization
   - Deploy to Cloud Run/AWS Lambda

3. **Desktop Application**
   - PyQt/Tkinter GUI
   - Packaged with PyInstaller
   - Cross-platform distribution

## Monitoring & Logging

### Current Logging
- User input/output to console
- Error messages and stack traces
- Success/failure indicators

### Future Monitoring
- API usage metrics
- Response time tracking
- Error rate monitoring
- User behavior analytics

## Configuration Management

### Environment Variables

Choose one:

```
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=<your-project>
GOOGLE_CLOUD_LOCATION=<your-location>
```

or

```
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=<your-key>
```

### Future Configuration
```
MODEL_NAME=gemini-2.0-flash-exp
RETRY_ATTEMPTS=5
SEARCH_RESULTS_LIMIT=10
CACHE_ENABLED=true
LOG_LEVEL=INFO
```

## Conclusion

This architecture provides a solid foundation for AI-powered places search. The single-agent pattern is simple yet powerful, with clear extension points for future enhancements.

---

**Next Steps**:
1. Test the current implementation
2. Gather user feedback
3. Add caching layer
4. Implement multi-agent patterns for complex queries
5. Build web interface
