# ⚡ Multi-Agent System Quick Reference

## 🎯 Pattern at a Glance

```
Sequential Pattern: ResearchAgent → FilterAgent → FormatterAgent
```

---

## 📝 Core Concepts

### Sequential Agent
```python
SequentialAgent(
    name="Pipeline",
    sub_agents=[agent1, agent2, agent3],
)
```
✅ Runs agents in guaranteed order  
✅ Automatic state passing  
✅ Deterministic execution  

### Output Keys
```python
Agent(
    output_key="my_result",  # Save to session state
)
```
✅ Stores agent output  
✅ Available to later agents  
✅ Automatic state management  

### State Placeholders
```python
Agent(
    instruction="Process this: {previous_result}",
)
```
✅ Access previous outputs  
✅ Auto-injection from state  
✅ Simple variable syntax  

---

## 🤖 Our Agents

### 1. ResearchAgent 🔍
```python
• Tools: google_search
• Output: research_findings
• Job: Find 5-7 relevant places
```

### 2. FilterAgent 🎯
```python
• Input: {research_findings}
• Output: filtered_results
• Job: Rate, filter, rank top 5
```

### 3. FormatterAgent 🎨
```python
• Input: {filtered_results}
• Output: final_recommendations
• Job: Create beautiful output
```

---

## 🔄 Data Flow

```python
User Query
    ↓
research_findings    # ResearchAgent output
    ↓
filtered_results     # FilterAgent output
    ↓
final_recommendations # FormatterAgent output
    ↓
Display to User
```

---

## 💻 Code Snippets

### Creating an Agent
```python
agent = Agent(
    name="MyAgent",
    model=Gemini(model="gemini-2.5-flash", retry_options=retry_config),
    instruction="What this agent does...",
    tools=[tool1, tool2],  # Optional
    output_key="my_output",
)
```

### Creating Sequential Pipeline
```python
pipeline = SequentialAgent(
    name="MyPipeline",
    sub_agents=[agent1, agent2, agent3],
)
```

### Running the Pipeline
```python
runner = InMemoryRunner(agent=pipeline)
response = await runner.run_debug("User query here")
```

### Retry Configuration
```python
retry_config = types.HttpRetryOptions(
    attempts=5,
    exp_base=7,
    initial_delay=1,
    http_status_codes=[429, 500, 503, 504],
)
```

---

## 🎨 Pattern Templates

### Sequential Pattern
```python
# When: Order matters
agent1 = Agent(name="A", output_key="a_output")
agent2 = Agent(name="B", instruction="Use {a_output}", output_key="b_output")
agent3 = Agent(name="C", instruction="Use {b_output}")

pipeline = SequentialAgent(sub_agents=[agent1, agent2, agent3])
```

### Parallel Pattern (Structure)
```python
# When: Independent tasks
parallel = ParallelAgent(sub_agents=[agent1, agent2, agent3])
aggregator = Agent(instruction="Combine {a}, {b}, {c}")

pipeline = SequentialAgent(sub_agents=[parallel, aggregator])
```

### Loop Pattern (Structure)
```python
# When: Iterative refinement
critic = Agent(instruction="Review {draft}")
refiner = Agent(instruction="Improve based on {critique}")

loop = LoopAgent(sub_agents=[critic, refiner], max_iterations=3)
pipeline = SequentialAgent(sub_agents=[writer, loop])
```

---

## 🛠️ Common Tasks

### Adding a New Agent
1. Create the agent
   ```python
   new_agent = Agent(
       name="NewAgent",
       instruction="...",
       output_key="new_output",
   )
   ```

2. Insert into pipeline
   ```python
   pipeline = SequentialAgent(
       sub_agents=[
           research_agent,
           new_agent,      # ← Add here
           filter_agent,
           formatter_agent,
       ],
   )
   ```

3. Use its output in next agent
   ```python
   next_agent = Agent(
       instruction="Process {new_output}...",
   )
   ```

### Accessing Previous Outputs
```python
Agent(
    instruction="""
    Research: {research_findings}
    Filtered: {filtered_results}
    Process both...
    """,
)
```

### Adding Tools
```python
from google.adk.tools import google_search, FunctionTool

def my_function():
    return "result"

agent = Agent(
    tools=[
        google_search,
        FunctionTool(my_function),
    ],
)
```

---

## 🐛 Debugging

### Run Debug Mode
```python
response = await runner.run_debug("query")  # Shows each step
```

### Check Agent Output
```python
# Each agent's output is stored in session state with its output_key
# Use run_debug to see intermediate outputs
```

### Test Individual Agent
```python
# Create runner with just one agent
test_runner = InMemoryRunner(agent=single_agent)
result = await test_runner.run_debug("test input")
```

---

## ⚠️ Common Pitfalls

### ❌ Placeholder Typo
```python
# Wrong
instruction="Use {research_finding}"  # Missing 's'

# Correct
instruction="Use {research_findings}"  # Matches output_key
```

### ❌ Missing output_key
```python
# Wrong
agent1 = Agent(...)  # No output_key

# Correct
agent1 = Agent(output_key="result")  # Can be referenced
```

### ❌ Circular Dependencies
```python
# Wrong
agent1 = Agent(instruction="Use {b}", output_key="a")
agent2 = Agent(instruction="Use {a}", output_key="b")

# Correct: Linear flow
agent1 = Agent(output_key="a")
agent2 = Agent(instruction="Use {a}")
```

---

## 📊 Decision Tree

```
Need guaranteed order?
├─ YES → Sequential
└─ NO
   └─ Tasks independent?
      ├─ YES → Parallel
      └─ NO
         └─ Need refinement?
            ├─ YES → Loop
            └─ NO → LLM Coordinator
```

---

## 🚀 Performance Tips

1. **Parallel for Speed**: Use ParallelAgent for independent tasks
2. **Cache Results**: Store frequently-used results
3. **Limit Iterations**: Set max_iterations in LoopAgent
4. **Optimize Instructions**: Clear, concise prompts are faster
5. **Choose Right Model**: Faster models for simple tasks

---

## 📚 Quick Links

| Resource | Link |
|----------|------|
| Main Code | [main.py](main.py) |
| Architecture | [MULTI_AGENT_ARCHITECTURE.md](MULTI_AGENT_ARCHITECTURE.md) |
| Examples | [examples/](examples/) |
| Diagrams | [ARCHITECTURE_DIAGRAM.md](ARCHITECTURE_DIAGRAM.md) |
| Upgrade Guide | [UPGRADE_SUMMARY.md](UPGRADE_SUMMARY.md) |

---

## 🎓 Learning Path

1. ✅ **Understand Sequential** (Current implementation)
2. 📖 Read MULTI_AGENT_ARCHITECTURE.md
3. 🔍 Explore examples/multi_agent_examples.py
4. ✏️ Modify existing agents
5. 🆕 Add a new agent to pipeline
6. 🚀 Try Parallel or Loop patterns

---

## 💡 Extension Ideas

### Beginner
```python
# Add ReviewAgent
review_agent = Agent(
    name="ReviewAgent",
    instruction="Find reviews for {filtered_results}",
    tools=[google_search],
    output_key="reviews",
)
```

### Intermediate
```python
# Add conditional logic
# Different paths based on preferences
```

### Advanced
```python
# Implement parallel multi-category search
# Add loop-based quality refinement
# Create adaptive coordinator
```

---

## 🔑 Key Takeaways

✅ **Sequential** = Guaranteed order, linear flow  
✅ **output_key** = Save to session state  
✅ **{placeholder}** = Access previous outputs  
✅ **Specialized agents** = Clear responsibilities  
✅ **Composable patterns** = Mix and match  

---

## 🆘 Help

```bash
# Test setup
python test_imports.py

# Verify environment
python verify_setup.py

# Run application
python main.py

# Try examples
python examples/multi_agent_examples.py
```

---

**Pro Tip**: Start simple, test often, add complexity gradually! 🚀
