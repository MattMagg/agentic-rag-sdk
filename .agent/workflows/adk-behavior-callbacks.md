---
description: Implement ADK callbacks to observe, customize, and control agent behavior
---

# ADK Workflow: Callbacks

Callbacks are functions you define that ADK calls at specific points during an agent's execution. They allow you to observe, customize, and control agent behavior without modifying core agent logic.

---

## Prerequisites

- [ ] ADK Python v0.1.0+ installed
- [ ] Basic agent created with `LlmAgent`

---

## Step 1: Understand Callback Categories

ADK provides callbacks at three levels:

| Category | Callbacks | Scope |
|----------|-----------|-------|
| **Agent** | `before_agent_callback`, `after_agent_callback` | Entire agent run |
| **Model** | `before_model_callback`, `after_model_callback` | LLM interactions |
| **Tool** | `before_tool_callback`, `after_tool_callback` | Tool execution |

---

## Step 2: Define Agent Callbacks

Agent callbacks wrap the entire agent execution.

### Before Agent Callback

Called before agent processing starts. Return `Content` to skip the agent entirely.

```python
from google.adk.agents import LlmAgent, CallbackContext
from google.genai import types
from typing import Optional

def check_if_agent_should_run(
    callback_context: CallbackContext
) -> Optional[types.Content]:
    """Check conditions before agent runs."""
    agent_name = callback_context.agent_name
    state = callback_context.state
    
    # Skip agent if flagged in state
    if state.get("skip_llm_agent"):
        return types.Content(
            parts=[types.Part.from_text("Agent skipped by pre-check.")]
        )
    
    # Return None to proceed normally
    return None
```

### After Agent Callback

Called after agent completes. Receives the agent's output event.

```python
def log_agent_completion(
    callback_context: CallbackContext
) -> Optional[types.Content]:
    """Log or modify output after agent finishes."""
    # Access state for logging
    callback_context.state["agent_completed"] = True
    
    # Return None to keep original output
    # Return Content to replace the output
    return None
```

---

## Step 3: Define Model Callbacks

Model callbacks intercept LLM requests and responses.

### Before Model Callback

Inspect or modify the `LlmRequest` before sending to the LLM. Return `LlmResponse` to skip the LLM call.

```python
from google.adk.agents import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from typing import Optional

def before_model_modifier(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Inspect/modify LLM request or skip the call."""
    agent_name = callback_context.agent_name
    
    # Log the request
    print(f"[{agent_name}] Sending request to LLM")
    
    # Modify request contents if needed
    # llm_request.contents.append(...)
    
    # Return None to proceed with LLM call
    # Return LlmResponse to skip LLM and use cached/mocked response
    return None
```

### After Model Callback

Process or modify the LLM response before the agent uses it.

```python
def after_model_processor(
    callback_context: CallbackContext,
    llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Process or modify LLM response."""
    # Log token usage
    if llm_response.usage_metadata:
        print(f"Tokens used: {llm_response.usage_metadata.total_token_count}")
    
    # Return None to use original response
    # Return modified LlmResponse to override
    return None
```

---

## Step 4: Define Tool Callbacks

Tool callbacks wrap individual tool executions.

### Before Tool Callback

Validate or modify tool arguments. Return a `dict` result to skip tool execution.

```python
from google.adk.tools import ToolContext
from typing import Any, Optional

def validate_tool_args(
    tool: Any,
    args: dict[str, Any],
    tool_context: ToolContext
) -> Optional[dict]:
    """Validate tool arguments before execution."""
    tool_name = tool.name
    
    # Example: Block destructive operations
    if tool_name == "delete_item" and not args.get("confirmed"):
        return {"error": "Confirmation required for delete operations"}
    
    # Return None to proceed with tool execution
    # Return dict to skip tool and use this as the result
    return None
```

### After Tool Callback

Process or modify tool results.

```python
def process_tool_result(
    tool: Any,
    args: dict[str, Any],
    tool_context: ToolContext,
    result: dict
) -> Optional[dict]:
    """Process or modify tool result."""
    # Log the result
    print(f"Tool {tool.name} returned: {result}")
    
    # Modify result if needed
    # Return None to use original result
    # Return dict to override the result
    return None
```

---

## Step 5: Attach Callbacks to Agent

Register callbacks when creating the `LlmAgent`:

```python
from google.adk.agents import LlmAgent

agent = LlmAgent(
    name="my_agent",
    model="gemini-3-flash-preview",
    instruction="You are a helpful assistant.",
    
    # Agent-level callbacks
    before_agent_callback=check_if_agent_should_run,
    after_agent_callback=log_agent_completion,
    
    # Model-level callbacks
    before_model_callback=before_model_modifier,
    after_model_callback=after_model_processor,
    
    # Tool-level callbacks
    before_tool_callback=validate_tool_args,
    after_tool_callback=process_tool_result,
)
```

---

## Configuration Options

| Parameter | Type | Return Type | Skip Behavior |
|-----------|------|-------------|---------------|
| `before_agent_callback` | `Callable` | `Optional[Content]` | Return `Content` to skip agent |
| `after_agent_callback` | `Callable` | `Optional[Content]` | Return `Content` to replace output |
| `before_model_callback` | `Callable` | `Optional[LlmResponse]` | Return `LlmResponse` to skip LLM |
| `after_model_callback` | `Callable` | `Optional[LlmResponse]` | Return `LlmResponse` to replace |
| `before_tool_callback` | `Callable` | `Optional[dict]` | Return `dict` to skip tool |
| `after_tool_callback` | `Callable` | `Optional[dict]` | Return `dict` to replace result |

---

## Common Design Patterns

### 1. Logging and Auditing

```python
def audit_callback(callback_context: CallbackContext) -> None:
    """Log agent activity for auditing."""
    callback_context.state["audit_log"] = callback_context.state.get("audit_log", [])
    callback_context.state["audit_log"].append({
        "agent": callback_context.agent_name,
        "timestamp": datetime.now().isoformat()
    })
    return None
```

### 2. Conditional Skipping

```python
def skip_on_cache_hit(
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Skip LLM if response is cached."""
    cache_key = hash(str(llm_request.contents))
    cached = callback_context.state.get(f"cache:{cache_key}")
    if cached:
        return cached  # Return cached LlmResponse
    return None
```

### 3. Input Validation

```python
def validate_inputs(
    tool: Any,
    args: dict[str, Any],
    tool_context: ToolContext
) -> Optional[dict]:
    """Validate tool inputs before execution."""
    if "user_id" in args and not args["user_id"].isalnum():
        return {"error": "Invalid user_id format"}
    return None
```

### 4. Response Modification

```python
def sanitize_response(
    callback_context: CallbackContext,
    llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Sanitize sensitive data from response."""
    # Clone and modify if needed
    # Return modified response or None
    return None
```

---

## Integration Points

- **With State:** Use `callback_context.state` or `tool_context.state` to read/write session state
- **With Plugins:** Plugins use the same callback mechanism but are registered at the `Runner` level
- **With Multi-Agent:** Each agent can have its own callbacks; parent callbacks wrap child agent execution

---

## Verification

```bash
adk run agent_folder
```

Add debug logging to your callbacks:

```python
def debug_callback(callback_context: CallbackContext) -> None:
    print(f"Callback triggered for: {callback_context.agent_name}")
    return None
```

Expected behavior:
- Callbacks execute in order: before → operation → after
- Return `None` to proceed normally
- Return a value to skip or modify the operation

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Callback not triggered | Wrong callback type for the hook | Verify callback parameter name matches the hook point |
| Agent skipped unexpectedly | `before_agent_callback` returns `Content` | Check callback logic; return `None` to proceed |
| Tool result replaced | `before_tool_callback` returns a `dict` | Ensure you return `None` when validation passes |
| Type errors | Wrong return type | Match return type to callback signature |

---

## References

- Callbacks Overview (docs/callbacks/index.md)
- Types of Callbacks (docs/callbacks/types-of-callbacks.md)
- Design Patterns and Best Practices (docs/callbacks/design-patterns-and-best-practices.md)
- Context Objects (docs/context/index.md)
