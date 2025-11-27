# 🔧 Day 4 Bug Fix: Plugin Configuration

## Issue

When running the application with Day 4 observability features, you may encounter this error:

```
❌ Configuration Error: When app is provided, plugins should not be provided 
and should be provided in the app instead.
```

## Root Cause

The initial Day 4 implementation incorrectly added plugins to the `Runner` constructor when using an `App`:

```python
# WRONG - Don't do this
runner = Runner(
    app=app,
    session_service=session_service,
    memory_service=memory_service,
    plugins=plugins  # ❌ Wrong when using App
)
```

## Solution

**Plugins must be added to the `App` constructor, not the `Runner` constructor.**

### Fixed Code

```python
# CORRECT - Do this
# 1. Create plugins list
plugins = [LoggingPlugin(), MetricsTrackingPlugin()]

# 2. Add plugins to App
app = App(
    name="PlacesSearchApp",
    root_agent=root_agent,
    events_compaction_config=EventsCompactionConfig(...),
    plugins=plugins  # ✅ Add plugins here
)

# 3. Create Runner WITHOUT plugins
runner = Runner(
    app=app,
    session_service=session_service,
    memory_service=memory_service
    # No plugins parameter
)
```

## What Was Changed

### File: `main.py`

#### 1. Updated `create_app_with_compaction()` function

**Before:**
```python
def create_app_with_compaction(root_agent):
    app = App(
        name="PlacesSearchApp",
        root_agent=root_agent,
        events_compaction_config=EventsCompactionConfig(...)
    )
    return app
```

**After:**
```python
def create_app_with_compaction(root_agent, plugins=None):
    """Create App with Events Compaction for context optimization.
    
    Args:
        root_agent: The root agent for the app
        plugins: List of plugins to add to the app (Day 4a)
    """
    app = App(
        name="PlacesSearchApp",
        root_agent=root_agent,
        events_compaction_config=EventsCompactionConfig(...),
        plugins=plugins or []  # ✅ Add plugins to App
    )
    return app
```

#### 2. Updated `search_places()` function

**Before:**
```python
# Create App (without plugins)
app = create_app_with_compaction(agent)

# Create plugins list
plugins = [...]

# Add plugins to Runner (WRONG)
runner = Runner(
    app=app,
    plugins=plugins  # ❌ Error!
)
```

**After:**
```python
# Create plugins list FIRST
plugins = []
if enable_logging_plugin:
    plugins.append(LoggingPlugin())
if enable_metrics_plugin:
    plugins.append(MetricsTrackingPlugin())

# Create App WITH plugins
app = create_app_with_compaction(agent, plugins=plugins)  # ✅ Pass plugins here

# Create Runner WITHOUT plugins
runner = Runner(
    app=app,
    session_service=session_service,
    memory_service=memory_service
    # No plugins parameter
)
```

## ADK Plugin Rules

### When Using `App`
```python
# ✅ CORRECT
app = App(root_agent=agent, plugins=[LoggingPlugin()])
runner = Runner(app=app)
```

### When Using Agent Directly (No App)
```python
# ✅ ALSO CORRECT
runner = Runner(
    agent=agent,  # Note: agent, not app
    plugins=[LoggingPlugin()]
)
```

### Summary
- **With App:** Plugins go in `App()` constructor
- **Without App:** Plugins go in `Runner()` constructor

## Verification

After this fix, the application should run successfully:

```bash
python3 main.py
```

**Expected output:**
```
✅ Logging configured: Level=INFO, File=places_search.log
🚀 Application started
✅ Environment loaded
...
📦 Creating App with Context Compaction...
✅ App created with EventsCompactionConfig
   - Compaction interval: 4 turns
   - Overlap size: 1 turn
   - Plugins: 2 enabled  # ✅ Confirms plugins loaded
🔌 LoggingPlugin enabled for comprehensive observability
🔌 MetricsTrackingPlugin enabled for performance metrics
...
```

## Status

✅ **FIXED** - This bug has been resolved in the current version of `main.py`

## Related Documentation

- [DAY4_OBSERVABILITY_EVALUATION_GUIDE.md](DAY4_OBSERVABILITY_EVALUATION_GUIDE.md) - Updated with correct plugin usage
- [GET_STARTED_DAY4.md](GET_STARTED_DAY4.md) - Quick start guide
- [Google ADK Plugin Documentation](https://github.com/google/adk) - Official ADK docs

---

**Fix Applied:** November 27, 2025  
**Affected File:** `main.py`  
**Lines Changed:** ~15 lines
