# Antigravity ADK Workflow System

> **Purpose**: Hierarchical workflow system for autonomous agents developing agentic systems using Google ADK.
> 
> **Usage**: Agent selects appropriate workflow based on current development phase and task requirements.

---

## Workflow Hierarchy

```
adk-master
├── adk-init
│   ├── adk-init-create-project
│   └── adk-init-yaml-config
├── adk-agents
│   ├── adk-agents-create
│   ├── adk-agents-custom
│   └── adk-agents-multi-model
├── adk-tools
│   ├── adk-tools-function
│   ├── adk-tools-long-running
│   ├── adk-tools-builtin
│   ├── adk-tools-openapi
│   ├── adk-tools-mcp
│   ├── adk-tools-third-party
│   └── adk-tools-computer-use
├── adk-behavior
│   ├── adk-behavior-callbacks
│   ├── adk-behavior-plugins
│   ├── adk-behavior-state
│   ├── adk-behavior-artifacts
│   ├── adk-behavior-events
│   └── adk-behavior-confirmation
├── adk-multi-agent
│   ├── adk-multi-agent-delegation
│   ├── adk-multi-agent-orchestration
│   └── adk-multi-agent-a2a
├── adk-memory
│   ├── adk-memory-service
│   └── adk-memory-grounding
├── adk-security
│   ├── adk-security-guardrails
│   ├── adk-security-auth
│   └── adk-security-plugins
├── adk-streaming
│   ├── adk-streaming-sse
│   ├── adk-streaming-bidi
│   └── adk-streaming-multimodal
├── adk-deploy
│   ├── adk-deploy-agent-engine
│   ├── adk-deploy-cloudrun
│   └── adk-deploy-gke
├── adk-quality
│   ├── adk-quality-tracing
│   ├── adk-quality-logging
│   ├── adk-quality-observability
│   ├── adk-quality-evals
│   └── adk-quality-user-sim
└── adk-advanced
    ├── adk-advanced-visual-builder
    └── adk-advanced-thinking
```

---

## Workflow Definitions

### Level 0: Master Orchestrator

| Workflow | Description |
|----------|-------------|
| `adk-master` | Entry point; routes to appropriate sub-workflow based on task |

---

### Level 1: Foundation (`adk-init`)

| Workflow | Description |
|----------|-------------|
| `adk-init` | Initialize new ADK project |
| `adk-init-create-project` | Scaffold project structure with `adk create` |
| `adk-init-yaml-config` | Configure agent via YAML instead of Python |

---

### Level 2: Agent Creation (`adk-agents`)

| Workflow | Description |
|----------|-------------|
| `adk-agents-create` | Create LlmAgent with model, name, instructions |
| `adk-agents-custom` | Implement custom agent extending BaseAgent |
| `adk-agents-multi-model` | Configure non-Gemini models via LiteLLM |

---

### Level 3: Tools & Capabilities (`adk-tools`)

| Workflow | Description |
|----------|-------------|
| `adk-tools-function` | Add FunctionTool with ToolContext |
| `adk-tools-long-running` | Add LongRunningFunctionTool for async operations |
| `adk-tools-builtin` | Integrate google_search, code_execution |
| `adk-tools-openapi` | Generate tools from OpenAPI specs |
| `adk-tools-mcp` | Connect to MCP servers for external tools |
| `adk-tools-third-party` | Integrate LangChain and CrewAI tool adapters |
| `adk-tools-computer-use` | Enable desktop/browser automation |

---

### Level 4: Agent Behavior (`adk-behavior`)

| Workflow | Description |
|----------|-------------|
| `adk-behavior-callbacks` | Add lifecycle callbacks (agent, model, tool) |
| `adk-behavior-plugins` | Add reusable plugins for cross-cutting concerns |
| `adk-behavior-state` | Configure session state with prefixes |
| `adk-behavior-artifacts` | Enable file/binary artifact handling |
| `adk-behavior-events` | Work with Event stream and EventActions |
| `adk-behavior-confirmation` | Add user confirmation for actions |

---

### Level 5: Multi-Agent Systems (`adk-multi-agent`)

| Workflow | Description |
|----------|-------------|
| `adk-multi-agent-delegation` | Configure sub-agents and transfer_to_agent |
| `adk-multi-agent-orchestration` | Add SequentialAgent, ParallelAgent, LoopAgent |
| `adk-multi-agent-a2a` | Enable A2A interoperability |

---

### Level 6: Memory & Knowledge (`adk-memory`)

| Workflow | Description |
|----------|-------------|
| `adk-memory-service` | Add long-term memory with MemoryService |
| `adk-memory-grounding` | Connect to external knowledge sources |

---

### Level 7: Security (`adk-security`)

| Workflow | Description |
|----------|-------------|
| `adk-security-guardrails` | Implement input/output guardrails |
| `adk-security-auth` | Configure tool authentication (API key, OAuth2) |
| `adk-security-plugins` | Add centralized security policy enforcement |

---

### Level 8: Streaming (`adk-streaming`)

| Workflow | Description |
|----------|-------------|
| `adk-streaming-sse` | Configure SSE streaming mode |
| `adk-streaming-bidi` | Implement BIDI WebSocket streaming |
| `adk-streaming-multimodal` | Enable audio/video multimodal streaming |

---

### Level 9: Deployment (`adk-deploy`)

| Workflow | Description |
|----------|-------------|
| `adk-deploy-agent-engine` | Deploy to Vertex AI Agent Engine |
| `adk-deploy-cloudrun` | Deploy to Cloud Run |
| `adk-deploy-gke` | Deploy to GKE |

---

### Level 10: Quality & Observability (`adk-quality`)

| Workflow | Description |
|----------|-------------|
| `adk-quality-tracing` | Enable Cloud Trace integration |
| `adk-quality-logging` | Configure LoggingPlugin and structured logs |
| `adk-quality-observability` | Add third-party observability (AgentOps, etc.) |
| `adk-quality-evals` | Run evaluation test suites |
| `adk-quality-user-sim` | Test with synthetic users and scenarios |

---

### Level 11: Advanced (`adk-advanced`)

| Workflow | Description |
|----------|-------------|
| `adk-advanced-visual-builder` | Use Visual Builder UI (experimental) |
| `adk-advanced-thinking` | Configure ThinkingConfig and planners |

---

## Workflow Selection Logic

```python
def select_workflow(task: str) -> str:
    """Route task to appropriate workflow."""
    
    # Keywords → Workflow mapping
    routing = {
        # Foundation
        "init|create|new project": "adk-init",
        "scaffold|project structure": "adk-init-create-project",
        "yaml|config file": "adk-init-yaml-config",
        
        # Agents
        "agent|llmagent": "adk-agents-create",
        "custom agent|baseagent": "adk-agents-custom",
        "multi-model|litellm|claude": "adk-agents-multi-model",
        
        # Tools
        "tool|function": "adk-tools-function",
        "long-running|async tool": "adk-tools-long-running",
        "builtin|google_search|code_execution": "adk-tools-builtin",
        "openapi|rest api|spec": "adk-tools-openapi",
        "mcp|model context protocol": "adk-tools-mcp",
        "langchain|crewai|third-party": "adk-tools-third-party",
        "computer|browser|automation": "adk-tools-computer-use",
        
        # Behavior
        "callback": "adk-behavior-callbacks",
        "plugin": "adk-behavior-plugins",
        "state|session": "adk-behavior-state",
        "artifact|file": "adk-behavior-artifacts",
        "event|eventactions": "adk-behavior-events",
        "confirmation|approve": "adk-behavior-confirmation",
        
        # Multi-Agent
        "sub-agent|delegation": "adk-multi-agent-delegation",
        "sequential|parallel|loop": "adk-multi-agent-orchestration",
        "a2a|interop|agent-to-agent": "adk-multi-agent-a2a",
        
        # Memory
        "memory|memoryservice": "adk-memory-service",
        "grounding|search|rag": "adk-memory-grounding",
        
        # Security
        "guardrail|safety": "adk-security-guardrails",
        "auth|oauth|credential": "adk-security-auth",
        "security plugin|policy": "adk-security-plugins",
        
        # Streaming
        "stream|sse": "adk-streaming-sse",
        "bidi|websocket|live": "adk-streaming-bidi",
        "audio|video|voice": "adk-streaming-multimodal",
        
        # Deployment
        "deploy|production|agent engine": "adk-deploy-agent-engine",
        "cloud run": "adk-deploy-cloudrun",
        "gke|kubernetes": "adk-deploy-gke",
        
        # Quality
        "trace|cloud trace": "adk-quality-tracing",
        "log|logging": "adk-quality-logging",
        "observability|agentops": "adk-quality-observability",
        "eval|test": "adk-quality-evals",
        "user sim|scenario|synthetic": "adk-quality-user-sim",
        
        # Advanced
        "visual builder|ui builder": "adk-advanced-visual-builder",
        "thinking|planner|thinkingconfig": "adk-advanced-thinking",
    }
    
    # Match and return workflow
    for pattern, workflow in routing.items():
        if any(kw in task.lower() for kw in pattern.split("|")):
            return workflow
    
    return "adk-master"  # Default to master orchestrator
```

---

## Workflow Execution Model

1. **Entry**: All tasks enter via `adk-master`
2. **Routing**: Master selects appropriate sub-workflow
3. **Execution**: Sub-workflow completes its specific task
4. **Chaining**: Complex tasks may chain multiple workflows
5. **Verification**: Each workflow includes verification steps

---

## Routing Scenarios

### Scenario 1: "Build a customer support agent"
```
adk-master
 └─→ adk-init                   (scaffold project)
 └─→ adk-agents-create          (create LlmAgent)
 └─→ adk-tools-function         (add support tools)
 └─→ adk-memory-grounding       (connect knowledge base)
 └─→ adk-deploy-*               (choose deployment target)
      ├─ adk-deploy-agent-engine  (managed, recommended)
      ├─ adk-deploy-cloudrun      (containerized, flexible)
      └─ adk-deploy-gke           (kubernetes, enterprise)
```

### Scenario 2: "Add LangChain web search to existing agent"
```
adk-master
 └─→ adk-tools-third-party      (wrap LangChain tool)
 └─→ adk-behavior-callbacks     (add validation callback)
 └─→ adk-behavior-artifacts     (save results)
```

### Scenario 3: "Implement multi-agent workflow with human approval"
```
adk-master
 └─→ adk-multi-agent-orchestration  (SequentialAgent setup)
 └─→ adk-multi-agent-delegation     (configure sub-agents)
 └─→ adk-behavior-confirmation      (add human-in-the-loop)
 └─→ adk-behavior-state             (shared state between agents)
```

### Scenario 4: "Enable real-time voice interaction"
```
adk-master
 └─→ adk-streaming-bidi         (WebSocket setup)
 └─→ adk-streaming-multimodal   (audio input/output)
 └─→ adk-streaming-sse          (configure RunConfig)
```

### Scenario 5: "Add production monitoring and evaluation"
```
adk-master
 └─→ adk-deploy-agent-engine    (includes Cloud Trace via --trace_to_cloud)
 └─→ adk-quality-evals          (test suite)
 └─→ adk-quality-user-sim       (synthetic user tests)
 └─→ [optional] adk-quality-observability  (AgentOps if 3rd-party needed)
```

### Scenario 6: "Secure agent with guardrails and auth"
```
adk-master
 └─→ adk-security-guardrails    (input/output filters)
 └─→ adk-security-auth          (OAuth2 for external APIs)
 └─→ adk-security-plugins       (policy engine)
 └─→ adk-behavior-callbacks     (before_tool_callback validation)
```

### Scenario 7: "Create browser automation agent"
```
adk-master
 └─→ adk-agents-create          (create agent)
 └─→ adk-tools-computer-use     (ComputerUseToolset)
 └─→ adk-behavior-artifacts     (save screenshots)
 └─→ adk-behavior-confirmation  (approve actions)
```

### Scenario 8: "Add long-term memory to existing agent"
```
adk-master
 └─→ adk-memory-service         (MemoryService setup)
 └─→ adk-behavior-state         (session state prefixes)
 └─→ adk-memory-grounding       (VertexAiRagRetrieval)
```

---

## Total Workflows: 37

| Category | Count |
|----------|-------|
| Foundation (`adk-init`) | 3 |
| Agents (`adk-agents`) | 3 |
| Tools (`adk-tools`) | 7 |
| Behavior (`adk-behavior`) | 6 |
| Multi-Agent (`adk-multi-agent`) | 3 |
| Memory (`adk-memory`) | 2 |
| Security (`adk-security`) | 3 |
| Streaming (`adk-streaming`) | 3 |
| Deployment (`adk-deploy`) | 3 |
| Quality (`adk-quality`) | 5 |
| Advanced (`adk-advanced`) | 2 |
| **Master** | 1 |
