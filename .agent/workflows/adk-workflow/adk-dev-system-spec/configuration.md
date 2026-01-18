# Configuration

Runtime configuration for the ADK Development System including models, thinking, services, and tools.

---

## Environment Variables

Create a `.env` file in the project root:

```bash
# .env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
ADK_STAGING_BUCKET=gs://your-staging-bucket

# For Vertex AI (production)
GOOGLE_GENAI_USE_VERTEXAI=TRUE
```

---

## Model Constants

```python
# adk_dev_system/config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Models
ORCHESTRATOR_MODEL = "gemini-3-pro"
SPECIALIST_MODEL = "gemini-3-flash-preview"

# Thinking budget (tokens)
THINKING_BUDGET = 1024

# GCP
GCP_PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
GCP_REGION = os.environ["GOOGLE_CLOUD_LOCATION"]
STAGING_BUCKET = os.environ["ADK_STAGING_BUCKET"]
```

---

## ThinkingConfig (All Agents)

> **Run the `/adk-advanced-thinking` workflow** to configure thinking for each agent.

Every agent in this system uses `ThinkingConfig` for enhanced reasoning:

```python
from google.genai.types import ThinkingConfig
from google.adk.planners import BuiltInPlanner

# Shared thinking configuration
thinking_config = ThinkingConfig(
    include_thoughts=True,
    thinking_budget=1024  # Adjust per agent complexity
)

# Create planner to attach to each agent
planner = BuiltInPlanner(thinking_config=thinking_config)
```

Attach `planner=planner` to each `LlmAgent` definition.

---

## ArtifactService

> **Run the `/adk-behavior-artifacts` workflow** to configure artifact storage.

Required for persisting generated code files across sessions.

### Development (Local)

```python
from google.adk.artifacts import InMemoryArtifactService

artifact_service = InMemoryArtifactService()
```

### Production (Agent Engine)

Agent Engine provides managed artifact storage automatically. No explicit configuration needed.

---

## MemoryService

> **Run the `/adk-memory-service` workflow** to configure long-term memory.

Enables the system to remember past projects and reuse patterns.

### Development (Local)

```python
from google.adk.memory import InMemoryMemoryService

memory_service = InMemoryMemoryService()
```

### Production

```python
from google.adk.memory import VertexAiRagMemoryService

memory_service = VertexAiRagMemoryService(
    rag_corpus="projects/{project}/locations/{location}/ragCorpora/{corpus_id}"
)
```

---

## Session Service

> **Run the `/adk-behavior-state` workflow** to understand state flow.

### Development

```python
from google.adk.sessions import InMemorySessionService

session_service = InMemorySessionService()
```

### Production

Agent Engine provides `VertexAiSessionService` automatically.

---

## Tool Configuration

> **Run the `/adk-tools-builtin` workflow** to configure built-in tools.

### google_search

```python
from google.adk.tools import google_search
```

### code_execution

```python
from google.adk.tools import code_execution
```

---

## Confirmation Callback (Human-in-the-Loop)

> **Run the `/adk-behavior-confirmation` workflow** to add deployment confirmation.

Add a confirmation step before Ops deploys:

```python
from google.adk.agents import CallbackContext
from google.genai import types

async def confirm_before_deploy(callback_context: CallbackContext) -> types.Content | None:
    """Request user confirmation before deployment."""
    implementation = callback_context.state.get("implementation")
    if implementation:
        # Return content that asks for confirmation
        return types.Content(
            role="model",
            parts=[types.Part(text=f"Ready to deploy. Review the implementation:\n\n{implementation}\n\nProceed? (yes/no)")]
        )
    return None
```

Attach via `before_agent_callback` on the Ops agent.

---

## State Keys

| Agent | output_key | Contents |
|-------|------------|----------|
| Architect | `architecture_doc` | Design document, project structure |
| Developer | `implementation` | Generated Python code |
| Ops | `deployment_status` | Validation results, deploy command |

---

## Dependencies

```
# requirements.txt
google-adk>=1.0.0
python-dotenv>=1.0.0
```

---

## LoggingPlugin (Observability)

> **Run the `/adk-behavior-plugins` workflow** to configure plugins.

Add logging for debugging multi-agent handoffs:

```python
from google.adk.plugins import LoggingPlugin

# Attach to Runner
logging_plugin = LoggingPlugin(log_level="DEBUG")
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
    plugins=[logging_plugin]
)
```

---

## LoggingPlugin (Debugging)

> **Run the `/adk-behavior-plugins` workflow** to configure plugins.

Add logging for debugging multi-agent handoffs:

```python
from google.adk.plugins import LoggingPlugin

# Attach to Runner
logging_plugin = LoggingPlugin(log_level="DEBUG")
runner = Runner(
    agent=root_agent,
    app_name=APP_NAME,
    session_service=session_service,
    plugins=[logging_plugin]
)
```

---

## Event Stream Processing

> **Run the `/adk-behavior-events` workflow** to handle events.

Process events from sub-agents:

```python
from google.adk.events import Event, EventActions

# Custom event handler in callbacks
async def on_agent_event(event: Event):
    if event.author == "architect":
        print(f"Architect produced: {event.content}")
    elif event.actions and event.actions.escalate:
        print("Agent requested escalation")
```
