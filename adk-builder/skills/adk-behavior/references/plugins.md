---
description: Create reusable ADK plugins with cross-cutting concerns like logging, analytics, and error handling
---

# ADK Workflow: Plugins

Plugins in ADK are reusable components that intercept agent, tool, and LLM behaviors at execution points. Unlike callbacks (which are per-agent), plugins are registered at the **Runner level** and apply across all agents.

**Supported:** ADK Python v1.7.0+

---

## Prerequisites

- [ ] ADK Python v1.7.0+ installed
- [ ] Basic agent and runner setup

---

## Step 1: Understand Plugin vs Callbacks

| Aspect | Callbacks | Plugins |
|--------|-----------|---------|
| **Registration** | Per-agent on `LlmAgent` | Per-runner on `Runner` |
| **Scope** | Single agent | All agents in runner |
| **Reusability** | Copy code to each agent | Instantiate and register once |
| **Use case** | Agent-specific logic | Cross-cutting concerns |

Plugins are ideal for:
- Logging and auditing across all agents
- Analytics and telemetry
- Error handling and retry logic
- Global state management

---

## Step 2: Create a Plugin Class

Extend `BasePlugin` and implement specific callback methods:

```python
from google.adk.plugins import BasePlugin
from google.adk.agents import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools import BaseTool, ToolContext
from google.adk.runners import InvocationContext
from google.genai import types
from typing import Optional, Any

class CountingPlugin(BasePlugin):
    """Plugin that counts LLM calls and tool executions."""
    
    def __init__(self):
        super().__init__()
        self.llm_call_count = 0
        self.tool_call_count = 0
    
    async def before_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        """Count LLM calls before they happen."""
        self.llm_call_count += 1
        print(f"[CountingPlugin] LLM call #{self.llm_call_count}")
        return None  # Proceed with LLM call
    
    async def before_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext
    ) -> Optional[dict]:
        """Count tool calls before execution."""
        self.tool_call_count += 1
        print(f"[CountingPlugin] Tool '{tool.name}' call #{self.tool_call_count}")
        return None  # Proceed with tool execution
```

---

## Step 3: Implement Plugin Lifecycle Callbacks

Plugins support the full callback lifecycle:

### Runner Start Callback

```python
async def before_run_callback(
    self,
    *,
    invocation_context: InvocationContext
) -> Optional[types.Content]:
    """Called when Runner starts processing a user message."""
    print(f"[Plugin] Starting run for session: {invocation_context.session.id}")
    # Return Content to skip the run, None to proceed
    return None
```

### Runner End Callback

```python
async def after_run_callback(
    self,
    *,
    invocation_context: InvocationContext
) -> None:
    """Called when Runner completes a run."""
    print(f"[Plugin] Run completed")
    # Cleanup, final logging, etc.
```

### Agent Callbacks

```python
async def before_agent_callback(
    self,
    *,
    callback_context: CallbackContext
) -> Optional[types.Content]:
    """Called before each agent runs."""
    print(f"[Plugin] Agent '{callback_context.agent_name}' starting")
    return None

async def after_agent_callback(
    self,
    *,
    callback_context: CallbackContext
) -> Optional[types.Content]:
    """Called after each agent completes."""
    print(f"[Plugin] Agent '{callback_context.agent_name}' finished")
    return None
```

### Model Callbacks

```python
async def before_model_callback(
    self,
    *,
    callback_context: CallbackContext,
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Called before LLM request is sent."""
    return None

async def after_model_callback(
    self,
    *,
    callback_context: CallbackContext,
    llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Called after LLM response is received."""
    return None
```

### Tool Callbacks

```python
async def before_tool_callback(
    self,
    *,
    tool: BaseTool,
    tool_args: dict[str, Any],
    tool_context: ToolContext
) -> Optional[dict]:
    """Called before tool execution."""
    return None

async def after_tool_callback(
    self,
    *,
    tool: BaseTool,
    tool_args: dict[str, Any],
    tool_context: ToolContext,
    result: dict
) -> Optional[dict]:
    """Called after tool execution."""
    return None

async def on_tool_error(
    self,
    *,
    tool: BaseTool,
    tool_args: dict[str, Any],
    tool_context: ToolContext,
    error: Exception
) -> Optional[dict]:
    """Called when tool execution raises an exception."""
    print(f"[Plugin] Tool '{tool.name}' error: {error}")
    # Return dict to replace error with result, None to propagate error
    return None
```

---

## Step 4: Register Plugin with Runner

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Create plugin instance
counting_plugin = CountingPlugin()

# Create runner with plugins
runner = Runner(
    agent=my_agent,
    app_name="my_app",
    session_service=InMemorySessionService(),
    plugins=[counting_plugin]  # Register plugins here
)
```

### Multiple Plugins

Register multiple plugins - they execute in order:

```python
runner = Runner(
    agent=my_agent,
    app_name="my_app",
    session_service=session_service,
    plugins=[
        LoggingPlugin(),
        AnalyticsPlugin(),
        ErrorHandlerPlugin(),
    ]
)
```

---

## Step 5: Complete Plugin Example

```python
from google.adk.plugins import BasePlugin
from google.adk.agents import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.adk.tools import BaseTool, ToolContext
from google.adk.runners import InvocationContext
from google.genai import types
from typing import Optional, Any
from datetime import datetime


class AnalyticsPlugin(BasePlugin):
    """Plugin for tracking agent analytics."""
    
    def __init__(self):
        super().__init__()
        self.metrics = {
            "runs": 0,
            "llm_calls": 0,
            "tool_calls": 0,
            "errors": 0,
            "total_tokens": 0,
        }
    
    async def before_run_callback(
        self,
        *,
        invocation_context: InvocationContext
    ) -> Optional[types.Content]:
        self.metrics["runs"] += 1
        self._run_start = datetime.now()
        return None
    
    async def after_run_callback(
        self,
        *,
        invocation_context: InvocationContext
    ) -> None:
        duration = (datetime.now() - self._run_start).total_seconds()
        print(f"[Analytics] Run completed in {duration:.2f}s")
        print(f"[Analytics] Metrics: {self.metrics}")
    
    async def before_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_request: LlmRequest
    ) -> Optional[LlmResponse]:
        self.metrics["llm_calls"] += 1
        return None
    
    async def after_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_response: LlmResponse
    ) -> Optional[LlmResponse]:
        if llm_response.usage_metadata:
            self.metrics["total_tokens"] += llm_response.usage_metadata.total_token_count or 0
        return None
    
    async def before_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext
    ) -> Optional[dict]:
        self.metrics["tool_calls"] += 1
        return None
    
    async def on_tool_error(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
        error: Exception
    ) -> Optional[dict]:
        self.metrics["errors"] += 1
        return None
```

---

## Configuration Options

| Callback | Parameters | Return Type | Skip Behavior |
|----------|------------|-------------|---------------|
| `before_run_callback` | `invocation_context` | `Optional[Content]` | Return `Content` to skip run |
| `after_run_callback` | `invocation_context` | `None` | No skip behavior |
| `before_agent_callback` | `callback_context` | `Optional[Content]` | Return `Content` to skip agent |
| `after_agent_callback` | `callback_context` | `Optional[Content]` | Return `Content` to replace output |
| `before_model_callback` | `callback_context`, `llm_request` | `Optional[LlmResponse]` | Return response to skip LLM |
| `after_model_callback` | `callback_context`, `llm_response` | `Optional[LlmResponse]` | Return response to replace |
| `before_tool_callback` | `tool`, `tool_args`, `tool_context` | `Optional[dict]` | Return dict to skip tool |
| `after_tool_callback` | `tool`, `tool_args`, `tool_context`, `result` | `Optional[dict]` | Return dict to replace result |
| `on_tool_error` | `tool`, `tool_args`, `tool_context`, `error` | `Optional[dict]` | Return dict to suppress error |

---

## Built-in Plugins

ADK includes several built-in plugins:

| Plugin | Purpose |
|--------|---------|
| `RecordingsPlugin` | Record agent interactions for replay |
| `ReplayPlugin` | Replay recorded interactions for testing |
| `GlobalInstructionPlugin` | Provide app-level instructions to all agents |
| `BigQueryAgentAnalyticsPlugin` | Send analytics to BigQuery |

---

## Integration Points

- **With Callbacks:** Plugins and agent callbacks both run; plugins at runner level, callbacks at agent level
- **With State:** Access state via `invocation_context.session.state` or `callback_context.state`
- **With Multi-Agent:** Plugin callbacks wrap parent and all child agent executions
- **Execution Order:** Plugins execute in registration order, before agent-level callbacks

---

## Verification

```bash
adk run agent_folder
```

Expected behavior:
- Plugin callbacks fire for all agents in the runner
- Metrics and logs appear in console output
- Plugin state persists across runs within the same instance

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Plugin callback not called | Method signature doesn't match | Use exact parameter names with keyword-only args (`*,`) |
| Multiple plugins conflict | Both modify same data | Order plugins appropriately; earlier plugins run first |
| Plugin state not persisting | New plugin instance per run | Reuse plugin instance across runs |
| `TypeError` on callback | Wrong return type | Match return type to callback signature |

---

## References

- Plugins Overview (docs/plugins/index.md)
- BasePlugin Class (src/google/adk/plugins/base_plugin.py)
- PluginManager (src/google/adk/plugins/plugin_manager.py)
