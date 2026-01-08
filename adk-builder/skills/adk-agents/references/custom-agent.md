---
description: Implement custom agent extending BaseAgent for complex orchestration logic
---

# ADK Workflow: Custom Agent Implementation

Build specialized agents by extending `BaseAgent` when your requirements exceed the capabilities of `LlmAgent` or standard workflow agents (`SequentialAgent`, `LoopAgent`, `ParallelAgent`).

---

## Prerequisites

- [ ] Understanding of `LlmAgent` (see `/adk-agents-create`)
- [ ] Understanding of async generators in Python
- [ ] ADK installed (`pip install google-adk`)

---

## When to Use Custom Agents

Use a custom agent when you need:

| Requirement | Why Custom Agent? |
|-------------|-------------------|
| Conditional logic | Execute different sub-agents based on runtime conditions |
| Complex state management | Intricate logic beyond simple sequential passing |
| External integrations | Incorporate API calls within orchestration flow |
| Dynamic agent selection | Choose sub-agents based on evaluation |
| Unique workflow patterns | Logic that doesn't fit standard patterns |

---

## Step 1: Create the Custom Agent Class

Inherit from `BaseAgent` and define sub-agents:

```python
from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from typing import AsyncGenerator
from typing_extensions import override

class MyCustomAgent(BaseAgent):
    """Custom agent with conditional orchestration logic."""

    # Define sub-agents as class attributes
    step_one_agent: LlmAgent
    step_two_agent: LlmAgent
    fallback_agent: LlmAgent

    def __init__(
        self,
        step_one: LlmAgent,
        step_two: LlmAgent,
        fallback: LlmAgent,
        **kwargs,
    ):
        # Store sub-agents as instance attributes
        super().__init__(
            sub_agents=[step_one, step_two, fallback],  # Register with framework
            **kwargs,
        )
        self.step_one_agent = step_one
        self.step_two_agent = step_two
        self.fallback_agent = fallback
```

---

## Step 2: Implement `_run_async_impl`

Override the core execution method:

```python
@override
async def _run_async_impl(
    self, ctx: InvocationContext
) -> AsyncGenerator[Event, None]:
    """Core logic for custom orchestration.
    
    Args:
        ctx: InvocationContext with access to session, state, and agent tree.
    
    Yields:
        Event: Events from sub-agents and custom logic.
    """
    # Step 1: Run first sub-agent
    async for event in self.step_one_agent.run_async(ctx):
        yield event
    
    # Step 2: Read state to make conditional decisions
    result = ctx.session.state.get("step_one_result")
    
    # Step 3: Conditional branching
    if result == "success":
        async for event in self.step_two_agent.run_async(ctx):
            yield event
    else:
        # Fallback path
        async for event in self.fallback_agent.run_async(ctx):
            yield event
```

---

## Step 3: InvocationContext Usage

The `ctx` parameter provides access to runtime information:

### Key Properties

| Property | Type | Access |
|----------|------|--------|
| `ctx.session` | `Session` | Current session object |
| `ctx.session.state` | `dict` | Shared state dictionary |
| `ctx.user_content` | `types.Content` | Original user message |
| `ctx.agent` | `BaseAgent` | Current agent reference |
| `ctx.invocation_id` | `str` | Unique invocation ID |
| `ctx.branch` | `str` | Agent hierarchy path |

### State Management

```python
# Read state from previous agent
previous_result = ctx.session.state.get("some_key")

# Write state for subsequent agents
ctx.session.state["my_custom_result"] = "calculated_value"

# Check if key exists
if "required_key" in ctx.session.state:
    # proceed
    pass
```

---

## Step 4: Yielding Events

Custom agents yield `Event` objects to communicate with the framework:

```python
from google.adk.events.event import Event
from google.adk.events.event_actions import EventActions
from google.genai import types

# Yield text content
yield Event(
    author=self.name,
    invocation_id=ctx.invocation_id,
    content=types.Content(
        role="model",
        parts=[types.Part(text="Processing complete.")]
    ),
)

# Yield with actions (e.g., escalate)
yield Event(
    author=self.name,
    invocation_id=ctx.invocation_id,
    content=types.Content(
        role="model",
        parts=[types.Part(text="Escalating to parent agent.")]
    ),
    actions=EventActions(escalate=True),
)
```

### EventActions

| Action | Purpose |
|--------|---------|
| `escalate=True` | Exit current loop, return to parent |
| `transfer_to_agent="name"` | Delegate to another agent |
| `skip_summarization=True` | Skip LLM summarization of tool results |
| `end_of_agent=True` | Mark agent execution complete |

---

## Step 5: Sub-Agent Orchestration

### Run Sub-Agent and Forward Events

```python
async for event in self.some_sub_agent.run_async(ctx):
    # Optionally inspect event
    if event.content:
        print(f"Sub-agent output: {event.content.parts[0].text}")
    # Forward to framework
    yield event
```

### Conditional Sub-Agent Execution

```python
# Choose sub-agent based on user input
user_text = ctx.user_content.parts[0].text if ctx.user_content else ""

if "urgent" in user_text.lower():
    target_agent = self.urgent_handler
else:
    target_agent = self.normal_handler

async for event in target_agent.run_async(ctx):
    yield event
```

### Iterative Refinement Loop

```python
max_iterations = 3
for i in range(max_iterations):
    # Run critique agent
    async for event in self.critic_agent.run_async(ctx):
        yield event
    
    # Check if quality is acceptable
    quality_score = ctx.session.state.get("quality_score", 0)
    if quality_score > 0.8:
        break
    
    # Run revision agent
    async for event in self.reviser_agent.run_async(ctx):
        yield event
```

---

## Complete Example: StoryFlowAgent

A multi-stage content generation workflow with conditional regeneration:

```python
from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.loop_agent import LoopAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.events.event import Event
from typing import AsyncGenerator
from typing_extensions import override

class StoryFlowAgent(BaseAgent):
    """Custom agent for story generation with conditional refinement."""

    story_generator: LlmAgent
    loop_agent: LoopAgent
    sequential_agent: SequentialAgent

    def __init__(
        self,
        story_generator: LlmAgent,
        critic: LlmAgent,
        reviser: LlmAgent,
        grammar_check: LlmAgent,
        tone_check: LlmAgent,
        max_iterations: int = 2,
        **kwargs,
    ):
        # Create composite agents
        loop_agent = LoopAgent(
            name="revision_loop",
            max_iterations=max_iterations,
            sub_agents=[critic, reviser],
        )
        sequential_agent = SequentialAgent(
            name="final_checks",
            sub_agents=[grammar_check, tone_check],
        )

        super().__init__(
            sub_agents=[story_generator, loop_agent, sequential_agent],
            **kwargs,
        )
        self.story_generator = story_generator
        self.loop_agent = loop_agent
        self.sequential_agent = sequential_agent

    @override
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        # Step 1: Generate initial story
        async for event in self.story_generator.run_async(ctx):
            yield event

        # Step 2: Critique and revise loop
        async for event in self.loop_agent.run_async(ctx):
            yield event

        # Step 3: Final grammar and tone checks
        async for event in self.sequential_agent.run_async(ctx):
            yield event

        # Step 4: CUSTOM LOGIC - Regenerate if tone is negative
        tone_result = ctx.session.state.get("tone_check_result", "")
        if tone_result == "negative":
            # Regenerate the story
            async for event in self.story_generator.run_async(ctx):
                yield event
```

---

## Verification

### Test with Runner

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Create session service
session_service = InMemorySessionService()
session = session_service.create_session(
    app_name="test_app",
    user_id="user1",
    session_id="session1"
)

# Create custom agent (with sub-agents defined)
custom_agent = MyCustomAgent(
    name="my_custom_agent",
    step_one=step_one_agent,
    step_two=step_two_agent,
    fallback=fallback_agent,
)

# Create runner
runner = Runner(
    agent=custom_agent,
    app_name="test_app",
    session_service=session_service
)

# Run and iterate events
from google.genai import types
content = types.Content(role='user', parts=[types.Part(text="Start workflow")])

for event in runner.run(user_id="user1", session_id="session1", new_message=content):
    if event.content:
        print(f"[{event.author}]: {event.content.parts[0].text}")
```

### Command Line

```bash
# Create folder structure
my_custom_agent/
  ├── __init__.py
  ├── agent.py  # Contains: root_agent = MyCustomAgent(...)

# Run
adk run my_custom_agent
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Sub-agent events not appearing | Not yielding events | Always `yield event` in the async for loop |
| State not persisting | Wrong state key | Verify `output_key` on sub-agents matches state access |
| Infinite loop | Missing break condition | Add explicit break or iteration limit |
| TypeError on ctx | Wrong method signature | Ensure `async def _run_async_impl(self, ctx: InvocationContext)` |

---

## References

- [Custom Agents](https://google.github.io/adk-docs/agents/custom-agents/) — Full custom agent documentation
- [Context](https://google.github.io/adk-docs/context/) — InvocationContext and context types
- [Events](https://google.github.io/adk-docs/events/) — Event model and EventActions
