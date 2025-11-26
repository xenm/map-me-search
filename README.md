# 🗺️ AI-Powered Nearby Places Search

Search for nearby places based on city name and your preferences using Google's Gemini AI and Agent Development Kit.

## ⚡ Quick Start

```bash
# 1. Run installation script (macOS/Linux)
./install.sh

# 2. Add your Google API key to .env file
# Get key from: https://aistudio.google.com/app/apikey

# 3. Run the application
python3 main.py
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

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | Get started in 3 steps |
| [SETUP.md](SETUP.md) | Detailed setup instructions |
| [SESSION_MEMORY_GUIDE.md](SESSION_MEMORY_GUIDE.md) | **🧠 Day 3: Sessions & Memory guide** |
| [DAY3_ENHANCEMENT_SUMMARY.md](DAY3_ENHANCEMENT_SUMMARY.md) | **Day 3: What's new** |
| [ADVANCED_TOOLS.md](ADVANCED_TOOLS.md) | **Day 2: Advanced tools & patterns** |
| [ENHANCEMENT_SUMMARY.md](ENHANCEMENT_SUMMARY.md) | **Day 2: Tools enhancement** |
| [MULTI_AGENT_ARCHITECTURE.md](MULTI_AGENT_ARCHITECTURE.md) | Day 1: Multi-agent system design |
| [examples/](examples/) | Multi-agent pattern examples |
| [PROJECT_README.md](PROJECT_README.md) | Full project documentation |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Technical architecture |
| [COMMANDS.md](COMMANDS.md) | Command reference |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Complete project overview |

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

## 🛠️ Tech Stack

- **Framework**: Google Agent Development Kit (ADK)
- **Architecture**: Multi-Agent System (Sequential Pattern)
- **AI Model**: Gemini 2.5 Flash
- **Language**: Python 3.8+
- **Tools**: Google Search, Custom FunctionTools, AgentTools
- **Execution**: BuiltInCodeExecutor for reliable calculations
- **Sessions**: DatabaseSessionService (SQLite persistence)
- **Memory**: InMemoryMemoryService (long-term knowledge)
- **Context**: EventsCompactionConfig (automatic summarization)

### Complete System Architecture (Days 1-3)

```
DatabaseSessionService (Persistent Conversations)
    ↓
InMemoryMemoryService (Long-term Knowledge)
    ↓
Runner (Session + Memory + App)
    ↓
ResearchAgent (Google Search)
    ↓
FilterAgent (Advanced Scoring + Session State)
    ├─ calculate_distance_score (FunctionTool)
    ├─ get_place_category_boost (FunctionTool)
    ├─ save_user_preferences (Session State)
    ├─ retrieve_user_preferences (Session State)
    └─ CalculationAgent (AgentTool + Code Executor)
    ↓
FormatterAgent (Beautiful Output)
    ↓
Callbacks (auto-save to memory)
```

**Day 1:** Multi-agent pipeline  
**Day 2:** Custom tools + code execution  
**Day 3:** Sessions + memory + context compaction  

Learn more: 
- [SESSION_MEMORY_GUIDE.md](SESSION_MEMORY_GUIDE.md) - Day 3 guide
- [ADVANCED_TOOLS.md](ADVANCED_TOOLS.md) - Day 2 tools
- [MULTI_AGENT_ARCHITECTURE.md](MULTI_AGENT_ARCHITECTURE.md) - Day 1 architecture

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
# Add your GOOGLE_API_KEY to .env
python3 verify_setup.py
```

## 🔐 API Key Setup

1. Get your free API key: [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Copy `.env.example` to `.env`
3. Add your key: `GOOGLE_API_KEY=your_key_here`

## 🧪 Testing

```bash
# Test imports
python3 test_imports.py

# Verify complete setup
python3 verify_setup.py

# Run the app
python3 main.py
```

## 📋 Requirements

- Python 3.8 or higher
- Google Gemini API key (free tier available)
- Internet connection

## 🤝 Contributing

This is an educational project demonstrating Google ADK usage. Feel free to fork and extend!

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🆘 Support

- Check [SETUP.md](SETUP.md) for troubleshooting
- Run `python3 verify_setup.py` for diagnostics
- Review documentation in the docs above

---

**Built with** ❤️ **using Google Agent Development Kit**
