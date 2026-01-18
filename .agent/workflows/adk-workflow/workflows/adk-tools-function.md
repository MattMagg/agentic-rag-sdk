---
description: Create custom tools using FunctionTool and ToolContext for agent capabilities
---

# ADK Workflow: Function Tools

This workflow guides you through creating custom tools using `FunctionTool` that extend your agent's capabilities beyond LLM reasoning.

---

## Prerequisites

- [ ] ADK project initialized (`/adk-init`)
- [ ] Agent created (`/adk-agents-create`)
- [ ] Required imports available:

```python
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext
from typing import Dict, Any
```

---

## Step 1: Define a Function Tool

A `FunctionTool` wraps a Python function and exposes it to the LLM. The function signature and docstring determine how the LLM understands and uses the tool.

### Basic Function Tool

```python
def get_weather(city: str, unit: str = "celsius") -> Dict[str, Any]:
    """Retrieves the current weather for a given city.
    
    Args:
        city: The name of the city to get weather for.
        unit: Temperature unit - "celsius" or "fahrenheit". Defaults to celsius.
    
    Returns:
        A dictionary containing temperature and conditions.
    """
    # Your implementation here
    return {"temperature": 22, "conditions": "sunny", "city": city}
```

### Key Design Principles

| Element | Purpose | Best Practice |
|---------|---------|---------------|
| Function name | LLM identifies the tool | Use clear, action-oriented names (e.g., `get_weather`, `send_email`) |
| Type hints | Schema generation | Always provide type hints for parameters and return type |
| Docstring | LLM understands purpose | Include clear description and document each parameter |
| Parameters | Input validation | Use `Optional[]` for optional params; required params have no default |

---

## Step 2: Register Tool with Agent

Add the function directly to your agent's `tools` list. ADK automatically wraps plain functions as `FunctionTool`:

```python
from google.adk.agents import LlmAgent

root_agent = LlmAgent(
    name="weather_agent",
    model="gemini-3-flash-preview",
    instruction="You are a helpful weather assistant.",
    tools=[get_weather]  # ADK auto-wraps as FunctionTool
)
```

### Explicit FunctionTool Wrapping

For more control, wrap explicitly:

```python
from google.adk.tools import FunctionTool

weather_tool = FunctionTool(func=get_weather)

root_agent = LlmAgent(
    name="weather_agent",
    model="gemini-3-flash-preview",
    instruction="You are a helpful weather assistant.",
    tools=[weather_tool]
)
```

---

## Step 3: Access ToolContext for Advanced Features

Include `tool_context: ToolContext` as a parameter to access session state, authentication, and event actions:

```python
from google.adk.tools.tool_context import ToolContext

def set_user_preference(
    preference: str, 
    value: str, 
    tool_context: ToolContext
) -> Dict[str, Any]:
    """Sets a user preference in the session state.
    
    Args:
        preference: The preference name to set.
        value: The value to assign to the preference.
        tool_context: Injected by ADK - provides access to state.
    
    Returns:
        Confirmation of the preference being set.
    """
    # Access session state via tool_context
    tool_context.state[f"user:{preference}"] = value
    return {"status": "success", "preference": preference, "value": value}
```

> [!IMPORTANT]
> ADK automatically injects `tool_context` - do NOT document it in the docstring for the LLM. The parameter is hidden from the schema.

---

## Step 4: State Management via ToolContext

The `tool_context.state` attribute provides direct access to session state:

### Reading State

```python
def get_user_name(tool_context: ToolContext) -> str:
    """Gets the current user's name from session state."""
    return tool_context.state.get("user_name", "Unknown")
```

### Writing State

```python
def save_calculation_result(
    result: float, 
    tool_context: ToolContext
) -> Dict[str, Any]:
    """Saves a calculation result to session state."""
    # State changes are automatically tracked and persisted
    tool_context.state["last_result"] = result
    return {"saved": True, "result": result}
```

### State Prefixes

| Prefix | Scope | Persistence |
|--------|-------|-------------|
| `app:` | Application-wide | Across all sessions |
| `user:` | User-specific | Across user's sessions |
| `temp:` | Temporary | Current session only |
| (none) | Session | Current session only |

---

## Step 5: Input Validation with Callbacks

Use `before_tool_callback` to validate or modify tool arguments before execution:

```python
from google.adk.agents import LlmAgent
from google.adk.tools.tool_context import ToolContext

def validate_city_input(
    tool: BaseTool, 
    args: Dict[str, Any], 
    tool_context: ToolContext
) -> Optional[Dict]:
    """Validates that city names are non-empty."""
    if "city" in args and not args["city"].strip():
        # Return a dict to skip tool execution with this response
        return {"error": "City name cannot be empty"}
    # Return None to proceed with tool execution
    return None

root_agent = LlmAgent(
    name="weather_agent",
    model="gemini-3-flash-preview",
    instruction="You are a weather assistant.",
    tools=[get_weather],
    before_tool_callback=validate_city_input
)
```

---

## Step 6: Post-Processing with after_tool_callback

Use `after_tool_callback` to modify or log tool results:

```python
def log_tool_result(
    tool: BaseTool, 
    args: Dict[str, Any], 
    tool_context: ToolContext, 
    tool_response: Dict
) -> Optional[Dict]:
    """Logs tool execution for auditing."""
    print(f"Tool {tool.name} called with {args}, returned {tool_response}")
    # Return None to use original response, or return modified response
    return None

root_agent = LlmAgent(
    name="weather_agent",
    model="gemini-3-flash-preview",
    tools=[get_weather],
    after_tool_callback=log_tool_result
)
```

---

## Configuration Options

### FunctionTool Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `func` | `Callable` | Required | The Python function to wrap |
| `name` | `str` | Function name | Override the tool name |
| `description` | `str` | From docstring | Override the tool description |

### ToolContext Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `state` | `MutableMapping` | Session state (read/write) |
| `actions` | `EventActions` | Event action controls |
| `function_call_id` | `str` | ID of current function call |
| `invocation_context` | `InvocationContext` | Full invocation context |

---

## Integration Points

- **With Callbacks:** Use `before_tool_callback` for validation, `after_tool_callback` for post-processing
- **With State:** Access `tool_context.state` for session data persistence
- **With Authentication:** Use `tool_context` to access credentials via `AuthenticatedFunctionTool`
- **With Artifacts:** Use `tool_context.save_artifact()` and `tool_context.load_artifact()` for file handling

---

## Common Patterns

### Pattern 1: Stateful Counter

```python
def increment_counter(tool_context: ToolContext) -> Dict[str, int]:
    """Increments and returns the session counter."""
    count = tool_context.state.get("counter", 0) + 1
    tool_context.state["counter"] = count
    return {"count": count}
```

### Pattern 2: Tool with Complex Return Type

```python
from pydantic import BaseModel

class WeatherResponse(BaseModel):
    temperature: float
    conditions: str
    humidity: int

def get_detailed_weather(city: str) -> WeatherResponse:
    """Gets detailed weather information."""
    return WeatherResponse(temperature=22.5, conditions="partly cloudy", humidity=65)
```

### Pattern 3: Multiple Related Tools

```python
from google.adk.tools.toolset import Toolset

# Group related tools into a Toolset
math_tools = Toolset(
    tools=[add_numbers, multiply_numbers, divide_numbers],
    description="Mathematical operation tools"
)

root_agent = LlmAgent(
    name="math_agent",
    model="gemini-3-flash-preview",
    tools=[math_tools]
)
```

---

## Verification

```bash
# Run the agent with dev UI
adk web agent_folder
```

**Expected behavior:**
1. Agent loads without errors
2. Tools appear in the agent's available capabilities
3. When prompted, agent correctly identifies and calls your custom tools
4. Tool responses are incorporated into agent's replies

### Verification Checklist

- [ ] Function has type hints for all parameters
- [ ] Function has descriptive docstring
- [ ] `ToolContext` parameter is NOT documented in docstring
- [ ] Tool appears in agent's tool list
- [ ] Tool is called with correct arguments
- [ ] State changes persist across turns

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Tool not called | Docstring unclear | Improve tool description and parameter docs |
| Wrong arguments passed | Missing type hints | Add explicit type hints to all parameters |
| State not persisting | Wrong state prefix | Use appropriate prefix (`user:`, `app:`, etc.) |
| `ToolContext` shown in schema | Documented in docstring | Remove `tool_context` from docstring Args |
| Tool error not handled | No error handling | Add try/except and return error dict |

---

## References

- ADK Tools Custom Documentation: `docs/tools-custom/function-tools.md`
- ToolContext Reference: `docs/tools-custom/index.md`
- Callback Patterns: `docs/callbacks/types-of-callbacks.md`
- State Management: `docs/context/index.md`
