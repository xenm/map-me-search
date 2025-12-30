# 🗺️ AI-Powered Nearby Places Search Agent

> **Kaggle AI Agents Intensive - Capstone Project (Concierge Agents Track)**

An intelligent multi-agent system that searches for personalized nearby places using Google's Gemini AI and Agent Development Kit (ADK). The agent learns your preferences, maintains conversational context across sessions, and provides intelligent recommendations with real-time data.

## 🎯 Problem Statement

Planning activities in a new city or finding places that match personal preferences is time-consuming and often requires searching through multiple sources. Users need an intelligent assistant that:
- Understands natural language preferences
- Provides personalized, scored recommendations
- Remembers past conversations and preferences
- Delivers reliable, real-time information

## 💡 Solution

This project demonstrates a sophisticated multi-agent system powered by Google's Gemini AI that:
- **Researches** real-time place information using Google Search
- **Analyzes** and scores results using custom tools and code execution
- **Remembers** user preferences across sessions with persistent memory
- **Presents** beautiful, personalized recommendations
- **Tracks** performance with comprehensive observability
- **Validates** quality through automated evaluation

## ⚡ Quick Start

```bash
# 1. Run installation script (macOS/Linux)
chmod +x install.sh
./install.sh

# 2. Configure authentication (see .env.example)
# - Recommended: Vertex AI (ADC)
# - Alternative: Google AI Studio (API key)

# 3. Run the application
source venv/bin/activate
python main.py
```

## ✨ Features

- 🤖 **Advanced Multi-Agent System**: Specialized AI agents with custom tools
- 🧠 **Session Management**: Persistent conversations that survive restarts (Day 3)
- 💾 **Memory System**: Long-term knowledge storage across sessions (Day 3)
- 🔍 **Smart Search**: Leverages Google Search for real-time information
- 🎯 **Intelligent Scoring**: Custom tools calculate distance and category relevance
- 💻 **Code Execution**: Reliable mathematical calculations using BuiltInCodeExecutor
- 🔧 **Custom Tools**: FunctionTools and AgentTools for sophisticated processing
- 📊 **Context Compaction**: Automatic conversation summarization (Day 3)
- 🎨 **Beautiful Formatting**: Presentation specialist creates engaging output
- 🔄 **Reliable**: Automatic retry logic for API calls
- 📝 **User-Friendly**: Simple command-line interface
- 🔎 **Observability**: Comprehensive logging, traces, and metrics (Day 4)
- 📝 **Agent Evaluation**: Automated testing and regression detection (Day 4)

## 🏆 Capstone Requirements Met

This submission demonstrates **8 key concepts** from the AI Agents Intensive Course:

✅ **Multi-Agent System** (Sequential agents with specialized roles)  
✅ **Custom Tools** (FunctionTools for scoring and state management)  
✅ **Built-in Tools** (Google Search, Code Execution)  
✅ **Agent-as-Tool** (CalculationAgent used by FilterAgent)  
✅ **Sessions & State Management** (DatabaseSessionService with SQLite persistence)  
✅ **Long-term Memory** (InMemoryMemoryService with auto-save callbacks)  
✅ **Context Engineering** (EventsCompactionConfig for conversation summarization)  
✅ **Observability** (LoggingPlugin + custom MetricsTrackingPlugin)  
✅ **Agent Evaluation** (pytest unit tests + ADK evaluation framework)  

## 📖 Documentation

- [docs/QUICKSTART.md](docs/QUICKSTART.md)

Older/legacy docs (including architecture deep-dives) live in `docs/old/`.

## 🚀 Example Usage

```
📍 Enter city name: Tokyo
❤️  What do you like?: ramen and temples

🔍 Searching for places in Tokyo...

📍 SEARCH RESULTS
============================================================
1. Ichiran Ramen (Shibuya) - Famous tonkotsu ramen...
2. Senso-ji Temple - Tokyo's oldest Buddhist temple...
3. Afuri Ramen - Known for yuzu-infused ramen...
...
============================================================
```

## 🏗️ Architecture

The system uses a **sequential multi-agent pipeline** where each agent has a specialized role:

### Agent Pipeline

1. **ResearchAgent** - Searches for places using Google Search API
2. **FilterAgent** - Scores and ranks results using custom tools:
   - `calculate_distance_score()` - Proximity scoring (FunctionTool)
   - `get_place_category_boost()` - Category matching (FunctionTool)
   - `save_user_preferences()` - Session state management (FunctionTool)
   - `retrieve_user_preferences()` - Session state retrieval (FunctionTool)
   - **CalculationAgent** - Mathematical scoring via code execution (AgentTool)
3. **FormatterAgent** - Presents beautiful, user-friendly recommendations

### Infrastructure

- **DatabaseSessionService**: Persistent conversations across restarts (SQLite)
- **InMemoryMemoryService**: Long-term knowledge storage with auto-save callbacks
- **EventsCompactionConfig**: Automatic context summarization (every 4 turns)
- **LoggingPlugin**: Comprehensive observability and tracing
- **MetricsTrackingPlugin**: Custom performance metrics tracking

## 🛠️ Tech Stack

- **Framework**: Google Agent Development Kit (ADK Python)
- **AI Model**: Gemini 2.5 Flash (default) with fallback to Gemini 2.5 Flash Lite on transient overload/quota (503/429)
- **Language**: Python 3.14+
- **Database**: SQLite (session persistence)
- **Tools**: Google Search, Custom FunctionTools, AgentTools, BuiltInCodeExecutor
- **Testing**: pytest, ADK evaluation framework
- **Observability**: Logging, Metrics, Tracing

### System Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ DatabaseSessionService (SQLite Persistence)             │
│ + InMemoryMemoryService (Long-term Knowledge)          │
└─────────────────────────┬───────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Runner (Session + Memory + App)                         │
│  ├─ LoggingPlugin (Observability & Tracing)            │
│  └─ MetricsTrackingPlugin (Performance Metrics)        │
└─────────────────────────┬───────────────────────────────┘
                          ↓
        ┌─────────────────┴─────────────────┐
        ↓                                   ↓
┌──────────────────┐              ┌──────────────────┐
│ ResearchAgent    │              │ Context          │
│ • Google Search  │──────────→   │ Compaction       │
└────────┬─────────┘              │ (Every 4 turns)  │
         ↓                        └──────────────────┘
┌──────────────────────────────────────────────┐
│ FilterAgent                                  │
│  ├─ calculate_distance_score (FunctionTool) │
│  ├─ get_place_category_boost (FunctionTool) │
│  ├─ save_user_preferences (FunctionTool)    │
│  ├─ retrieve_user_preferences (FunctionTool)│
│  ├─ preload_memory (Memory retrieval)       │
│  └─ CalculationAgent (AgentTool)            │
│      └─ BuiltInCodeExecutor (Python code)   │
└────────┬─────────────────────────────────────┘
         ↓
┌──────────────────┐
│ FormatterAgent   │
│ • Beautiful UI   │
└────────┬─────────┘
         ↓
┌──────────────────────────────────────┐
│ Auto-save Callback                   │
│ → Memory persistence                 │
└──────────────────────────────────────┘
         ↓
┌──────────────────────────────────────┐
│ Outputs:                             │
│ • places_search.log (Logs & Traces)  │
│ • Metrics Summary (Performance)      │
│ • User Recommendations               │
└──────────────────────────────────────┘
```

**Learn More:**

See `docs/old/` for legacy deep-dives.

## 📦 Installation

### Automated (Recommended)
```bash
chmod +x install.sh
./install.sh
```

### Manual
```bash
pip3 install -r requirements.txt
cp .env.example .env
# Configure authentication in .env (Vertex AI ADC or GOOGLE_API_KEY)
python3 verify_setup.py
```

## 🔐 Authentication Setup

1. Copy `.env.example` to `.env`
2. Recommended (Vertex AI): authenticate via ADC (e.g. `gcloud auth application-default login`) and set `GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION`
3. Alternative (AI Studio): set `GOOGLE_API_KEY` from [Google AI Studio](https://aistudio.google.com/app/apikey)

## 🧪 Testing & Evaluation

Comprehensive testing ensures agent quality and prevents regression:

### Unit Tests
```bash
# Test custom tools (calculate_distance_score, get_place_category_boost)
python3 -m pytest tests/test_tools.py -v
```

### Integration Evaluation
```bash
# Run all evaluations (unit + integration)
python3 run_evaluation.py

# Run with detailed results
python3 run_evaluation.py --detailed

# Show evaluation summary
python3 run_evaluation.py --summary
```

### Observability
```bash
# Run the app (generates logs and metrics)
python3 main.py

# View comprehensive logs
cat places_search.log
```

**Evaluation Files:**
- `tests/test_tools.py` - Unit tests for custom tools
- `tests/integration.evalset.json` - Integration test cases
- `tests/test_config.json` - Evaluation configuration

**Success Criteria:**
- Tool trajectory match: ≥70%
- Response similarity: ≥60%
- All unit tests passing

## 📋 Requirements

- **Python 3.14+**
- Authentication for Gemini:
  - Recommended: Vertex AI via ADC (e.g. `gcloud auth application-default login`)
  - Optional: Google AI Studio API key (free tier available at [AI Studio](https://aistudio.google.com/app/apikey))
- Internet connection for Google Search API
- ~50MB disk space for dependencies

## 🎓 Educational Value

This project demonstrates production-ready patterns for building AI agents:
- **Multi-agent orchestration** with clear separation of concerns
- **Tool composition** (FunctionTools + AgentTools + Built-in Tools)
- **State management** across sessions with persistence
- **Memory systems** for long-term knowledge retention
- **Context optimization** to manage token limits
- **Observability** for debugging and performance monitoring
- **Quality assurance** through automated evaluation

## 🎯 Use Cases

This architecture can be adapted for:
- Travel planning and itinerary creation
- Restaurant and activity recommendations
- Event discovery and planning
- Local business search
- Real estate and neighborhood exploration

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🆘 Troubleshooting

- **Diagnostics**: Run `python3 verify_setup.py`
- **Legacy docs**: See `docs/old/`

---

## 📊 Project Stats

- **Lines of Code**: ~800 (main.py + observability_plugin.py)
- **Agents**: 4 (Research, Filter, Calculation, Formatter)
- **Custom Tools**: 4 FunctionTools + 1 AgentTool
- **Test Coverage**: Unit tests + Integration evaluation
- **Documentation**: 25+ markdown files

## 🏅 Kaggle AI Agents Intensive

**Track**: Concierge Agents  
**Submission Date**: November 2025  
**Key Concepts**: 8/9 course concepts implemented  
**Model**: Gemini 2.5 Flash (default)  

### Optional model configuration

You can override the default model selection via environment variables:

```bash
GEMINI_MODEL=gemini-2.5-flash
GEMINI_FALLBACK_MODEL=gemini-2.5-flash-lite
```

---

**Built with** ❤️ **using Google Agent Development Kit (ADK Python)**  
**Course**: [5-Day AI Agents Intensive with Google](https://www.kaggle.com/competitions/agents-intensive-capstone-project)
