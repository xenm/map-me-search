# 🧰 Advanced Tools & Patterns Guide

## Overview

This guide documents the advanced ADK tools and patterns implemented in the enhanced multi-agent system.

---

## 🎯 What's New?

### Enhanced Architecture
```
ResearchAgent (Google Search)
    ↓ research_findings
FilterAgent (Custom Tools + Code Execution)
    ├─ calculate_distance_score (FunctionTool)
    ├─ get_place_category_boost (FunctionTool)
    └─ CalculationAgent (AgentTool with BuiltInCodeExecutor)
    ↓ filtered_results
FormatterAgent (Presentation)
    ↓ final_recommendations
```

---

## 🔧 Custom Function Tools

### What are Function Tools?

Function Tools convert your Python functions into agent-callable tools following ADK best practices.

### Best Practices Implemented

1. **Dictionary Returns** with status codes
2. **Clear Docstrings** for LLM understanding
3. **Type Hints** for proper schema generation
4. **Error Handling** with structured responses

### Our Custom Tools

#### 1. `calculate_distance_score()`

**Purpose**: Score places by proximity to city center

```python
def calculate_distance_score(distance_km: float) -> dict:
    """Calculates a relevance score based on distance from city center.
    
    Args:
        distance_km: Distance in kilometers from city center
        
    Returns:
        Dictionary with status and score.
        Success: {"status": "success", "score": 10}
        Error: {"status": "error", "error_message": "Invalid distance"}
    """
```

**Scoring Logic**:
- ≤1 km: 10 points (walking distance)
- ≤3 km: 8 points (short ride)
- ≤5 km: 6 points (medium distance)
- ≤10 km: 4 points (far)
- >10 km: 2 points (very far)

**Usage in Agent**:
```python
tools=[FunctionTool(func=calculate_distance_score)]
```

**Example Call**:
```python
>>> calculate_distance_score(2.5)
{"status": "success", "score": 8, "distance_km": 2.5}

>>> calculate_distance_score(-1)
{"status": "error", "error_message": "Distance cannot be negative"}
```

---

#### 2. `get_place_category_boost()`

**Purpose**: Boost score based on category-preference match

```python
def get_place_category_boost(category: str, preferences: str) -> dict:
    """Calculates a boost score based on how well a category matches preferences.
    
    Args:
        category: Category of the place (e.g., "restaurant", "museum")
        preferences: User's stated preferences
        
    Returns:
        Dictionary with status and boost score.
        Success: {"status": "success", "boost": 2}
    """
```

**Scoring Logic**:
- **Direct match**: +3 points ("coffee" in "coffee shops")
- **Food-related**: +2 points (restaurant, cafe, coffee, bar)
- **Culture-related**: +2 points (museum, gallery, theater, art)
- **Outdoor-related**: +2 points (park, garden, hiking, beach)
- **No match**: 0 points

**Example Calls**:
```python
>>> get_place_category_boost("cafe", "coffee shops")
{"status": "success", "boost": 3, "reason": "Direct match"}

>>> get_place_category_boost("restaurant", "food and dining")
{"status": "success", "boost": 2, "reason": "Food-related match"}

>>> get_place_category_boost("hotel", "museums")
{"status": "success", "boost": 0, "reason": "No special match"}
```

---

## 🤖 Agent Tools Pattern

### What is AgentTool?

AgentTool wraps an agent so it can be used as a tool by another agent. This creates powerful hierarchical agent systems.

### Our Implementation: CalculationAgent

**Purpose**: Provides reliable mathematical calculations using code execution

```python
calculation_agent = LlmAgent(
    name="CalculationAgent",
    model=Gemini(model="gemini-2.5-flash"),
    instruction="""You are a specialized calculator that ONLY responds with Python code.
    
    Generate Python code that calculates weighted scores.""",
    code_executor=BuiltInCodeExecutor(),
)

# Use as a tool in another agent
filter_agent = LlmAgent(
    tools=[AgentTool(agent=calculation_agent)],
)
```

### Why Use BuiltInCodeExecutor?

**Problem**: LLMs aren't reliable at math
```python
# LLM might get this wrong
final_score = (8 * 0.6) + (3 * 0.3) + (10 * 0.1)  # LLM: "around 6.5" ❌
```

**Solution**: Generate code and execute it
```python
# CalculationAgent generates:
base_score = 8
category_boost = 3
distance_score = 10
final_score = (base_score * 0.6) + (category_boost * 0.3) + (distance_score * 0.1)
print(final_score)  # Exact: 6.7 ✅
```

### How It Works

1. **FilterAgent** needs calculation
2. **FilterAgent** calls CalculationAgent as a tool
3. **CalculationAgent** generates Python code
4. **BuiltInCodeExecutor** runs the code safely
5. **Result** returns to FilterAgent
6. **FilterAgent** continues with precise numbers

### Agent Tools vs Sub-Agents

| Aspect | Agent Tools | Sub-Agents |
|--------|-------------|------------|
| **Control Flow** | Agent A calls B, gets result, continues | Agent A transfers to B, B takes over |
| **Response** | Goes back to calling agent | Goes to user |
| **Use Case** | Delegation for tasks | Handoff to specialists |
| **Example** | CalculationAgent | Customer support tiers |

**We use Agent Tools** because FilterAgent needs to:
1. Get calculation results
2. Continue processing with those results
3. Maintain control of the workflow

---

## 💻 Code Executor Deep Dive

### BuiltInCodeExecutor Features

```python
from google.adk.code_executors import BuiltInCodeExecutor

agent = LlmAgent(
    code_executor=BuiltInCodeExecutor(),
)
```

**What it does**:
- Executes Python code in a sandbox
- Returns stdout/stderr
- Provides isolated environment
- Uses Gemini's Code Execution capability

**Safety**:
✅ Sandboxed execution  
✅ No filesystem access  
✅ Limited system calls  
✅ Timeout protection  

### When to Use Code Execution

✅ **Mathematical calculations** - Precise arithmetic  
✅ **Data transformations** - Complex data processing  
✅ **Statistical analysis** - Mean, median, variance  
✅ **Algorithm implementation** - Sorting, searching  

❌ **Don't use for**:
- Simple operations (just add two numbers)
- I/O operations (file access, network)
- Long-running computations
- External library dependencies

---

## 🏗️ Complete Tool Types Reference

### 1. Custom Tools (You Build)

#### Function Tools ✅ (Implemented)
```python
FunctionTool(func=calculate_distance_score)
```
- Convert Python functions to tools
- Full control over logic
- Business rule implementation

#### Long Running Function Tools
```python
def approve_order(amount, tool_context: ToolContext):
    if amount > 1000:
        tool_context.request_confirmation(...)
```
- Human-in-the-loop operations
- Approval workflows
- Pausable operations

#### Agent Tools ✅ (Implemented)
```python
AgentTool(agent=calculation_agent)
```
- Use agents as tools
- Hierarchical agent systems
- Specialist delegation

#### MCP Tools
```python
McpToolset(connection_params=...)
```
- Model Context Protocol servers
- Community integrations
- External system access

#### OpenAPI Tools
```python
OpenApiToolset(spec_url="...")
```
- Auto-generated from API specs
- REST API integration
- No manual coding

### 2. Built-in Tools (Ready to Use)

#### Gemini Tools ✅ (Using)
```python
google_search  # Already implemented
BuiltInCodeExecutor  # Already implemented
```

#### Google Cloud Tools
```python
BigQueryToolset
SpannerToolset
APIHubToolset
```
- Requires Google Cloud access
- Enterprise integrations

#### Third-party Tools
```python
HuggingFaceToolset
GitHubToolset
```
- Existing tool ecosystems

---

## 📊 Tool Selection Guide

```
Decision Tree:

Need exact calculations?
├─ YES → BuiltInCodeExecutor ✅
└─ NO → Continue

Need business logic?
├─ YES → FunctionTool ✅
└─ NO → Continue

Need human approval?
├─ YES → Long Running Function
└─ NO → Continue

Need specialist agent?
├─ YES → AgentTool ✅
└─ NO → Continue

Need external system?
├─ Community integration exists?
│  ├─ YES → MCP Tool
│  └─ NO → Need REST API?
│     ├─ YES → OpenAPI Tool
│     └─ NO → Custom FunctionTool
└─ NO → Built-in Tool
```

---

## 🎯 Implementation Checklist

### Custom Function Tools

- [x] Clear docstrings explaining purpose
- [x] Type hints for all parameters
- [x] Dictionary returns with "status" field
- [x] Error handling with structured responses
- [x] Wrapped in FunctionTool()
- [x] Added to agent's tools list

### Agent Tools

- [x] Specialist agent created (CalculationAgent)
- [x] Clear, focused instructions
- [x] Wrapped in AgentTool()
- [x] Used by parent agent (FilterAgent)
- [x] Proper output_key for state management

### Code Executor

- [x] BuiltInCodeExecutor configured
- [x] Agent instructions emphasize code-only output
- [x] Used for mathematical operations
- [x] Results integrated into workflow

---

## 💡 Best Practices Summary

### 1. Function Design
```python
def my_tool(param: type) -> dict:
    """Clear explanation for LLM.
    
    Args:
        param: What it means
    
    Returns:
        {"status": "success/error", "data": ...}
    """
    try:
        result = do_something(param)
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
```

### 2. Agent Instructions
```python
instruction="""
1. Use tool_name() to do X
2. Check "status" field for errors
3. If status is "error", explain to user
4. Otherwise, use the "data" field
"""
```

### 3. Tool Composition
```python
# Simple → Complex
tools=[
    FunctionTool(simple_lookup),      # Fast, simple
    AgentTool(complex_analysis),      # When needed
]
```

---

## 🚀 Extension Ideas

### Beginner
1. **Rating Tool** - Fetch review scores
2. **Hours Tool** - Check if place is open
3. **Price Tool** - Get price range

### Intermediate
4. **Weather Agent** - Check weather for outdoor activities
5. **Translation Agent** - Translate place descriptions
6. **Sentiment Agent** - Analyze review sentiment

### Advanced
7. **MCP Integration** - Connect to Maps API
8. **Long-Running** - Human approval for bookings
9. **Multi-Modal** - Image analysis of places

---

## 📚 Learn More

### In This Project
- [main.py](main.py) - Complete implementation
- [MULTI_AGENT_ARCHITECTURE.md](MULTI_AGENT_ARCHITECTURE.md) - Architecture overview
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick lookup

### External Resources
- [ADK Tools Guide](https://google.github.io/adk/guides/tools/)
- [Function Tools](https://google.github.io/adk/guides/function-tools/)
- [Agent Tools](https://google.github.io/adk/guides/agent-tools/)
- [Code Execution](https://google.github.io/adk/guides/code-execution/)
- [MCP Tools](https://google.github.io/adk/guides/mcp-tools/)

---

## 🎉 Summary

Your enhanced system now includes:

✅ **Custom Function Tools** - Business logic integration  
✅ **Agent Tools** - Hierarchical agent composition  
✅ **Code Executor** - Reliable calculations  
✅ **Best Practices** - Production-ready patterns  

**Key Insight**: Tools transform isolated LLMs into capable agents that can access external data, execute code, and take actions in the real world!

---

**Built with** ❤️ **using Google Agent Development Kit Advanced Patterns**
