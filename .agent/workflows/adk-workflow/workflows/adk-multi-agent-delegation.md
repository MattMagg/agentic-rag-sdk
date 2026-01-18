---
description: Implement multi-agent delegation patterns with sub-agents, workflow orchestrators, and agent handoffs
---

# ADK Workflow: Multi-Agent Delegation

Build multi-agent systems where agents delegate work to specialized sub-agents, orchestrate complex workflows, and communicate through shared state.

---

## Prerequisites

- [ ] ADK project initialized (`adk create` or manual setup)
- [ ] Basic `LlmAgent` understanding
- [ ] Import required classes:

```python
from google.adk.agents import LlmAgent, SequentialAgent, ParallelAgent, LoopAgent
from google.adk.tools import AgentTool
```

---

## Step 1: Understand Agent Hierarchy Fundamentals

ADK multi-agent systems are built on **parent-child relationships**:

- Every `BaseAgent` has a `sub_agents` property accepting a list of child agents
- Parent agents can delegate to any of their registered sub-agents
- Sub-agents share the same session state as their parent

```python
# Basic parent-child structure
parent_agent = LlmAgent(
    name="coordinator",
    model="gemini-3-flash-preview",
    instruction="Route requests to appropriate specialists",
    sub_agents=[
        specialist_agent_1,
        specialist_agent_2,
    ]
)
```

---

## Step 2: Choose a Delegation Pattern

ADK provides three primary delegation mechanisms:

| Pattern | Mechanism | Use Case |
|---------|-----------|----------|
| **LLM-Chosen Transfer** | `transfer_to_agent()` function call | Dynamic routing based on context |
| **Workflow Orchestration** | `SequentialAgent`, `ParallelAgent`, `LoopAgent` | Fixed execution patterns |
| **Agent-as-Tool** | `AgentTool` wrapper | Invoke agent like a function, get result back |

---

## Step 3: Implement LLM-Chosen Transfer (Dynamic Delegation)

When sub-agents are present, ADK automatically enables `transfer_to_agent` via the `AutoFlow`:

```python
# Greeting specialist
greeting_agent = LlmAgent(
    name="greeting_specialist",
    model="gemini-3-flash-preview",
    instruction="Handle greetings and introductions warmly."
)

# Weather specialist
weather_agent = LlmAgent(
    name="weather_specialist",
    model="gemini-3-flash-preview",
    instruction="Provide weather information using available tools.",
    tools=[get_weather]
)

# Coordinator with transfer capability
coordinator = LlmAgent(
    name="coordinator",
    model="gemini-3-flash-preview",
    instruction="""You are a dispatcher. Based on user requests:
    - Transfer to 'greeting_specialist' for greetings
    - Transfer to 'weather_specialist' for weather queries
    - Handle general questions yourself""",
    sub_agents=[greeting_agent, weather_agent]
)
```

**How it works:**
1. LLM generates `transfer_to_agent(agent_name='target_agent_name')`
2. `AutoFlow` intercepts and routes to the target sub-agent
3. Target agent processes and responds
4. Control returns to parent based on flow configuration

---

## Step 4: Use Workflow Agents for Fixed Patterns

### SequentialAgent - Pipeline Processing

Executes sub-agents in defined order. Use for multi-step pipelines where each step depends on the previous.

```python
from google.adk.agents import SequentialAgent

# Define pipeline stages
research_agent = LlmAgent(
    name="researcher",
    model="gemini-3-flash-preview",
    instruction="Research the topic and save findings to state['research']."
)

writer_agent = LlmAgent(
    name="writer", 
    model="gemini-3-flash-preview",
    instruction="Read state['research'] and write a summary."
)

reviewer_agent = LlmAgent(
    name="reviewer",
    model="gemini-3-flash-preview", 
    instruction="Review the summary and provide feedback."
)

# Create sequential pipeline
content_pipeline = SequentialAgent(
    name="content_pipeline",
    sub_agents=[research_agent, writer_agent, reviewer_agent]
)
```

### ParallelAgent - Concurrent Execution

Executes all sub-agents simultaneously. Use for independent tasks that can run concurrently.

```python
from google.adk.agents import ParallelAgent

# Independent data fetchers
weather_fetcher = LlmAgent(
    name="weather_fetcher",
    model="gemini-3-flash-preview",
    instruction="Fetch current weather and save to state['weather'].",
    tools=[get_weather]
)

news_fetcher = LlmAgent(
    name="news_fetcher",
    model="gemini-3-flash-preview",
    instruction="Fetch top news and save to state['news'].",
    tools=[get_news]
)

# Run both concurrently
info_gatherer = ParallelAgent(
    name="info_gatherer",
    sub_agents=[weather_fetcher, news_fetcher]
)

# Often combined with Sequential for gather-then-process
report_generator = SequentialAgent(
    name="daily_briefing",
    sub_agents=[
        info_gatherer,  # Parallel fetch
        summary_agent   # Process gathered data
    ]
)
```

### LoopAgent - Iterative Execution

Repeats sub-agent execution. Use for iterative refinement until a condition is met.

```python
from google.adk.agents import LoopAgent

# Agent that refines until satisfied
refinement_agent = LlmAgent(
    name="refiner",
    model="gemini-3-flash-preview",
    instruction="""Review and improve the content in state['draft'].
    If quality is acceptable, call escalate() to exit the loop.
    Otherwise, update state['draft'] with improvements."""
)

# Loop until escalate() is called or max iterations
refinement_loop = LoopAgent(
    name="refinement_loop",
    sub_agents=[refinement_agent],
    max_iterations=5  # Safety limit
)
```

---

## Step 5: Implement Agent-as-Tool Pattern

Wrap an agent as a tool to invoke it like a function and receive its output:

```python
from google.adk.tools import AgentTool

# Specialist agent to be called as a tool
image_generator = LlmAgent(
    name="image_generator",
    model="gemini-3-flash-preview",
    instruction="Generate an image based on the provided prompt.",
    tools=[image_generation_tool]
)

# Wrap as AgentTool
image_tool = AgentTool(agent=image_generator)

# Parent agent uses it like any other tool
artist_agent = LlmAgent(
    name="artist",
    model="gemini-3-flash-preview",
    instruction="Create a prompt and use the ImageGen tool to create images.",
    tools=[image_tool]
)
```

**Key difference from transfer:**
- `transfer_to_agent`: Control moves to sub-agent, response comes from sub-agent
- `AgentTool`: Parent calls sub-agent, receives result, continues processing

---

## Step 6: Share Data via Session State

All agents in a hierarchy share the same session state:

```python
# Agent 1: Writes to state
researcher = LlmAgent(
    name="researcher",
    model="gemini-3-flash-preview",
    instruction="""Research the topic and store findings.
    Save your research to state using: state['findings'] = your_findings"""
)

# Agent 2: Reads from state
writer = LlmAgent(
    name="writer",
    model="gemini-3-flash-preview",
    instruction="""Write a report based on research findings.
    Read the research from: state['findings']"""
)

# Combined in a pipeline - state is automatically shared
pipeline = SequentialAgent(
    name="research_pipeline",
    sub_agents=[researcher, writer]
)
```

### State Prefix Scopes

| Prefix | Scope | Persistence |
|--------|-------|-------------|
| (none) | Session | Current session only |
| `user:` | User | Across all user sessions |
| `app:` | Application | Shared by all users |
| `temp:` | Temporary | Discarded after turn |

```python
# Examples of state access in tool functions
def save_user_preference(preference: str, tool_context: ToolContext):
    tool_context.state["user:preference"] = preference  # User-scoped
    tool_context.state["last_action"] = "saved_pref"    # Session-scoped
```

---

## Delegation Patterns Reference

### Coordinator/Dispatcher Pattern

Central agent routes to specialists:

```python
coordinator = LlmAgent(
    name="coordinator",
    model="gemini-3-flash-preview",
    instruction="""Analyze requests and route to:
    - billing_agent for payment issues
    - tech_support_agent for technical problems
    - general_agent for other queries""",
    sub_agents=[billing_agent, tech_support_agent, general_agent]
)
```

### Hierarchical Task Decomposition

Multi-level tree for complex goals:

```python
# Level 2: Specialists
data_collector = LlmAgent(name="data_collector", ...)
analyzer = LlmAgent(name="analyzer", ...)

# Level 1: Team leads
research_lead = LlmAgent(
    name="research_lead",
    sub_agents=[data_collector, analyzer]
)

# Level 0: Project manager
project_manager = LlmAgent(
    name="project_manager",
    sub_agents=[research_lead, writing_lead, review_lead]
)
```

### Parallel Fan-Out/Gather

Concurrent processing with aggregation:

```python
# Parallel data gathering
gather = ParallelAgent(
    name="gather",
    sub_agents=[source1_agent, source2_agent, source3_agent]
)

# Sequential aggregation
pipeline = SequentialAgent(
    name="pipeline",
    sub_agents=[gather, aggregator_agent]
)
```

---

## Configuration Options

### LlmAgent with Sub-agents

| Parameter | Type | Description |
|-----------|------|-------------|
| `sub_agents` | `list[BaseAgent]` | List of child agents |
| `instruction` | `str` | Should guide when to delegate |

### SequentialAgent

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Agent identifier |
| `sub_agents` | `list[BaseAgent]` | required | Agents to run in order |

### ParallelAgent

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Agent identifier |
| `sub_agents` | `list[BaseAgent]` | required | Agents to run concurrently |

### LoopAgent

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Agent identifier |
| `sub_agents` | `list[BaseAgent]` | required | Agents to run iteratively |
| `max_iterations` | `int` | None | Maximum loop iterations |

### AgentTool

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent` | `BaseAgent` | Agent to wrap as tool |

---

## Verification

```bash
# Run the multi-agent system
adk run agent_folder

# Or with verbose output
adk run agent_folder --verbose
```

**Expected behaviors:**

1. **Transfer working**: Coordinator routes to correct sub-agent based on query
2. **Sequential flow**: Agents execute in order, each seeing previous agent's state
3. **Parallel execution**: All parallel agents complete before next step
4. **State sharing**: Later agents can read state written by earlier agents

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `transfer_to_agent` not available | No sub-agents registered | Add `sub_agents=[...]` to parent |
| Sub-agent not found | Name mismatch | Ensure `agent_name` matches `name` property exactly |
| State not shared | Different sessions | Verify all agents run in same session context |
| Parallel agent timeout | Long-running sub-agent | Add timeout handling or split into smaller tasks |
| Loop runs forever | No exit condition | Use `escalate()` tool or set `max_iterations` |

---

## References

- ADK Multi-Agent Documentation (`docs/agents/multi-agents.md`)
- Workflow Agents Overview (`docs/agents/workflow-agents/index.md`)
- Sequential Agents (`docs/agents/workflow-agents/sequential-agents.md`)
- Loop Agents (`docs/agents/workflow-agents/loop-agents.md`)
- Agent-as-Tool (`docs/tools-custom/function-tools.md#agent-tool`)
- Session State (`docs/sessions/state.md`)
- Agent Team Tutorial (`docs/tutorials/agent-team.md`)
