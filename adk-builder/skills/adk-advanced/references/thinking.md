---
description: Enable model thinking/reasoning capabilities with ThinkingConfig and planners for enhanced problem-solving
---

# ADK Workflow: Advanced Thinking & Reasoning

Configure ADK agents to leverage model-level thinking capabilities for improved multi-step reasoning, planning, and complex problem-solving.

---

## Prerequisites

- [ ] ADK Python v0.1.0+ installed
- [ ] Model supporting thinking features (Gemini 2.5 series)
- [ ] Imports configured:

```python
from google.adk import Agent
from google.adk.planners import BuiltInPlanner, PlanReActPlanner
from google.genai.types import ThinkingConfig
```

---

## Approach Selection

ADK provides two approaches for enhanced reasoning:

| Approach | Best For | Model Requirement |
|----------|----------|-------------------|
| **BuiltInPlanner** | Models with native thinking | Gemini 2.5+ with thinking support |
| **PlanReActPlanner** | Any model | No special requirements |

---

## Step 1: Using BuiltInPlanner (Native Thinking)

For Gemini models that support built-in thinking, use `BuiltInPlanner` with `ThinkingConfig`:

### Configure ThinkingConfig

```python
from google.genai.types import ThinkingConfig

# Create thinking configuration
thinking_config = ThinkingConfig(
    include_thoughts=True,   # Include thoughts in response
    thinking_budget=1024     # Token limit for thinking (adjust as needed)
)
```

### Attach to Agent via Planner

```python
from google.adk import Agent
from google.adk.planners import BuiltInPlanner

# Create the planner with thinking configuration
planner = BuiltInPlanner(thinking_config=thinking_config)

# Attach planner to agent
agent = Agent(
    model="gemini-3-flash-preview",  # Must support thinking
    name="reasoning_agent",
    instruction="You are an analytical agent that thinks through problems carefully.",
    planner=planner,
    tools=[my_tool_1, my_tool_2]  # Optional tools
)
```

### Complete Example

```python
from google.genai import types
from google.genai.types import ThinkingConfig
from google.adk import Agent
from google.adk.planners import BuiltInPlanner
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Step 1: Configure thinking
thinking_config = ThinkingConfig(
    include_thoughts=True,
    thinking_budget=256
)

# Step 2: Create planner
planner = BuiltInPlanner(thinking_config=thinking_config)

# Step 3: Create agent with planner
agent = Agent(
    model="gemini-3-pro-preview",
    name="weather_agent",
    instruction="You are an agent that provides weather information",
    planner=planner,
    tools=[get_weather, get_current_time]
)

# Step 4: Run with runner
session_service = InMemorySessionService()
session = session_service.create_session(
    app_name="my_app", 
    user_id="user1", 
    session_id="session1"
)
runner = Runner(agent=agent, app_name="my_app", session_service=session_service)

# Execute query
content = types.Content(role='user', parts=[types.Part(text="What's the weather?")])
events = runner.run(user_id="user1", session_id="session1", new_message=content)
```

---

## Step 2: Using PlanReActPlanner (Universal)

For models without native thinking, use `PlanReActPlanner` which prompts the model to follow a structured reasoning format:

```python
from google.adk import Agent
from google.adk.planners import PlanReActPlanner

# Create agent with PlanReActPlanner
agent = Agent(
    model="gemini-3-flash-preview",  # Works with any model
    name="planning_agent",
    instruction="You are a helpful research assistant.",
    planner=PlanReActPlanner(),
    tools=[search_tool, calculator_tool]
)
```

### PlanReActPlanner Output Format

The model's response follows this structured format:

```
/*PLANNING*/
1. First, I will search for the latest AI news.
2. Then, I will synthesize the findings into a summary.

/*ACTION*/
[Tool calls happen here]

/*REASONING*/
The search results provide comprehensive coverage of recent AI news.
I have enough information to answer the user's request.

/*FINAL_ANSWER*/
Here's a summary of recent AI news:
...
```

### When to Use Each Planner

| Scenario | Recommended Planner |
|----------|---------------------|
| Gemini 2.5+ models | `BuiltInPlanner` |
| Non-thinking Gemini models | `PlanReActPlanner` |
| LiteLLM/third-party models | `PlanReActPlanner` |
| Need structured output format | `PlanReActPlanner` |
| Optimal thinking quality | `BuiltInPlanner` |

---

## ThinkingConfig Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `include_thoughts` | `bool` | Whether to include model's internal thoughts in response |
| `thinking_budget` | `int` | Token limit for thinking process (e.g., 256, 512, 1024) |

### Token Budget Guidelines

| Budget | Use Case |
|--------|----------|
| 128-256 | Simple reasoning, quick decisions |
| 512-1024 | Multi-step problems, tool selection |
| 2048+ | Complex analysis, detailed planning |

---

## Integration with LiteLLM Models

For non-Gemini models using LiteLLM, ADK automatically handles reasoning content:

```python
from google.adk import Agent
from google.adk.planners import PlanReActPlanner

# Use PlanReActPlanner for thinking-capable models via LiteLLM
agent = Agent(
    model="litellm/openai/o1-preview",  # OpenAI reasoning model
    name="reasoning_agent",
    instruction="Solve problems step by step.",
    planner=PlanReActPlanner()  # Works with any model
)
```

> **Note**: ADK's LiteLLM integration converts provider-specific reasoning payloads (like `reasoning_content`) into Gemini-compatible thought parts automatically.

---

## Accessing Thoughts in Responses

When `include_thoughts=True`, thoughts appear as `Part` objects with `thought=True`:

```python
for event in runner.run(user_id=user_id, session_id=session_id, new_message=content):
    if event.content:
        for part in event.content.parts:
            if hasattr(part, 'thought') and part.thought:
                print(f"[THOUGHT]: {part.text}")
            elif part.text:
                print(f"[RESPONSE]: {part.text}")
```

---

## Verification

```bash
# Run agent and observe thinking output
python your_agent.py
```

**Expected behavior:**
- With `include_thoughts=True`: See internal reasoning before final answer
- With `PlanReActPlanner`: See `/*PLANNING*/`, `/*REASONING*/`, `/*FINAL_ANSWER*/` sections
- Tools should be called after planning phase completes

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| No thoughts in output | `include_thoughts=False` | Set `include_thoughts=True` |
| Error with thinking config | Model doesn't support thinking | Use `PlanReActPlanner` instead |
| Incomplete reasoning | Budget too low | Increase `thinking_budget` |
| PlanReActPlanner tags missing | Model ignoring format | Strengthen instruction emphasis |

---

## Related Workflows

- [/adk-agents-create](file:///Users/mac-main/rag_qdrant_voyage/.agent/workflows/adk-agents-create.md) - Basic agent creation
- [/adk-agents-multi-model](file:///Users/mac-main/rag_qdrant_voyage/.agent/workflows/adk-agents-multi-model.md) - LiteLLM integration

---

## References

- [Gemini Thinking Documentation](https://ai.google.dev/gemini-api/docs/thinking)
- ADK LLM Agents Guide: `docs/agents/llm-agents.md` (Planner section)
- ADK BuiltInPlanner: `src/google/adk/planners/built_in_planner.py`
- ADK PlanReActPlanner: `src/google/adk/planners/plan_re_act_planner.py`
