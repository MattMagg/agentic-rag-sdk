# Project Structure

File layout for the ADK Development System.

---

## Directory Layout

```
adk_dev_system/
├── __init__.py          # Exports root_agent
├── agent.py             # Orchestrator definition
├── specialists.py       # Architect, Developer, Ops agents
├── config.py            # Models, thinking, GCP config
└── requirements.txt     # Dependencies
```

---

## Implementation

> **Run the `/adk-init-create-project` workflow** for scaffolding patterns.

### `__init__.py`

```python
"""ADK Development System - Multi-agent system for building ADK agents."""
from .agent import root_agent

# ADK expects either `root_agent` or `agent` export
agent = root_agent
```

### `config.py`

> **Run the `/adk-advanced-thinking` workflow** for ThinkingConfig setup.

```python
"""Configuration constants."""
import os
from dotenv import load_dotenv
from google.genai.types import ThinkingConfig
from google.adk.planners import BuiltInPlanner

load_dotenv()

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

### `agent.py`

> **Run the `/adk-agents-create` workflow** for LlmAgent setup.
> **Run the `/adk-multi-agent-delegation` workflow** for sub_agents configuration.

```python
"""Root orchestrator agent."""
from google.adk.agents import LlmAgent
from .config import ORCHESTRATOR_MODEL, planner
from .specialists import architect_agent, developer_agent, ops_agent

root_agent = LlmAgent(
    name="orchestrator",
    model=ORCHESTRATOR_MODEL,
    planner=planner,
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
- deployment_status: Deployment info from Ops""",
    sub_agents=[architect_agent, developer_agent, ops_agent]
)
```

### `specialists.py`

> See [agents.md](./agents.md) for the complete specialist agent definitions with all workflow references.

```python
"""Specialist agents: Architect, Developer, Ops."""
from google.adk.agents import LlmAgent
from google.adk.tools import google_search, code_execution, AgentTool
from .config import SPECIALIST_MODEL, planner, GCP_PROJECT, GCP_REGION, STAGING_BUCKET

# --- ARCHITECT ---
# Run /adk-tools-builtin for google_search setup (requires AgentTool wrapper)
# Run /adk-memory-grounding for RAG grounding

# google_search cannot mix with other tools - wrap in sub-agent
search_sub_agent = LlmAgent(
    name="search_sub_agent",
    model=SPECIALIST_MODEL,
    instruction="Search the web for ADK patterns and documentation. Return relevant information.",
    tools=[google_search]
)
search_tool = AgentTool.create(agent=search_sub_agent)

architect_agent = LlmAgent(
    name="architect",
    model=SPECIALIST_MODEL,
    planner=planner,
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
- State management approach""",
    tools=[search_tool, code_execution],
    output_key="architecture_doc"
)

# --- DEVELOPER ---
# Run /adk-tools-function for custom tools
# Run /adk-multi-agent-orchestration for Sequential/Parallel/Loop
# Run /adk-behavior-state for output_key patterns
developer_agent = LlmAgent(
    name="developer",
    model=SPECIALIST_MODEL,
    planner=planner,
    description="Generates ADK agent code, tools, and multi-agent orchestration.",
    instruction="""You are the Developer for ADK systems.

Read state['architecture_doc'] for the design you must implement.

Your responsibilities:
1. Generate LlmAgent definitions with proper configuration
2. Write clear, specific agent instructions
3. Create FunctionTool definitions with complete docstrings
4. Integrate built-in tools (google_search, code_execution)
5. Set up multi-agent patterns as needed
6. Configure state management with output_key

Code requirements:
- Type hints on all functions
- Comprehensive docstrings
- snake_case agent names
- Complete, runnable code""",
    tools=[code_execution],
    output_key="implementation"
)

# --- OPS ---
# Run /adk-quality-evals for testing
# Run /adk-behavior-confirmation for human-in-the-loop
# Run /adk-deploy-agent-engine for deployment
ops_agent = LlmAgent(
    name="ops",
    model=SPECIALIST_MODEL,
    planner=planner,
    description="Validates code, runs tests, and deploys to Agent Engine.",
    instruction=f"""You are the Ops Engineer for ADK systems.

Read state['implementation'] for the code to validate.

Your responsibilities:
1. Validate Python syntax and imports
2. Check ADK conventions (naming, structure, exports)
3. Verify agent instructions are clear
4. Ensure tools have proper docstrings
5. Create test cases
6. Generate deployment configuration

Validation checklist:
- [ ] All imports are valid
- [ ] Agent names follow snake_case
- [ ] Tools have complete docstrings
- [ ] __init__.py exports root_agent or agent
- [ ] No hardcoded values

If validation passes, provide deployment command:

```bash
adk deploy agent_engine \\
  --project={GCP_PROJECT} \\
  --region={GCP_REGION} \\
  --staging_bucket={STAGING_BUCKET} \\
  --trace_to_cloud \\
  AGENT_FOLDER
```""",
    tools=[code_execution],
    output_key="deployment_status"
)
```

### `requirements.txt`

```
google-adk>=1.0.0
python-dotenv>=1.0.0
```

---

## Verification

```bash
# Test locally
adk run adk_dev_system --verbose

# Test with web UI
adk web
```
