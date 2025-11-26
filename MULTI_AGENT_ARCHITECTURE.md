# 🤖 Multi-Agent System Architecture

## Overview

This project has been upgraded from a **single-agent system** to a **multi-agent system** using Google's Agent Development Kit (ADK). Instead of one agent doing everything, we now have a team of specialized agents working together.

## 🎯 Why Multi-Agent?

### The Problem with Single Agents
A single "do-it-all" agent becomes problematic as tasks grow complex:
- **Long, confusing instructions** - Hard to maintain
- **Difficult to debug** - Which part failed?
- **Unreliable results** - Too many responsibilities
- **Hard to improve** - Changes affect everything

### The Solution: Team of Specialists
Multiple simple agents collaborating like a real team:
- **Clear responsibilities** - Each agent has one job
- **Easy to test** - Test each specialist independently
- **Maintainable** - Update one agent without breaking others
- **Powerful together** - Collaboration creates better results

---

## 🏗️ Architecture

### Single Agent (Before)
```
User Input → [Single Agent] → Output
              ↓
         Google Search
```

One agent did everything: research, filtering, formatting.

### Multi-Agent Pipeline (After)
```
User Input → [ResearchAgent] → [FilterAgent] → [FormatterAgent] → Output
                ↓
           Google Search
```

Three specialized agents in a **sequential pipeline**.

---

## 👥 Our Agent Team

### 1. ResearchAgent 🔍
**Role**: Information Gatherer  
**Responsibility**: Find places using Google Search

**What it does**:
- Searches for 5-7 relevant places based on city and preferences
- Gathers structured data for each place:
  - Name
  - Type (restaurant, museum, park, etc.)
  - Description
  - Match reasoning

**Tools**: `google_search`  
**Output**: `research_findings` (stored in session state)

**Why specialized?** Focuses only on gathering comprehensive raw data.

---

### 2. FilterAgent 🎯
**Role**: Quality Analyst  
**Responsibility**: Analyze and rank results

**What it does**:
- Reviews all research findings
- Rates each place (1-10 scale) based on preference match
- Removes duplicates and irrelevant results
- Selects top 5 best matches
- Organizes by relevance (best first)

**Input**: `{research_findings}` from ResearchAgent  
**Output**: `filtered_results` (stored in session state)

**Why specialized?** Dedicated to quality control and relevance ranking.

---

### 3. FormatterAgent 🎨
**Role**: Presentation Specialist  
**Responsibility**: Create beautiful final output

**What it does**:
- Takes curated results from FilterAgent
- Formats into user-friendly recommendations
- Adds visual elements (emojis, structure)
- Provides engaging descriptions
- Creates summary insights

**Input**: `{filtered_results}` from FilterAgent  
**Output**: `final_recommendations` (final output)

**Why specialized?** Focuses purely on presentation and user experience.

---

## 🚥 Sequential Workflow Pattern

We use a **SequentialAgent** to orchestrate the team:

```python
root_agent = SequentialAgent(
    name="PlacesSearchPipeline",
    sub_agents=[research_agent, filter_agent, formatter_agent],
)
```

### How it Works
1. **Deterministic Order** - Agents run in exact order listed
2. **Automatic State Passing** - Output of one agent becomes input for next
3. **Reliable Pipeline** - No LLM decides order; it's guaranteed
4. **Linear Flow** - Each step builds on previous

### Pipeline Flow
```
Step 1: ResearchAgent
   ↓ (research_findings)
Step 2: FilterAgent
   ↓ (filtered_results)
Step 3: FormatterAgent
   ↓ (final_recommendations)
Final Output
```

---

## 🔄 State Management

### Output Keys
Each agent stores its output in session state using `output_key`:

```python
research_agent = Agent(
    ...,
    output_key="research_findings",
)
```

### State Placeholders
Later agents access previous outputs using `{placeholder}` syntax:

```python
filter_agent = Agent(
    instruction="Review the research findings: {research_findings}",
    ...,
)
```

This creates an automatic data flow between agents.

---

## 📊 Comparison: Before vs After

| Aspect | Single Agent | Multi-Agent |
|--------|-------------|-------------|
| **Instruction Length** | Very long (all tasks) | Short (one task each) |
| **Debugging** | Hard (what failed?) | Easy (which agent?) |
| **Testing** | Test everything | Test each agent |
| **Maintenance** | Change affects all | Update one agent |
| **Reliability** | Variable | More consistent |
| **Extensibility** | Difficult | Add new agents |

---

## 🎯 Pattern Selection

We chose **Sequential** because:

✅ **Order matters** - Research must happen before filtering  
✅ **Linear pipeline** - Each step builds on previous  
✅ **Predictable** - Guaranteed execution order  
✅ **Simple** - Easy to understand and maintain

### When to Use Other Patterns

**Parallel Pattern** - Use when:
- Tasks are independent
- Speed is critical
- Can run simultaneously
- Example: Research multiple cities at once

**Loop Pattern** - Use when:
- Iterative refinement needed
- Quality improvement cycles
- Feedback and revision
- Example: Writer + Critic loop

**LLM-based Coordination** - Use when:
- Dynamic orchestration needed
- LLM should decide flow
- Complex decision trees
- Example: Adaptive workflows

---

## 💻 Implementation Details

### Code Structure
```python
def initialize_multi_agent_system():
    # 1. Configure retry options
    retry_config = types.HttpRetryOptions(...)
    
    # 2. Create specialized agents
    research_agent = Agent(...)
    filter_agent = Agent(...)
    formatter_agent = Agent(...)
    
    # 3. Create sequential pipeline
    root_agent = SequentialAgent(
        name="PlacesSearchPipeline",
        sub_agents=[research_agent, filter_agent, formatter_agent],
    )
    
    return root_agent
```

### Running the System
```python
runner = InMemoryRunner(agent=root_agent)
response = await runner.run_debug(prompt)
```

---

## 🚀 Benefits We Achieved

### 1. **Better Results**
- Specialized agents excel at their task
- Quality control step ensures relevance
- Professional formatting improves readability

### 2. **Easier Maintenance**
- Update one agent without affecting others
- Clear separation of concerns
- Simple to understand flow

### 3. **Better Debugging**
- Know exactly which agent had issues
- Test each agent independently
- Clear error isolation

### 4. **Extensibility**
- Easy to add new agents (e.g., PriceComparator)
- Can swap agents (e.g., different formatter)
- Modular architecture

---

## 🔮 Future Enhancements

### Potential Additions

1. **ReviewAgent** - Scrape and summarize reviews
2. **PriceComparator** - Compare prices across venues
3. **DistanceCalculator** - Calculate distances from user location
4. **PersonalizerAgent** - Learn from user feedback

### Advanced Patterns

1. **Add Parallel** - Research multiple categories simultaneously
2. **Add Loop** - Refine recommendations based on feedback
3. **Add Conditional** - Branch based on user preferences

---

## 📚 Learn More

- [Google ADK Documentation](https://google.github.io/adk/)
- [Agent Patterns Guide](https://google.github.io/adk/guides/agents/)
- [Sequential Agents](https://google.github.io/adk/guides/sequential-agents/)
- [State Management](https://google.github.io/adk/guides/state/)

---

## 🎉 Summary

You now have a **production-ready multi-agent system** that:
- ✅ Uses specialized agents for clear responsibilities
- ✅ Implements a reliable sequential pipeline
- ✅ Passes state automatically between agents
- ✅ Produces higher quality results
- ✅ Is easy to maintain and extend

**The power of multi-agent systems: Simple specialists working together create complex intelligence!** 🚀
