---
description: Configure non-Gemini models via LiteLLM or direct integrations
---

# ADK Workflow: Multi-Model Support

Use non-Gemini models (OpenAI, Anthropic, Cohere, Ollama, etc.) in ADK agents via the `LiteLlm` wrapper or direct model integrations.

---

## Prerequisites

- [ ] ADK installed (`pip install google-adk`)
- [ ] LiteLLM installed (`pip install litellm`)
- [ ] API keys for target providers

---

## Integration Methods

| Method | Use Case | Models |
|--------|----------|--------|
| `LiteLlm` wrapper | Cloud providers, 100+ models | OpenAI, Anthropic, Cohere, etc. |
| Direct registry | Vertex AI third-party | Claude on Vertex |
| `LiteLlm` + Ollama | Local models | Llama, Mistral, Phi, etc. |
| Custom endpoint | Self-hosted (vLLM) | Any OpenAI-compatible |

---

## Option 1: Cloud Models via LiteLLM

LiteLLM provides a unified OpenAI-compatible interface to 100+ LLMs.

### Step 1: Install LiteLLM

```bash
pip install litellm
```

### Step 2: Set API Keys

```bash
# OpenAI
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"

# Anthropic
export ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY"

# Cohere
export COHERE_API_KEY="YOUR_COHERE_API_KEY"
```

### Step 3: Create Agent

```python
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# OpenAI GPT-4o
agent_openai = LlmAgent(
    model=LiteLlm(model="openai/gpt-4o"),
    name="openai_agent",
    instruction="You are a helpful assistant powered by GPT-4o.",
)

# Anthropic Claude
agent_claude = LlmAgent(
    model=LiteLlm(model="anthropic/claude-3-haiku-20240307"),
    name="claude_agent",
    instruction="You are an assistant powered by Claude Haiku.",
)

# Cohere Command
agent_cohere = LlmAgent(
    model=LiteLlm(model="command-r-plus"),
    name="cohere_agent",
    instruction="You are an assistant powered by Cohere Command-R+.",
)
```

### LiteLLM Model String Format

```
provider/model_name

Examples:
- openai/gpt-4o
- openai/gpt-4-turbo
- anthropic/claude-3-5-sonnet-20241022
- anthropic/claude-3-haiku-20240307
- cohere/command-r-plus
- mistral/mistral-large-latest
```

See [LiteLLM Providers Documentation](https://docs.litellm.ai/docs/providers) for all supported models.

---

## Option 2: Ollama Local Models

Run open-source models locally with Ollama.

### Step 1: Install and Run Ollama

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama server
ollama serve

# Pull a model
ollama pull mistral-small3.1
```

### Step 2: Verify Tool Support

```bash
ollama show mistral-small3.1
# Look for "tools" under Capabilities
```

> **Important**: For tool-using agents, select models with tool support from [Ollama Tools Models](https://ollama.com/search?c=tools).

### Step 3: Set Environment Variable

```bash
export OLLAMA_API_BASE="http://localhost:11434"
```

### Step 4: Create Agent

```python
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# Use ollama_chat provider (NOT ollama)
agent_ollama = LlmAgent(
    model=LiteLlm(model="ollama_chat/mistral-small3.1"),
    name="ollama_agent",
    instruction="You are a helpful local assistant.",
    tools=[my_tool],  # Tools work with ollama_chat
)
```

> **Critical**: Always use `ollama_chat/` prefix, not `ollama/`. Using `ollama` causes infinite tool call loops and ignores context.

### Alternative: OpenAI Provider

```bash
export OPENAI_API_BASE="http://localhost:11434/v1"  # Note: /v1 suffix
export OPENAI_API_KEY="anything"  # Required but ignored

# Then use:
model=LiteLlm(model="openai/mistral-small3.1")
```

### Debugging Ollama

```python
import litellm
litellm._turn_on_debug()  # Shows raw requests
```

---

## Option 3: Anthropic Claude on Vertex AI

Use Claude models directly through Google Cloud Vertex AI.

### Step 1: Install Anthropic Vertex Library

```bash
pip install "anthropic[vertex]"
```

### Step 2: Configure Vertex AI Environment

```bash
export GOOGLE_CLOUD_PROJECT="YOUR_PROJECT_ID"
export GOOGLE_CLOUD_LOCATION="us-central1"
export GOOGLE_GENAI_USE_VERTEXAI=TRUE

# Authenticate
gcloud auth application-default login
```

### Step 3: Register Claude Model Class

```python
from google.adk.models.anthropic_llm import Claude
from google.adk.models.registry import LLMRegistry

# Register once at application startup
LLMRegistry.register(Claude)
```

### Step 4: Create Agent

```python
from google.adk.agents import LlmAgent
from google.genai import types

# Claude 3 Sonnet on Vertex AI
agent_claude_vertex = LlmAgent(
    model="claude-3-sonnet@20240229",  # Direct string after registration
    name="claude_vertexai_agent",
    instruction="You are an assistant powered by Claude 3 Sonnet on Vertex AI.",
    generate_content_config=types.GenerateContentConfig(max_output_tokens=4096),
)
```

---

## Option 4: Self-Hosted Models (vLLM)

Connect to OpenAI-compatible endpoints hosted via vLLM or similar tools.

### Step 1: Deploy Model

Deploy your model to an OpenAI-compatible endpoint (e.g., vLLM with `--enable-auto-tool-choice`).

### Step 2: Create Agent

```python
import subprocess
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# Endpoint URL
api_base_url = "https://your-vllm-endpoint.run.app/v1"
model_name = "hosted_vllm/google/gemma-3-4b-it"

# Authentication (example: gcloud token for Cloud Run)
try:
    gcloud_token = subprocess.check_output(
        ["gcloud", "auth", "print-identity-token", "-q"]
    ).decode().strip()
    auth_headers = {"Authorization": f"Bearer {gcloud_token}"}
except Exception:
    auth_headers = None

agent_vllm = LlmAgent(
    model=LiteLlm(
        model=model_name,
        api_base=api_base_url,
        extra_headers=auth_headers,
        # Or if using API key:
        # api_key="YOUR_ENDPOINT_API_KEY"
    ),
    name="vllm_agent",
    instruction="You are a helpful assistant on a self-hosted endpoint.",
)
```

---

## Option 5: Model Garden Deployments

Use models deployed from Vertex AI Model Garden.

```python
from google.adk.agents import LlmAgent
from google.genai import types

# Vertex AI endpoint resource name
llama3_endpoint = "projects/YOUR_PROJECT/locations/us-central1/endpoints/YOUR_ENDPOINT_ID"

agent_llama3 = LlmAgent(
    model=llama3_endpoint,
    name="llama3_vertex_agent",
    instruction="You are a helpful assistant based on Llama 3.",
    generate_content_config=types.GenerateContentConfig(max_output_tokens=2048),
)
```

---

## Multi-Model Agent Teams

Combine different models in the same system:

```python
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# Fast, cheap model for routing
router_agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="router",
    description="Routes requests to specialized agents",
    instruction="Route user requests to the appropriate agent.",
)

# Powerful model for complex reasoning
reasoning_agent = LlmAgent(
    model=LiteLlm(model="openai/o1-preview"),
    name="reasoning_agent",
    description="Handles complex reasoning and analysis tasks",
    instruction="You are an expert analyst.",
)

# Creative model for content
creative_agent = LlmAgent(
    model=LiteLlm(model="anthropic/claude-3-5-sonnet-20241022"),
    name="creative_agent",
    description="Generates creative content and writing",
    instruction="You are a creative writer.",
)

# Combine with sub-agents
router_agent = LlmAgent(
    model="gemini-3-flash-preview",
    name="router",
    instruction="Route to the appropriate specialist.",
    sub_agents=[reasoning_agent, creative_agent],
)
```

---

## Verification

### Test with CLI

```bash
# Set required API keys
export OPENAI_API_KEY="your_key"

# Run agent
adk run my_multi_model_agent
```

### Test with Runner

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

session_service = InMemorySessionService()
session = session_service.create_session(
    app_name="test_app",
    user_id="user1",
    session_id="session1"
)

runner = Runner(
    agent=agent_openai,
    app_name="test_app",
    session_service=session_service
)

content = types.Content(role='user', parts=[types.Part(text="Hello!")])
for event in runner.run(user_id="user1", session_id="session1", new_message=content):
    if event.is_final_response() and event.content:
        print(event.content.parts[0].text)
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `UnicodeDecodeError` (Windows) | LiteLLM encoding issue | Set `PYTHONUTF8=1` |
| Infinite tool loops (Ollama) | Using `ollama` provider | Use `ollama_chat/` prefix |
| `No tools` with Ollama | Model lacks tool support | Choose model from [tools list](https://ollama.com/search?c=tools) |
| Authentication error (Vertex) | Missing credentials | Run `gcloud auth application-default login` |
| Claude not recognized | Registry not registered | Add `LLMRegistry.register(Claude)` |

### Windows Encoding Fix

```powershell
# Set for current session
$env:PYTHONUTF8 = "1"

# Set persistently
[System.Environment]::SetEnvironmentVariable('PYTHONUTF8', '1', [System.EnvironmentVariableTarget]::User)
```

---

## References

- [Models](https://google.github.io/adk-docs/agents/models/) — Full model configuration documentation
- [LiteLLM Providers](https://docs.litellm.ai/docs/providers) — Supported models list
- [Ollama Tools Models](https://ollama.com/search?c=tools) — Tool-capable local models
