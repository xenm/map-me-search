# 🔎 Day 4: Agent Observability & Evaluation Guide

## Overview

This guide covers the **Day 4 enhancements** to the AI-Powered Nearby Places Search project:

1. **Observability** - Logs, traces, and metrics for debugging and monitoring
2. **Evaluation** - Systematic testing and regression detection

---

## Part 1: Agent Observability (Day 4a)

### What is Observability?

Observability gives you complete visibility into your agent's decision-making process:

- **What happened?** (Logs)
- **Why did it happen?** (Traces)
- **How well is it performing?** (Metrics)

### Key Components

#### 1. Logging Configuration

The application now includes comprehensive logging:

```python
# Configure logging at startup
configure_logging(
    log_level=logging.INFO,  # Change to DEBUG for detailed traces
    log_file="places_search.log"
)
```

**Log Levels:**
- `DEBUG`: Detailed debugging information (LLM requests/responses, tool calls)
- `INFO`: General informational messages (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages

**Log Location:** `places_search.log` (created automatically)

#### 2. LoggingPlugin (Built-in ADK)

Automatically captures:
- ✅ User messages and agent responses
- ✅ LLM requests and responses
- ✅ Tool calls and results
- ✅ Complete execution traces
- ✅ Timing data

**Usage:**
```python
from google.adk.plugins.logging_plugin import LoggingPlugin

runner = Runner(
    app=app,
    plugins=[LoggingPlugin()]
)
```

**What it logs:**
```
[logging_plugin] 🚀 USER MESSAGE RECEIVED
[logging_plugin] 🤖 AGENT STARTING
[logging_plugin] 🧠 LLM REQUEST
[logging_plugin] 🔧 TOOL STARTING
[logging_plugin] ✅ INVOCATION COMPLETED
```

#### 3. Custom MetricsTrackingPlugin

Tracks performance metrics:

```python
from observability_plugin import MetricsTrackingPlugin

metrics_plugin = MetricsTrackingPlugin()
runner = Runner(
    app=app,
    plugins=[LoggingPlugin(), metrics_plugin]
)
```

**Metrics Tracked:**
- 🤖 Agent invocation count
- 🔧 Tool usage count (with breakdown)
- 🧠 LLM request count
- 🎯 Token usage (input/output)
- ⏱️ Response times

**Get Metrics:**
```python
metrics = metrics_plugin.get_metrics_summary()
print(metrics)
# {
#   "agent_invocations": 3,
#   "total_tool_calls": 5,
#   "llm_requests": 4,
#   "total_tokens": 2500,
#   "tool_usage_breakdown": {
#     "google_search": 2,
#     "calculate_distance_score": 3
#   }
# }
```

### Running with Observability

**Basic (INFO level):**
```bash
python3 main.py
# Logs saved to: places_search.log
```

**Debug Mode (Detailed traces):**

Edit `main.py`:
```python
configure_logging(
    log_level=logging.DEBUG,  # Change from INFO to DEBUG
    log_file="places_search.log"
)
```

**View Logs:**
```bash
# Follow logs in real-time
tail -f places_search.log

# Search for specific events
grep "TOOL" places_search.log
grep "ERROR" places_search.log
```

### Debugging Example

**Scenario:** Agent fails mysteriously

1. **Check logs:**
```bash
grep "ERROR" places_search.log
```

2. **Examine tool calls:**
```bash
grep "TOOL" places_search.log
```

3. **Review LLM requests:**
```bash
grep "LLM REQUEST" places_search.log
```

4. **Check metrics:**
```
[MetricsPlugin] 📊 METRICS SUMMARY
🤖 Agent Invocations: 3
🔧 Total Tool Calls: 0  ← Problem: No tools called!
```

**Root Cause Found:** Tools not properly registered with agent.

---

## Part 2: Agent Evaluation (Day 4b)

### What is Evaluation?

Systematic testing to ensure agent quality and catch regressions.

**Key Differences from Traditional Testing:**
- Agents are non-deterministic
- Users give unpredictable prompts
- Need to test both response AND reasoning path

### Components

#### 1. Test Cases (`integration.evalset.json`)

Structured test scenarios with expected outcomes:

```json
{
  "eval_set_id": "places_search_integration_suite",
  "eval_cases": [
    {
      "eval_id": "basic_coffee_search_tokyo",
      "conversation": [
        {
          "user_content": {
            "parts": [{"text": "Find coffee shops in Tokyo"}]
          },
          "final_response": {
            "parts": [{"text": "Based on your interest in coffee..."}]
          },
          "intermediate_data": {
            "tool_uses": [
              {"name": "google_search", "args": {"query": "coffee Tokyo"}}
            ]
          }
        }
      ]
    }
  ]
}
```

**What's Tested:**
- ✅ Tool trajectory (which tools were called)
- ✅ Tool parameters (correct arguments)
- ✅ Response quality (text similarity)

#### 2. Evaluation Config (`test_config.json`)

Pass/fail thresholds:

```json
{
  "criteria": {
    "tool_trajectory_avg_score": 0.7,  // 70% tool match required
    "response_match_score": 0.6        // 60% text similarity required
  }
}
```

**Metrics Explained:**

| Metric | What it Measures | Threshold |
|--------|------------------|-----------|
| `tool_trajectory_avg_score` | Correct tools used with correct parameters | 0.7 (70%) |
| `response_match_score` | Text similarity between expected and actual | 0.6 (60%) |

#### 3. Unit Tests (`test_tools.py`)

Traditional pytest tests for custom tools:

```python
def test_very_close_distance():
    result = calculate_distance_score(0.5)
    assert result["status"] == "success"
    assert result["score"] == 10
```

**Coverage:**
- ✅ Distance scoring logic
- ✅ Category boost calculation
- ✅ Error handling
- ✅ Edge cases

### Running Evaluations

#### Option 1: Unit Tests Only
```bash
python3 run_evaluation.py --unit-tests
```

#### Option 2: Evaluation Summary
```bash
python3 run_evaluation.py --summary
```

#### Option 3: All Tests (with details)
```bash
python3 run_evaluation.py --detailed
```

#### Option 4: Using pytest directly
```bash
python3 -m pytest tests/test_tools.py -v
```

### Evaluation Results

**Example Output:**
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

**Understanding Results:**

| Status | Score | Meaning |
|--------|-------|---------|
| ✅ PASSED | 1.0 | Perfect match |
| ✅ PASSED | 0.75 | Good match (above threshold) |
| ❌ FAILED | 0.45 | Below threshold - investigate |

### Creating New Test Cases

1. **Run the agent** and save successful interactions
2. **Create test case** in `integration.evalset.json`:

```json
{
  "eval_id": "my_new_test",
  "description": "What this test validates",
  "conversation": [
    {
      "user_content": {"parts": [{"text": "User query"}]},
      "final_response": {"parts": [{"text": "Expected response snippet"}]},
      "intermediate_data": {
        "tool_uses": [
          {"name": "tool_name", "args": {"param": "value"}}
        ]
      }
    }
  ]
}
```

3. **Run evaluation** to verify

### Regression Testing

**Before Making Changes:**
```bash
python3 run_evaluation.py --detailed > baseline.txt
```

**After Making Changes:**
```bash
python3 run_evaluation.py --detailed > after_changes.txt
diff baseline.txt after_changes.txt
```

**What to Look For:**
- Previously passing tests now failing
- Decreased scores in metrics
- New errors in tool usage

---

## Architecture Changes (Day 4)

### Before Day 4
```
Runner → Agent → Tools
```

### After Day 4
```
Runner (with Plugins)
  ├─ LoggingPlugin (observability)
  ├─ MetricsTrackingPlugin (metrics)
  └─ Agent → Tools
```

---

## Files Added/Modified

### New Files
- `observability_plugin.py` - Custom metrics tracking plugin
- `tests/integration.evalset.json` - Integration test cases
- `tests/test_config.json` - Evaluation configuration
- `tests/test_tools.py` - Unit tests
- `tests/__init__.py` - Test package
- `run_evaluation.py` - Evaluation runner script
- `DAY4_OBSERVABILITY_EVALUATION_GUIDE.md` - This guide

### Modified Files
- `main.py` - Added logging, plugins, metrics
- `requirements.txt` - Added pytest

---

## Best Practices

### 1. Logging
- ✅ Use `INFO` for production
- ✅ Use `DEBUG` for development/debugging
- ✅ Review logs after each run
- ❌ Don't leave DEBUG on in production (verbose)

### 2. Metrics
- ✅ Track metrics for performance analysis
- ✅ Monitor token usage for cost control
- ✅ Compare metrics before/after changes
- ❌ Don't obsess over minor variations

### 3. Evaluation
- ✅ Run evaluations before major changes
- ✅ Create test cases for bug fixes
- ✅ Lower thresholds for natural language variation
- ❌ Don't expect 100% match on responses

### 4. Debugging Workflow
1. Enable DEBUG logging
2. Review LoggingPlugin output
3. Check MetricsTrackingPlugin summary
4. Identify failing component
5. Fix and re-evaluate

---

## Troubleshooting

### "No logs generated"
- Check file permissions
- Verify `configure_logging()` is called
- Look for `places_search.log` in project root

### "Tests failing unexpectedly"
- Agent responses vary (LLM non-determinism)
- Lower `response_match_score` threshold
- Focus on `tool_trajectory` for consistency

### "Metrics not showing"
- Ensure `MetricsTrackingPlugin` is imported
- Check `METRICS_PLUGIN_AVAILABLE` flag
- Verify plugin is added to runner

### "Pytest not found"
```bash
pip3 install -r requirements.txt
```

---

## Next Steps

1. **Review logs** from a test run
2. **Run evaluations** to establish baseline
3. **Create custom test cases** for your use cases
4. **Monitor metrics** over time
5. **Adjust thresholds** based on your requirements

---

## Resources

- [ADK Observability Documentation](https://github.com/google/adk)
- [ADK Evaluation Guide](https://github.com/google/adk)
- [Pytest Documentation](https://pytest.org)
- Day 4a Notebook (Observability)
- Day 4b Notebook (Evaluation)

---

**Built with** ❤️ **using Google Agent Development Kit**
