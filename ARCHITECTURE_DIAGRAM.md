# 🏗️ Multi-Agent System Architecture Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   User Input                                 │
│         "Find coffee shops in San Francisco"                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              InMemoryRunner                                  │
│              (Orchestrates execution)                        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│           SequentialAgent                                    │
│           "PlacesSearchPipeline"                             │
│                                                              │
│   ┌──────────────────────────────────────────────────┐     │
│   │  STAGE 1: ResearchAgent 🔍                       │     │
│   │  ─────────────────────────                       │     │
│   │  Model: Gemini 2.5 Flash                         │     │
│   │  Tools: google_search                            │     │
│   │  Task: Find 5-7 relevant places                  │     │
│   │                                                   │     │
│   │  Output: research_findings                       │     │
│   │  ├─ Place 1 (name, type, description)           │     │
│   │  ├─ Place 2 (name, type, description)           │     │
│   │  ├─ Place 3 (name, type, description)           │     │
│   │  └─ ... (up to 7 places)                        │     │
│   └──────────────────┬───────────────────────────────┘     │
│                      │                                       │
│                      ▼                                       │
│   ┌──────────────────────────────────────────────────┐     │
│   │  STAGE 2: FilterAgent 🎯                         │     │
│   │  ─────────────────────                           │     │
│   │  Model: Gemini 2.5 Flash                         │     │
│   │  Input: {research_findings}                      │     │
│   │  Task: Analyze, rate, select top 5              │     │
│   │                                                   │     │
│   │  Process:                                         │     │
│   │  1. Rate each place (1-10)                       │     │
│   │  2. Remove duplicates                            │     │
│   │  3. Select best matches                          │     │
│   │  4. Rank by relevance                            │     │
│   │                                                   │     │
│   │  Output: filtered_results                        │     │
│   │  ├─ Place A (rating: 9/10)                       │     │
│   │  ├─ Place B (rating: 8/10)                       │     │
│   │  ├─ Place C (rating: 8/10)                       │     │
│   │  ├─ Place D (rating: 7/10)                       │     │
│   │  └─ Place E (rating: 7/10)                       │     │
│   └──────────────────┬───────────────────────────────┘     │
│                      │                                       │
│                      ▼                                       │
│   ┌──────────────────────────────────────────────────┐     │
│   │  STAGE 3: FormatterAgent 🎨                      │     │
│   │  ────────────────────────                        │     │
│   │  Model: Gemini 2.5 Flash                         │     │
│   │  Input: {filtered_results}                       │     │
│   │  Task: Create beautiful output                   │     │
│   │                                                   │     │
│   │  Format:                                          │     │
│   │  📍 Name and type                                │     │
│   │  📝 Description (2-3 sentences)                  │     │
│   │  ⭐ Relevance score                              │     │
│   │  💡 Why it matches preferences                   │     │
│   │  ✨ Summary insights                             │     │
│   │                                                   │     │
│   │  Output: final_recommendations                   │     │
│   └──────────────────┬───────────────────────────────┘     │
│                      │                                       │
└──────────────────────┼───────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Final Output to User                        │
│                                                              │
│  📍 Top Coffee Shops in San Francisco                       │
│  ═════════════════════════════════════                      │
│                                                              │
│  ⭐⭐⭐⭐⭐ Blue Bottle Coffee                                │
│  Artisanal coffee roaster with modern aesthetic...          │
│  Perfect for: Quality coffee enthusiasts                    │
│                                                              │
│  ⭐⭐⭐⭐ Sightglass Coffee                                  │
│  Spacious cafe with house-roasted beans...                  │
│  Perfect for: Remote work and meetings                      │
│                                                              │
│  ... (more results)                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## State Flow

```
┌─────────────────┐
│   User Input    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│    ResearchAgent                    │
│    ─────────────                    │
│    Input: User query                │
│    Tools: google_search             │
│    Output: research_findings        │
└────────┬────────────────────────────┘
         │
         │ research_findings = {
         │   place1: {...},
         │   place2: {...},
         │   ...
         │ }
         │
         ▼
┌─────────────────────────────────────┐
│    FilterAgent                      │
│    ────────────                     │
│    Input: {research_findings}       │
│    Process: Rate & select           │
│    Output: filtered_results         │
└────────┬────────────────────────────┘
         │
         │ filtered_results = {
         │   top_place1: {rating: 9},
         │   top_place2: {rating: 8},
         │   ...
         │ }
         │
         ▼
┌─────────────────────────────────────┐
│    FormatterAgent                   │
│    ─────────────                    │
│    Input: {filtered_results}        │
│    Process: Format beautifully      │
│    Output: final_recommendations    │
└────────┬────────────────────────────┘
         │
         │ final_recommendations = 
         │   "📍 Top Coffee Shops..."
         │
         ▼
┌─────────────────┐
│  Display to     │
│  User           │
└─────────────────┘
```

---

## Agent Communication

```
╔═══════════════════════════════════════════════════════════╗
║             Session State (Shared Memory)                 ║
╠═══════════════════════════════════════════════════════════╣
║                                                           ║
║  research_findings: { ... }  ← Written by ResearchAgent  ║
║       ↓ Read by FilterAgent                              ║
║                                                           ║
║  filtered_results: { ... }   ← Written by FilterAgent    ║
║       ↓ Read by FormatterAgent                           ║
║                                                           ║
║  final_recommendations: "..." ← Written by FormatterAgent║
║       ↓ Returned to user                                 ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
```

---

## Pattern Comparison

### Single Agent (Before)

```
┌──────────────────────┐
│   Single Agent       │
│   ──────────         │
│   Responsibilities:  │
│   • Research         │
│   • Filter           │
│   • Format           │
│   • Everything!      │
└──────────────────────┘
        ↓
   One big black box
   Hard to debug
   Long instructions
```

### Multi-Agent (After)

```
┌────────────────┐    ┌────────────────┐    ┌────────────────┐
│ ResearchAgent  │ →  │  FilterAgent   │ →  │ FormatterAgent │
│ ────────────── │    │ ────────────── │    │ ────────────── │
│ Specialized in │    │ Specialized in │    │ Specialized in │
│ searching      │    │ quality ctrl   │    │ presentation   │
└────────────────┘    └────────────────┘    └────────────────┘
        ↓                     ↓                      ↓
   Clear stages         Easy to debug         Simple testing
```

---

## Code Structure

```
main.py
├── load_environment()
│   └── Load .env and API key
│
├── initialize_multi_agent_system()
│   ├── Setup retry_config
│   │
│   ├── Create ResearchAgent
│   │   ├── name: "ResearchAgent"
│   │   ├── tools: [google_search]
│   │   └── output_key: "research_findings"
│   │
│   ├── Create FilterAgent
│   │   ├── name: "FilterAgent"
│   │   ├── input: {research_findings}
│   │   └── output_key: "filtered_results"
│   │
│   ├── Create FormatterAgent
│   │   ├── name: "FormatterAgent"
│   │   ├── input: {filtered_results}
│   │   └── output_key: "final_recommendations"
│   │
│   └── Create SequentialAgent
│       └── sub_agents: [research, filter, formatter]
│
├── search_places(city, preferences)
│   ├── Initialize multi-agent system
│   ├── Create runner
│   └── Execute with run_debug()
│
└── main()
    ├── Get user input
    ├── Call search_places()
    └── Display results
```

---

## Execution Timeline

```
Time   │ Agent           │ Activity
───────┼─────────────────┼──────────────────────────────────
T0     │ User            │ Enters query
T1     │ Runner          │ Starts pipeline
       │                 │
T2     │ ResearchAgent   │ ⏳ Searching Google...
T3     │ ResearchAgent   │ Found 7 places
T4     │ ResearchAgent   │ ✅ Saved to research_findings
       │                 │
T5     │ FilterAgent     │ ⏳ Analyzing results...
T6     │ FilterAgent     │ Rated all places
T7     │ FilterAgent     │ Selected top 5
T8     │ FilterAgent     │ ✅ Saved to filtered_results
       │                 │
T9     │ FormatterAgent  │ ⏳ Formatting output...
T10    │ FormatterAgent  │ Created beautiful guide
T11    │ FormatterAgent  │ ✅ Saved to final_recommendations
       │                 │
T12    │ Runner          │ Pipeline complete
T13    │ User            │ Receives formatted results
```

---

## Error Handling Flow

```
┌─────────────────┐
│  API Call       │
└────────┬────────┘
         │
         ▼
    ┌─────────┐
    │Success? │
    └────┬────┘
         │
    ┌────┴────┐
    │         │
   YES       NO
    │         │
    │         ▼
    │    ┌─────────────────┐
    │    │ Retry Config    │
    │    │ ──────────────  │
    │    │ Attempts: 5     │
    │    │ Backoff: 7s     │
    │    │ Status: 429,    │
    │    │         500,    │
    │    │         503     │
    │    └────┬────────────┘
    │         │
    │         ▼
    │    ┌──────────┐
    │    │Try again?│
    │    └─────┬────┘
    │          │
    │     ┌────┴────┐
    │     │         │
    │    YES       NO
    │     │         │
    │     └──┐      └─→ ❌ Error
    │        │
    ▼        ▼
┌──────────────────┐
│  Continue        │
│  Pipeline        │
└──────────────────┘
```

---

## Extension Points

### Easy to Add

```
Current Pipeline:
  Research → Filter → Format

Add ReviewAgent:
  Research → Filter → Reviews → Format

Add PriceAgent:
  Research → Filter → Price → Format

Add MapAgent:
  Research → Filter → Maps → Format

Add Multiple:
  Research → Filter → [Reviews, Price, Maps] → Aggregate → Format
```

### Pattern Evolution

```
Current: Sequential
  A → B → C

Next: Add Parallel
  A → [B1, B2, B3] → C

Advanced: Add Loop
  A → [B1, B2, B3] → C → (Quality Check → Refine)⟲

Expert: Hybrid
  [A1, A2] → Sequential(B → C) → Loop(Review → Refine)
```

---

## Performance Characteristics

```
Operation           │ Time    │ Notes
────────────────────┼─────────┼─────────────────────────
ResearchAgent       │ 2-5s    │ Google Search API calls
FilterAgent         │ 1-2s    │ LLM analysis
FormatterAgent      │ 1-2s    │ LLM formatting
────────────────────┼─────────┼─────────────────────────
Total Pipeline      │ 4-9s    │ Sequential execution
────────────────────┼─────────┼─────────────────────────

With Parallel:      │ 3-6s    │ If independent tasks
With Caching:       │ 1-3s    │ If results cached
```

---

## Best Practices Implemented

✅ **Separation of Concerns**
   - Each agent has one clear responsibility

✅ **State Management**
   - Automatic passing via output_key and placeholders

✅ **Error Handling**
   - Retry configuration for reliability

✅ **Testability**
   - Each agent can be tested independently

✅ **Extensibility**
   - Easy to add new agents to pipeline

✅ **Documentation**
   - Clear instructions per agent

✅ **Type Safety**
   - Structured outputs with keys

✅ **Observability**
   - Debug mode shows each stage

---

## Learn More

- Implementation: [main.py](main.py)
- Deep Dive: [MULTI_AGENT_ARCHITECTURE.md](MULTI_AGENT_ARCHITECTURE.md)
- Examples: [examples/](examples/)
- Upgrade Guide: [UPGRADE_SUMMARY.md](UPGRADE_SUMMARY.md)

---

**Built with** ❤️ **using Google Agent Development Kit**
