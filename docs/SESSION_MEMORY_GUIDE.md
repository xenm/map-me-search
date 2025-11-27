# 🧠 Session Management & Memory Guide (Day 3)

## Overview

Your multi-agent system now includes **Sessions** for short-term memory and **Memory** for long-term knowledge storage, following Day 3 of the Kaggle 5-day Agents course.

---

## 🎯 What's New?

### Session Management (Short-Term Memory)
- ✅ **DatabaseSessionService** - Persistent sessions across restarts
- ✅ **Session State Tools** - Store/retrieve user preferences
- ✅ **Context Compaction** - Automatic conversation summarization
- ✅ **Event Tracking** - Complete conversation history

### Memory Management (Long-Term Knowledge)
- ✅ **InMemoryMemoryService** - Knowledge storage across sessions
- ✅ **Memory Tools** - `load_memory`, `preload_memory`
- ✅ **Automatic Callbacks** - Save to memory after each turn
- ✅ **Cross-Session Recall** - Remember user preferences forever

---

## 📦 Session vs Memory

| Aspect | Session | Memory |
|--------|---------|--------|
| **Scope** | Single conversation | All conversations |
| **Duration** | Conversation lifetime | Persistent |
| **Storage** | Events (chronological) | Facts (consolidated) |
| **Use Case** | "What did I just say?" | "What are my preferences?" |
| **Example** | Recent messages | "User likes coffee shops" |

Think of it like this:
- **Session** = Your conversation today 💬
- **Memory** = Your knowledge base 🧠

---

## 🏗️ Architecture

### Complete System Flow

```
User Query
    ↓
Runner (with Session & Memory)
    ↓
SessionService (DatabaseSessionService)
    ├─ Creates/retrieves session
    ├─ Tracks conversation events
    └─ Enables context compaction
    ↓
Multi-Agent Pipeline
    ├─ ResearchAgent
    ├─ FilterAgent (with session state tools)
    └─ FormatterAgent
    ↓
MemoryService (InMemoryMemoryService)
    ├─ Stores session → memory
    ├─ Enables cross-session recall
    └─ Provides load_memory/preload_memory
    ↓
Final Response + Persistent Knowledge
```

---

## 🔧 Implementation Details

### 1. Session Service Setup

**What:** Persistent conversation storage

**Code:**
```python
from google.adk.sessions import DatabaseSessionService

def initialize_services():
    # SQLite database for session persistence
    db_url = "sqlite:///places_search_sessions.db"
    session_service = DatabaseSessionService(db_url=db_url)
    return session_service
```

**Features:**
- ✅ Survives application restarts
- ✅ Stores all conversation events
- ✅ Enables session resumption
- ✅ Automatic event logging

**Database:** `places_search_sessions.db` (SQLite)

---

### 2. Session State Management

**What:** Store user preferences within a session

**Custom Tools:**

#### `save_user_preferences()`
```python
def save_user_preferences(
    tool_context: ToolContext, 
    city: str, 
    preferences: str
) -> Dict[str, Any]:
    """Save user's city and preferences to session state."""
    tool_context.state["user:last_city"] = city
    tool_context.state["user:last_preferences"] = preferences
    return {"status": "success"}
```

#### `retrieve_user_preferences()`
```python
def retrieve_user_preferences(
    tool_context: ToolContext
) -> Dict[str, Any]:
    """Retrieve previously saved preferences."""
    city = tool_context.state.get("user:last_city", "Not set")
    preferences = tool_context.state.get("user:last_preferences", "Not set")
    return {
        "status": "success",
        "city": city,
        "preferences": preferences
    }
```

**Use Cases:**
- Remember last searched city
- Recall user preferences
- Share context across sub-agents
- Avoid re-asking for information

**Key Prefix:** `user:` (indicates user-specific data)

---

### 3. Context Compaction

**What:** Automatic conversation summarization to reduce token usage

**Configuration:**
```python
from google.adk.apps.app import App, EventsCompactionConfig

app = App(
    name="PlacesSearchApp",
    root_agent=root_agent,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=4,  # Compact every 4 turns
        overlap_size=1,         # Keep 1 turn for context
    ),
)
```

**How It Works:**

**Before Compaction** (Turn 1-4):
```
Turn 1: User: "I like coffee shops"
        Agent: "Great! I'll remember that."
Turn 2: User: "Tell me about cafes in SF"
        Agent: "Here are 5 cafes..."
Turn 3: User: "What about the second one?"
        Agent: "Blue Bottle is..."
Turn 4: User: "Thanks!"
        Agent: "You're welcome!"
```

**After Compaction** (Turn 5+):
```
Summary: User prefers coffee shops. Discussed cafes in San Francisco.
         Provided details on Blue Bottle Coffee.

[Overlap: Turn 4 kept for continuity]
Turn 5: [New conversation continues...]
```

**Benefits:**
- 📉 Reduces token usage (lower costs)
- ⚡ Faster response times
- 🎯 Maintains key information
- 🔄 Automatic (no manual intervention)

**Settings Explained:**
- `compaction_interval=4`: Summarize after every 4 turns
- `overlap_size=1`: Keep last turn for smooth transition

---

### 4. Memory Service Setup

**What:** Long-term knowledge storage across sessions

**Code:**
```python
from google.adk.memory import InMemoryMemoryService

def initialize_services():
    # Memory service for cross-session recall
    memory_service = InMemoryMemoryService()
    return memory_service
```

**Capabilities:**
- ✅ Cross-session knowledge
- ✅ User preference recall
- ✅ Historical context
- ✅ Searchable memories

**Note:** `InMemoryMemoryService` is for development. Production should use `VertexAiMemoryBankService` (Day 5).

---

### 5. Memory Tools

**Two Patterns:**

#### Reactive: `load_memory` (Agent decides when)
```python
tools=[load_memory]
```

**How It Works:**
1. Agent receives query
2. Agent recognizes need for memory
3. Agent calls `load_memory("preference")`
4. Memory returns relevant facts
5. Agent uses facts to respond

**Pros:** Efficient (only searches when needed)  
**Cons:** Agent might forget to search

---

#### Proactive: `preload_memory` (Always loads)
```python
tools=[preload_memory]
```

**How It Works:**
1. Before every turn, automatically search memory
2. Load relevant memories into agent's context
3. Agent always has access to memories
4. Respond with full knowledge

**Pros:** Guaranteed context  
**Cons:** Higher token usage (searches every turn)

---

### 6. Automatic Memory Storage

**What:** Save sessions to memory automatically using callbacks

**Implementation:**
```python
# Callback function
async def auto_save_to_memory(callback_context):
    """Automatically save session to memory after each turn."""
    await callback_context._invocation_context.memory_service.add_session_to_memory(
        callback_context._invocation_context.session
    )
    print("💾 Session automatically saved to memory")

# Agent with callback
agent = LlmAgent(
    name="AutoMemoryAgent",
    tools=[preload_memory],
    after_agent_callback=auto_save_to_memory  # Triggers after each turn
)
```

**What Happens:**
1. User asks question
2. Agent responds
3. `after_agent_callback` triggers automatically
4. Session → saved to memory
5. Next session can access this knowledge

**Zero Manual Calls!** The framework handles everything.

---

## 🔄 Complete Workflow

### Scenario: User searches for places twice

#### Session 1: "Find coffee shops in San Francisco"

**Steps:**
1. **Create Session** → `session_01` created in `DatabaseSessionService`
2. **Multi-Agent Pipeline** → Searches, filters, formats results
3. **Session State** → Saves `user:last_city = "San Francisco"`, `user:last_preferences = "coffee"`
4. **Save to Memory** → Entire conversation stored in `MemoryService`

**Database:**
- `places_search_sessions.db` → Session events
- `InMemoryMemoryService` → User preferences

---

#### Session 2: "What were my last preferences?"

**Steps:**
1. **Create Session** → `session_02` created (NEW session)
2. **Agent Query** → "What were my last preferences?"
3. **load_memory** → Agent searches memory
4. **Memory Returns** → "coffee shops in San Francisco"
5. **Agent Responds** → "Your last search was for coffee shops in San Francisco"

**Key:** Session 2 doesn't have Session 1's history, but **Memory** bridges the gap!

---

## 💾 Data Storage

### Session Data (DatabaseSessionService)
**File:** `places_search_sessions.db`

**Schema:**
```sql
CREATE TABLE sessions (
    app_name TEXT,
    user_id TEXT,
    session_id TEXT,
    ...
);

CREATE TABLE events (
    app_name TEXT,
    session_id TEXT,
    author TEXT,
    content JSON,
    timestamp DATETIME,
    ...
);
```

**Example Events:**
```json
{
  "session_id": "session_01",
  "author": "user",
  "content": {
    "parts": [{"text": "Find coffee shops in SF"}],
    "role": "user"
  }
}
```

---

### Memory Data (InMemoryMemoryService)
**Storage:** RAM (resets on restart)

**For Production:** Use `VertexAiMemoryBankService` (persistent cloud storage)

**What's Stored:**
- User preferences
- Past search history
- Key facts from conversations
- Cross-session knowledge

---

## 🎯 Use Cases

### Session State Use Cases
1. **Remember Last Search**
   - User: "Show me more like the last search"
   - Agent: Retrieves `user:last_city` and `user:last_preferences`

2. **Conversation Continuity**
   - User: "Tell me about the second place"
   - Agent: Uses session history to know which places were listed

3. **Preference Sharing**
   - ResearchAgent finds places
   - FilterAgent uses same preferences from session state
   - FormatterAgent formats with user's style

---

### Memory Use Cases
1. **Cross-Session Recall**
   ```
   Monday: "I like Italian food"
   Friday: "What restaurants would I like?"
   Agent: "Based on your preference for Italian food..."
   ```

2. **User Profiling**
   ```
   Session 1: Prefers outdoor activities
   Session 2: Likes coffee shops
   Session 3: Agent recommends outdoor cafes (combines knowledge)
   ```

3. **Historical Context**
   ```
   User: "Have I searched San Francisco before?"
   Agent: "Yes, 3 times. You looked for coffee, museums, and parks."
   ```

---

## 🆚 Comparison

### Without Sessions & Memory
```
User: "Find coffee in SF"
Agent: [Searches and responds]

User: "What did I just ask?"
Agent: "I don't remember" ❌

[Restart application]
User: "What was my last search?"
Agent: "I have no idea" ❌
```

---

### With Sessions (No Memory)
```
User: "Find coffee in SF"
Agent: [Searches and responds]

User: "What did I just ask?"
Agent: "You asked about coffee in SF" ✅

[Restart application]
User: "What was my last search?"
Agent: "You asked about coffee in SF" ✅ (if same session)

[Different session]
User: "What was my last search?"
Agent: "I don't know" ❌ (session isolation)
```

---

### With Sessions + Memory
```
User: "Find coffee in SF"
Agent: [Searches and responds]

User: "What did I just ask?"
Agent: "You asked about coffee in SF" ✅

[Restart application, different session]
User: "What was my last search?"
Agent: "You searched for coffee in San Francisco" ✅

User: "What do I usually like?"
Agent: "Based on your history, you prefer coffee shops and outdoor activities" ✅
```

---

## 📊 Feature Matrix

| Feature | Without | Session Only | Session + Memory |
|---------|---------|--------------|------------------|
| **Same turn recall** | ❌ | ✅ | ✅ |
| **Previous turn recall** | ❌ | ✅ | ✅ |
| **Restart persistence** | ❌ | ✅ | ✅ |
| **Cross-session recall** | ❌ | ❌ | ✅ |
| **User profiling** | ❌ | ❌ | ✅ |
| **Long-term knowledge** | ❌ | ❌ | ✅ |
| **Context optimization** | N/A | ✅ (compaction) | ✅ |

---

## 🔍 Debugging & Verification

### Check Session Data
```python
# View session events
session = await session_service.get_session(
    app_name="PlacesSearchApp",
    user_id="default_user",
    session_id="session_01"
)

for event in session.events:
    print(f"{event.author}: {event.content.parts[0].text}")
```

### Check Session State
```python
# View session state
print(session.state)
# Output: {'user:last_city': 'San Francisco', 'user:last_preferences': 'coffee'}
```

### Search Memory
```python
# Search memories
search_result = await memory_service.search_memory(
    app_name="PlacesSearchApp",
    user_id="default_user",
    query="What does the user like?"
)

for memory in search_result.memories:
    print(memory.content.parts[0].text)
```

---

## ⚙️ Configuration Options

### Session Service Options

```python
# In-Memory (development only)
from google.adk.sessions import InMemorySessionService
session_service = InMemorySessionService()

# Database (recommended)
from google.adk.sessions import DatabaseSessionService
session_service = DatabaseSessionService(db_url="sqlite:///sessions.db")

# Production (Day 5)
# Agent Engine Sessions on GCP
```

---

### Memory Service Options

```python
# In-Memory (this project - development)
from google.adk.memory import InMemoryMemoryService
memory_service = InMemoryMemoryService()

# Production (Day 5)
# from google.adk.memory import VertexAiMemoryBankService
# memory_service = VertexAiMemoryBankService(...)
```

---

### Compaction Settings

```python
# Aggressive compaction (frequent summarization)
EventsCompactionConfig(
    compaction_interval=2,  # Every 2 turns
    overlap_size=0          # No overlap
)

# Balanced (recommended)
EventsCompactionConfig(
    compaction_interval=4,  # Every 4 turns
    overlap_size=1          # 1 turn overlap
)

# Conservative (rare summarization)
EventsCompactionConfig(
    compaction_interval=10, # Every 10 turns
    overlap_size=2          # 2 turns overlap
)
```

---

## 🚀 Best Practices

### 1. Session State Keys
✅ **Use prefixes:**
- `user:` - User-specific data
- `app:` - Application-wide data
- `temp:` - Temporary data

```python
tool_context.state["user:name"] = "Sam"
tool_context.state["app:version"] = "2.0"
tool_context.state["temp:search_count"] = 5
```

### 2. Memory Tools Choice
✅ **Use `load_memory` when:**
- Performance is critical
- Memory lookups are rare
- Agent is smart about when to search

✅ **Use `preload_memory` when:**
- Context is always needed
- Missing memories would break experience
- Token cost is not a concern

### 3. Session Management
✅ **Create new sessions when:**
- Starting a completely new conversation
- Different user starts chatting
- Context reset is needed

✅ **Reuse sessions when:**
- Continuing an existing conversation
- User comes back within reasonable time
- Context continuity is important

### 4. Compaction Settings
✅ **Higher interval (6-10 turns):**
- Complex, nuanced conversations
- Need detailed history
- Token cost not critical

✅ **Lower interval (2-4 turns):**
- High-volume conversations
- Simple query-response patterns
- Cost optimization critical

---

## 🎓 Learning Outcomes

From Day 3 of Kaggle Course:

✅ **Session Management**
- Understand Session vs Memory
- Implement DatabaseSessionService
- Use session state for data sharing
- Configure context compaction

✅ **Memory Management**
- Initialize MemoryService
- Transfer sessions to memory
- Enable cross-session recall
- Choose reactive vs proactive tools

✅ **Callbacks**
- Implement `after_agent_callback`
- Automate memory storage
- Hook into agent lifecycle

✅ **Production Patterns**
- Persistent storage
- Context optimization
- Long-term knowledge management

---

## 📚 Files Modified

1. **main.py**
   - Added session service initialization
   - Added memory service initialization
   - Created session state tools
   - Implemented auto-save callback
   - Updated Runner to use Session + Memory
   - Added App with EventsCompactionConfig

2. **test_imports.py**
   - Added session import tests
   - Added memory import tests
   - Added ToolContext import test

---

## 🔮 What's Next?

### Day 4: Observability & Evaluation
- Logging and monitoring
- Agent performance metrics
- Debugging tools
- Production monitoring

### Day 5: Production Deployment
- Vertex AI Memory Bank (semantic search)
- Cloud deployment
- Scaling strategies
- Enterprise features

---

## 💡 Key Insights

### Session = Conversation Thread
"Sessions are like notebook pages - each conversation gets its own page, but they're all in the same notebook."

### Memory = Knowledge Base
"Memory is like your brain's long-term storage - it extracts important facts and makes them searchable across all conversations."

### Compaction = Summarization
"Context compaction is like taking notes - you keep the key points and discard the filler."

### Callbacks = Automation
"Callbacks are like helpful assistants - they do important tasks automatically so you don't have to remember."

---

## 🎉 Summary

Your system now features:

✅ **Persistent Sessions** - Conversations survive restarts  
✅ **Session State** - Share data within conversations  
✅ **Context Compaction** - Optimize token usage  
✅ **Long-Term Memory** - Cross-session knowledge  
✅ **Automatic Storage** - Callbacks handle saving  
✅ **Memory Tools** - Reactive and proactive patterns  

**You've implemented production-grade memory management!** 🚀

---

**Built with** ❤️ **using Google ADK Day 3 Patterns**  
**Session Management & Memory from Kaggle 5-Day Agents Course**
