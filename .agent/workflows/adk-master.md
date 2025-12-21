---
description: Master orchestrator for ADK agent development - routes to appropriate sub-workflow
---

# ADK Master Workflow

You are building an agentic system using **Google Agent Development Kit (ADK)**.

This workflow routes your task to the appropriate specialized sub-workflow based on what you need to accomplish.

---

## Step 1: Identify the Development Phase

Determine which category your task falls into:

| If you need to... | Go to workflow |
|-------------------|----------------|
| Start a new project | `/adk-init` |
| Create or modify agents | `/adk-agents-create` or `/adk-agents-custom` |
| Add tools/capabilities | `/adk-tools-*` |
| Configure behavior | `/adk-behavior-*` |
| Build multi-agent systems | `/adk-multi-agent-*` |
| Add memory/grounding | `/adk-memory-*` |
| Implement security | `/adk-security-*` |
| Enable streaming | `/adk-streaming-*` |
| Deploy to production | `/adk-deploy-*` |
| Add observability/evals | `/adk-quality-*` |
| Advanced features | `/adk-advanced-*` |

---

## Step 2: Keyword-Based Routing

Match task keywords to workflows:

```
# Foundation (adk-init)
init, create, new project     → adk-init
scaffold, project structure   → adk-init-create-project
yaml, config file             → adk-init-yaml-config

# Agents (adk-agents)
agent, llmagent              → adk-agents-create
custom agent, baseagent      → adk-agents-custom
multi-model, litellm, claude → adk-agents-multi-model

# Tools (adk-tools)
tool, function               → adk-tools-function
long-running, async tool     → adk-tools-long-running
builtin, google_search       → adk-tools-builtin
openapi, rest api, spec      → adk-tools-openapi
mcp, model context protocol  → adk-tools-mcp
langchain, crewai            → adk-tools-third-party
computer, browser            → adk-tools-computer-use

# Behavior (adk-behavior)
callback                     → adk-behavior-callbacks
plugin                       → adk-behavior-plugins
state, session               → adk-behavior-state
artifact, file, binary       → adk-behavior-artifacts
event, eventactions          → adk-behavior-events
confirmation, approve        → adk-behavior-confirmation

# Multi-Agent (adk-multi-agent)
sub-agent, delegation        → adk-multi-agent-delegation
sequential, parallel, loop   → adk-multi-agent-orchestration
transfer, hierarchy, compose → adk-multi-agent-advanced
a2a, interop                 → adk-multi-agent-a2a

# Memory (adk-memory)
memory, memoryservice        → adk-memory-service
grounding, search, rag       → adk-memory-grounding

# Security (adk-security)
guardrail, safety            → adk-security-guardrails
auth, oauth, credential      → adk-security-auth
security plugin, policy      → adk-security-plugins

# Streaming (adk-streaming)
stream, sse                  → adk-streaming-sse
bidi, websocket, live        → adk-streaming-bidi
audio, video, voice          → adk-streaming-multimodal

# Deployment (adk-deploy)
deploy, production           → adk-deploy-agent-engine
cloud run                    → adk-deploy-cloudrun
gke, kubernetes              → adk-deploy-gke

# Quality (adk-quality)
trace, cloud trace           → adk-quality-tracing
log, logging                 → adk-quality-logging
observability, agentops      → adk-quality-observability
eval, test                   → adk-quality-evals
user sim, scenario           → adk-quality-user-sim

# Advanced (adk-advanced)
visual builder               → adk-advanced-visual-builder
thinking, planner            → adk-advanced-thinking
```

---

## Step 3: Execute Sub-Workflow

Once you've identified the appropriate workflow:

1. **Invoke** the sub-workflow using `/workflow-name`
2. **Follow** all steps in the sub-workflow
3. **Return** here if the task requires chaining multiple workflows

---

## Step 4: Multi-Workflow Chaining

For complex tasks, chain workflows in order:

### Example: "Build a customer support agent"
```
1. /adk-init                  → scaffold project
2. /adk-agents-create         → create LlmAgent
3. /adk-tools-function        → add support tools
4. /adk-memory-grounding      → connect knowledge base
5. /adk-deploy-*              → deploy to production
```

### Example: "Add LangChain search to existing agent"
```
1. /adk-tools-third-party     → wrap LangChain tool
2. /adk-behavior-callbacks    → add validation
```

### Example: "Enable voice streaming"
```
1. /adk-streaming-bidi        → WebSocket setup
2. /adk-streaming-multimodal  → audio input/output
```

### Example: "Secure an agent"
```
1. /adk-security-guardrails   → input/output filters
2. /adk-security-auth         → OAuth2 for APIs
3. /adk-behavior-callbacks    → before_tool_callback
```

---

## Step 5: Verification Checklist

After completing any workflow:

- [ ] Agent runs without errors (`adk run` or `adk web`)
- [ ] Tools are callable and return expected results
- [ ] State persists correctly across turns
- [ ] Deployment target is reachable (if deployed)

---

## Reference: Available Workflows (37 Total)

### Foundation (`adk-init`)
| Workflow | Description |
|----------|-------------|
| `adk-init` | Initialize new ADK project |
| `adk-init-create-project` | Scaffold project structure |
| `adk-init-yaml-config` | Configure via YAML |

### Agents (`adk-agents`)
| Workflow | Description |
|----------|-------------|
| `adk-agents-create` | Create LlmAgent |
| `adk-agents-custom` | Implement custom BaseAgent |
| `adk-agents-multi-model` | Configure non-Gemini models |

### Tools (`adk-tools`)
| Workflow | Description |
|----------|-------------|
| `adk-tools-function` | Add FunctionTool |
| `adk-tools-long-running` | Async operations |
| `adk-tools-builtin` | google_search, code_execution |
| `adk-tools-openapi` | Generate from OpenAPI specs |
| `adk-tools-mcp` | MCP server integration |
| `adk-tools-third-party` | LangChain, CrewAI adapters |
| `adk-tools-computer-use` | Desktop/browser automation |

### Behavior (`adk-behavior`)
| Workflow | Description |
|----------|-------------|
| `adk-behavior-callbacks` | Lifecycle callbacks |
| `adk-behavior-plugins` | Reusable plugins |
| `adk-behavior-state` | Session state management |
| `adk-behavior-artifacts` | File/binary handling |
| `adk-behavior-events` | Event stream processing |
| `adk-behavior-confirmation` | Human approval workflows |

### Multi-Agent (`adk-multi-agent`)
| Workflow | Description |
|----------|-------------|
| `adk-multi-agent-delegation` | Sub-agent configuration |
| `adk-multi-agent-orchestration` | Sequential/Parallel/Loop agents |
| `adk-multi-agent-advanced` | Transfer control, hierarchical patterns |
| `adk-multi-agent-a2a` | A2A interoperability |

### Memory (`adk-memory`)
| Workflow | Description |
|----------|-------------|
| `adk-memory-service` | Long-term MemoryService |
| `adk-memory-grounding` | External knowledge sources |

### Security (`adk-security`)
| Workflow | Description |
|----------|-------------|
| `adk-security-guardrails` | Input/output guardrails |
| `adk-security-auth` | Tool authentication |
| `adk-security-plugins` | Policy enforcement |

### Streaming (`adk-streaming`)
| Workflow | Description |
|----------|-------------|
| `adk-streaming-sse` | SSE streaming |
| `adk-streaming-bidi` | BIDI WebSocket |
| `adk-streaming-multimodal` | Audio/video multimodal |

### Deployment (`adk-deploy`)
| Workflow | Description |
|----------|-------------|
| `adk-deploy-agent-engine` | Vertex AI Agent Engine |
| `adk-deploy-cloudrun` | Cloud Run |
| `adk-deploy-gke` | GKE |

### Quality (`adk-quality`)
| Workflow | Description |
|----------|-------------|
| `adk-quality-tracing` | Cloud Trace |
| `adk-quality-logging` | LoggingPlugin |
| `adk-quality-observability` | Third-party platforms |
| `adk-quality-evals` | Evaluation test suites |
| `adk-quality-user-sim` | Synthetic user testing |

### Advanced (`adk-advanced`)
| Workflow | Description |
|----------|-------------|
| `adk-advanced-visual-builder` | Visual Builder UI |
| `adk-advanced-thinking` | ThinkingConfig and planners |
