---
description: Configure ADK agent via YAML instead of Python code
---

# ADK Workflow: YAML Declarative Configuration

Build ADK agents using YAML configuration files instead of Python code. This no-code approach enables rapid agent development and is suitable for straightforward agent definitions.

---

> [!NOTE]
> The Agent Config feature is **experimental** (ADK Python v1.11.0+) and currently supports only Gemini models.

---

## Prerequisites

- [ ] Python 3.10+ installed
- [ ] Virtual environment activated
- [ ] ADK installed (`pip install google-adk`)
- [ ] API key or GCP credentials configured

---

## Step 1: Create Config-Based Project

Use the `adk create` command with the `--type=config` flag:

```bash
adk create --type=config my_agent
```

This generates:

```
my_agent/
    root_agent.yaml    # Agent configuration (YAML)
    .env               # Environment configuration
```

---

## Step 2: Configure Environment

Edit `my_agent/.env`:

### Google AI Studio

```env
GOOGLE_GENAI_USE_VERTEXAI=0
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
```

### Vertex AI

```env
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GOOGLE_CLOUD_LOCATION=us-central1
```

---

## Step 3: Define Agent in YAML

Edit `my_agent/root_agent.yaml`:

### Basic Agent

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/google/adk-python/refs/heads/main/src/google/adk/agents/config_schemas/AgentConfig.json
name: assistant_agent
model: gemini-2.5-flash
description: A helper agent that can answer users' questions.
instruction: You are an agent to help answer users' various questions.
```

### Agent with Built-in Tool

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/google/adk-python/refs/heads/main/src/google/adk/agents/config_schemas/AgentConfig.json
name: search_agent
model: gemini-2.0-flash
description: An agent that performs Google search queries.
instruction: You are an agent whose job is to perform Google search queries and answer questions about the results.
tools:
  - name: google_search
```

### Agent with Custom Tool

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/google/adk-python/refs/heads/main/src/google/adk/agents/config_schemas/AgentConfig.json
agent_class: LlmAgent
model: gemini-2.5-flash
name: prime_agent
description: Handles checking if numbers are prime.
instruction: |
  You are responsible for checking whether numbers are prime.
  When asked to check primes, call the check_prime tool with a list of integers.
  Never attempt to determine prime numbers manually.
tools:
  - name: my_module.check_prime
```

### Agent with Sub-Agents

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/google/adk-python/refs/heads/main/src/google/adk/agents/config_schemas/AgentConfig.json
agent_class: LlmAgent
model: gemini-2.5-flash
name: root_agent
description: Learning assistant that provides tutoring in code and math.
instruction: |
  You are a learning assistant that helps students with coding and math questions.

  Follow these steps:
  1. If the user asks about programming or coding, delegate to the code_tutor_agent.
  2. If the user asks about math concepts or problems, delegate to the math_tutor_agent.
  3. Always provide clear explanations and encourage learning.
sub_agents:
  - config_path: code_tutor_agent.yaml
  - config_path: math_tutor_agent.yaml
```

---

## Configuration Schema

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Agent identifier |
| `model` | string | LLM model (e.g., `gemini-2.5-flash`) |
| `instruction` | string | System prompt defining agent behavior |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `agent_class` | string | Agent type (default: `LlmAgent`) |
| `description` | string | Purpose description for routing |
| `tools` | list | Tools available to the agent |
| `sub_agents` | list | Child agents for delegation |

### Tools Configuration

```yaml
tools:
  # Built-in tool (name only)
  - name: google_search
  
  # Custom tool (module.function)
  - name: my_module.check_prime
```

### Sub-Agents Configuration

```yaml
sub_agents:
  # Reference another YAML config
  - config_path: sub_agent.yaml
  
  # Inline definition
  - name: inline_agent
    model: gemini-2.0-flash
    instruction: You are a specialized sub-agent.
```

---

## Supported Built-in Tools

| Tool | Description |
|------|-------------|
| `google_search` | Web search grounding |
| `load_artifacts` | Load stored artifacts |
| `url_context` | Fetch and use URL content |
| `exit_loop` | Exit LoopAgent iteration |
| `preload_memory` | Load memory context |
| `get_user_choice` | Prompt user for selection |
| `enterprise_web_search` | Enterprise search |
| `load_web_page` | Load web page content |

---

## Step 4: Run the Agent

```bash
# Navigate to parent directory
cd parent_folder/

# Interactive web UI
adk web

# Terminal CLI
adk run my_agent

# API server mode
adk api_server
```

---

## Loading Config Agents in Python

You can also load YAML-configured agents programmatically:

```python
from google.adk.agents import LlmAgent

# Load from YAML config
agent = LlmAgent.from_config("path/to/root_agent.yaml")
```

Or use the agent loader:

```python
from google.adk.cli.utils.agent_loader import AgentLoader

loader = AgentLoader()
agent = loader.load_agent("my_agent", "agents_directory/")
```

---

## Verification

- [ ] `adk --version` returns v1.11.0 or later
- [ ] `root_agent.yaml` validates against JSON schema
- [ ] `adk run my_agent` starts without errors
- [ ] Agent responds to test prompts
- [ ] Tools are invoked when appropriate

---

## Known Limitations

| Limitation | Details |
|------------|---------|
| **Model support** | Only Gemini models supported |
| **Programming language** | Custom tools must be Python |
| **Unsupported agent types** | `LangGraphAgent`, `A2aAgent` |
| **Unsupported tools** | `AgentTool`, `LongRunningFunctionTool`, `McpToolset`, `VertexAiSearchTool` |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Schema validation error | Invalid YAML structure | Use JSON schema comment for IDE validation |
| Tool not found | Wrong module path | Use `module.function` format |
| Sub-agent not loading | Wrong path | Use relative path from root config |
| Model not supported | Non-Gemini model | Use Gemini model identifier |

---

## IDE Support

Add JSON schema reference for autocomplete and validation:

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/google/adk-python/refs/heads/main/src/google/adk/agents/config_schemas/AgentConfig.json
name: my_agent
...
```

---

## References

- [Agent Config Guide](https://google.github.io/adk-docs/agents/config/)
- [Agent Config Syntax Reference](https://google.github.io/adk-docs/api-reference/agentconfig/)
- [ADK Samples Repository](https://github.com/google/adk-python/tree/main/contributing/samples)

---

## Next Steps

After YAML configuration:
- Add custom Python tools referenced in `tools:` section
- Define sub-agents in separate YAML files
- Deploy with `/adk-deploy-cloudrun` or `/adk-deploy-agent-engine`
