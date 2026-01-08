---
description: Configure built-in tools like google_search, code_execution, and Vertex AI Search
---

# ADK Workflow: Built-in Tools

This workflow guides you through configuring ADK's built-in tools that provide grounding, code execution, and enterprise search capabilities without custom implementation.

---

## Prerequisites

- [ ] ADK project initialized (`/adk-init`)
- [ ] Agent created (`/adk-agents-create`)
- [ ] For `google_search`: Gemini API access or Vertex AI project
- [ ] For `code_execution`: Gemini 2.0+ model
- [ ] For `vertex_ai_search`: Vertex AI Search data store configured
- [ ] Required imports:

```python
from google.adk.agents import LlmAgent
from google.adk.tools import google_search, code_execution
from google.adk.tools import VertexAiSearchTool
```

---

## Built-in Tools Overview

| Tool | Purpose | Model Requirement | Best For |
|------|---------|-------------------|----------|
| `google_search` | Real-time web search grounding | Gemini 2.0+ | Current events, facts, research |
| `code_execution` | Execute Python code | Gemini 2.0+ | Calculations, data processing |
| `VertexAiSearchTool` | Enterprise data search | Any | Private/enterprise knowledge bases |

---

## Step 1: Google Search Tool

The `google_search` tool enables real-time web grounding for factual responses.

### Basic Usage

```python
from google.adk.agents import LlmAgent
from google.adk.tools import google_search

root_agent = LlmAgent(
    name="research_agent",
    model="gemini-3-flash-preview",
    instruction="""You are a research assistant. 
    Use Google Search to find current information when answering questions.
    Always cite your sources.""",
    tools=[google_search]
)
```

> [!IMPORTANT]
> The `google_search` tool is a special built-in tool that operates internally within Gemini models. It cannot be combined directly with other function tools due to API limitations.

### Workaround: Using with Other Tools

To use `google_search` alongside custom tools, wrap it in a sub-agent:

```python
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from google.adk.tools import AgentTool

# Create a dedicated search sub-agent
search_agent = LlmAgent(
    name="search_sub_agent",
    model="gemini-3-flash-preview",
    instruction="Search the web and return relevant information.",
    tools=[google_search]
)

# Wrap as a tool
search_tool = AgentTool.create(agent=search_agent)

# Main agent with both custom and search tools
root_agent = LlmAgent(
    name="main_agent",
    model="gemini-3-flash-preview",
    instruction="You help users with various tasks.",
    tools=[search_tool, my_custom_tool]
)
```

### Google Search Response Structure

When using Google Search grounding, the response includes:

| Field | Description |
|-------|-------------|
| `grounding_chunks` | Source documents/pages used |
| `grounding_supports` | Text segments with citations |
| `web_search_queries` | Queries the model generated |
| `search_entry_point` | Google Search entry point |

---

## Step 2: Code Execution Tool

The `code_execution` tool allows the model to write and execute Python code.

### Basic Usage

```python
from google.adk.agents import LlmAgent
from google.adk.tools import code_execution

root_agent = LlmAgent(
    name="calculator_agent",
    model="gemini-3-flash-preview",
    instruction="""You are a helpful assistant that can perform calculations.
    Use code execution for any mathematical operations or data processing.""",
    tools=[code_execution]
)
```

### How It Works

1. The model generates Python code based on the user's request
2. Code executes in a sandboxed environment
3. Results (stdout, return values) are returned to the model
4. Model interprets results and responds to the user

> [!CAUTION]
> Code execution runs in a sandboxed environment for security. The sandbox has limited capabilities and cannot access external networks or the local filesystem.

### Code Execution Variants

| Executor | Description | Use Case |
|----------|-------------|----------|
| Built-in | Gemini's internal executor | Simple calculations, quick scripts |
| `AgentEngineCodeExecutor` | Vertex AI Agent Engine sandbox | Production, persistent state |
| `GKECodeExecutor` | GKE-based sandbox | Custom dependencies, advanced use |

### Using AgentEngineCodeExecutor (Production)

```python
from google.adk.agents import LlmAgent
from google.adk.code_executors import AgentEngineCodeExecutor

code_executor = AgentEngineCodeExecutor(
    project_id="your-project-id",
    location="us-central1"
)

root_agent = LlmAgent(
    name="data_agent",
    model="gemini-3-flash-preview",
    instruction="You process data using Python code.",
    code_executor=code_executor  # Note: uses code_executor, not tools
)
```

---

## Step 3: Vertex AI Search Tool

`VertexAiSearchTool` grounds agent responses in your enterprise data stores.

### Prerequisites

1. Create a Vertex AI Search data store in Google Cloud Console
2. Index your documents/data
3. Note the `data_store_id` or `search_engine_id`

### Basic Usage

```python
from google.adk.agents import LlmAgent
from google.adk.tools import VertexAiSearchTool

# Configure the search tool
search_tool = VertexAiSearchTool(
    data_store_id="projects/YOUR_PROJECT/locations/global/collections/default_collection/dataStores/YOUR_DATASTORE_ID"
)

root_agent = LlmAgent(
    name="enterprise_agent",
    model="gemini-3-flash-preview",
    instruction="""You are an enterprise knowledge assistant.
    Search the company knowledge base to answer questions accurately.
    Always base your answers on the retrieved documents.""",
    tools=[search_tool]
)
```

### Configuration Options

```python
search_tool = VertexAiSearchTool(
    # Option 1: Use data_store_id
    data_store_id="projects/.../dataStores/my_datastore",
    
    # Option 2: Use search_engine_id (for search apps)
    # search_engine_id="projects/.../searchEngines/my_engine",
)
```

### Using Multiple Data Stores

```python
from google.adk.tools import VertexAiSearchTool

# For multiple data stores, use data_store_specs
search_tool = VertexAiSearchTool(
    data_store_specs=[
        {
            "data_store": "projects/my-project/locations/us-central1/collections/default_collection/dataStores/docs_store",
            "filter": ""  # Optional filter expression
        },
        {
            "data_store": "projects/my-project/locations/us-central1/collections/default_collection/dataStores/faq_store",
            "filter": ""
        }
    ]
)
```

---

## Step 4: Combining Built-in Tools

### Pattern: Search + Code Execution

Use sub-agents to combine capabilities:

```python
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import google_search, code_execution

# Research agent
research_agent = LlmAgent(
    name="researcher",
    model="gemini-3-flash-preview",
    instruction="Find relevant data using web search.",
    tools=[google_search]
)

# Analysis agent  
analysis_agent = LlmAgent(
    name="analyst",
    model="gemini-3-flash-preview",
    instruction="Analyze data using Python code.",
    tools=[code_execution]
)

# Orchestrate sequentially
root_agent = SequentialAgent(
    name="research_and_analyze",
    sub_agents=[research_agent, analysis_agent]
)
```

### Pattern: Enterprise Search + Custom Tools

```python
from google.adk.agents import LlmAgent
from google.adk.tools import VertexAiSearchTool

# Enterprise search tool
enterprise_search = VertexAiSearchTool(
    data_store_id="projects/my-proj/locations/us-central1/collections/default_collection/dataStores/company_docs"
)

# Custom tool for actions
def submit_ticket(title: str, description: str, priority: str) -> dict:
    """Submits an IT support ticket."""
    return {"ticket_id": "TKT-12345", "status": "created"}

# Combine both
root_agent = LlmAgent(
    name="it_support_agent",
    model="gemini-3-flash-preview",
    instruction="""You are an IT support agent.
    Search the knowledge base for solutions first.
    If no solution found, create a support ticket.""",
    tools=[enterprise_search, submit_ticket]
)
```

---

## Configuration Options

### google_search

| Aspect | Details |
|--------|---------|
| Import | `from google.adk.tools import google_search` |
| Type | Built-in tool (no instantiation needed) |
| Models | Gemini 2.0+ only |
| Limitation | Cannot mix with other function tools directly |

### code_execution

| Aspect | Details |
|--------|---------|
| Import | `from google.adk.tools import code_execution` |
| Type | Built-in tool (no instantiation needed) |
| Models | Gemini 2.0+ only |
| Environment | Sandboxed Python execution |

### VertexAiSearchTool

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `data_store_id` | `str` | One of these | Full resource path to data store |
| `search_engine_id` | `str` | One of these | Full resource path to search engine |
| `data_store_specs` | `list` | One of these | Multiple data stores with filters |

---

## Integration Points

- **With Callbacks:** Use `before_tool_callback` to filter search queries
- **With State:** Store search results in session state for reference
- **With Sub-agents:** Delegate to specialized search agents
- **With Streaming:** All built-in tools support streaming responses

---

## Verification

```bash
# Run the agent
adk web agent_folder
```

### Test Queries

**For google_search:**
```
What is the current weather in San Francisco?
What are the latest news about AI?
```

**For code_execution:**
```
Calculate the compound interest on $10,000 at 5% for 10 years
Generate a list of prime numbers up to 100
```

**For VertexAiSearchTool:**
```
What is our company's vacation policy?
How do I reset my password?
```

### Verification Checklist

- [ ] Agent loads without import errors
- [ ] Tool appears in agent capabilities
- [ ] Search returns grounded results with citations
- [ ] Code execution output is correct
- [ ] Enterprise search retrieves relevant documents

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `google_search` fails with other tools | API limitation | Use `AgentTool.create()` workaround |
| "Tool use unsupported" error | Wrong model version | Use Gemini 2.0+ model |
| No search results | Data store empty/not indexed | Verify data store configuration |
| Code execution timeout | Complex code | Simplify or use production executor |
| Authentication error | Missing credentials | Set `GOOGLE_APPLICATION_CREDENTIALS` |
| Data store not found | Wrong resource path | Verify full resource path format |

### Common Error Messages

| Error | Meaning | Fix |
|-------|---------|-----|
| `INVALID_ARGUMENT: Tool use with function calling is unsupported` | Mixing `google_search` with function tools | Use AgentTool wrapper |
| `Permission denied` | Missing IAM permissions | Grant required roles |
| `Data store not found` | Invalid resource path | Check data store ID format |

---

## References

- Google Search Tool: `docs/tools/gemini-api/google-search.md`
- Google Search Grounding: `docs/grounding/google_search_grounding.md`
- Code Execution: `docs/tools/gemini-api/code-execution.md`
- Agent Engine Code Executor: `docs/tools/google-cloud/code-exec-agent-engine.md`
- Vertex AI Search: `docs/tools/google-cloud/vertex-ai-search.md`
- Vertex AI Search Grounding: `docs/grounding/vertex_ai_search_grounding.md`
- Tool Limitations: `docs/tools/limitations.md`
