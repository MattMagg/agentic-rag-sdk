---
description: Manage session, user, and app state in ADK agents using prefixes and context objects
---

# ADK Workflow: State Management

State management in ADK allows agents to persist data across turns, users, and application instances. State is accessed through context objects (`ToolContext`, `CallbackContext`) and organized using key prefixes.

---

## Prerequisites

- [ ] ADK Python installed
- [ ] Basic agent created with `LlmAgent`
- [ ] Session service configured (in-memory or persistent)

---

## Step 1: Understand State Scopes

State is organized into three scopes using key prefixes:

| Prefix | Scope | Persistence | Use Case |
|--------|-------|-------------|----------|
| *(none)* | Session | Current session only | Conversation context, temp data |
| `user:` | User | Across sessions for user | Preferences, user profile |
| `app:` | Application | Across all users | Global config, shared data |
| `temp:` | Temporary | Current turn only | Intermediate calculations |

```python
# Examples of state keys
state["conversation_history"]      # Session-scoped
state["user:preferred_language"]   # User-scoped (persists across sessions)
state["app:rate_limit"]            # App-scoped (shared across all users)
state["temp:intermediate_result"]  # Temporary (cleared after turn)
```

---

## Step 2: Access State in Tools

Use `ToolContext` to read and write state within tool functions:

```python
from google.adk.tools import ToolContext

def get_user_preference(
    preference_key: str,
    tool_context: ToolContext
) -> dict:
    """Read a user preference from state."""
    # Read from user-scoped state
    value = tool_context.state.get(f"user:{preference_key}")
    return {"preference": preference_key, "value": value}


def set_user_preference(
    preference_key: str,
    value: str,
    tool_context: ToolContext
) -> dict:
    """Write a user preference to state."""
    # Write to user-scoped state
    state_key = f"user:{preference_key}"
    tool_context.state[state_key] = value
    return {"status": "saved", "key": state_key, "value": value}


def track_interaction(
    action: str,
    tool_context: ToolContext
) -> dict:
    """Track user interactions in session state."""
    # Initialize interaction log if not exists
    if "interaction_log" not in tool_context.state:
        tool_context.state["interaction_log"] = []
    
    # Append to session-scoped state
    tool_context.state["interaction_log"].append({
        "action": action,
        "timestamp": datetime.now().isoformat()
    })
    
    return {"logged": action}
```

---

## Step 3: Access State in Callbacks

Use `CallbackContext` to access state in agent and model callbacks:

```python
from google.adk.agents import CallbackContext
from google.genai import types
from typing import Optional

def check_rate_limit(
    callback_context: CallbackContext
) -> Optional[types.Content]:
    """Check app-wide rate limit before agent runs."""
    state = callback_context.state
    
    # Read app-scoped counter
    request_count = state.get("app:request_count", 0)
    rate_limit = state.get("app:rate_limit", 100)
    
    if request_count >= rate_limit:
        return types.Content(
            parts=[types.Part.from_text("Rate limit exceeded. Please try later.")]
        )
    
    # Increment counter
    state["app:request_count"] = request_count + 1
    return None
```

---

## Step 4: Initialize Session with State

Pass initial state when creating a session:

```python
from google.adk.sessions import InMemorySessionService

session_service = InMemorySessionService()

# Create session with initial state
session = await session_service.create_session(
    app_name="my_app",
    user_id="user_123",
    session_id="session_456",
    state={
        # Session-scoped defaults
        "conversation_context": "general",
        
        # User-scoped (will persist if using DatabaseSessionService)
        "user:name": "Alice",
        "user:language": "en",
        
        # App-scoped (shared across all users)
        "app:version": "1.0.0",
    }
)
```

---

## Step 5: State in Multi-Agent Systems

State flows through the agent hierarchy:

```python
from google.adk.agents import LlmAgent

# Parent agent with initial state
parent_agent = LlmAgent(
    name="coordinator",
    model="gemini-3-flash-preview",
    instruction="You coordinate between specialist agents.",
    sub_agents=[
        LlmAgent(
            name="researcher",
            model="gemini-3-flash-preview",
            instruction="You research topics.",
        ),
        LlmAgent(
            name="writer",
            model="gemini-3-flash-preview",
            instruction="You write content.",
        ),
    ]
)
```

- **Parent state** is visible to sub-agents
- **Sub-agent state changes** propagate back to parent
- Use prefixes to control scope visibility

---

## Step 6: Persistent State with Database

For persistent state across sessions, use `DatabaseSessionService`:

```python
from google.adk.sessions import DatabaseSessionService

# SQLite for local persistence
session_service = DatabaseSessionService(
    db_url="sqlite:///./agent_state.db"
)

# PostgreSQL for production
session_service = DatabaseSessionService(
    db_url="postgresql://user:pass@host:5432/dbname"
)
```

With persistent services:
- Session state (`key`) persists for the session lifetime
- User state (`user:key`) persists across sessions for the same user
- App state (`app:key`) persists across all users

---

## Step 7: Using output_key for Automatic State Storage

Configure `LlmAgent` to automatically save its output to state:

```python
from google.adk.agents import LlmAgent

agent = LlmAgent(
    name="summarizer",
    model="gemini-3-flash-preview",
    instruction="Summarize the provided text.",
    output_key="last_summary",  # Auto-saves output to state["last_summary"]
)
```

The agent's final response text is automatically stored in `state["last_summary"]`.

---

## Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `output_key` | `str` | State key to auto-save agent output |
| `state` | `dict` | Initial state when creating session |

### State Class Methods

```python
from google.adk.sessions.state import State

# Prefix constants
State.APP_PREFIX    # "app:"
State.USER_PREFIX   # "user:"
State.TEMP_PREFIX   # "temp:"
```

---

## Common Patterns

### 1. Track Conversation History

```python
def add_to_history(message: str, tool_context: ToolContext) -> dict:
    """Add message to conversation history."""
    history = tool_context.state.get("history", [])
    history.append({"role": "user", "content": message})
    tool_context.state["history"] = history
    return {"added": True}
```

### 2. User Preferences

```python
def get_preferences(tool_context: ToolContext) -> dict:
    """Get all user preferences."""
    return {
        "language": tool_context.state.get("user:language", "en"),
        "timezone": tool_context.state.get("user:timezone", "UTC"),
        "notifications": tool_context.state.get("user:notifications", True),
    }
```

### 3. Feature Flags

```python
def check_feature(feature_name: str, tool_context: ToolContext) -> bool:
    """Check if app feature is enabled."""
    return tool_context.state.get(f"app:feature:{feature_name}", False)
```

### 4. Caching Results

```python
def cached_lookup(key: str, tool_context: ToolContext) -> dict:
    """Look up with caching."""
    cache_key = f"temp:cache:{key}"
    cached = tool_context.state.get(cache_key)
    
    if cached:
        return {"result": cached, "from_cache": True}
    
    # Perform lookup
    result = expensive_lookup(key)
    tool_context.state[cache_key] = result  # Cache for this turn
    
    return {"result": result, "from_cache": False}
```

---

## Integration Points

- **With Callbacks:** Use `callback_context.state` in before/after callbacks
- **With Tools:** Use `tool_context.state` in tool functions
- **With Runner:** State persists across turns within a session
- **With Plugins:** Plugins access state via `invocation_context.session.state`

---

## Verification

```bash
adk run agent_folder
```

Test state persistence:

```python
# Turn 1: Set state
await runner.run_async(user_id="user1", session_id="s1", new_message="set preference theme=dark")

# Turn 2: Read state  
await runner.run_async(user_id="user1", session_id="s1", new_message="what is my theme preference?")

# Verify state was persisted
session = await session_service.get_session(app_name="app", user_id="user1", session_id="s1")
print(session.state.get("user:theme"))  # Should be "dark"
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| State not persisting | Using `InMemorySessionService` | Switch to `DatabaseSessionService` for persistence |
| User state not shared | Wrong prefix | Use `user:` prefix for cross-session data |
| State cleared each turn | Using `temp:` prefix | Use unprefixed keys for session scope |
| State conflicts in multi-agent | Same key names | Use agent-specific prefixes or namespaces |

---

## Best Practices

1. **Use the Right Context**: Always use `ToolContext` or `CallbackContext` to modify state, not direct session access
2. **Prefix Correctly**: Match prefix to intended scope (`user:`, `app:`, `temp:`, or none)
3. **Don't Modify Session Directly**: Avoid `session.state["key"] = value`; use context objects instead
4. **Initialize Defaults**: Set defaults when creating sessions for required state keys
5. **Namespace Keys**: Use descriptive, namespaced keys like `user:preferences:language`

---

## References

- State Management (docs/sessions/state.md)
- Context Objects (docs/context/index.md)
- Tool Context (docs/tools-custom/index.md)
- Session State Tutorial (docs/tutorials/agent-team.md)
