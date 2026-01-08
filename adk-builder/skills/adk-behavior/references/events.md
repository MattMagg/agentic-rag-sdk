---
description: Understand and handle ADK events in agent execution flow
---

# ADK Workflow: Events

Events are immutable records representing specific points in agent execution. They capture user messages, agent replies, tool calls, state changes, and control signals. Understanding events is essential for observability, debugging, and building streaming applications.

---

## Prerequisites

- [ ] ADK project initialized
- [ ] Basic understanding of Runner execution flow
- [ ] Imports ready:

```python
from google.adk.events import Event, EventActions
from google.adk.runners import Runner
from google.adk.agents import LlmAgent
```

---

## Step 1: Understand Event Structure

Every `Event` contains these key attributes:

| Attribute | Type | Description |
|-----------|------|-------------|
| `author` | `str` | Who created: `"user"`, agent name, or `"tool"` |
| `invocation_id` | `str` | Unique ID for this agent invocation |
| `content` | `types.Content` | Message content (text, function calls, etc.) |
| `actions` | `EventActions` | Side effects and control signals |
| `partial` | `bool` | True if this is a streaming partial update |
| `turn_complete` | `bool` | True if this ends the current turn |
| `long_running_tool_ids` | `set[str]` | IDs of async tools still running |

```python
# Inspect an event
print(f"Author: {event.author}")
print(f"Partial: {event.partial}")
print(f"Turn Complete: {event.turn_complete}")
print(f"Content: {event.content}")
print(f"Actions: {event.actions}")
```

---

## Step 2: Identify Event Types

Determine what an event represents by checking `author` and `content`:

### User Input Event

```python
if event.author == "user":
    # This is input from the user
    user_text = event.get_text()  # Extract text content
    print(f"User said: {user_text}")
```

### Agent Response Event

```python
if event.author == "my_agent" and event.get_text():
    # Agent is providing a text response
    agent_text = event.get_text()
    print(f"Agent said: {agent_text}")
```

### Tool Call Request Event

```python
def has_function_calls(event: Event) -> bool:
    """Check if event contains function call requests."""
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.function_call:
                return True
    return False

if has_function_calls(event):
    for part in event.content.parts:
        if part.function_call:
            print(f"Tool called: {part.function_call.name}")
            print(f"Args: {part.function_call.args}")
```

### Tool Response Event

```python
def has_function_responses(event: Event) -> bool:
    """Check if event contains function responses."""
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.function_response:
                return True
    return False

if has_function_responses(event):
    for part in event.content.parts:
        if part.function_response:
            print(f"Tool: {part.function_response.name}")
            print(f"Response: {part.function_response.response}")
```

---

## Step 3: Handle EventActions

`EventActions` captures side effects and control signals attached to events:

```python
from google.adk.events import EventActions
```

### Key EventActions Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `state_delta` | `dict` | State changes to persist |
| `artifact_delta` | `dict` | Artifacts created/updated |
| `transfer_to_agent` | `str` | Control should pass to this agent |
| `escalate` | `bool` | Terminate the current loop |
| `skip_summarization` | `bool` | Don't summarize this agent's output |
| `requested_auth_configs` | `dict` | Authentication needed |

### Check for State Changes

```python
if event.actions and event.actions.state_delta:
    for key, value in event.actions.state_delta.items():
        print(f"State changed: {key} = {value}")
```

### Check for Agent Transfer

```python
if event.actions and event.actions.transfer_to_agent:
    next_agent = event.actions.transfer_to_agent
    print(f"Transferring control to: {next_agent}")
```

### Check for Escalation

```python
if event.actions and event.actions.escalate:
    print("Agent requested escalation - loop will terminate")
```

---

## Step 4: Process Events in Runner Loop

### Synchronous Processing

```python
async def run_agent(runner: Runner, session, user_message: str):
    """Process events from agent run."""
    
    from google import genai
    
    content = genai.types.Content(
        role="user",
        parts=[genai.types.Part(text=user_message)]
    )
    
    async for event in runner.run_async(
        session=session,
        user_id="user123",
        new_message=content,
    ):
        # Skip partial events (streaming chunks)
        if event.partial:
            continue
        
        # Process based on author
        if event.author == "user":
            print(f"[User] {event.get_text()}")
        elif event.get_text():
            print(f"[{event.author}] {event.get_text()}")
        
        # Check for actions
        if event.actions:
            if event.actions.state_delta:
                print(f"  State updated: {event.actions.state_delta}")
            if event.actions.transfer_to_agent:
                print(f"  → Transferring to: {event.actions.transfer_to_agent}")
        
        # Check for turn complete
        if event.turn_complete:
            print("--- Turn Complete ---")
```

### Streaming with run_live()

For bidirectional streaming applications:

```python
async def stream_conversation(runner: Runner, session, live_request_queue):
    """Process streaming events with run_live."""
    
    async for event in runner.run_live(
        session=session,
        live_request_queue=live_request_queue,
    ):
        if event.partial:
            # Streaming text chunk - display incrementally
            if event.get_text():
                print(event.get_text(), end="", flush=True)
        else:
            # Complete event
            if event.turn_complete:
                print()  # Newline after complete response
```

---

## Step 5: Filter and Classify Events

Create utility functions for event classification:

```python
from google.adk.events import Event

def classify_event(event: Event) -> str:
    """Classify an event by type."""
    if event.author == "user":
        return "user_input"
    
    if event.content and event.content.parts:
        for part in event.content.parts:
            if part.function_call:
                return "tool_call"
            if part.function_response:
                return "tool_response"
    
    if event.get_text():
        return "agent_response"
    
    if event.actions and event.actions.state_delta:
        return "state_update"
    
    return "other"


def filter_events(events: list[Event], event_type: str) -> list[Event]:
    """Filter events by type."""
    return [e for e in events if classify_event(e) == event_type]


# Usage
events = list_of_collected_events
tool_calls = filter_events(events, "tool_call")
agent_responses = filter_events(events, "agent_response")
```

---

## Step 6: Extract Data from Events

### Get All Text from Events

```python
def get_all_text(events: list[Event]) -> list[str]:
    """Extract all text content from events."""
    texts = []
    for event in events:
        text = event.get_text()
        if text:
            texts.append(text)
    return texts
```

### Get All Tool Calls

```python
def get_all_tool_calls(events: list[Event]) -> list[dict]:
    """Extract all tool calls from events."""
    tool_calls = []
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.function_call:
                    tool_calls.append({
                        "name": part.function_call.name,
                        "args": dict(part.function_call.args) if part.function_call.args else {},
                    })
    return tool_calls
```

### Get State Changes

```python
def get_state_changes(events: list[Event]) -> dict:
    """Collect all state changes from events."""
    combined_state = {}
    for event in events:
        if event.actions and event.actions.state_delta:
            combined_state.update(event.actions.state_delta)
    return combined_state
```

---

## Common Event Examples

### User Input Event

```json
{
  "author": "user",
  "invocation_id": "e-1234",
  "content": {
    "role": "user",
    "parts": [{"text": "What's the weather?"}]
  }
}
```

### Agent Text Response

```json
{
  "author": "weather_agent",
  "invocation_id": "e-1234",
  "content": {
    "role": "model",
    "parts": [{"text": "The weather today is sunny and 72°F."}]
  },
  "turn_complete": true
}
```

### Tool Call Event

```json
{
  "author": "weather_agent",
  "invocation_id": "e-1234",
  "content": {
    "role": "model",
    "parts": [{
      "function_call": {
        "name": "get_weather",
        "args": {"location": "San Francisco"}
      }
    }]
  }
}
```

### State Change Event

```json
{
  "author": "state_agent",
  "invocation_id": "e-1234",
  "actions": {
    "state_delta": {"last_location": "San Francisco"}
  }
}
```

---

## Verification

```bash
adk run agent_folder
```

1. Interact with agent and observe event stream
2. Check for proper event types in output
3. Verify state_delta in events with state changes
4. Monitor turn_complete signals

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Missing events | Partial events filtered too aggressively | Check `event.partial` handling |
| No text content | Event is a tool call, not text | Check for `function_call` in parts |
| State not persisting | Ignoring `state_delta` | Process `event.actions.state_delta` |
| Incomplete responses | Not waiting for `turn_complete` | Continue until `event.turn_complete` |

---

## Best Practices

- **Don't skip partial events in streaming UIs**: They provide incremental text updates
- **Always check for `None`**: Event attributes may be absent
- **Collect events for debugging**: Store events for replay and analysis
- **Use `turn_complete` to determine boundaries**: Indicates when agent has finished responding
- **Process `state_delta` if persisting state**: Contains all state mutations from that event
