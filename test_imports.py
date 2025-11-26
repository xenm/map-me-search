"""
Test script to verify all Google ADK imports work correctly
Run this before running the main application
"""

print("🧪 Testing Google ADK imports...\n")

# Check if we're in a virtual environment
import sys
if 'venv' in sys.executable or 'site-packages' in sys.executable:
    print("✅ Running in virtual environment")
else:
    print("⚠️  Not in virtual environment - may need to activate venv")
    print("   Try: source venv/bin/activate")
    print()

try:
    print("1️⃣  Testing dotenv import...")
    from dotenv import load_dotenv
    print("   ✅ python-dotenv imported successfully\n")
    
    print("2️⃣  Testing Google ADK Agent imports...")
    from google.adk.agents import LlmAgent, SequentialAgent
    print("   ✅ LlmAgent and SequentialAgent imported successfully\n")
    
    print("3️⃣  Testing additional Agent patterns...")
    try:
        from google.adk.agents import ParallelAgent, LoopAgent
        print("   ✅ ParallelAgent and LoopAgent imported (optional)\n")
    except ImportError:
        print("   ⚠️  ParallelAgent/LoopAgent not available (optional for basic usage)\n")
    
    print("4️⃣  Testing Google ADK Model imports...")
    from google.adk.models.google_llm import Gemini
    print("   ✅ Gemini model imported successfully\n")
    
    print("5️⃣  Testing Google ADK Runner imports...")
    from google.adk.runners import InMemoryRunner
    print("   ✅ InMemoryRunner imported successfully\n")
    
    print("6️⃣  Testing Google ADK Tools imports...")
    from google.adk.tools import google_search, AgentTool, FunctionTool
    print("   ✅ google_search, AgentTool, FunctionTool imported successfully\n")
    
    print("7️⃣  Testing Code Executor imports...")
    from google.adk.code_executors import BuiltInCodeExecutor
    print("   ✅ BuiltInCodeExecutor imported successfully\n")
    
    print("8️⃣  Testing Google GenAI types...")
    from google.genai import types
    print("   ✅ GenAI types imported successfully\n")
    
    print("9️⃣  Testing Session Management imports...")
    from google.adk.sessions import DatabaseSessionService, InMemorySessionService
    from google.adk.apps.app import App, EventsCompactionConfig
    print("   ✅ Session services and App imported successfully\n")
    
    print("🔟 Testing Memory Management imports...")
    from google.adk.memory import InMemoryMemoryService
    from google.adk.tools import load_memory, preload_memory
    from google.adk.tools.tool_context import ToolContext
    print("   ✅ Memory services and tools imported successfully\n")
    
    print("=" * 60)
    print("✅ ALL IMPORTS SUCCESSFUL!")
    print("=" * 60)
    print("\n🎉 Your environment is ready to run the AI Places Search!")
    print("\nNext steps:")
    print("1. Set up your .env file with GOOGLE_API_KEY")
    print("2. Run: python verify_setup.py")
    print("3. Run: python main.py")
    
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("\n🔧 Fix: Install dependencies with:")
    print("   pip install -r requirements.txt")
    exit(1)
    
except Exception as e:
    print(f"\n❌ Unexpected Error: {e}")
    exit(1)
