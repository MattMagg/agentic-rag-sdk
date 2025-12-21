---
description: Create LlmAgent with model, name, instructions, and optional configuration
---

# ADK Workflow: Create LlmAgent

Create an `LlmAgent` (aliased as `Agent`) — the core "thinking" component that leverages an LLM for reasoning, decision-making, and tool interaction.

---

## Prerequisites

- [ ] ADK installed (`pip install google-adk`)
- [ ] Google Cloud project or API key configured
- [ ] Environment variables set:
  ```bash
  # For Google AI Studio
  export GOOGLE_API_KEY="YOUR_API_KEY"
  export GOOGLE_GENAI_USE_VERTEXAI=FALSE
  
  # For Vertex AI
  export GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"
  export GOOGLE_CLOUD_LOCATION="us-central1"
  export GOOGLE_GENAI_USE_VERTEXAI=TRUE
  ```

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
| `model` | ✓ | LLM model string (e.g., `gemini-2.0-flash`) |
| `description` | Recommended | Used by other agents for routing decisions |
| `instruction` | Recommended | Defines behavior, constraints, output format |

```python
capital_agent = LlmAgent(
    model="gemini-2.0-flash",
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
| `gemini-2.0-flash` | Fast, cost-effective, general tasks |
| `gemini-2.5-flash` | Latest flash with improved capabilities |
| `gemini-2.5-pro-preview-03-25` | Most powerful, complex reasoning |

```python
# Fast agent
fast_agent = LlmAgent(
    model="gemini-2.0-flash",
    name="fast_agent",
    instruction="You are a fast and helpful assistant.",
)

# Powerful agent
powerful_agent = LlmAgent(
    model="gemini-2.5-pro-preview-03-25",
    name="powerful_agent",
    instruction="You are a knowledgeable assistant for complex tasks.",
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
    model="gemini-2.0-flash",
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
    model="gemini-2.0-flash",
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
    model="gemini-2.0-flash",
    name="billing_agent",
    description="Handles inquiries about current billing statements and payment history.",
    # ...
)

# Bad: Too vague
billing_agent = LlmAgent(
    model="gemini-2.0-flash",
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
    model="gemini-2.0-flash",
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
    model="gemini-2.0-flash",
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
    model="gemini-2.0-flash",
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

## References

- [LLM Agents](https://google.github.io/adk-docs/agents/llm-agents/) — Full LlmAgent documentation
- [Models](https://google.github.io/adk-docs/agents/models/) — Model selection and authentication
- [Multi-Agents](https://google.github.io/adk-docs/agents/multi-agents/) — Agent routing and sub-agents
