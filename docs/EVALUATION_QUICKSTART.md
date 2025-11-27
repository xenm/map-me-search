# 🧪 Evaluation & Observability Quick Start

## One-Command Testing

```bash
# Run everything
python3 run_evaluation.py
```

---

## Observability (Logs & Metrics)

### 1. Run with Logging
```bash
python3 main.py
```

**Output:** `places_search.log`

### 2. View Logs
```bash
# Real-time monitoring
tail -f places_search.log

# Search for errors
grep "ERROR" places_search.log

# View metrics summary
grep "METRICS SUMMARY" places_search.log -A 20
```

### 3. Enable Debug Mode
Edit `main.py` line 483:
```python
configure_logging(log_level=logging.DEBUG)  # Change from INFO
```

Then run:
```bash
python3 main.py
```

**Result:** Detailed LLM requests/responses in logs

---

## Evaluation (Testing)

### Unit Tests
```bash
# Run all unit tests
python3 -m pytest tests/test_tools.py -v

# Run specific test
python3 -m pytest tests/test_tools.py::TestDistanceScoreCalculation::test_very_close_distance -v
```

### Integration Tests (ADK Eval)

**Note:** Requires ADK agent directory structure

```bash
# Show evaluation summary
python3 run_evaluation.py --summary

# Run unit tests only
python3 run_evaluation.py --unit-tests
```

---

## What Gets Logged?

### LoggingPlugin Output
```
[logging_plugin] 🚀 USER MESSAGE RECEIVED
[logging_plugin] 🤖 AGENT STARTING: ResearchAgent
[logging_plugin] 🧠 LLM REQUEST
[logging_plugin] 🧠 LLM RESPONSE
[logging_plugin] 🔧 TOOL STARTING: google_search
[logging_plugin] 🔧 TOOL COMPLETED: google_search
[logging_plugin] ✅ AGENT COMPLETED
```

### MetricsTrackingPlugin Output
```
📊 METRICS SUMMARY
🤖 Agent Invocations: 3
🔧 Total Tool Calls: 5
🧠 LLM Requests: 7
🎯 Total Tokens: 2847 (Input: 1523, Output: 1324)

📋 Tool Usage Breakdown:
   • google_search: 1 calls
   • get_place_category_boost: 3 calls
   • calculate_distance_score: 1 calls
```

---

## Evaluation Results Example

```
============================================================
Eval Run Summary
places_search_integration_suite:
  Tests passed: 4
  Tests failed: 1
============================================================

Eval Id: basic_coffee_search_tokyo
Overall Eval Status: PASSED
-------------------------------------------------------------
Metric: tool_trajectory_avg_score, Status: PASSED, Score: 1.0
Metric: response_match_score, Status: PASSED, Score: 0.85
-------------------------------------------------------------
```

---

## File Locations

| File | Purpose |
|------|---------|
| `places_search.log` | Main log file (auto-generated) |
| `tests/integration.evalset.json` | Integration test cases |
| `tests/test_config.json` | Evaluation thresholds |
| `tests/test_tools.py` | Unit tests |
| `run_evaluation.py` | Test runner script |
| `observability_plugin.py` | Custom metrics plugin |

---

## Common Commands

```bash
# Run app with observability
python3 main.py

# View logs
cat places_search.log

# Run tests
python3 run_evaluation.py

# Run specific unit test
python3 -m pytest tests/test_tools.py::TestDistanceScoreCalculation -v

# Clean logs
rm places_search.log
```

---

## Debugging Workflow

1. **Run app**: `python3 main.py`
2. **Check logs**: `cat places_search.log`
3. **Find errors**: `grep ERROR places_search.log`
4. **View tool calls**: `grep TOOL places_search.log`
5. **Check metrics**: `grep "METRICS SUMMARY" places_search.log -A 20`
6. **Enable DEBUG**: Edit `main.py` → `logging.DEBUG`
7. **Re-run**: `python3 main.py`

---

## Key Metrics to Monitor

- **Agent Invocations**: How many agents ran
- **Tool Calls**: Which tools were used (and how often)
- **LLM Requests**: How many API calls made
- **Token Usage**: Cost tracking (input + output tokens)
- **Response Times**: Performance bottlenecks

---

## Next Steps

1. ✅ Run `python3 main.py` to generate logs
2. ✅ View `places_search.log` to see observability in action
3. ✅ Run `python3 run_evaluation.py` to execute tests
4. ✅ Read [DAY4_OBSERVABILITY_EVALUATION_GUIDE.md](DAY4_OBSERVABILITY_EVALUATION_GUIDE.md) for details

---

**Pro Tip:** Always run evaluations before major changes to catch regressions!
