---
name: adk-add-tool
description: Add a tool to an ADK agent with intelligent tool type selection
argument-hint: Optional tool description
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Add Tool to Agent

Add a tool to an existing ADK agent with intelligent selection of tool type.

## Decision Logic

**Step 1: Find existing agent**

Search for agent.py files in current project.

**Step 2: Understand tool requirements**

Ask user:
> "What capability do you want to add? Choose one:
>
> 1. **Custom Python function** - I'll write the code
> 2. **Google Search** - Web search capability
> 3. **Code Execution** - Run Python in sandbox
> 4. **REST API** - I have an OpenAPI/Swagger spec
> 5. **MCP Server** - Connect to MCP tools
> 6. **Existing tool** - From LangChain or other framework"

**Step 3: Implement based on selection**

**If Custom Python function:**
- Ask what the function should do
- Generate function with proper type hints and docstring
- Add to agent's tools list

**If Google Search or Code Execution:**
```python
from google.adk.tools import google_search, code_execution
# Add to tools list
```

**If OpenAPI:**
- Ask for spec URL or file path
- Generate OpenAPIToolset configuration

**If MCP:**
- Ask for MCP server command/URL
- Generate MCPToolset configuration

**If Third-party:**
- Ask which framework (LangChain, CrewAI)
- Generate wrapper code

**Step 4: Update agent.py**

Add tool to agent's tools list.

**Step 5: Verify**

```bash
adk run <agent_name>
# Test the new tool
```

## Usage Examples

```
/adk-add-tool                              # Interactive
/adk-add-tool "fetch weather data"        # Custom function
/adk-add-tool google_search               # Built-in tool
```

## References

Load `@adk-tools` skill for detailed tool implementation.
