# Agent Definitions

This document defines the 4 agents in the ADK Development System. Each section tells you which workflow to run for implementation.

---

## Pre-requisites

Before defining agents, configure the shared components:

1. **Run the `/adk-advanced-thinking` workflow** — Configure `ThinkingConfig` for all agents
2. **Run the `/adk-behavior-artifacts` workflow** — Set up `ArtifactService`
3. See [configuration.md](./configuration.md) for full setup

---

## Model Configuration

```python
# config.py
import os
from google.genai.types import ThinkingConfig
from google.adk.planners import BuiltInPlanner

# Models
ORCHESTRATOR_MODEL = "gemini-3-pro"
SPECIALIST_MODEL = "gemini-3-flash-preview"

# Thinking (all agents)
thinking_config = ThinkingConfig(include_thoughts=True, thinking_budget=1024)
planner = BuiltInPlanner(thinking_config=thinking_config)

# GCP
GCP_PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
GCP_REGION = os.environ["GOOGLE_CLOUD_LOCATION"]
STAGING_BUCKET = os.environ["ADK_STAGING_BUCKET"]
```

---

## Agent 1: Orchestrator (Root Agent)

**Role**: Coordinates the end-to-end development workflow by delegating to specialist agents.

> **Run the `/adk-agents-create` workflow** to create this agent.
> **Run the `/adk-multi-agent-delegation` workflow** to configure sub-agent transfers.

```python
from google.adk.agents import LlmAgent
from .config import ORCHESTRATOR_MODEL, planner
from .specialists import architect_agent, developer_agent, ops_agent

root_agent = LlmAgent(
    name="orchestrator",
    model=ORCHESTRATOR_MODEL,
    planner=planner,  # ThinkingConfig attached
    description="Coordinates end-to-end ADK system development.",
    instruction="""You are the Project Orchestrator for ADK development.

You coordinate a focused team to build ADK agentic systems end-to-end.

Your team:
- architect: Planning, analysis, project structure
- developer: Code generation, tools, multi-agent patterns
- ops: Validation, testing, deployment

Development workflow:
1. Understand user requirements
2. Transfer to architect for planning
3. Transfer to developer for implementation
4. Transfer to ops for validation and deployment
5. Report final status

State keys to monitor:
- architecture_doc: Design decisions from Architect
- implementation: Generated code from Developer
- deployment_status: Deployment info from Ops

Always maintain context across all phases.""",
    sub_agents=[architect_agent, developer_agent, ops_agent]
)
```

---

## Agent 2: Architect

**Role**: Analyzes requirements, plans architecture, scaffolds project structure.

> **Run the `/adk-agents-create` workflow** to create this agent.
> **Run the `/adk-init` workflow** for project initialization patterns.
> **Run the `/adk-init-create-project` workflow** for scaffolding.
> **Run the `/adk-tools-builtin` workflow** to configure `google_search` (requires `AgentTool` wrapper).
> **Run the `/adk-memory-grounding` workflow** to add RAG/search grounding.

> [!IMPORTANT]
> `google_search` cannot be mixed with other tools directly. Use the `AgentTool.create()` wrapper.

```python
from google.adk.agents import LlmAgent
from google.adk.tools import google_search, code_execution, AgentTool
from .config import SPECIALIST_MODEL, planner

# Create a dedicated search sub-agent (google_search cannot mix with other tools)
search_sub_agent = LlmAgent(
    name="search_sub_agent",
    model=SPECIALIST_MODEL,
    instruction="Search the web for ADK patterns and documentation. Return relevant information.",
    tools=[google_search]
)

# Wrap as a tool
search_tool = AgentTool.create(agent=search_sub_agent)

architect_agent = LlmAgent(
    name="architect",
    model=SPECIALIST_MODEL,
    planner=planner,  # ThinkingConfig attached
    description="Handles project planning, requirements analysis, and scaffolding.",
    instruction="""You are the Architect for ADK development.

Your responsibilities:
1. Analyze user requirements and break them into agent capabilities
2. Research ADK patterns using the search tool
3. Create project directory structure
4. Generate scaffolding (__init__.py, agent.py, requirements.txt)
5. Recommend single-agent vs multi-agent architecture

Output a complete architecture document with:
- Agent capabilities needed
- Recommended tools (built-in vs custom)
- Project structure
- State management approach (which output_keys)

Your output is saved to state['architecture_doc'] for the Developer to consume.""",
    tools=[search_tool, code_execution],  # Wrapped search + code_execution
    output_key="architecture_doc"
)
```

---

## Agent 3: Developer

**Role**: Generates ADK agent code, tools, and multi-agent patterns.

> **Run the `/adk-agents-create` workflow** for agent definitions.
> **Run the `/adk-tools-function` workflow** for custom FunctionTool creation.
> **Run the `/adk-tools-builtin` workflow** for built-in tools.
> **Run the `/adk-multi-agent-delegation` workflow** for sub_agents patterns.
> **Run the `/adk-multi-agent-orchestration` workflow** for Sequential/Parallel/Loop agents.
> **Run the `/adk-behavior-state` workflow** for output_key and state management.
> **Run the `/adk-behavior-callbacks` workflow** for lifecycle hooks.

```python
from google.adk.agents import LlmAgent
from google.adk.tools import code_execution
from .config import SPECIALIST_MODEL, planner

developer_agent = LlmAgent(
    name="developer",
    model=SPECIALIST_MODEL,
    planner=planner,  # ThinkingConfig attached
    description="Generates ADK agent code, tools, and multi-agent orchestration.",
    instruction="""You are the Developer for ADK systems.

Read state['architecture_doc'] for the design you must implement.

Your responsibilities:
1. Generate LlmAgent definitions with proper configuration
2. Write clear, specific agent instructions
3. Create FunctionTool definitions with complete docstrings
4. Integrate built-in tools (google_search, code_execution)
5. Set up multi-agent patterns (Sequential, Parallel, Loop) as needed
6. Configure state management with output_key

Code requirements:
- Type hints on all functions
- Comprehensive docstrings (Google style)
- snake_case agent names
- Specific, actionable instructions (no vague directives)
- All code must be complete and runnable

Your output is saved to state['implementation'] for Ops to validate.""",
    tools=[code_execution],
    output_key="implementation"
)
```

---

## Agent 4: Ops

**Role**: Validates code, runs tests, deploys to Agent Engine.

> **Run the `/adk-quality-evals` workflow** for testing and evalsets.
> **Run the `/adk-quality-logging` workflow** for debug logging.
> **Run the `/adk-behavior-confirmation` workflow** to add human-in-the-loop before deploy.
> **Run the `/adk-deploy-agent-engine` workflow** for Agent Engine deployment.

```python
from google.adk.agents import LlmAgent
from google.adk.tools import code_execution
from .config import SPECIALIST_MODEL, planner, GCP_PROJECT, GCP_REGION, STAGING_BUCKET

ops_agent = LlmAgent(
    name="ops",
    model=SPECIALIST_MODEL,
    planner=planner,  # ThinkingConfig attached
    description="Validates code, runs tests, and deploys to Agent Engine.",
    instruction=f"""You are the Ops Engineer for ADK systems.

Read state['implementation'] for the code to validate.

Your responsibilities:
1. Validate Python syntax and imports
2. Check ADK conventions (naming, structure, exports)
3. Verify agent instructions are clear and actionable
4. Ensure tools have proper docstrings
5. Create test cases using evalsets
6. Generate deployment configuration

Validation checklist:
- [ ] All imports are valid
- [ ] Agent names follow snake_case
- [ ] Tools have complete docstrings
- [ ] __init__.py exports root_agent or agent
- [ ] No hardcoded values (use env vars)

If validation passes, provide this deployment command:

```bash
adk deploy agent_engine \\
  --project={GCP_PROJECT} \\
  --region={GCP_REGION} \\
  --staging_bucket={STAGING_BUCKET} \\
  --trace_to_cloud \\
  AGENT_FOLDER
```

Your output is saved to state['deployment_status'].""",
    tools=[code_execution],
    output_key="deployment_status"
)
```

---

## State Flow

```
┌─────────────┐    architecture_doc    ┌─────────────┐    implementation    ┌─────────────┐
│  ARCHITECT  │ ───────────────────▶  │  DEVELOPER  │ ──────────────────▶ │     OPS     │
└─────────────┘                        └─────────────┘                      └─────────────┘
                                                                                   │
                                                                                   ▼
                                                                          deployment_status
```

Each agent reads the previous agent's output from session state and writes its own output for the next phase.
