# ADK Builder Plugin Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a Claude Code plugin (`adk-builder`) that provides comprehensive ADK development guidance through 11 auto-activated skills and 10 commands with intelligent decision logic.

**Architecture:** Plugin adapts 43 existing workflow files from `.agent/workflows/` into Claude Code plugin structure. Skills provide domain knowledge (auto-activated), commands provide explicit actions with decision logic. Source workflows remain unchanged.

**Tech Stack:** Claude Code plugin system (markdown files with YAML frontmatter), no external dependencies.

---

## Pre-Implementation Checklist

Before starting:
- [ ] Design document exists: `docs/plans/2026-01-07-adk-builder-plugin-design.md`
- [ ] Source workflows exist: `.agent/workflows/adk-*.md` (43 files)
- [ ] Understand Claude Code plugin structure (see `plugin-dev:plugin-structure` skill)

---

## Task 1: Create Plugin Directory Structure

**Files:**
- Create: `adk-builder/.claude-plugin/plugin.json`
- Create: `adk-builder/README.md`
- Create: `adk-builder/skills/` (directory)
- Create: `adk-builder/commands/` (directory)

**Step 1: Create directory structure**

```bash
mkdir -p adk-builder/.claude-plugin
mkdir -p adk-builder/skills
mkdir -p adk-builder/commands
```

**Step 2: Create plugin.json manifest**

Write to `adk-builder/.claude-plugin/plugin.json`:

```json
{
  "name": "adk-builder",
  "version": "1.0.0",
  "description": "End-to-end agentic systems development with Google ADK. Comprehensive guidance for building production-ready agentic systems covering the full lifecycle: project setup, agent creation, tools, multi-agent orchestration, memory, security, streaming, deployment, and quality assurance.",
  "author": {
    "name": "ADK Builder Contributors"
  },
  "keywords": ["adk", "google", "agents", "agentic", "gemini", "vertex-ai"]
}
```

**Step 3: Create README.md**

Write to `adk-builder/README.md`:

```markdown
# ADK Builder

> End-to-end agentic systems development with Google ADK

A Claude Code plugin providing comprehensive guidance for building production-ready agentic systems with Google's Agent Development Kit (ADK).

## Features

- **11 Auto-Activated Skills**: Domain knowledge surfaces automatically based on context
- **10 Explicit Commands**: Action-oriented workflows with intelligent decision logic
- **Full Lifecycle Coverage**: From project setup to production deployment

## Installation

### Direct (for development)

```bash
claude --plugin-dir /path/to/adk-builder
```

### From This Repo

```bash
git clone https://github.com/yourname/rag_qdrant_voyage.git
claude --plugin-dir ./rag_qdrant_voyage/adk-builder
```

## Skills (Auto-Activated)

| Skill | Triggers When |
|-------|---------------|
| `adk-getting-started` | "new project", "setup", "initialize" |
| `adk-agents` | "create agent", "LlmAgent", "BaseAgent" |
| `adk-tools` | "add tool", "FunctionTool", "MCP" |
| `adk-behavior` | "callback", "state", "artifacts" |
| `adk-multi-agent` | "delegation", "orchestration" |
| `adk-memory` | "memory", "RAG", "grounding" |
| `adk-security` | "guardrail", "auth", "safety" |
| `adk-streaming` | "streaming", "SSE", "Live API" |
| `adk-deployment` | "deploy", "production" |
| `adk-quality` | "test", "eval", "tracing" |
| `adk-advanced` | "visual builder", "thinking" |

## Commands

| Command | Purpose |
|---------|---------|
| `/adk-init` | Initialize new ADK project |
| `/adk-create-agent` | Create new agent |
| `/adk-add-tool` | Add tool to agent |
| `/adk-add-behavior` | Add callbacks, state, events |
| `/adk-multi-agent` | Set up multi-agent system |
| `/adk-add-memory` | Add memory capabilities |
| `/adk-secure` | Add security features |
| `/adk-streaming` | Enable streaming |
| `/adk-deploy` | Deploy to production |
| `/adk-test` | Create tests/evals |

## License

MIT
```

**Step 4: Verify structure**

```bash
ls -la adk-builder/
ls -la adk-builder/.claude-plugin/
```

Expected: Directories exist, plugin.json present

**Step 5: Commit**

```bash
git add adk-builder/
git commit -m "feat(adk-builder): initialize plugin structure"
```

---

## Task 2: Create adk-getting-started Skill

**Files:**
- Create: `adk-builder/skills/adk-getting-started/SKILL.md`
- Create: `adk-builder/skills/adk-getting-started/references/init.md`
- Create: `adk-builder/skills/adk-getting-started/references/create-project.md`
- Create: `adk-builder/skills/adk-getting-started/references/yaml-config.md`
- Source: `.agent/workflows/adk-init.md`, `adk-init-create-project.md`, `adk-init-yaml-config.md`

**Step 1: Create skill directory**

```bash
mkdir -p adk-builder/skills/adk-getting-started/references
```

**Step 2: Create SKILL.md**

Write to `adk-builder/skills/adk-getting-started/SKILL.md`:

```markdown
---
name: ADK Getting Started
description: This skill should be used when the user asks about "creating a new ADK project", "initializing ADK", "setting up Google ADK", "adk create command", "ADK project structure", "YAML agent configuration", or needs guidance on bootstrapping an ADK development environment, authentication setup, or choosing between Python code and YAML-based agent definitions.
version: 1.0.0
---

# ADK Getting Started

Guide for initializing and setting up Google Agent Development Kit (ADK) projects.

## Overview

ADK projects can be created in two ways:
1. **Python Code** (`adk create`) - Full flexibility, custom tools, advanced patterns
2. **YAML Config** - Quick setup, no-code agents, declarative definition

## Quick Start

### Prerequisites

- Python 3.10+ (3.11+ recommended)
- Virtual environment
- Google API key or GCP credentials

### Initialize Project

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install ADK
pip install google-adk

# Verify installation
adk --version

# Create new agent project
adk create my_agent
```

### Authentication Options

**Option A: Google AI Studio (Simplest)**
```env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=YOUR_API_KEY
```

**Option B: Vertex AI (Production)**
```env
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GOOGLE_CLOUD_LOCATION=us-central1
```

### Run Your Agent

```bash
# Interactive CLI
adk run my_agent

# Web UI (recommended for development)
adk web

# API server
adk api_server
```

## Project Structure

```
my_agent/
├── __init__.py      # Package marker
├── agent.py         # Agent definition (root_agent)
└── .env             # Authentication credentials
```

## Decision Guide

| If you need... | Use |
|----------------|-----|
| Custom Python tools | `adk create` (Python) |
| Quick prototyping | YAML config |
| Full control | Python code |
| No-code approach | YAML config |

## References

For detailed guides:
- `references/init.md` - Complete initialization workflow
- `references/create-project.md` - Python project scaffolding
- `references/yaml-config.md` - YAML-based configuration
```

**Step 3: Copy and adapt reference files**

Copy `.agent/workflows/adk-init.md` to `adk-builder/skills/adk-getting-started/references/init.md`:
- Remove Antigravity frontmatter (keep only content after `---`)
- Keep all code examples, tables, steps
- Ensure code blocks have language specifiers

Copy `.agent/workflows/adk-init-create-project.md` to `references/create-project.md`
Copy `.agent/workflows/adk-init-yaml-config.md` to `references/yaml-config.md`

**Step 4: Verify skill structure**

```bash
ls -la adk-builder/skills/adk-getting-started/
ls -la adk-builder/skills/adk-getting-started/references/
```

**Step 5: Commit**

```bash
git add adk-builder/skills/adk-getting-started/
git commit -m "feat(adk-builder): add adk-getting-started skill"
```

---

## Task 3: Create adk-agents Skill

**Files:**
- Create: `adk-builder/skills/adk-agents/SKILL.md`
- Create: `adk-builder/skills/adk-agents/references/llm-agent.md`
- Create: `adk-builder/skills/adk-agents/references/custom-agent.md`
- Create: `adk-builder/skills/adk-agents/references/multi-model.md`
- Source: `.agent/workflows/adk-agents-create.md`, `adk-agents-custom.md`, `adk-agents-multi-model.md`

**Step 1: Create skill directory**

```bash
mkdir -p adk-builder/skills/adk-agents/references
```

**Step 2: Create SKILL.md**

Write to `adk-builder/skills/adk-agents/SKILL.md`:

```markdown
---
name: ADK Agents
description: This skill should be used when the user asks about "creating an agent", "LlmAgent", "BaseAgent", "custom agent", "agent with different model", "Claude with ADK", "OpenAI with ADK", "LiteLLM", "multi-model agent", or needs guidance on agent configuration, model selection, system instructions, or extending the base agent class for non-LLM logic.
version: 1.0.0
---

# ADK Agents

Guide for creating and configuring agents in Google ADK.

## Agent Types

| Type | Use Case | Class |
|------|----------|-------|
| **LLM Agent** | AI reasoning, tool use, conversation | `LlmAgent` |
| **Custom Agent** | Non-LLM logic, orchestration, API calls | `BaseAgent` |

## Creating an LlmAgent

```python
from google.adk.agents import LlmAgent

agent = LlmAgent(
    model="gemini-3-flash",
    name="my_agent",
    description="Handles user requests about X",  # For routing
    instruction="""You are a helpful assistant.
    - Be concise
    - Use tools when needed
    """,
)

# Export as root_agent for ADK CLI
root_agent = agent
```

### Required Parameters

| Parameter | Purpose |
|-----------|---------|
| `model` | LLM model string (e.g., `gemini-3-flash`) |
| `name` | Unique identifier (avoid `user`) |

### Recommended Parameters

| Parameter | Purpose |
|-----------|---------|
| `description` | Used by other agents for routing |
| `instruction` | System prompt defining behavior |

## Model Selection

### Gemini Models (Default)
- `gemini-3-flash` - Fast, cost-effective
- `gemini-3-pro` - Most capable

### Other Providers (via LiteLLM)
- `anthropic/claude-sonnet-4` - Claude
- `openai/gpt-4o` - OpenAI

```python
# Using Claude via LiteLLM
agent = LlmAgent(
    model="anthropic/claude-sonnet-4",
    name="claude_agent",
    instruction="...",
)
```

Requires: `pip install litellm` and `ANTHROPIC_API_KEY` env var.

## Custom Agents (BaseAgent)

For non-LLM logic:

```python
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.genai import types

class MyCustomAgent(BaseAgent):
    async def run_async(self, ctx: InvocationContext):
        # Your logic here
        yield types.Content(
            role="model",
            parts=[types.Part(text="Response")]
        )

root_agent = MyCustomAgent(name="custom_agent")
```

## References

For detailed guides:
- `references/llm-agent.md` - Complete LlmAgent configuration
- `references/custom-agent.md` - BaseAgent extension patterns
- `references/multi-model.md` - LiteLLM and model switching
```

**Step 3: Copy and adapt reference files**

Copy `.agent/workflows/adk-agents-create.md` → `references/llm-agent.md`
Copy `.agent/workflows/adk-agents-custom.md` → `references/custom-agent.md`
Copy `.agent/workflows/adk-agents-multi-model.md` → `references/multi-model.md`

Adaptation: Remove Antigravity frontmatter, keep content.

**Step 4: Commit**

```bash
git add adk-builder/skills/adk-agents/
git commit -m "feat(adk-builder): add adk-agents skill"
```

---

## Task 4: Create adk-tools Skill

**Files:**
- Create: `adk-builder/skills/adk-tools/SKILL.md`
- Create: `adk-builder/skills/adk-tools/references/` (7 files)
- Source: 7 tool workflows

**Step 1: Create skill directory**

```bash
mkdir -p adk-builder/skills/adk-tools/references
```

**Step 2: Create SKILL.md**

Write to `adk-builder/skills/adk-tools/SKILL.md`:

```markdown
---
name: ADK Tools
description: This skill should be used when the user asks about "adding a tool", "FunctionTool", "creating tools", "MCP integration", "OpenAPI tools", "built-in tools", "google_search tool", "code_execution tool", "long-running tools", "async tools", "third-party tools", "LangChain tools", "computer use", or needs guidance on extending agent capabilities with custom functions, API integrations, or external tool frameworks.
version: 1.0.0
---

# ADK Tools

Guide for adding tools to ADK agents. Tools extend agent capabilities beyond LLM reasoning.

## Tool Types

| Type | Use Case | Complexity |
|------|----------|------------|
| **FunctionTool** | Custom Python functions | Beginner |
| **Built-in** | Google Search, Code Execution | Beginner |
| **OpenAPI** | REST APIs with spec | Intermediate |
| **MCP** | Model Context Protocol servers | Intermediate |
| **Third-Party** | LangChain, CrewAI tools | Intermediate |
| **Long-Running** | Async operations >30s | Intermediate |
| **Computer Use** | Browser/desktop automation | Advanced |

## Quick Start: FunctionTool

```python
def get_weather(city: str) -> dict:
    """Get current weather for a city.

    Args:
        city: City name to get weather for.

    Returns:
        Weather data including temperature and conditions.
    """
    return {"temp": 72, "conditions": "sunny"}

agent = LlmAgent(
    model="gemini-3-flash",
    name="weather_agent",
    tools=[get_weather],  # ADK auto-wraps as FunctionTool
)
```

### Key Requirements

1. **Type hints** - Required for schema generation
2. **Docstring** - LLM uses this to understand the tool
3. **Return type** - Should be JSON-serializable

## Built-in Tools

```python
from google.adk.tools import google_search, code_execution

agent = LlmAgent(
    model="gemini-3-flash",
    name="research_agent",
    tools=[google_search, code_execution],
)
```

## Decision Guide

| If you have... | Use |
|----------------|-----|
| Python function | FunctionTool |
| OpenAPI/Swagger spec | OpenAPIToolset |
| MCP server | MCPToolset |
| LangChain tools | LangchainTool wrapper |
| Need web search | google_search built-in |
| Need code sandbox | code_execution built-in |
| Operation >30s | Long-running pattern |

## References

For detailed guides:
- `references/function-tools.md` - Custom Python functions
- `references/builtin-tools.md` - Google Search, Code Execution
- `references/openapi-tools.md` - REST API integration
- `references/mcp-tools.md` - MCP server integration
- `references/third-party-tools.md` - LangChain, CrewAI
- `references/long-running-tools.md` - Async operations
- `references/computer-use.md` - Browser/desktop automation
```

**Step 3: Copy and adapt reference files**

```
.agent/workflows/adk-tools-function.md → references/function-tools.md
.agent/workflows/adk-tools-builtin.md → references/builtin-tools.md
.agent/workflows/adk-tools-openapi.md → references/openapi-tools.md
.agent/workflows/adk-tools-mcp.md → references/mcp-tools.md
.agent/workflows/adk-tools-third-party.md → references/third-party-tools.md
.agent/workflows/adk-tools-long-running.md → references/long-running-tools.md
.agent/workflows/adk-tools-computer-use.md → references/computer-use.md
```

**Step 4: Commit**

```bash
git add adk-builder/skills/adk-tools/
git commit -m "feat(adk-builder): add adk-tools skill"
```

---

## Task 5: Create adk-behavior Skill

**Files:**
- Create: `adk-builder/skills/adk-behavior/SKILL.md`
- Create: `adk-builder/skills/adk-behavior/references/` (6 files)
- Source: 6 behavior workflows

**Step 1: Create skill directory**

```bash
mkdir -p adk-builder/skills/adk-behavior/references
```

**Step 2: Create SKILL.md**

Write to `adk-builder/skills/adk-behavior/SKILL.md`:

```markdown
---
name: ADK Behavior
description: This skill should be used when the user asks about "callbacks", "lifecycle hooks", "before_model_call", "after_tool_call", "plugins", "session state", "state management", "artifacts", "file uploads", "events", "EventActions", "human-in-the-loop", "confirmation", or needs guidance on customizing agent behavior, intercepting execution, managing state across turns, or implementing approval workflows.
version: 1.0.0
---

# ADK Behavior

Guide for customizing agent behavior through callbacks, state, artifacts, and events.

## Behavior Components

| Component | Purpose |
|-----------|---------|
| **Callbacks** | Intercept lifecycle events (before/after) |
| **Plugins** | Reusable callback bundles |
| **State** | Session data persistence |
| **Artifacts** | File/binary handling |
| **Events** | Flow control, custom events |
| **Confirmation** | Human-in-the-loop approval |

## Callbacks

Intercept agent execution at lifecycle points:

```python
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

async def log_model_call(ctx: CallbackContext) -> None:
    print(f"Calling model with: {ctx.request}")

agent = LlmAgent(
    model="gemini-3-flash",
    name="agent",
    before_model_callback=log_model_call,
)
```

### Available Callbacks

| Callback | Trigger Point |
|----------|---------------|
| `before_model_callback` | Before LLM call |
| `after_model_callback` | After LLM response |
| `before_tool_callback` | Before tool execution |
| `after_tool_callback` | After tool returns |

## Session State

Store data across conversation turns:

```python
def my_tool(ctx: ToolContext, query: str) -> str:
    # Read state
    count = ctx.state.get("query_count", 0)

    # Update state
    ctx.state["query_count"] = count + 1

    return f"Query #{count + 1}: {query}"
```

## Human-in-the-Loop

Require user confirmation for sensitive actions:

```python
async def confirm_action(ctx: CallbackContext) -> types.Content | None:
    tool_name = ctx.tool_call.name
    if tool_name in ["delete_file", "send_email"]:
        # Return content to ask for confirmation
        return types.Content(
            role="model",
            parts=[types.Part(text=f"Confirm {tool_name}? (yes/no)")]
        )
    return None  # Allow without confirmation
```

## References

For detailed guides:
- `references/callbacks.md` - Lifecycle callback patterns
- `references/plugins.md` - Reusable callback bundles
- `references/state.md` - Session state management
- `references/artifacts.md` - File/binary handling
- `references/events.md` - EventActions and flow control
- `references/confirmation.md` - Human-in-the-loop patterns
```

**Step 3: Copy reference files**

```
.agent/workflows/adk-behavior-callbacks.md → references/callbacks.md
.agent/workflows/adk-behavior-plugins.md → references/plugins.md
.agent/workflows/adk-behavior-state.md → references/state.md
.agent/workflows/adk-behavior-artifacts.md → references/artifacts.md
.agent/workflows/adk-behavior-events.md → references/events.md
.agent/workflows/adk-behavior-confirmation.md → references/confirmation.md
```

**Step 4: Commit**

```bash
git add adk-builder/skills/adk-behavior/
git commit -m "feat(adk-builder): add adk-behavior skill"
```

---

## Task 6: Create adk-multi-agent Skill

**Files:**
- Create: `adk-builder/skills/adk-multi-agent/SKILL.md`
- Create: `adk-builder/skills/adk-multi-agent/references/` (4 files)
- Source: 4 multi-agent workflows

**Step 1: Create skill directory**

```bash
mkdir -p adk-builder/skills/adk-multi-agent/references
```

**Step 2: Create SKILL.md**

Write to `adk-builder/skills/adk-multi-agent/SKILL.md`:

```markdown
---
name: ADK Multi-Agent
description: This skill should be used when the user asks about "multi-agent systems", "sub-agents", "delegation", "agent routing", "orchestration", "SequentialAgent", "ParallelAgent", "LoopAgent", "agent-to-agent", "A2A protocol", "agent hierarchy", or needs guidance on building systems with multiple specialized agents working together.
version: 1.0.0
---

# ADK Multi-Agent Systems

Guide for building multi-agent systems with delegation, orchestration, and inter-agent communication.

## Multi-Agent Patterns

| Pattern | Use Case | Complexity |
|---------|----------|------------|
| **Delegation** | Route to specialized sub-agents | Intermediate |
| **Sequential** | Pipeline of agents in order | Intermediate |
| **Parallel** | Concurrent agent execution | Intermediate |
| **Loop** | Iterative agent execution | Intermediate |
| **Hierarchy** | Nested agent teams | Advanced |
| **A2A** | Cross-system communication | Advanced |

## Quick Start: Delegation

```python
from google.adk.agents import LlmAgent

# Specialized sub-agents
billing_agent = LlmAgent(
    model="gemini-3-flash",
    name="billing",
    description="Handles billing inquiries and payment issues",
    instruction="You handle billing questions...",
)

support_agent = LlmAgent(
    model="gemini-3-flash",
    name="support",
    description="Handles technical support and troubleshooting",
    instruction="You handle technical issues...",
)

# Parent agent routes based on descriptions
root_agent = LlmAgent(
    model="gemini-3-flash",
    name="router",
    instruction="Route user requests to the appropriate specialist.",
    sub_agents=[billing_agent, support_agent],
)
```

## Workflow Agents

For deterministic execution patterns:

```python
from google.adk.agents import SequentialAgent, ParallelAgent

# Sequential: A → B → C
pipeline = SequentialAgent(
    name="pipeline",
    sub_agents=[research_agent, write_agent, review_agent],
)

# Parallel: A, B, C run concurrently
parallel = ParallelAgent(
    name="parallel",
    sub_agents=[search_agent, analyze_agent],
)
```

## Decision Guide

| If you need... | Use |
|----------------|-----|
| Dynamic routing based on query | Delegation (sub_agents) |
| Fixed execution order | SequentialAgent |
| Concurrent execution | ParallelAgent |
| Retry/iteration | LoopAgent |
| Cross-system agents | A2A protocol |

## References

For detailed guides:
- `references/delegation.md` - Sub-agent routing patterns
- `references/orchestration.md` - Sequential, Parallel, Loop agents
- `references/advanced.md` - Hierarchical and complex patterns
- `references/a2a.md` - Agent-to-Agent protocol
```

**Step 3: Copy reference files**

```
.agent/workflows/adk-multi-agent-delegation.md → references/delegation.md
.agent/workflows/adk-multi-agent-orchestration.md → references/orchestration.md
.agent/workflows/adk-multi-agent-advanced.md → references/advanced.md
.agent/workflows/adk-multi-agent-a2a.md → references/a2a.md
```

**Step 4: Commit**

```bash
git add adk-builder/skills/adk-multi-agent/
git commit -m "feat(adk-builder): add adk-multi-agent skill"
```

---

## Task 7: Create adk-memory Skill

**Files:**
- Create: `adk-builder/skills/adk-memory/SKILL.md`
- Create: `adk-builder/skills/adk-memory/references/` (2 files)
- Source: 2 memory workflows

**Step 1: Create skill directory**

```bash
mkdir -p adk-builder/skills/adk-memory/references
```

**Step 2: Create SKILL.md**

Write to `adk-builder/skills/adk-memory/SKILL.md`:

```markdown
---
name: ADK Memory
description: This skill should be used when the user asks about "memory", "MemoryService", "long-term memory", "remember across sessions", "RAG", "retrieval augmented generation", "grounding", "knowledge base", "vector search", or needs guidance on implementing persistent memory or grounding agent responses in external knowledge.
version: 1.0.0
---

# ADK Memory

Guide for implementing memory and grounding in ADK agents.

## Memory Types

| Type | Purpose | Persistence |
|------|---------|-------------|
| **Session State** | Within-conversation data | Session only |
| **MemoryService** | Long-term memories | Cross-session |
| **Grounding** | External knowledge (RAG) | External store |

## MemoryService

Store and recall information across sessions:

```python
from google.adk.memory import MemoryService

memory_service = MemoryService()

agent = LlmAgent(
    model="gemini-3-flash",
    name="agent",
    memory_service=memory_service,
)
```

The agent can now:
- Remember facts across conversations
- Recall user preferences
- Build context over time

## Grounding (RAG)

Ground responses in external knowledge:

```python
from google.adk.tools import VertexAISearchTool

# Connect to Vertex AI Search datastore
search_tool = VertexAISearchTool(
    project_id="my-project",
    location="us-central1",
    datastore_id="my-datastore",
)

agent = LlmAgent(
    model="gemini-3-flash",
    name="grounded_agent",
    tools=[search_tool],
    instruction="Always search for relevant information before answering.",
)
```

## Decision Guide

| If you need... | Use |
|----------------|-----|
| Remember facts across sessions | MemoryService |
| Search documents/knowledge base | Grounding (RAG) |
| Store data within session | Session State |
| Cite sources | Grounding with attribution |

## References

For detailed guides:
- `references/memory-service.md` - Long-term memory patterns
- `references/grounding.md` - RAG and knowledge grounding
```

**Step 3: Copy reference files**

```
.agent/workflows/adk-memory-service.md → references/memory-service.md
.agent/workflows/adk-memory-grounding.md → references/grounding.md
```

**Step 4: Commit**

```bash
git add adk-builder/skills/adk-memory/
git commit -m "feat(adk-builder): add adk-memory skill"
```

---

## Task 8: Create adk-security Skill

**Files:**
- Create: `adk-builder/skills/adk-security/SKILL.md`
- Create: `adk-builder/skills/adk-security/references/` (3 files)
- Source: 3 security workflows

**Step 1: Create skill directory**

```bash
mkdir -p adk-builder/skills/adk-security/references
```

**Step 2: Create SKILL.md**

Write to `adk-builder/skills/adk-security/SKILL.md`:

```markdown
---
name: ADK Security
description: This skill should be used when the user asks about "guardrails", "safety", "content filtering", "input validation", "output validation", "authentication", "OAuth", "API keys", "credentials", "security plugins", or needs guidance on implementing safety measures, access control, or secure authentication in ADK agents.
version: 1.0.0
---

# ADK Security

Guide for implementing security features in ADK agents.

## Security Components

| Component | Purpose |
|-----------|---------|
| **Input Guardrails** | Validate/filter user input |
| **Output Guardrails** | Validate/filter agent responses |
| **Authentication** | Secure API access |
| **Security Plugins** | Reusable security bundles |

## Input Guardrails

Block or modify unsafe input:

```python
from google.adk.agents.callback_context import CallbackContext
from google.genai import types

BLOCKED_TOPICS = ["illegal", "harmful"]

async def input_guardrail(ctx: CallbackContext) -> types.Content | None:
    user_input = ctx.user_content.parts[0].text.lower()

    for topic in BLOCKED_TOPICS:
        if topic in user_input:
            return types.Content(
                role="model",
                parts=[types.Part(text="I cannot help with that topic.")]
            )
    return None  # Allow input

agent = LlmAgent(
    model="gemini-3-flash",
    name="safe_agent",
    before_model_callback=input_guardrail,
)
```

## Output Guardrails

Filter agent responses before returning:

```python
async def output_guardrail(ctx: CallbackContext) -> types.Content | None:
    response = ctx.response.parts[0].text

    # Check for PII, profanity, etc.
    if contains_pii(response):
        return types.Content(
            role="model",
            parts=[types.Part(text="[Response filtered for privacy]")]
        )
    return None  # Allow output
```

## Authentication

For tools requiring auth:

```python
# OAuth credentials in environment
# GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET

from google.adk.auth import OAuthCredentials

credentials = OAuthCredentials(
    scopes=["https://www.googleapis.com/auth/calendar"],
)
```

## References

For detailed guides:
- `references/guardrails.md` - Input/output validation
- `references/auth.md` - Authentication patterns
- `references/security-plugins.md` - Reusable security bundles
```

**Step 3: Copy reference files**

```
.agent/workflows/adk-security-guardrails.md → references/guardrails.md
.agent/workflows/adk-security-auth.md → references/auth.md
.agent/workflows/adk-security-plugins.md → references/security-plugins.md
```

**Step 4: Commit**

```bash
git add adk-builder/skills/adk-security/
git commit -m "feat(adk-builder): add adk-security skill"
```

---

## Task 9: Create adk-streaming Skill

**Files:**
- Create: `adk-builder/skills/adk-streaming/SKILL.md`
- Create: `adk-builder/skills/adk-streaming/references/` (3 files)
- Source: 3 streaming workflows

**Step 1: Create skill directory**

```bash
mkdir -p adk-builder/skills/adk-streaming/references
```

**Step 2: Create SKILL.md**

Write to `adk-builder/skills/adk-streaming/SKILL.md`:

```markdown
---
name: ADK Streaming
description: This skill should be used when the user asks about "streaming", "real-time responses", "SSE", "server-sent events", "websocket", "bidirectional", "Live API", "voice", "audio", "video", "multimodal streaming", or needs guidance on implementing real-time communication between agents and clients.
version: 1.0.0
---

# ADK Streaming

Guide for implementing streaming and real-time communication in ADK agents.

## Streaming Types

| Type | Use Case | Complexity |
|------|----------|------------|
| **SSE** | Text streaming, progress updates | Intermediate |
| **Bidirectional** | Real-time chat, interrupts | Intermediate |
| **Multimodal** | Voice, video, Live API | Advanced |

## Server-Sent Events (SSE)

Stream responses as they're generated:

```python
from google.adk.runners import Runner

runner = Runner(agent=agent, app_name="app", session_service=sessions)

# Streaming execution
async for event in runner.run_async(
    user_id="user1",
    session_id="session1",
    new_message=content
):
    if event.content:
        print(event.content.parts[0].text, end="", flush=True)
```

## Bidirectional Streaming

Real-time two-way communication:

```python
from google.adk.streaming import BidiStreamingRunner

async with BidiStreamingRunner(agent) as runner:
    # Send messages
    await runner.send(user_message)

    # Receive responses
    async for response in runner.receive():
        process(response)
```

## Live API (Voice/Video)

For voice agents and multimodal:

```python
from google.adk.live import LiveAPIRunner

# Requires Live API compatible model
agent = LlmAgent(
    model="gemini-3-flash-live",  # Live API model
    name="voice_agent",
)

runner = LiveAPIRunner(agent)
# Handle audio/video streams
```

## Decision Guide

| If you need... | Use |
|----------------|-----|
| Text streaming | SSE |
| Real-time chat with interrupts | Bidirectional |
| Voice interaction | Live API |
| Video processing | Live API (multimodal) |

## References

For detailed guides:
- `references/sse.md` - Server-sent events streaming
- `references/bidirectional.md` - WebSocket bidirectional
- `references/multimodal.md` - Live API voice/video
```

**Step 3: Copy reference files**

```
.agent/workflows/adk-streaming-sse.md → references/sse.md
.agent/workflows/adk-streaming-bidi.md → references/bidirectional.md
.agent/workflows/adk-streaming-multimodal.md → references/multimodal.md
```

**Step 4: Commit**

```bash
git add adk-builder/skills/adk-streaming/
git commit -m "feat(adk-builder): add adk-streaming skill"
```

---

## Task 10: Create adk-deployment Skill

**Files:**
- Create: `adk-builder/skills/adk-deployment/SKILL.md`
- Create: `adk-builder/skills/adk-deployment/references/` (3 files)
- Source: 3 deploy workflows

**Step 1: Create skill directory**

```bash
mkdir -p adk-builder/skills/adk-deployment/references
```

**Step 2: Create SKILL.md**

Write to `adk-builder/skills/adk-deployment/SKILL.md`:

```markdown
---
name: ADK Deployment
description: This skill should be used when the user asks about "deploying", "production", "Agent Engine", "Vertex AI", "Cloud Run", "GKE", "Kubernetes", "hosting", "scaling", or needs guidance on deploying ADK agents to production environments.
version: 1.0.0
---

# ADK Deployment

Guide for deploying ADK agents to production.

## Deployment Options

| Platform | Best For | Complexity |
|----------|----------|------------|
| **Agent Engine** | Managed hosting, integrated services | Recommended |
| **Cloud Run** | Container control, serverless | Intermediate |
| **GKE** | Kubernetes, enterprise scale | Advanced |

## Agent Engine (Recommended)

Fully managed deployment with integrated Vertex AI services:

```bash
# Deploy to Agent Engine
adk deploy --project=my-project --region=us-central1

# Or via Python
from google.adk.deploy import deploy_to_agent_engine

deploy_to_agent_engine(
    agent=root_agent,
    project_id="my-project",
    location="us-central1",
)
```

### Benefits
- Auto-scaling
- Built-in session management
- Integrated with Vertex AI Search, Memory
- No infrastructure management

## Cloud Run

For more container control:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install google-adk
CMD ["adk", "api_server", "--host", "0.0.0.0", "--port", "8080"]
```

```bash
gcloud run deploy my-agent \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

## Decision Guide

| If you need... | Use |
|----------------|-----|
| Simplest deployment | Agent Engine |
| Custom container | Cloud Run |
| Kubernetes control | GKE |
| Integrated Vertex services | Agent Engine |

## References

For detailed guides:
- `references/agent-engine.md` - Vertex AI Agent Engine
- `references/cloudrun.md` - Cloud Run deployment
- `references/gke.md` - Kubernetes deployment
```

**Step 3: Copy reference files**

```
.agent/workflows/adk-deploy-agent-engine.md → references/agent-engine.md
.agent/workflows/adk-deploy-cloudrun.md → references/cloudrun.md
.agent/workflows/adk-deploy-gke.md → references/gke.md
```

**Step 4: Commit**

```bash
git add adk-builder/skills/adk-deployment/
git commit -m "feat(adk-builder): add adk-deployment skill"
```

---

## Task 11: Create adk-quality Skill

**Files:**
- Create: `adk-builder/skills/adk-quality/SKILL.md`
- Create: `adk-builder/skills/adk-quality/references/` (5 files)
- Source: 5 quality workflows

**Step 1: Create skill directory**

```bash
mkdir -p adk-builder/skills/adk-quality/references
```

**Step 2: Create SKILL.md**

Write to `adk-builder/skills/adk-quality/SKILL.md`:

```markdown
---
name: ADK Quality
description: This skill should be used when the user asks about "testing agents", "evaluation", "evals", "benchmarks", "tracing", "Cloud Trace", "logging", "observability", "AgentOps", "LangSmith", "user simulation", or needs guidance on testing, debugging, monitoring, or evaluating ADK agent quality.
version: 1.0.0
---

# ADK Quality

Guide for testing, evaluating, and monitoring ADK agents.

## Quality Components

| Component | Purpose |
|-----------|---------|
| **Evals** | Test agent behavior against criteria |
| **Tracing** | Debug execution flow |
| **Logging** | Capture events and errors |
| **Observability** | Third-party monitoring (AgentOps, etc.) |
| **User Simulation** | Automated testing with synthetic users |

## Evaluations

Test agent quality with eval sets:

```python
from google.adk.evals import EvalSet, EvalCase

eval_set = EvalSet(
    name="basic_tests",
    cases=[
        EvalCase(
            input="What's the capital of France?",
            expected_output_contains=["Paris"],
        ),
        EvalCase(
            input="Calculate 2+2",
            expected_output_contains=["4"],
        ),
    ],
)

# Run evals
results = eval_set.run(agent)
print(f"Pass rate: {results.pass_rate}%")
```

## Tracing

Debug with Cloud Trace:

```python
from google.adk.tracing import enable_tracing

enable_tracing(project_id="my-project")

# Agent calls now traced
# View in Cloud Console → Trace
```

## Logging

Enable structured logging:

```python
from google.adk.plugins import LoggingPlugin

agent = LlmAgent(
    model="gemini-3-flash",
    name="agent",
    plugins=[LoggingPlugin(level="DEBUG")],
)
```

## References

For detailed guides:
- `references/evals.md` - Evaluation framework
- `references/tracing.md` - Cloud Trace integration
- `references/logging.md` - Structured logging
- `references/observability.md` - Third-party integrations
- `references/user-sim.md` - Synthetic user testing
```

**Step 3: Copy reference files**

```
.agent/workflows/adk-quality-evals.md → references/evals.md
.agent/workflows/adk-quality-tracing.md → references/tracing.md
.agent/workflows/adk-quality-logging.md → references/logging.md
.agent/workflows/adk-quality-observability.md → references/observability.md
.agent/workflows/adk-quality-user-sim.md → references/user-sim.md
```

**Step 4: Commit**

```bash
git add adk-builder/skills/adk-quality/
git commit -m "feat(adk-builder): add adk-quality skill"
```

---

## Task 12: Create adk-advanced Skill

**Files:**
- Create: `adk-builder/skills/adk-advanced/SKILL.md`
- Create: `adk-builder/skills/adk-advanced/references/` (2 files)
- Source: 2 advanced workflows

**Step 1: Create skill directory**

```bash
mkdir -p adk-builder/skills/adk-advanced/references
```

**Step 2: Create SKILL.md**

Write to `adk-builder/skills/adk-advanced/SKILL.md`:

```markdown
---
name: ADK Advanced
description: This skill should be used when the user asks about "visual builder", "no-code agent builder", "drag and drop", "ThinkingConfig", "extended thinking", "chain of thought", "reasoning", or needs guidance on using ADK's visual development tools or configuring advanced reasoning capabilities.
version: 1.0.0
---

# ADK Advanced Features

Guide for advanced ADK features including visual building and extended thinking.

## Advanced Features

| Feature | Purpose |
|---------|---------|
| **Visual Builder** | No-code agent design |
| **ThinkingConfig** | Extended reasoning |

## Visual Builder

Build agents with drag-and-drop:

```bash
# Launch visual builder
adk web --builder

# Access at http://localhost:8000/builder
```

Features:
- Drag-and-drop agent design
- Visual tool configuration
- Export to Python code

## Extended Thinking

Enable chain-of-thought reasoning:

```python
from google.adk.agents import LlmAgent
from google.genai.types import ThinkingConfig

agent = LlmAgent(
    model="gemini-3-flash",
    name="thinking_agent",
    thinking_config=ThinkingConfig(
        thinking_budget=1024,  # Token budget for thinking
    ),
    instruction="Think step by step before answering.",
)
```

### When to Use

- Complex reasoning tasks
- Multi-step problems
- Tasks requiring planning

## References

For detailed guides:
- `references/visual-builder.md` - Visual development tools
- `references/thinking.md` - Extended thinking configuration
```

**Step 3: Copy reference files**

```
.agent/workflows/adk-advanced-visual-builder.md → references/visual-builder.md
.agent/workflows/adk-advanced-thinking.md → references/thinking.md
```

**Step 4: Commit**

```bash
git add adk-builder/skills/adk-advanced/
git commit -m "feat(adk-builder): add adk-advanced skill"
```

---

## Task 13: Create /adk-init Command

**Files:**
- Create: `adk-builder/commands/adk-init.md`

**Step 1: Create command file**

Write to `adk-builder/commands/adk-init.md`:

```markdown
---
name: adk-init
description: Initialize a new ADK project with intelligent authentication detection
argument-hint: Optional project name
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Initialize ADK Project

Initialize a new Google ADK project with proper structure, dependencies, and authentication.

## Decision Logic

**Step 1: Check for existing ADK project**

```bash
# Check for existing agent.py or pyproject.toml with google-adk
```

If exists: Ask user if they want to reinitialize or abort.

**Step 2: Detect GCP environment**

Check for:
- `GOOGLE_CLOUD_PROJECT` environment variable
- `~/.config/gcloud/application_default_credentials.json`
- Existing `.env` with Vertex AI config

**Step 3: Recommend authentication method**

If GCP detected:
> "I detected GCP credentials. I recommend **Vertex AI** authentication for production-ready setup with access to all Vertex AI services.
>
> Alternatively, use **Google AI Studio** (API key) for simpler setup.
>
> Which would you prefer?"

If no GCP:
> "I recommend **Google AI Studio** (API key) for the quickest setup.
>
> Get your API key at: https://aistudio.google.com/apikey
>
> Or configure **Vertex AI** if you have a GCP project.
>
> Which would you prefer?"

**Step 4: Execute initialization**

Based on selection, follow the appropriate path from `@adk-getting-started` skill.

1. Create virtual environment (if not exists)
2. Install google-adk
3. Create `.env` with selected auth method
4. Scaffold project with `adk create` or create manually
5. Verify with `adk --version` and test run

**Step 5: Verify success**

```bash
adk --version
adk run <project_name>  # Quick test
```

## Usage Examples

```
/adk-init                    # Interactive, detects best auth
/adk-init my_agent          # Create project named my_agent
```

## References

Load `@adk-getting-started` skill for detailed initialization guidance.
```

**Step 2: Commit**

```bash
git add adk-builder/commands/adk-init.md
git commit -m "feat(adk-builder): add /adk-init command"
```

---

## Task 14: Create /adk-create-agent Command

**Files:**
- Create: `adk-builder/commands/adk-create-agent.md`

**Step 1: Create command file**

Write to `adk-builder/commands/adk-create-agent.md`:

```markdown
---
name: adk-create-agent
description: Create a new ADK agent with intelligent type selection
argument-hint: Optional agent name and purpose
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Create ADK Agent

Create a new agent with intelligent selection of agent type and configuration.

## Decision Logic

**Step 1: Understand requirements**

Ask user:
> "What should this agent do? (Brief description)"

**Step 2: Recommend agent type**

Based on description:

If requires LLM reasoning (conversation, analysis, decisions):
> "I recommend **LlmAgent** because your use case requires AI reasoning.
>
> - Uses Gemini 3 Flash by default (fast, cost-effective)
> - Can use tools and have conversations
>
> Proceed with LlmAgent?"

If purely programmatic (API calls, calculations, orchestration):
> "I recommend **Custom Agent (BaseAgent)** because your use case is deterministic without LLM reasoning.
>
> - Full control over execution
> - No LLM costs
> - Best for orchestration logic
>
> Proceed with BaseAgent?"

**Step 3: Configure agent**

For LlmAgent:
1. Ask for agent name (or use provided)
2. Ask for model preference (default: gemini-3-flash)
3. Generate instruction based on purpose
4. Create agent.py

For BaseAgent:
1. Ask for agent name
2. Create agent.py with run_async skeleton

**Step 4: Create the agent file**

Use `@adk-agents` skill for implementation details.

**Step 5: Verify**

```bash
adk run <agent_name>
```

## Usage Examples

```
/adk-create-agent                           # Interactive
/adk-create-agent customer_support         # Named agent
/adk-create-agent "handles billing questions"  # With purpose
```

## References

Load `@adk-agents` skill for detailed agent configuration.
```

**Step 2: Commit**

```bash
git add adk-builder/commands/adk-create-agent.md
git commit -m "feat(adk-builder): add /adk-create-agent command"
```

---

## Task 15: Create /adk-add-tool Command

**Files:**
- Create: `adk-builder/commands/adk-add-tool.md`

**Step 1: Create command file**

Write to `adk-builder/commands/adk-add-tool.md`:

```markdown
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
```

**Step 2: Commit**

```bash
git add adk-builder/commands/adk-add-tool.md
git commit -m "feat(adk-builder): add /adk-add-tool command"
```

---

## Task 16: Create Remaining Commands (Batch)

**Files:**
- Create: `adk-builder/commands/adk-add-behavior.md`
- Create: `adk-builder/commands/adk-multi-agent.md`
- Create: `adk-builder/commands/adk-add-memory.md`
- Create: `adk-builder/commands/adk-secure.md`
- Create: `adk-builder/commands/adk-streaming.md`
- Create: `adk-builder/commands/adk-deploy.md`
- Create: `adk-builder/commands/adk-test.md`

**Step 1: Create adk-add-behavior.md**

```markdown
---
name: adk-add-behavior
description: Add behavior customization (callbacks, state, events) to an ADK agent
argument-hint: Optional behavior type
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Add Behavior to Agent

Add behavior customization to an existing ADK agent.

## Decision Logic

Ask user:
> "What behavior do you want to add?
>
> 1. **Callbacks** - Intercept lifecycle events (logging, validation)
> 2. **State Management** - Store data across turns
> 3. **Artifacts** - Handle file uploads/downloads
> 4. **Events** - Custom event handling
> 5. **Human-in-the-Loop** - Require confirmation for actions"

Based on selection, load appropriate section from `@adk-behavior` skill and implement.

## References

Load `@adk-behavior` skill for detailed implementation.
```

**Step 2: Create adk-multi-agent.md**

```markdown
---
name: adk-multi-agent
description: Set up a multi-agent system with intelligent pattern selection
argument-hint: Optional pattern type
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Set Up Multi-Agent System

Create a multi-agent system with appropriate orchestration pattern.

## Decision Logic

Ask user:
> "What multi-agent pattern do you need?
>
> 1. **Delegation** (Recommended) - Route to specialized sub-agents
> 2. **Sequential** - Pipeline of agents in order
> 3. **Parallel** - Run agents concurrently
> 4. **A2A** - Cross-system agent communication"

**Recommendation:** Start with delegation - it's the most flexible and covers most use cases.

Based on selection, load appropriate section from `@adk-multi-agent` skill.

## References

Load `@adk-multi-agent` skill for detailed implementation.
```

**Step 3: Create adk-add-memory.md**

```markdown
---
name: adk-add-memory
description: Add memory capabilities to an ADK agent
argument-hint: Optional memory type
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Add Memory to Agent

Add memory or grounding capabilities to an existing agent.

## Decision Logic

Ask user:
> "What memory capability do you need?
>
> 1. **Long-term Memory** - Remember facts across sessions (MemoryService)
> 2. **Knowledge Grounding** - Search documents/knowledge base (RAG)"

Based on selection, load appropriate section from `@adk-memory` skill.

## References

Load `@adk-memory` skill for detailed implementation.
```

**Step 4: Create adk-secure.md**

```markdown
---
name: adk-secure
description: Add security features to an ADK agent
argument-hint: Optional security type
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Secure ADK Agent

Add security features to an existing agent.

## Decision Logic

Ask user:
> "What security features do you need?
>
> 1. **Input Guardrails** (Recommended) - Filter/validate user input
> 2. **Output Guardrails** - Filter agent responses
> 3. **Authentication** - Secure API access (OAuth, API keys)
> 4. **All of the above**"

**Recommendation:** Start with input guardrails - they're the first line of defense.

Based on selection, load appropriate section from `@adk-security` skill.

## References

Load `@adk-security` skill for detailed implementation.
```

**Step 5: Create adk-streaming.md**

```markdown
---
name: adk-streaming
description: Enable streaming responses for an ADK agent
argument-hint: Optional streaming type
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Enable Streaming

Enable real-time streaming responses for an agent.

## Decision Logic

Ask user:
> "What streaming capability do you need?
>
> 1. **SSE** (Recommended) - Stream text responses progressively
> 2. **Bidirectional** - Real-time two-way communication
> 3. **Voice/Video** - Live API for audio/video streaming"

**Recommendation:** Start with SSE - it covers most chat use cases.

Based on selection, load appropriate section from `@adk-streaming` skill.

## References

Load `@adk-streaming` skill for detailed implementation.
```

**Step 6: Create adk-deploy.md**

```markdown
---
name: adk-deploy
description: Deploy an ADK agent to production with intelligent platform selection
argument-hint: Optional target (agent-engine, cloudrun, gke)
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Deploy ADK Agent

Deploy an agent to production with intelligent platform selection.

## Decision Logic

**Step 1: Analyze project**

Check for:
- Dockerfile (suggests Cloud Run/GKE preference)
- Vertex AI dependencies (suggests Agent Engine)
- GCP project configuration

**Step 2: Recommend platform**

> "I recommend **Agent Engine** for deployment because:
>
> - Managed hosting with auto-scaling
> - Built-in session management
> - Integrated Vertex AI services (Search, Memory)
> - No infrastructure to manage
>
> Alternatives:
> - **Cloud Run** - More container control
> - **GKE** - Full Kubernetes for enterprise
>
> Proceed with Agent Engine?"

**Step 3: Execute deployment**

Based on selection, follow deployment steps from `@adk-deployment` skill.

For Agent Engine:
```bash
adk deploy --project=PROJECT_ID --region=us-central1
```

**Step 4: Verify**

Confirm deployment successful and provide endpoint URL.

## Usage Examples

```
/adk-deploy                    # Interactive, recommends Agent Engine
/adk-deploy agent-engine      # Direct to Agent Engine
/adk-deploy cloudrun          # Direct to Cloud Run
```

## References

Load `@adk-deployment` skill for detailed deployment guides.
```

**Step 7: Create adk-test.md**

```markdown
---
name: adk-test
description: Create tests and evaluations for an ADK agent
argument-hint: Optional test type
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Test ADK Agent

Create tests and evaluations for agent quality assurance.

## Decision Logic

Ask user:
> "What testing do you need?
>
> 1. **Evaluations** (Recommended) - Test agent behavior with eval sets
> 2. **Tracing** - Debug execution flow with Cloud Trace
> 3. **Logging** - Add structured logging
> 4. **User Simulation** - Automated testing with synthetic users"

**Recommendation:** Start with evaluations - they're the foundation of agent testing.

Based on selection, load appropriate section from `@adk-quality` skill.

## References

Load `@adk-quality` skill for detailed testing guidance.
```

**Step 8: Commit all commands**

```bash
git add adk-builder/commands/
git commit -m "feat(adk-builder): add remaining commands"
```

---

## Task 17: Validate Plugin Structure

**Step 1: Verify all files exist**

```bash
# Check plugin structure
ls -la adk-builder/
ls -la adk-builder/.claude-plugin/
ls -la adk-builder/skills/
ls -la adk-builder/commands/

# Count skills (should be 11)
ls adk-builder/skills/ | wc -l

# Count commands (should be 10)
ls adk-builder/commands/ | wc -l
```

Expected:
- 11 skill directories
- 10 command files
- plugin.json exists
- README.md exists

**Step 2: Validate plugin.json**

```bash
cat adk-builder/.claude-plugin/plugin.json | python -m json.tool
```

Expected: Valid JSON output

**Step 3: Check skill structure**

```bash
# Each skill should have SKILL.md and references/
for skill in adk-builder/skills/*/; do
  echo "=== $skill ==="
  ls "$skill"
done
```

**Step 4: Commit validation**

```bash
git add -A
git commit -m "chore(adk-builder): complete plugin structure"
```

---

## Task 18: Test Plugin Loading

**Step 1: Test with Claude Code**

```bash
# Navigate to repo root
cd /Users/mac-main/rag_qdrant_voyage

# Launch Claude Code with plugin
claude --plugin-dir ./adk-builder
```

**Step 2: Verify skills load**

In Claude Code, ask:
> "How do I create an ADK agent?"

Expected: Claude should reference `adk-agents` skill knowledge.

**Step 3: Verify commands available**

In Claude Code, type:
> `/adk-init`

Expected: Command executes with decision logic.

**Step 4: Document any issues**

If issues found, create fixes and commit.

---

## Task 19: Final Commit and Push

**Step 1: Final commit**

```bash
git add -A
git status

# If any uncommitted changes
git commit -m "feat(adk-builder): complete v1.0.0 plugin

- 11 skills covering full ADK development lifecycle
- 10 commands with intelligent decision logic
- Adapted from 43 workflow files
- Ready for use with Claude Code"
```

**Step 2: Push to remote**

```bash
git push origin main
```

---

## Summary

| Component | Count | Status |
|-----------|-------|--------|
| Plugin manifest | 1 | Task 1 |
| Skills | 11 | Tasks 2-12 |
| Commands | 10 | Tasks 13-16 |
| README | 1 | Task 1 |
| **Total files** | ~65 | |

## v2 Roadmap (Future Tasks)

After v1 is stable:
1. Add `adk-architect` agent
2. Add `adk-reviewer` agent
3. Add `adk-debugger` agent
4. Create marketplace repo for distribution
5. Add hooks for auto-validation
