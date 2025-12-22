---
description: Build a streamlined multi-agent ADK development system for end-to-end agentic application creation
---

# ADK Workflow: Multi-Agent Development System

Build a **focused multi-agent system** that develops ADK agentic applications end-to-end by **chaining existing ADK workflows** through 4 specialized agents.

> [!NOTE]
> This system is designed for deployment on **Vertex AI Agent Engine**.

---

## Architecture Overview

```
                    ┌────────────────────────────────┐
                    │       ORCHESTRATOR             │
                    │       (gemini-3-pro)           │
                    │                                │
                    │  Coordinates project phases    │
                    └───────────────┬────────────────┘
                                    │ sub_agents
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
      ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
      │   ARCHITECT   │    │   DEVELOPER   │    │      OPS      │
      │               │    │               │    │               │
      │ • Planning    │    │ • Code gen    │    │ • Validation  │
      │ • Analysis    │    │ • Tools       │    │ • Testing     │
      │ • Structure   │    │ • Multi-agent │    │ • Deployment  │
      └───────────────┘    └───────────────┘    └───────────────┘
```

**Total: 4 agents** (down from 12)

---

## Model Configuration

```python
import os

# Orchestrator - most capable model
ORCHESTRATOR_MODEL = "gemini-3-pro"

# Specialist agents - fast, cost-effective
SPECIALIST_MODEL = "gemini-flash-3-preview"

# GCP Configuration (from .env)
GCP_PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
GCP_REGION = os.environ["GOOGLE_CLOUD_LOCATION"]
STAGING_BUCKET = os.environ["ADK_STAGING_BUCKET"]
```

---

## Step 1: Create Specialist Agents

### 1.1 Architect Agent

Handles planning, analysis, and project structure. Chains: `/adk-init`, `/adk-init-create-project`, `/adk-memory-grounding`

```python
from google.adk.agents import LlmAgent
from google.adk.tools import google_search, code_execution

architect_agent = LlmAgent(
    name="architect",
    model=SPECIALIST_MODEL,
    description="Handles project planning, requirements analysis, and scaffolding.",
    instruction="""You are the Architect for ADK development.

Your responsibilities:
1. Analyze user requirements and break them into agent capabilities
2. Research ADK patterns using google_search
3. Create project directory structure
4. Generate scaffolding (__init__.py, agent.py, requirements.txt)
5. Recommend single-agent vs multi-agent architecture

Follow workflows:
- /adk-init for initialization
- /adk-init-create-project for scaffolding
- /adk-memory-grounding for research

Output a complete architecture document with:
- Agent capabilities needed
- Recommended tools (built-in vs custom)
- Project structure
- State management approach
""",
    tools=[google_search, code_execution],
    output_key="architecture_doc"
)
```

### 1.2 Developer Agent

Handles code generation, tools, and multi-agent patterns. Chains: `/adk-agents-create`, `/adk-tools-*`, `/adk-multi-agent-*`, `/adk-behavior-*`

```python
developer_agent = LlmAgent(
    name="developer",
    model=SPECIALIST_MODEL,
    description="Generates ADK agent code, tools, and multi-agent orchestration.",
    instruction="""You are the Developer for ADK systems.

Your responsibilities:
1. Generate LlmAgent definitions with proper configuration
2. Write clear, specific agent instructions
3. Create FunctionTool definitions with docstrings
4. Integrate built-in tools (google_search, code_execution)
5. Set up multi-agent patterns (Sequential, Parallel, Loop)
6. Configure state management with output_key

Follow workflows:
- /adk-agents-create for agent definitions
- /adk-tools-function for custom tools
- /adk-tools-builtin for built-in tools
- /adk-multi-agent-delegation for orchestration
- /adk-behavior-callbacks for lifecycle hooks
- /adk-behavior-state for state management

Read state['architecture_doc'] for design decisions.

Code requirements:
- Type hints throughout
- Comprehensive docstrings
- snake_case agent names
- Specific, actionable instructions
""",
    tools=[code_execution],
    output_key="implementation"
)
```

### 1.3 Ops Agent

Handles validation, testing, and deployment. Chains: `/adk-quality-*`, `/adk-deploy-agent-engine`

```python
ops_agent = LlmAgent(
    name="ops",
    model=SPECIALIST_MODEL,
    description="Validates code, runs tests, and deploys to Agent Engine.",
    instruction="""You are the Ops Engineer for ADK systems.

Your responsibilities:
1. Validate Python syntax and imports
2. Check ADK conventions (naming, structure, exports)
3. Verify agent instructions are clear
4. Ensure tools have proper docstrings
5. Create test cases and run validation
6. Generate deployment configuration

Follow workflows:
- /adk-quality-evals for testing
- /adk-quality-logging for debugging
- /adk-deploy-agent-engine for deployment

Read state['implementation'] for code to validate.

Validation checklist:
- [ ] All imports are valid
- [ ] Agent names follow snake_case
- [ ] Tools have complete docstrings
- [ ] __init__.py exports root_agent or agent
- [ ] No hardcoded values (use env vars)

If validation passes, generate deployment command:
```bash
adk deploy agent_engine \\
  --project=$GCP_PROJECT \\
  --region=$GCP_REGION \\
  --staging_bucket=$STAGING_BUCKET \\
  --trace_to_cloud \\
  AGENT_FOLDER
```
""",
    tools=[code_execution],
    output_key="deployment_status"
)
```

---

## Step 2: Create Orchestrator

```python
root_agent = LlmAgent(
    name="orchestrator",
    model=ORCHESTRATOR_MODEL,
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

State keys:
- architecture_doc: Design decisions
- implementation: Generated code
- deployment_status: Deployment info

Always maintain context across all phases.
""",
    sub_agents=[architect_agent, developer_agent, ops_agent]
)
```

---

## Step 3: Project Structure

```
adk_dev_system/
├── __init__.py          # Exports root_agent
├── agent.py             # Orchestrator + specialists
├── config.py            # Model constants
└── requirements.txt
```

### __init__.py

```python
from .agent import root_agent
agent = root_agent
```

---

## Step 4: Deploy

```bash
adk deploy agent_engine \
  --project=$GOOGLE_CLOUD_PROJECT \
  --region=$GOOGLE_CLOUD_LOCATION \
  --staging_bucket=$ADK_STAGING_BUCKET \
  --trace_to_cloud \
  adk_dev_system
```

---

## Workflow Chaining Reference

| Agent | Workflows Invoked |
|-------|-------------------|
| Architect | `/adk-init`, `/adk-init-create-project`, `/adk-memory-grounding` |
| Developer | `/adk-agents-create`, `/adk-tools-*`, `/adk-multi-agent-*`, `/adk-behavior-*` |
| Ops | `/adk-quality-*`, `/adk-deploy-agent-engine` |

---

## Verification

```bash
adk run adk_dev_system --verbose
```

Test prompts:
- "Create a weather agent with google_search grounding"
- "Build a customer support system with routing"
- "Develop a research assistant with parallel web search"

---

## Why This Works Better

| Aspect | 12-Agent Version | 4-Agent Version |
|--------|------------------|-----------------|
| Latency | 12+ LLM calls | 4 LLM calls |
| Debugging | Complex traces | Simple traces |
| State | 8+ output_keys | 3 output_keys |
| Failure points | Many | Few |
| Maintenance | High | Low |

---

## References

- Agent creation: `/adk-agents-create`
- Multi-agent: `/adk-multi-agent-delegation`
- Deployment: `/adk-deploy-agent-engine`

---

## RAG-Validated Design Patterns

The following patterns are validated against the ingested ADK documentation and Agentic Design Patterns corpus.

### Pattern 1: Supervisor/Coordinator (Current Design)

```
ORCHESTRATOR (Supervisor)
     │
     ├─→ ARCHITECT
     ├─→ DEVELOPER
     └─→ OPS
```

> *"A central LlmAgent (Coordinator) manages several specialized sub_agents... Route incoming requests to the appropriate specialized agent."*

**When to use:** Sequential phase-dependent workflows where each phase builds on the previous.

---

### Pattern 2: Optional Parallelization (Enhancement)

For projects with **independent research tasks**, wrap parallel operations:

```python
from google.adk.agents import ParallelAgent

# Example: Parallel research within Architect phase
parallel_research = ParallelAgent(
    name="parallel_research",
    sub_agents=[
        requirements_analyzer,  # Analyze user requirements
        pattern_researcher,     # Research ADK patterns
        tool_scanner           # Scan available tools
    ]
)
```

**When to use:** Multiple independent lookups or research tasks.

---

### Pattern 3: Reflection/Critic Loop (Enhancement)

For **quality-critical code generation**, add iterative refinement:

```python
from google.adk.agents import LoopAgent

# Coder + Validator in a refinement loop
code_refinement_loop = LoopAgent(
    name="code_refinement",
    sub_agents=[coder_agent, validator_agent],
    max_iterations=3  # Prevent infinite loops
)
```

> *"The Reflection pattern involves an agent evaluating its own work... and using that evaluation to improve its performance."*

**When to use:** Code generation, documentation, or any output requiring high accuracy.

---

### Pattern Selection Guide

| Task Type | Pattern | ADK Agent |
|-----------|---------|-----------|
| Sequential phases | Supervisor | `LlmAgent` + `sub_agents` |
| Independent parallel tasks | Fan-out/gather | `ParallelAgent` |
| Iterative refinement | Reflection loop | `LoopAgent` |
| Dynamic routing | Coordinator | `LlmAgent` + `sub_agents` |
| Fixed pipeline | Pipeline | `SequentialAgent` |

---

### Hybrid Architecture (Advanced)

Combine patterns for complex projects:

```python
from google.adk.agents import SequentialAgent, ParallelAgent, LoopAgent

# Phase 1: Parallel research
research_phase = ParallelAgent(
    name="research",
    sub_agents=[requirements_agent, patterns_agent]
)

# Phase 2: Code generation with refinement loop
dev_phase = LoopAgent(
    name="development",
    sub_agents=[coder_agent, validator_agent],
    max_iterations=3
)

# Phase 3: Deploy
deploy_phase = deployer_agent

# Full pipeline
pipeline = SequentialAgent(
    name="full_pipeline",
    sub_agents=[research_phase, dev_phase, deploy_phase]
)
```

This architecture:
- Parallelizes independent research
- Iteratively refines code generation
- Sequentially executes dependent phases

---

### AgentTool vs sub_agents

| Mechanism | Behavior | Use Case |
|-----------|----------|----------|
| `sub_agents` | Transfer control, agent takes over | Phase transitions |
| `AgentTool` | Call agent as function, get result back | Invoke specialist mid-task |

**Current design uses `sub_agents`** because each phase fully transfers control.