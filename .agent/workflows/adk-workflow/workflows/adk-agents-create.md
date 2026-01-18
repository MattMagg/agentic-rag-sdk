---
description: Create LlmAgent with model, name, instructions, and optional configuration
triggers:
  - create agent
  - new agent
  - LlmAgent
  - agent setup
  - build agent
category: agents
dependencies:
  - adk-init
outputs:
  - path: "{agent_name}/agent.py"
    type: file
  - path: "{agent_name}/__init__.py"
    type: file
context_required:
  - agent_name
  - agent_purpose
  - model_choice
completion_criteria:
  - "agent.py contains root_agent = LlmAgent(...)"
  - "adk run {agent_name} executes without errors"
estimated_steps: 5
difficulty: beginner
---

# ADK Workflow: Create LlmAgent

Create an `LlmAgent` (aliased as `Agent`) — the core "thinking" component that leverages an LLM for reasoning, decision-making, and tool interaction.

---

## Agent Decision Logic

> **Use this workflow when:**
> - User wants to create a new LLM-powered agent
> - User mentions "agent", "LlmAgent", or wants AI reasoning capabilities
> - Building the core "thinking" component of an agentic system
>
> **Do NOT use when:**
> - User needs a custom agent with non-LLM logic → use `/adk-agents-custom`
> - User wants to configure an existing agent's model → use `/adk-agents-multi-model`
> - User needs workflow orchestration without LLM → use `/adk-multi-agent-orchestration`
>
> **Prerequisites:** `/adk-init` must be completed (project structure exists)

---

## Step 1: Import LlmAgent

```python
from google.adk.agents import LlmAgent
# Or use the alias:
from google.adk.agents.llm_agent import LlmAgent
```

---

## Step 2: Define Agent Identity

Every agent requires:

| Parameter | Required | Purpose |
|-----------|----------|---------|
| `name` | ✓ | Unique identifier (avoid reserved name `user`) |
| `model` | ✓ | LLM model string (e.g., `gemini-3-flash-preview`) |
| `description` | Recommended | Used by other agents for routing decisions |
| `instruction` | Recommended | Defines behavior, constraints, output format |

```python
capital_agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="capital_agent",
    description="Answers user questions about the capital city of a given country.",
    instruction="""You are an agent that provides the capital city of a country.
When a user asks for the capital of a country:
1. Identify the country name from the user's query.
2. Use the `get_capital_city` tool to find the capital.
3. Respond clearly to the user, stating the capital city.
""",
)
```

---

## Step 3: Model Selection

### Gemini Models

| Model | Use Case |
|-------|----------|
| `gemini-3-flash-preview` | Latest flash with improved capabilities |
| `gemini-3-pro` | Most powerful, complex reasoning |

```python
# Agent
agent = LlmAgent(
    model="gemini-3-pro",
    name="agent",
    instruction="You are a fast and helpful assistant.",
)
```

### Voice/Video Streaming

For live streaming, use models that support the Live API:
- Check [Google AI Studio Live API docs](https://ai.google.dev/gemini-api/docs/models#live-api)
- Check [Vertex AI Live API docs](https://cloud.google.com/vertex-ai/generative-ai/docs/live-api)

---

## Step 4: System Instructions

### Static Instructions

Pass a string directly:

```python
agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="support_agent",
    instruction="""You are a customer support agent.
- Be polite and helpful
- Only answer questions about our product
- Escalate billing issues to the billing team
""",
)
```

### Dynamic Instructions with State

Use `{variable}` syntax to inject session state values:

```python
agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="personalized_agent",
    instruction="""You are helping {user_name}.
Their account type is: {account_type}
Their preferred language is: {language?}
""",  # ? makes variable optional
)
```

### Best Practices

1. **Be Clear and Specific** — Avoid ambiguity
2. **Use Markdown** — Improves readability for complex instructions
3. **Provide Examples (Few-Shot)** — Include input/output examples
4. **Guide Tool Use** — Explain *when* and *why* to use each tool

---

## Step 5: Agent Description (Multi-Agent Routing)

The `description` field is used by **other LLM agents** to decide if they should route a task to this agent.

```python
# Good: Specific and differentiating
billing_agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="billing_agent",
    description="Handles inquiries about current billing statements and payment history.",
    # ...
)

# Bad: Too vague
billing_agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="billing_agent",
    description="Billing agent",  # Not helpful for routing
    # ...
)
```

---

## Advanced Configuration

### Generate Content Config

Control LLM generation parameters:

```python
from google.genai import types

agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="deterministic_agent",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.2,  # More deterministic
        max_output_tokens=250,
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
            )
        ],
    ),
    # ...
)
```

### Input/Output Schema

Enforce structured data exchange:

```python
from pydantic import BaseModel, Field

class CapitalOutput(BaseModel):
    capital: str = Field(description="The capital of the country.")

structured_agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="structured_agent",
    instruction='Respond ONLY with JSON: {"capital": "capital_name"}',
    output_schema=CapitalOutput,  # Enforce JSON output
    output_key="found_capital",   # Store in state['found_capital']
)
```

### Context Control

```python
# Stateless agent (no conversation history)
stateless_agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="stateless_agent",
    include_contents='none',  # No prior history
    # ...
)
```

---

## Verification

### Local Testing

```bash
# Create agent folder structure
my_agent/
  ├── __init__.py
  ├── agent.py        # Contains: root_agent = LlmAgent(...)

# Test with CLI
adk run my_agent

# Test with web UI
adk web
```

### Minimal Test Code

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Create session
session_service = InMemorySessionService()
session = session_service.create_session(
    app_name="test_app",
    user_id="user1",
    session_id="session1"
)

# Run agent
runner = Runner(
    agent=capital_agent,
    app_name="test_app",
    session_service=session_service
)

content = types.Content(role='user', parts=[types.Part(text="What is the capital of France?")])
events = runner.run(user_id="user1", session_id="session1", new_message=content)

for event in events:
    if event.is_final_response() and event.content:
        print(event.content.parts[0].text)
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `429 RESOURCE_EXHAUSTED` | Quota exceeded | Request higher quota or enable client retries |
| Agent not routing correctly | Poor description | Make description specific and differentiating |
| Unexpected responses | Unclear instructions | Use structured markdown, add examples |
| State variable error | Missing state key | Add `?` suffix for optional: `{var?}` |

---

## Error Recovery

| Error | Cause | Recovery Action |
|-------|-------|-----------------|
| `ModuleNotFoundError: google.adk` | ADK not installed | Run `pip install google-adk` in virtual env |
| `ValueError: name 'user' is reserved` | Used reserved agent name | Change `name` parameter to different value |
| Agent not appearing in `adk web` | `root_agent` not defined | Ensure agent is assigned to `root_agent` variable |
| `TypeError: missing model` | Model not specified | Add `model="gemini-3-flash-preview"` parameter |

---

## Next Workflows

After completing this workflow:
- `/adk-tools-function` — Add custom tools to your agent
- `/adk-behavior-state` — Configure session state management
- `/adk-behavior-callbacks` — Add lifecycle callbacks for logging/validation
- `/adk-multi-agent-delegation` — Create sub-agents for task delegation

---

## References

- [LLM Agents](https://google.github.io/adk-docs/agents/llm-agents/) — Full LlmAgent documentation
- [Models](https://google.github.io/adk-docs/agents/models/) — Model selection and authentication
- [Multi-Agents](https://google.github.io/adk-docs/agents/multi-agents/) — Agent routing and sub-agents