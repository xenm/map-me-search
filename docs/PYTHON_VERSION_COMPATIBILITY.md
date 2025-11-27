# 🐍 Python Version Compatibility Guide

## Current Status

The application is designed for **Python 3.10+** but includes fallback mechanisms for **Python 3.9**.

## Python Version Requirements

| Python Version | Status | DatabaseSessionService | Features |
|----------------|--------|------------------------|----------|
| **3.10+** | ✅ Fully Supported | ✅ Works | All features available |
| **3.9** | ⚠️ Limited Support | ❌ May fail | Fallback to in-memory sessions |
| **3.8 or lower** | ❌ Not Supported | ❌ Fails | Not tested |

## Known Issues with Python 3.9

### Issue 1: DatabaseSessionService Fails

**Error:**
```
ERROR - ❌ Configuration Error: Failed to create database engine for URL 'sqlite:///places_search_sessions.db'
```

**Cause:**
- Python 3.9.6 is past end-of-life
- SQLAlchemy 2.x has compatibility issues with older Python versions
- ADK's DatabaseSessionService uses SQLAlchemy under the hood

**Solution Applied:**
The application now automatically falls back to `InMemorySessionService`:

```
⚠️ DatabaseSessionService failed: [error details]
⚠️ Using InMemorySessionService instead (sessions won't persist across restarts)
💡 Tip: Upgrade to Python 3.10+ (currently using Python 3.9.6)
✅ InMemorySessionService initialized (fallback mode)
```

**Impact:**
- ✅ Application still works
- ⚠️ Sessions won't persist across restarts
- ⚠️ Each run starts fresh (no conversation history)

### Issue 2: MCP Warnings

**Warning:**
```
MCP requires Python 3.10 or above. Please upgrade your Python version in order to use it.
```

**Cause:**
- ADK's Model Context Protocol (MCP) requires Python 3.10+

**Impact:**
- ⚠️ MCP features unavailable
- ✅ Core functionality still works

### Issue 3: importlib.metadata Warning

**Warning:**
```
An error occurred: module 'importlib.metadata' has no attribute 'packages_distributions'
```

**Cause:**
- Python 3.9 has an older version of `importlib.metadata`

**Impact:**
- ⚠️ Some package introspection may not work
- ✅ Core functionality not affected

## Upgrade to Python 3.10+

### Check Current Version
```bash
python --version
# or
python3 --version
```

### macOS Installation

#### Option 1: Homebrew (Recommended)
```bash
# Install Python 3.11 (stable)
brew install python@3.11

# Verify
python3.11 --version
```

#### Option 2: Python.org
1. Download from [python.org](https://www.python.org/downloads/)
2. Install the package
3. Verify: `python3.11 --version`

### Linux (Ubuntu/Debian)
```bash
# Add deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.11
sudo apt install python3.11 python3.11-venv

# Verify
python3.11 --version
```

### Windows
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer
3. Check "Add Python to PATH"
4. Verify: `python --version`

## Using a Specific Python Version

### Create Virtual Environment with Python 3.11
```bash
# macOS/Linux
python3.11 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Verify
```bash
python --version  # Should show 3.11.x
python main.py    # Should work without warnings
```

## What Works in Python 3.9 (Fallback Mode)

✅ **Still Works:**
- All agent functionality
- Google Search integration
- Custom tools (distance scoring, category boost)
- Code execution (CalculationAgent)
- Memory service
- Observability (logs, metrics)
- Evaluation (unit tests, integration tests)

⚠️ **Limited/Unavailable:**
- Session persistence (uses in-memory instead)
- MCP features
- Some advanced ADK features

## Application Behavior by Python Version

### Python 3.10+ (Recommended)
```
✅ Logging configured: Level=INFO, File=places_search.log
🚀 Application started
✅ Environment loaded
...
🗄️ Initializing Services...
✅ DatabaseSessionService initialized: sqlite:///places_search_sessions.db
✅ InMemoryMemoryService initialized
```

### Python 3.9 (Fallback Mode)
```
✅ Logging configured: Level=INFO, File=places_search.log
🚀 Application started
⚠️ Warning: Python 3.9.6 detected
⚠️ Python 3.10+ is recommended for full compatibility
⚠️ The app will work with limited features (sessions won't persist)

✅ Environment loaded
...
🗄️ Initializing Services...
⚠️ DatabaseSessionService failed: [error]
⚠️ Using InMemorySessionService instead (sessions won't persist across restarts)
💡 Tip: Upgrade to Python 3.10+ (currently using Python 3.9.6)
✅ InMemorySessionService initialized (fallback mode)
✅ InMemoryMemoryService initialized
```

## Code Changes for Compatibility

### Automatic Fallback (Day 4 Fix)

The `initialize_services()` function now handles database failures gracefully:

```python
def initialize_services():
    try:
        session_service = DatabaseSessionService(db_url=db_url)
        print("✅ DatabaseSessionService initialized")
    except Exception as e:
        # Fallback to InMemorySessionService
        print(f"⚠️ DatabaseSessionService failed: {e}")
        print("⚠️ Using InMemorySessionService instead")
        session_service = InMemorySessionService()
        print("✅ InMemorySessionService initialized (fallback mode)")
    
    return session_service, memory_service
```

### Python Version Check

Added at startup:
```python
def check_python_version():
    if sys.version_info < (3, 10):
        print(f"⚠️ Warning: Python {version} detected")
        print("⚠️ Python 3.10+ is recommended for full compatibility")
```

## Troubleshooting

### "Application works but sessions don't persist"
**Cause:** Using Python 3.9 with InMemorySessionService fallback  
**Solution:** Upgrade to Python 3.10+

### "Still getting database errors after upgrade"
**Possible causes:**
1. Still using old Python in venv
   ```bash
   deactivate
   rm -rf venv
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Corrupted database file
   ```bash
   rm places_search_sessions.db
   ```

### "MCP warnings persist"
**Cause:** Python 3.9 or lower  
**Solution:** Upgrade to Python 3.10+  
**Workaround:** Warnings are harmless, core features still work

## Recommended Setup

For the best experience:

1. **Use Python 3.11** (latest stable)
2. **Create fresh virtual environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Run application**
   ```bash
   python main.py
   ```

## Summary

| Feature | Python 3.9 | Python 3.10+ |
|---------|-----------|--------------|
| Core Agent System | ✅ Works | ✅ Works |
| Tools & Search | ✅ Works | ✅ Works |
| Session Persistence | ❌ In-memory only | ✅ Database |
| Memory Service | ✅ Works | ✅ Works |
| Observability | ✅ Works | ✅ Works |
| Evaluation | ✅ Works | ✅ Works |
| MCP Features | ❌ Unavailable | ✅ Available |
| No Warnings | ❌ | ✅ |

**Bottom Line:** The application works in Python 3.9 with reduced features. For full functionality, upgrade to Python 3.10+.

---

**Updated:** November 27, 2025  
**Status:** ✅ Fallback mechanisms implemented
