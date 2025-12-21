---
description: Build complex multi-agent systems with workflow composition, advanced patterns, and transfer control
---

# ADK Workflow: Multi-Agent Orchestration

Design and implement multi-agent workflows using ADK's workflow agents (SequentialAgent, ParallelAgent, LoopAgent) for deterministic orchestration patterns.

> [!NOTE]
> For basic delegation patterns (LLM transfer, AgentTool), see `/adk-multi-agent-delegation`.  
> For advanced patterns (transfer control, hierarchical decomposition), see `/adk-multi-agent-advanced`.

---

## Prerequisites

- [ ] ADK project initialized (`adk create` or manual setup)
- [ ] Basic understanding of `LlmAgent` and workflow agents
- [ ] Import required classes:

```python
from google.adk.agents import (
    LlmAgent,
    BaseAgent,
    SequentialAgent,
    ParallelAgent,
    LoopAgent,
)
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from typing import AsyncGenerator
```

---

## Step 1: Understand Workflow Agent Architecture

ADK provides three specialized **workflow agents** that orchestrate sub-agent execution with **deterministic patterns**:

| Agent Type | Execution Pattern | Key Property |
|------------|-------------------|--------------|
| `SequentialAgent` | Runs sub-agents one-by-one in list order | Passes same `InvocationContext` |
| `ParallelAgent` | Runs all sub-agents concurrently | Creates isolated branches per sub-agent |
| `LoopAgent` | Repeats sub-agents until condition met | Stops on `escalate=True` or `max_iterations` |

**Critical insight:** Workflow agents do NOT use LLMs for orchestration—they are purely deterministic flow controllers. The sub-agents they orchestrate *may* use LLMs.

---

## Step 2: Compose Nested Workflow Patterns

Workflow agents can be nested to create sophisticated execution graphs.

### Fan-Out/Gather (Parallel → Sequential)

Run independent tasks concurrently, then aggregate results:

```python
# Parallel data fetchers
source1_fetcher = LlmAgent(
    name="source1_fetcher",
    model="gemini-2.0-flash",
    instruction="Fetch data from source 1.",
    output_key="source1_data"
)

source2_fetcher = LlmAgent(
    name="source2_fetcher", 
    model="gemini-2.0-flash",
    instruction="Fetch data from source 2.",
    output_key="source2_data"
)

source3_fetcher = LlmAgent(
    name="source3_fetcher",
    model="gemini-2.0-flash", 
    instruction="Fetch data from source 3.",
    output_key="source3_data"
)

# Parallel execution (fan-out)
data_gatherer = ParallelAgent(
    name="data_gatherer",
    sub_agents=[source1_fetcher, source2_fetcher, source3_fetcher]
)

# Aggregator runs after all parallel tasks complete
aggregator = LlmAgent(
    name="aggregator",
    model="gemini-2.0-flash",
    instruction="""Read data from state['source1_data'], state['source2_data'], 
    and state['source3_data']. Synthesize into a unified report."""
)

# Sequential wrapper: parallel gather → aggregate
fan_out_gather = SequentialAgent(
    name="fan_out_gather_pipeline",
    sub_agents=[data_gatherer, aggregator]
)
```

---

## Step 3: Implement Iterative Refinement Loops

Use `LoopAgent` for progressive improvement patterns with explicit termination.

### Generator-Critic-Escalate Pattern

```python
# Generator agent - creates/refines content
generator = LlmAgent(
    name="generator",
    model="gemini-2.0-flash",
    instruction="""Read state['requirements'] and state.get('feedback', '').
    Generate/refine content meeting requirements.""",
    output_key="draft"
)

# Critic agent - evaluates quality
critic = LlmAgent(
    name="critic",
    model="gemini-2.0-flash",
    instruction="""Evaluate state['draft'] against state['requirements'].
    Output either:
    - 'APPROVED' if requirements are met
    - 'NEEDS_WORK: <specific feedback>' if improvements needed""",
    output_key="evaluation"
)

# Custom escalation agent - terminates loop when approved
class EscalationChecker(BaseAgent):
    """Check evaluation and escalate if approved."""
    
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        evaluation = ctx.session.state.get("evaluation", "")
        should_stop = evaluation.startswith("APPROVED")
        
        # Extract feedback for next iteration if continuing
        if not should_stop and "NEEDS_WORK:" in evaluation:
            feedback = evaluation.split("NEEDS_WORK:")[1].strip()
            ctx.session.state["feedback"] = feedback
        
        yield Event(
            author=self.name,
            actions=EventActions(escalate=should_stop)
        )

# Assemble refinement loop
refinement_loop = LoopAgent(
    name="refinement_loop",
    max_iterations=5,  # Safety limit
    sub_agents=[
        generator,
        critic,
        EscalationChecker(name="escalation_checker")
    ]
)
```

**Termination mechanisms:**
1. Sub-agent emits `Event` with `actions.escalate=True`
2. `max_iterations` limit is reached

---

## Configuration Reference

### SequentialAgent

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Agent identifier |
| `sub_agents` | `list[BaseAgent]` | required | Agents executed in order |

### ParallelAgent

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Agent identifier |
| `sub_agents` | `list[BaseAgent]` | required | Agents executed concurrently |

**Note:** `ParallelAgent` creates isolated branches with unique `InvocationContext.branch` per sub-agent. All parallel sub-agents share access to `session.state` (use distinct keys to avoid races).

### LoopAgent

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | required | Agent identifier |
| `sub_agents` | `list[BaseAgent]` | required | Agents executed each iteration |
| `max_iterations` | `int` | `None` | Maximum iterations (safety limit) |

---

## Integration Points

- **With State:** All workflow sub-agents share session state. Use `output_key` for automatic output storage.
- **With Callbacks:** Workflow agents respect `before_agent_callback` and `after_agent_callback`.
- **With Runner:** Pass the root workflow agent to the `Runner` like any other agent.

---

## Verification

```bash
# Run your multi-agent workflow
adk run agent_folder --verbose
```

**Expected behaviors:**
1. **Sequential execution:** Sub-agents run in list order, each seeing previous state
2. **Parallel execution:** All sub-agents start approximately simultaneously
3. **Loop termination:** Loop exits on `escalate=True` or `max_iterations`

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Loop never terminates | No escalate signal, no `max_iterations` | Add `max_iterations` and/or escalation agent |
| Parallel results missing | Race conditions in state keys | Use distinct output keys per parallel agent |
| Nested workflow order wrong | Incorrect sub_agents list order | Verify agent list ordering |

---

## References

- Workflow Agents Index: `docs/agents/workflow-agents/index.md`
- SequentialAgent: `docs/agents/workflow-agents/sequential-agents.md`
- ParallelAgent: `docs/agents/workflow-agents/parallel-agents.md`
- LoopAgent: `docs/agents/workflow-agents/loop-agents.md`
