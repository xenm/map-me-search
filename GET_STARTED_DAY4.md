# 🚀 Get Started with Day 4 Features

## Quick Start (3 Steps)

### 1️⃣ Run with Observability
```bash
python3 main.py
```

**What you'll see:**
- ✅ Application runs normally
- ✅ Logs saved to `places_search.log`
- ✅ Metrics summary at the end

### 2️⃣ View the Logs
```bash
cat places_search.log
```

**What's inside:**
- Agent invocations
- Tool calls
- LLM requests/responses
- Metrics summary

### 3️⃣ Run Evaluations
```bash
python3 run_evaluation.py
```

**What happens:**
- Runs 15 unit tests
- Shows evaluation summary
- Validates tool functionality

---

## What's New?

### 🔎 Observability
- **Logs**: See what happened (`places_search.log`)
- **Traces**: Understand why it happened (execution flow)
- **Metrics**: Track performance (tokens, timing, tool usage)

### 📝 Evaluation
- **Unit Tests**: 15 tests for custom tools
- **Integration Tests**: 5 end-to-end scenarios
- **Regression Detection**: Catch bugs before production

---

## Example Output

### When You Run the App
```
🧹 Cleaned up old log file: places_search.log
✅ Logging configured: Level=INFO, File=places_search.log
2024-11-27 05:38:00,123 - main.py:486 - INFO - 🚀 Application started

🔍 Searching for places in Tokyo based on: 'coffee'
============================================================
🤖 AI Agent is working...

🎯 FINAL RECOMMENDATIONS
============================================================
☕ Top Coffee Shops in Tokyo

1. **Blue Bottle Coffee** ⭐ 9.5/10
   Located in the trendy Nakameguro area...

============================================================

💾 Session saved to memory for future recall

============================================================
📊 METRICS SUMMARY
============================================================
🤖 Agent Invocations: 3
🔧 Total Tool Calls: 5
🧠 LLM Requests: 7
🎯 Total Tokens: 2847 (Input: 1523, Output: 1324)

📋 Tool Usage Breakdown:
   • google_search: 1 calls
   • get_place_category_boost: 3 calls
   • calculate_distance_score: 1 calls
============================================================

✅ Search completed successfully!
📊 Logs saved to: places_search.log
```

### When You Run Tests
```
🚀 AI-Powered Nearby Places Search - Evaluation Suite (Day 4b)
============================================================
🧪 Running Unit Tests
============================================================
tests/test_tools.py::TestDistanceScoreCalculation::test_very_close_distance PASSED
tests/test_tools.py::TestDistanceScoreCalculation::test_close_distance PASSED
tests/test_tools.py::TestDistanceScoreCalculation::test_medium_distance PASSED
...
15 passed in 0.42s

============================================================
📋 Evaluation Summary
============================================================

✅ Available Evaluations:
  • Unit Tests: tests/test_tools.py
  • Integration Tests: tests/integration.evalset.json
  • Evaluation Config: tests/test_config.json

📊 Evaluation Criteria:
  • tool_trajectory_avg_score: 0.7 (70% tool usage match)
  • response_match_score: 0.6 (60% text similarity)

✅ All evaluations completed successfully!
```

---

## Common Use Cases

### Debug a Problem
```bash
# 1. Run app
python3 main.py

# 2. Check for errors
grep "ERROR" places_search.log

# 3. View tool calls
grep "TOOL" places_search.log
```

### Enable Detailed Logging
Edit `main.py` line 483:
```python
configure_logging(log_level=logging.DEBUG)  # Was: INFO
```

Then run:
```bash
python3 main.py
cat places_search.log  # See detailed LLM requests/responses
```

### Test Before Making Changes
```bash
# Establish baseline
python3 run_evaluation.py > baseline.txt

# Make your changes to code
# ...

# Test again
python3 run_evaluation.py > after.txt

# Compare
diff baseline.txt after.txt
```

### Monitor Token Usage (Cost)
```bash
# Run app
python3 main.py

# View token metrics
grep "Total Tokens" places_search.log
```

---

## Key Files

| File | Purpose | Auto-generated? |
|------|---------|-----------------|
| `places_search.log` | Application logs | ✅ Yes |
| `places_search_sessions.db` | Session persistence | ✅ Yes |
| `observability_plugin.py` | Custom metrics | ❌ No |
| `tests/integration.evalset.json` | Test cases | ❌ No |
| `tests/test_tools.py` | Unit tests | ❌ No |
| `run_evaluation.py` | Test runner | ❌ No |

---

## Tips & Tricks

### 1. Real-time Log Monitoring
```bash
tail -f places_search.log
```

### 2. Search Logs Efficiently
```bash
# Find errors
grep "ERROR" places_search.log

# Find tool calls
grep "TOOL" places_search.log

# Find metrics
grep "METRICS SUMMARY" places_search.log -A 20

# Find specific agent
grep "ResearchAgent" places_search.log
```

### 3. Clean Up
```bash
# Remove old logs
rm places_search.log

# Remove session database
rm places_search_sessions.db
```

### 4. Run Specific Tests
```bash
# Run all tests
python3 -m pytest tests/test_tools.py -v

# Run specific test class
python3 -m pytest tests/test_tools.py::TestDistanceScoreCalculation -v

# Run specific test
python3 -m pytest tests/test_tools.py::TestDistanceScoreCalculation::test_very_close_distance -v
```

---

## Learn More

### Quick References
- [EVALUATION_QUICKSTART.md](EVALUATION_QUICKSTART.md) - Commands and examples

### Comprehensive Guides
- [DAY4_OBSERVABILITY_EVALUATION_GUIDE.md](DAY4_OBSERVABILITY_EVALUATION_GUIDE.md) - Complete guide
- [DAY4_ENHANCEMENT_SUMMARY.md](DAY4_ENHANCEMENT_SUMMARY.md) - What's new
- [DAY4_IMPLEMENTATION_COMPLETE.md](DAY4_IMPLEMENTATION_COMPLETE.md) - Technical details

### Previous Days
- [SESSION_MEMORY_GUIDE.md](SESSION_MEMORY_GUIDE.md) - Day 3: Sessions & Memory
- [ADVANCED_TOOLS.md](ADVANCED_TOOLS.md) - Day 2: Tools
- [MULTI_AGENT_ARCHITECTURE.md](MULTI_AGENT_ARCHITECTURE.md) - Day 1: Architecture

---

## Troubleshooting

### "No logs generated"
**Solution:**
```bash
# Check if logging is configured
python3 main.py
ls -la places_search.log
```

### "Tests failing"
**Solution:**
```bash
# Install dependencies
pip3 install -r requirements.txt

# Run tests
python3 -m pytest tests/test_tools.py -v
```

### "Import error for MetricsTrackingPlugin"
**Solution:**
- File `observability_plugin.py` must be in the same directory as `main.py`
- Check file exists: `ls observability_plugin.py`

---

## Next Steps

1. ✅ **Run the app** to see observability in action
2. ✅ **Read the logs** to understand the execution flow
3. ✅ **Run tests** to verify everything works
4. ✅ **Try DEBUG mode** for detailed traces
5. ✅ **Create your own test cases** for specific scenarios

---

## Questions?

### "Where are the logs?"
`places_search.log` in the project root

### "How do I see detailed LLM requests?"
Enable DEBUG mode (see "Enable Detailed Logging" above)

### "How do I track costs?"
Check "Total Tokens" in the metrics summary

### "How do I test my changes?"
Run `python3 run_evaluation.py` before and after changes

---

**You're ready to use production-grade observability and evaluation!** 🎉

Start with: `python3 main.py`

Then explore: `cat places_search.log`
