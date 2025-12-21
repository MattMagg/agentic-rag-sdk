---
description: Advanced multi-agent patterns including transfer control, hierarchical decomposition, and hybrid workflows
---

# ADK Workflow: Multi-Agent Advanced Patterns

Implement advanced multi-agent orchestration patterns including transfer restrictions, hierarchical task decomposition, and complex hybrid workflows.

> [!NOTE]
> For workflow agents basics, see `/adk-multi-agent-orchestration`.  
> For delegation patterns, see `/adk-multi-agent-delegation`.

---

## Prerequisites

- [ ] Familiarity with workflow agents (`SequentialAgent`, `ParallelAgent`, `LoopAgent`)
- [ ] Understanding of `transfer_to_agent()` mechanism
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
from google.adk.tools import AgentTool
from typing import AsyncGenerator
```

---

## Step 1: Control Agent Transfer Behavior

ADK's `AutoFlow` handles dynamic agent transfers via `transfer_to_agent()`. Control transfer scope with these parameters:

| Parameter | Default | Effect |
|-----------|---------|--------|
| `disallow_transfer_to_parent` | `False` | When `True`, prevents transfer back to parent |
| `disallow_transfer_to_peers` | `False` | When `True`, prevents transfer to sibling agents |

```python
# Restricted transfer: can only transfer to sub-agents
restricted_coordinator = LlmAgent(
    name="coordinator",
    model="gemini-2.0-flash",
    instruction="Route to specialists. Cannot return to supervisor.",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    sub_agents=[specialist_a, specialist_b]
)

# When both are True and no sub_agents exist, SingleFlow is used
# (no transfer capability at all)
isolated_agent = LlmAgent(
    name="isolated_worker",
    model="gemini-2.0-flash",
    instruction="Complete tasks independently. No delegation.",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True
)
```

### Transfer Target Resolution

The `AutoFlow` resolves transfer targets in this priority:
1. Direct sub-agents of current agent
2. Parent agent (if allowed)
3. Sibling agents (if allowed)

---

## Step 2: Build Hierarchical Task Decomposition

Multi-level agent trees for complex goal decomposition using `AgentTool`:

```python
# Level 2: Specialists (workers)
web_searcher = LlmAgent(
    name="web_searcher",
    model="gemini-2.0-flash",
    description="Searches the web for factual information."
)

summarizer = LlmAgent(
    name="summarizer", 
    model="gemini-2.0-flash",
    description="Condenses text into concise summaries."
)

fact_checker = LlmAgent(
    name="fact_checker",
    model="gemini-2.0-flash",
    description="Verifies claims for accuracy."
)

# Level 1: Team leads (wrap specialists as tools)
research_lead = LlmAgent(
    name="research_lead",
    model="gemini-2.0-flash",
    instruction="""You manage research tasks.
    Use WebSearcher for information gathering.
    Use Summarizer to condense findings.""",
    tools=[
        AgentTool(agent=web_searcher),
        AgentTool(agent=summarizer)
    ]
)

verification_lead = LlmAgent(
    name="verification_lead",
    model="gemini-2.0-flash",
    instruction="Verify all claims using the FactChecker tool.",
    tools=[AgentTool(agent=fact_checker)]
)

# Level 0: Project manager  
project_manager = LlmAgent(
    name="project_manager",
    model="gemini-2.0-flash",
    instruction="""Break down user requests into research and verification.
    Delegate to ResearchLead for gathering, VerificationLead for fact-checking.""",
    tools=[
        AgentTool(agent=research_lead),
        AgentTool(agent=verification_lead)
    ]
)
```

**AgentTool vs sub_agents:**
- `AgentTool`: Invoke as function, receive result, continue processing
- `sub_agents`: Transfer control to sub-agent, sub-agent produces response

---

## Step 3: Combine Patterns for Complex Workflows

Real applications often require mixing multiple patterns:

### Example: Research → Parallel Sources → Review Loop

```python
# Stage 1: Plan research
research_planner = LlmAgent(
    name="research_planner",
    model="gemini-2.0-flash",
    instruction="Analyze the topic and plan research approach.",
    output_key="research_plan"
)

# Stage 2: Parallel research across sources
academic_researcher = LlmAgent(
    name="academic_researcher",
    model="gemini-2.0-flash",
    instruction="Research academic sources.",
    output_key="academic_findings"
)
industry_researcher = LlmAgent(
    name="industry_researcher",
    model="gemini-2.0-flash", 
    instruction="Research industry sources.",
    output_key="industry_findings"
)
news_researcher = LlmAgent(
    name="news_researcher",
    model="gemini-2.0-flash",
    instruction="Research news sources.",
    output_key="news_findings"
)

parallel_research = ParallelAgent(
    name="parallel_research",
    sub_agents=[academic_researcher, industry_researcher, news_researcher]
)

# Stage 3: Synthesize findings
synthesizer = LlmAgent(
    name="synthesizer",
    model="gemini-2.0-flash",
    instruction="""Combine findings from state['academic_findings'], 
    state['industry_findings'], and state['news_findings'].""",
    output_key="draft_report"
)

# Stage 4: Quality review loop
quality_reviewer = LlmAgent(
    name="quality_reviewer",
    model="gemini-2.0-flash",
    instruction="Review state['draft_report']. Output 'APPROVED' or 'REVISE: <feedback>'.",
    output_key="review_status"
)

class ReviewEscalator(BaseAgent):
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        status = ctx.session.state.get("review_status", "")
        yield Event(
            author=self.name, 
            actions=EventActions(escalate=status.startswith("APPROVED"))
        )

review_loop = LoopAgent(
    name="review_loop",
    max_iterations=3,
    sub_agents=[synthesizer, quality_reviewer, ReviewEscalator(name="review_escalator")]
)

# Full pipeline: Sequential → Parallel → Loop (nested)
research_pipeline = SequentialAgent(
    name="comprehensive_research_pipeline",
    sub_agents=[
        research_planner,
        parallel_research,
        review_loop  # Nested loop within sequential
    ]
)
```

---

## Pattern Reference

| Pattern | Structure | Use Case |
|---------|-----------|----------|
| **Fan-out/Gather** | `Sequential[Parallel, Aggregator]` | Concurrent data fetching + synthesis |
| **Iterative Refinement** | `Loop[Generator, Critic, Escalator]` | Progressive improvement |
| **Hierarchical Delegation** | Multi-level `AgentTool` tree | Complex task decomposition |
| **Review Pipeline** | `Sequential[Generator, Reviewer]` | Content creation with quality check |
| **Hybrid** | Nested workflow agents | Complex real-world applications |

---

## Configuration Options

### LlmAgent Transfer Control

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `disallow_transfer_to_parent` | `bool` | `False` | Prevent upward transfers |
| `disallow_transfer_to_peers` | `bool` | `False` | Prevent sibling transfers |

### AgentTool

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent` | `BaseAgent` | Agent to wrap as callable tool |

---

## Verification

```bash
adk run agent_folder --verbose
```

**Check:**
1. Transfer restrictions respected (agent cannot transfer where disallowed)
2. Hierarchical delegation returns results to parent correctly
3. Nested workflows execute in expected order

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Transfer not working | `disallow_transfer_*` flags set | Check transfer restriction config |
| Agent not found in transfer | Name mismatch | Ensure exact `name` match |
| AgentTool result not returned | Agent didn't produce output | Check sub-agent produces content |
| Hybrid workflow fails | Missing state keys | Verify `output_key` usage across agents |

---

## References

- Multi-Agent Systems: `docs/agents/multi-agents.md`
- Agent Transfer: `src/google/adk/flows/llm_flows/agent_transfer.py`
- Transfer Tool: `src/google/adk/tools/transfer_to_agent_tool.py`
- Session State: `docs/sessions/state.md`
