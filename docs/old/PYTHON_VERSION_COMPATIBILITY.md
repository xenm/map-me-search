## 🐍 Python Version Compatibility Guide

## Current Status

This project requires **Python 3.14+**.

## Python Version Requirements

| Python Version | Status | Notes |
|----------------|--------|-------|
| **3.14+** | ✅ Supported | Required for local dev + CI |
| **< 3.14** | ❌ Not Supported | Upgrade Python |

## Upgrade to Python 3.14+

### Issue 1: DatabaseSessionService Fails

**Error:**
```
ERROR - ❌ Configuration Error: Failed to create database engine for URL 'sqlite:///places_search_sessions.db'
```

### Check Current Version
```bash
python --version
# or
python3 --version
```

### macOS Installation

#### Option 1: Python.org
1. Download from [python.org](https://www.python.org/downloads/)
2. Install the package
3. Verify: `python3 --version`

### Linux

Install Python 3.14 using your distro's preferred method (or from python.org) and ensure `python3 --version` reports 3.14+.

### Windows
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer
3. Check "Add Python to PATH"
4. Verify: `python --version`

## Using a Specific Python Version

### Create Virtual Environment with Python 3.14
```bash
# macOS/Linux
python3 -m venv venv
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
python --version  # Should show 3.14.x
python main.py
```
## Code Changes

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
    if sys.version_info < (3, 14):
        print(f"⚠️ Warning: Python {version} detected")
        print("⚠️ Python 3.14+ is recommended for full compatibility")
```

## Troubleshooting

If you see errors related to database/session setup, first verify you're running Python 3.14+ and that you created your venv using that interpreter.

---

**Updated:** November 27, 2025  
**Status:** ✅ Fallback mechanisms implemented
