# 🤖 Multi-Agent Examples

This directory contains examples of different multi-agent patterns using Google's Agent Development Kit (ADK).

## 📁 Files

### `multi_agent_examples.py`
Comprehensive examples demonstrating all major multi-agent patterns.

## 🎯 Pattern Examples

### 1. Sequential Pattern ✅ (Currently Implemented)
**File**: See main `main.py`  
**Use Case**: Order matters, each step builds on previous

```python
Research → Filter → Format
```

**Example**: Places search pipeline
- ResearchAgent finds places
- FilterAgent curates best matches
- FormatterAgent creates beautiful output

### 2. Parallel Pattern 🏃
**File**: `multi_agent_examples.py` (structure example)  
**Use Case**: Independent tasks, speed critical

```python
[Restaurants] ─┐
[Attractions] ─┼→ [Aggregator]
[Hotels]      ─┘
```

**Example**: Multi-category travel research
- Three agents research simultaneously
- Aggregator combines into travel guide

### 3. Loop Pattern 🔄
**File**: `multi_agent_examples.py` (structure example)  
**Use Case**: Iterative refinement, quality improvement

```python
Writer → Critic → Refiner → (loop until approved)
```

**Example**: Iterative recommendation refinement
- Writer creates draft
- Critic reviews quality
- Refiner improves based on feedback

### 4. LLM-Based Coordination 🧠
**File**: `multi_agent_examples.py` (structure example)  
**Use Case**: Dynamic decisions, complex workflows

```python
Coordinator (decides) → [Sub-agents as tools]
```

**Example**: Adaptive search coordinator
- Root agent decides which sub-agents to call
- Dynamic workflow based on user request

### 5. Hybrid Pattern 🔀
**File**: `multi_agent_examples.py` (concept example)  
**Use Case**: Complex systems, multiple patterns combined

```python
Parallel(Sequential pipelines) → Aggregator → Loop(Refinement)
```

**Example**: Multi-city comparison system
- Research multiple cities in parallel
- Each city has its own sequential pipeline
- Final output refined through loop

## 🚀 Running Examples

### View All Patterns
```bash
python examples/multi_agent_examples.py
```

### Run Sequential Demo
```bash
python examples/multi_agent_examples.py --demo
```

### Run Current Implementation
```bash
python main.py
```

## 📊 Pattern Comparison

| Pattern | Execution | Best For | Complexity |
|---------|-----------|----------|------------|
| Sequential | Linear | Order matters | Low |
| Parallel | Concurrent | Independent tasks | Medium |
| Loop | Iterative | Refinement | Medium |
| LLM-Coordinator | Dynamic | Complex decisions | High |
| Hybrid | Mixed | Advanced systems | High |

## 🎓 Learning Path

1. **Start**: Understand Sequential (current implementation)
2. **Learn**: Study pattern examples in `multi_agent_examples.py`
3. **Explore**: Read `MULTI_AGENT_ARCHITECTURE.md`
4. **Extend**: Try adding new agents to current system
5. **Advanced**: Implement Parallel or Loop patterns

## 💡 Extension Ideas

### Beginner
- Add a `ReviewAgent` to fetch reviews
- Add a `MapAgent` to generate map links
- Add a `PriceAgent` to compare prices

### Intermediate
- Convert to Parallel for multi-category search
- Add Loop pattern for quality refinement
- Add conditional branching logic

### Advanced
- Implement hybrid multi-city comparison
- Add dynamic LLM-based coordination
- Create adaptive learning system

## 📚 Resources

- [Google ADK Documentation](https://google.github.io/adk/)
- [Agent Patterns Guide](https://google.github.io/adk/guides/agents/)
- [Sequential Agents](https://google.github.io/adk/guides/sequential-agents/)
- [State Management](https://google.github.io/adk/guides/state/)

## 🐛 Troubleshooting

### Import Errors
```bash
pip install -r requirements.txt
```

### Missing API Key
```bash
cp .env.example .env
# Add your GOOGLE_API_KEY to .env
```

### Pattern Not Available
Some patterns (Parallel, Loop) may require specific ADK versions. The examples show the structure even if not fully runnable.

## 🎉 Next Steps

1. Run the sequential demo
2. Read the pattern examples
3. Experiment with modifications
4. Try implementing a new pattern
5. Share your improvements!

Happy coding! 🚀
