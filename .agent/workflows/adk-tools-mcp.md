---
description: Integrate Model Context Protocol (MCP) server tools into ADK agents
---

# ADK Workflow: MCP Tools Integration

Integrate tools from MCP (Model Context Protocol) servers into your ADK agent. MCP is an open standard that enables AI applications to connect with external data sources and tools through a unified protocol.

---

## Prerequisites

- [ ] ADK Python v0.1.0+ installed
- [ ] MCP server accessible (local process or remote endpoint)
- [ ] `mcp` package installed: `pip install mcp`

---

## Overview: Two Integration Patterns

ADK supports two MCP integration patterns:

1. **ADK as MCP Client**: Your agent consumes tools from an MCP server
2. **ADK as MCP Server**: Expose your ADK tools to other MCP clients

This workflow covers both patterns.

---

## Pattern 1: Using MCP Server Tools in ADK

### Step 1: Choose Connection Type

MCP supports two transport mechanisms:

| Transport | Use Case | Class |
|-----------|----------|-------|
| **Stdio** | Local process (subprocess) | `StdioServerParameters` |
| **SSE** | Remote HTTP server | `SseServerParams` |

### Step 2: Configure Stdio Connection (Local Server)

For MCP servers running as local processes:

```python
from mcp import StdioServerParameters

# Define the MCP server command
stdio_params = StdioServerParameters(
    command="npx",
    args=["-y", "@anthropic/mcp-server-filesystem", "/path/to/allowed/dir"],
    env={"NODE_ENV": "production"}  # Optional environment variables
)
```

### Step 3: Configure SSE Connection (Remote Server)

For MCP servers accessible via HTTP:

```python
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams

sse_params = SseServerParams(
    url="http://localhost:8080/mcp",
    headers={"Authorization": "Bearer your-token"}  # Optional headers
)
```

### Step 4: Create McpToolset

```python
from google.adk.tools.mcp_tool import McpToolset

# Using Stdio connection
mcp_toolset = McpToolset(
    connection_params=stdio_params,
    # Optional: filter which tools to expose
    # tool_filter=["read_file", "write_file"]
)

# OR using SSE connection
mcp_toolset = McpToolset(
    connection_params=sse_params
)
```

### Step 5: Add to Agent

```python
from google.adk.agents import LlmAgent

agent = LlmAgent(
    model="gemini-2.0-flash",
    name="mcp_agent",
    instruction="""You are an assistant with access to external tools 
    via MCP. Use these tools to help users with their requests.""",
    tools=[mcp_toolset]
)
```

---

## Pattern 2: Exposing ADK Tools as MCP Server

Wrap existing ADK tools and make them available to any MCP client:

### Step 1: Define Your ADK Tools

```python
from google.adk.tools import FunctionTool

def calculate_sum(a: int, b: int) -> int:
    """Calculate the sum of two numbers."""
    return a + b

def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: Sunny, 72°F"

tools = [
    FunctionTool(func=calculate_sum),
    FunctionTool(func=get_weather)
]
```

### Step 2: Create MCP Server

```python
from google.adk.tools.mcp_tool import mcp_server

# Create server exposing ADK tools
server = mcp_server.create_mcp_server(
    tools=tools,
    name="my-adk-tools-server"
)

# Run the server (typically in a separate process)
if __name__ == "__main__":
    server.run()
```

---

## Complete Agent Example

```python
# ./mcp_agent/agent.py
import os
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from mcp import StdioServerParameters

# Configure filesystem MCP server
filesystem_server = StdioServerParameters(
    command="npx",
    args=["-y", "@anthropic/mcp-server-filesystem", os.getcwd()]
)

# Create the toolset
mcp_tools = McpToolset(connection_params=filesystem_server)

# Create agent with MCP tools
root_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="filesystem_agent",
    instruction="""You can read and write files using the filesystem tools.
    Always confirm with the user before modifying files.""",
    tools=[mcp_tools]
)
```

```python
# ./mcp_agent/__init__.py
from . import agent
```

---

## Configuration Options

### McpToolset Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `connection_params` | `StdioServerParameters` or `SseServerParams` | Connection configuration |
| `tool_filter` | `List[str]` | Optional list of tool names to include |
| `errlog` | `TextIO` | Optional error log stream |

### StdioServerParameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `command` | `str` | Executable command to run |
| `args` | `List[str]` | Command line arguments |
| `env` | `Dict[str, str]` | Environment variables |

### SseServerParams

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | SSE endpoint URL |
| `headers` | `Dict[str, str]` | HTTP headers for requests |

---

## MCP Session Management

For advanced scenarios, manage the MCP session explicitly:

```python
from google.adk.tools.mcp_tool.mcp_session_manager import McpSessionManager

# Create session manager
session_manager = McpSessionManager(
    connection_params=stdio_params,
    errlog=sys.stderr
)

# Start session
await session_manager.start()

# Get available tools
tools = await session_manager.list_tools()

# Close session when done
await session_manager.close()
```

---

## Integration Points

- **With Agent Lifecycle:** McpToolset automatically manages MCP server lifecycle
- **With Authentication:** MCP tools can integrate with ADK's auth framework via headers
- **With Multiple Servers:** Add multiple `McpToolset` instances to connect to different servers

---

## Verification

```bash
# Run the agent
adk run mcp_agent

# Or use the web interface
adk web mcp_agent
```

**Expected behavior:**
1. MCP server process starts automatically
2. Tools from the MCP server appear in agent's available tools
3. Agent can invoke MCP tools based on user requests
4. MCP server closes when agent session ends

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Connection refused" | MCP server not running | Check `command` path and ensure server is installed |
| "Tool not found" | Tool filtered out or unavailable | Remove `tool_filter` or check MCP server exposes the tool |
| Timeout errors | Slow MCP server startup | Increase connection timeout in params |
| Permission denied | Subprocess cannot execute | Check file permissions and PATH |

---

## Deployment Considerations

### Vertex AI Agent Engine

```bash
# Deploy with MCP sidecar (if using external MCP server)
uv run adk deploy agent_engine \
  --project=<your-gcp-project-id> \
  --region=<your-gcp-region> \
  --staging_bucket="gs://<your-gcs-bucket>"
```

### Cloud Run

For Cloud Run deployments with MCP:
- Use SSE transport for remote MCP servers
- Or bundle the MCP server in a sidecar container

---

## References

- MCP Tools Documentation: `docs/tools-custom/mcp-tools.md`
- MCP Overview: `docs/mcp/index.md`
- McpToolset Implementation: `src/google/adk/tools/mcp_tool/mcp_toolset.py`
- McpTool Implementation: `src/google/adk/tools/mcp_tool/mcp_tool.py`
- MCP Session Manager: `src/google/adk/tools/mcp_tool/mcp_session_manager.py`
