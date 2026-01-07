---
description: Wrap LangChain and CrewAI tools for use in ADK agents
---

# ADK Workflow: Third-Party Tool Integration

Integrate tools from third-party frameworks like LangChain and CrewAI into your ADK agent. ADK provides adapter classes that wrap these external tools, making them compatible with the ADK tool interface.

---

## Prerequisites

- [ ] ADK Python installed
- [ ] For LangChain tools: `pip install langchain langchain-community`
- [ ] For CrewAI tools: `pip install "crewai[tools]"`

---

## Overview: Supported Frameworks

| Framework | Adapter Class | Use Case |
|-----------|---------------|----------|
| LangChain | `LangchainTool` | Wrap any LangChain BaseTool |
| CrewAI | `CrewaiTool` | Wrap any CrewAI BaseTool |

Both adapters extend `FunctionTool` and support ADK's `ToolContext` for state management.

---

## LangChain Tool Integration

### Step 1: Install LangChain and Required Packages

```bash
pip install langchain langchain-community tavily-python
```

### Step 2: Create the LangChain Tool

```python
from langchain_community.tools.tavily_search import TavilySearchResults
import os

# Set API key
os.environ["TAVILY_API_KEY"] = "your-tavily-api-key"

# Create the LangChain tool
langchain_tavily = TavilySearchResults(
    max_results=5,
    search_depth="advanced",
    include_answer=True
)
```

### Step 3: Wrap with LangchainTool Adapter

```python
from google.adk.tools.langchain_tool import LangchainTool

# Wrap the LangChain tool for ADK
adk_search_tool = LangchainTool(
    tool=langchain_tavily,
    # Optional: Override name and description
    name="web_search",
    description="Search the web for current information."
)
```

### Step 4: Add to Agent

```python
from google.adk.agents import LlmAgent

agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="search_agent",
    instruction="""You are a helpful assistant with web search capabilities.
    Use the search tool to find current information for user queries.""",
    tools=[adk_search_tool]
)
```

---

## CrewAI Tool Integration

### Step 1: Install CrewAI with Tools

```bash
pip install "crewai[tools]"
```

### Step 2: Create the CrewAI Tool

```python
from crewai_tools import SerperDevTool
import os

# Set API key
os.environ["SERPER_API_KEY"] = "your-serper-api-key"

# Create the CrewAI tool
crewai_serper = SerperDevTool()
```

### Step 3: Wrap with CrewaiTool Adapter

```python
from google.adk.tools.crewai_tool import CrewaiTool

# Wrap the CrewAI tool for ADK
adk_serper_tool = CrewaiTool(
    tool=crewai_serper,
    # Optional: Override name and description
    name="serper_search",
    description="Search the web using Serper API."
)
```

### Step 4: Add to Agent

```python
from google.adk.agents import LlmAgent

agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="crewai_agent",
    instruction="""You are a research assistant with web search capabilities.
    Use the serper search tool to find information.""",
    tools=[adk_serper_tool]
)
```

---

## Using ToolContext with Third-Party Tools

Both adapters support passing `ToolContext` to access ADK state:

### LangChain with ToolContext

```python
from google.adk.tools import ToolContext
from google.adk.tools.langchain_tool import LangchainTool

# For tools that need access to ADK context, 
# the adapter automatically injects tool_context if the 
# underlying tool's function signature includes it

adk_tool = LangchainTool(
    tool=langchain_tool,
    name="context_aware_tool",
    description="A tool that can access ADK session state."
)
```

### CrewAI with ToolContext

```python
from google.adk.tools.crewai_tool import CrewaiTool

# CrewAI tools can also receive tool_context
# if their underlying function accepts a tool_context parameter

def crewai_tool_with_context(search_query: str, tool_context: ToolContext):
    """Tool that uses ADK context."""
    # Access session state
    user_prefs = tool_context.state.get("user_preferences", {})
    # Perform search with preferences
    return f"Searching for {search_query} with prefs: {user_prefs}"

# Wrap the context-aware function
adk_tool = CrewaiTool(
    tool=crewai_tool_instance,
    name="context_search",
    description="Search with user preferences."
)
```

---

## Configuration Options

### LangchainTool Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tool` | `BaseTool` | Required | The LangChain tool instance to wrap |
| `name` | `str` | Tool's name | Override the tool name |
| `description` | `str` | Tool's description | Override the description |

### CrewaiTool Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tool` | `CrewAI BaseTool` | Required | The CrewAI tool instance to wrap |
| `name` | `str` | Tool's name | Override the tool name |
| `description` | `str` | Tool's description | Override the description |

---

## Complete Example: Multi-Tool Agent

```python
import os
from google.adk.agents import LlmAgent
from google.adk.tools.langchain_tool import LangchainTool
from google.adk.tools.crewai_tool import CrewaiTool
from langchain_community.tools.tavily_search import TavilySearchResults
from crewai_tools import SerperDevTool

# Set API keys
os.environ["TAVILY_API_KEY"] = "your-tavily-key"
os.environ["SERPER_API_KEY"] = "your-serper-key"

# Create LangChain tool
tavily_tool = LangchainTool(
    tool=TavilySearchResults(max_results=3),
    name="tavily_search",
    description="Search with Tavily for detailed web results."
)

# Create CrewAI tool
serper_tool = CrewaiTool(
    tool=SerperDevTool(),
    name="serper_search", 
    description="Quick web search using Serper."
)

# Create agent with both tools
root_agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="research_agent",
    instruction="""You are a research assistant with multiple search tools.
    - Use tavily_search for detailed, comprehensive results
    - Use serper_search for quick factual lookups
    Choose the appropriate tool based on the user's needs.""",
    tools=[tavily_tool, serper_tool]
)
```

---

## Integration Points

- **With Callbacks:** Use `before_tool_callback` to intercept calls to third-party tools
- **With State:** Third-party tools can access session state via `ToolContext`
- **With Other Tools:** Combine with native ADK tools, OpenAPI tools, or MCP tools

---

## Verification

```bash
# Run the agent
adk run research_agent

# Or use web interface
adk web research_agent
```

**Expected behavior:**
1. Agent loads with wrapped third-party tools
2. User can invoke LangChain/CrewAI tools through natural language
3. Tool results are processed and returned to the user
4. State is maintained across interactions if using ToolContext

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| ImportError for `langchain` | Package not installed | Run `pip install langchain langchain-community` |
| ImportError for `crewai` | Package not installed | Run `pip install "crewai[tools]"` |
| API key errors | Missing environment variable | Set `TAVILY_API_KEY`, `SERPER_API_KEY`, etc. |
| Schema mismatch | Tool signature incompatible | Check tool's input schema matches ADK requirements |
| ToolContext not available | Tool not accepting context | Ensure tool function signature includes `tool_context: ToolContext` |

---

## Available Third-Party Tools

ADK documentation lists these pre-integrated third-party tools:

- **Atlassian** - Jira, Confluence integration
- **Tavily** - Web search via LangChain
- **Serper** - Google search via CrewAI
- **And more** - See `docs/tools/third-party/index.md`

---

## References

- Third-Party Tools Index: `docs/tools/third-party/index.md`
- LangchainTool Implementation: `src/google/adk/tools/langchain_tool.py`
- CrewaiTool Implementation: `src/google/adk/tools/crewai_tool.py`
- LangChain Tavily Example: `examples/python/snippets/tools/third-party/langchain_tavily_search.py`
- CrewAI Serper Example: `examples/python/snippets/tools/third-party/crewai_serper_search.py`
