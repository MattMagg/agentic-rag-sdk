---
description: Scaffold ADK project structure with adk create CLI command
---

# ADK Workflow: Create Project Structure

Scaffold a new ADK project with the proper directory structure, files, and dependencies using the `adk create` CLI command.

---

## Prerequisites

- [ ] Python 3.10+ installed
- [ ] Virtual environment activated
- [ ] ADK installed (`pip install google-adk`)
- [ ] API key or GCP credentials ready

---

## Step 1: Create Project with CLI

Use the `adk create` command to scaffold your project:

```bash
# Basic project creation
adk create my_agent

# With specific model
adk create my_agent --model gemini-2.0-flash

# For YAML-based agent (no Python code)
adk create --type=config my_agent
```

### CLI Options

| Option | Description | Example |
|--------|-------------|---------|
| `--model` | Specify the LLM model | `--model gemini-2.5-pro` |
| `--type` | Project type (`code` or `config`) | `--type=config` |
| `--api-key` | Set API key directly | `--api-key=YOUR_KEY` |
| `--project` | GCP project ID | `--project=my-gcp-project` |
| `--region` | GCP region | `--region=us-central1` |

---

## Step 2: Understand Project Structure

The generated project follows this structure:

```
parent_folder/
    my_agent/
        __init__.py      # Module exports
        agent.py         # Main agent definition with root_agent
        .env             # Environment configuration
```

### `__init__.py`

Exports the agent module for discovery:

```python
from . import agent
```

### `agent.py`

Contains the `root_agent` definition (required):

```python
from google.adk.agents.llm_agent import Agent

def get_current_time(city: str) -> dict:
    """Returns the current time in a specified city."""
    return {"status": "success", "city": city, "time": "10:30 AM"}

root_agent = Agent(
    model='gemini-2.0-flash',
    name='root_agent',
    description="Tells the current time in a specified city.",
    instruction="You are a helpful assistant that tells the current time in cities. Use the 'get_current_time' tool for this purpose.",
    tools=[get_current_time],
)
```

### `.env`

Environment configuration for authentication:

```env
# For Google AI Studio
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=YOUR_API_KEY

# For Vertex AI (alternative)
# GOOGLE_GENAI_USE_VERTEXAI=TRUE
# GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
# GOOGLE_CLOUD_LOCATION=us-central1
```

---

## Step 3: Manual Project Creation (Alternative)

If you prefer to create the structure manually:

```bash
# Create agent folder
mkdir my_agent

# Create files
echo "from . import agent" > my_agent/__init__.py
touch my_agent/agent.py
touch my_agent/.env
```

Then populate `agent.py` with your agent code.

---

## Step 4: Configure Environment

Set up your `.env` file based on your authentication method:

### Google AI Studio

```env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
```

### Vertex AI

```env
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GOOGLE_CLOUD_LOCATION=us-central1
```

Also authenticate with:
```bash
gcloud auth application-default login
```

---

## Step 5: Configure Agent

Edit `agent.py` to define your agent:

```python
from google.adk.agents import LlmAgent

# Define tools
def my_tool(input: str) -> dict:
    """Tool description for the LLM."""
    return {"result": f"Processed: {input}"}

# Define the root agent (required name)
root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='my_agent',
    description='Brief description for multi-agent routing.',
    instruction='''
        You are a helpful assistant.
        Use the my_tool function when the user asks you to process something.
    ''',
    tools=[my_tool],
)
```

### Key Agent Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `model` | Yes | Model identifier (e.g., `gemini-2.0-flash`) |
| `name` | Yes | Agent identifier |
| `instruction` | Yes | System prompt defining behavior |
| `description` | No | For multi-agent routing |
| `tools` | No | List of tool functions |
| `sub_agents` | No | Child agents for delegation |

### Model Options

| Model | Use Case |
|-------|----------|
| `gemini-2.0-flash` | Fast responses, general use |
| `gemini-2.5-pro` | Complex reasoning, accuracy |
| `gemini-2.5-flash` | Balanced performance |
| `gemini-2.0-flash-live-001` | Voice/video streaming |

---

## Verification

```bash
# Navigate to parent directory
cd parent_folder/

# Test with CLI
adk run my_agent

# Test with web UI
adk web
```

### Expected Behavior

1. `adk run my_agent` starts interactive console
2. Agent responds to prompts
3. Tools are called when appropriate
4. No authentication errors

---

## Configuration Options

### Generate Content Config

Advanced model configuration:

```python
from google.genai import types

root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='my_agent',
    instruction='You are helpful.',
    generate_content_config=types.GenerateContentConfig(
        temperature=0.7,
        max_output_tokens=1024,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(
                initial_delay=1,
                attempts=2
            ),
        ),
    ),
)
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError` | Missing `__init__.py` | Add `from . import agent` to `__init__.py` |
| Agent not found | Wrong directory | Run `adk run` from parent folder |
| `root_agent` not found | Missing export | Ensure `root_agent` is defined in `agent.py` |
| API key error | Invalid/missing key | Check `.env` file |

---

## References

- [ADK Quickstart](https://google.github.io/adk-docs/get-started/quickstart/)
- [Python Quickstart](https://google.github.io/adk-docs/get-started/python/)
- [ADK Python SDK](https://github.com/google/adk-python)

---

## Next Steps

After project creation:
- Add tools with `/adk-tools-function`
- Configure callbacks with `/adk-behavior-callbacks`
- Add state management with `/adk-behavior-state`
