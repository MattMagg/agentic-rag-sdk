# ADK Development System Specification

Build a **4-agent multi-agent system** that develops ADK agentic applications end-to-end by orchestrating specialized agents through existing ADK workflows.

> [!NOTE]
> This is a **meta-system**: agents that build other agents.

---

## Quick Reference

| Document | Purpose |
|----------|---------|
| [agents.md](./agents.md) | Agent definitions with workflow references |
| [configuration.md](./configuration.md) | Models, thinking, services, tools |
| [project-structure.md](./project-structure.md) | File layout and exports |
| [deployment.md](./deployment.md) | Agent Engine deployment |

---

## Architecture Overview

```
                    ┌────────────────────────────────┐
                    │       ORCHESTRATOR             │
                    │       (gemini-3-pro)           │
                    │       + ThinkingConfig         │
                    │  Coordinates project phases    │
                    └───────────────┬────────────────┘
                                    │ sub_agents
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     ▼
      ┌───────────────┐    ┌───────────────┐    ┌───────────────┐
      │   ARCHITECT   │    │   DEVELOPER   │    │      OPS      │
      │  gemini-3-    │    │  gemini-3-    │    │  gemini-3-    │
      │  flash-preview│    │  flash-preview│    │  flash-preview│
      │ + Thinking    │    │ + Thinking    │    │ + Thinking    │
      │ • Planning    │    │ • Code gen    │    │ • Validation  │
      │ • Analysis    │    │ • Tools       │    │ • Testing     │
      │ • Structure   │    │ • Multi-agent │    │ • Deployment  │
      └───────────────┘    └───────────────┘    └───────────────┘
```

---

## Features

| Feature | Status | Workflow |
|---------|--------|----------|
| Multi-agent delegation | ✅ | `/adk-multi-agent-delegation` |
| Sequential/Parallel/Loop agents | ✅ | `/adk-multi-agent-orchestration` |
| Transfer control, hierarchical | ✅ | `/adk-multi-agent-advanced` |
| ThinkingConfig (all agents) | ✅ | `/adk-advanced-thinking` |
| State sharing via output_key | ✅ | `/adk-behavior-state` |
| Lifecycle callbacks | ✅ | `/adk-behavior-callbacks` |
| Reusable plugins | ✅ | `/adk-behavior-plugins` |
| Event stream processing | ✅ | `/adk-behavior-events` |
| google_search, code_execution | ✅ | `/adk-tools-builtin` |
| ArtifactService | ✅ | `/adk-behavior-artifacts` |
| MemoryService | ✅ | `/adk-memory-service` |
| Confirmation before deploy | ✅ | `/adk-behavior-confirmation` |
| Agent Engine deployment | ✅ | `/adk-deploy-agent-engine` |

---

## Implementation Steps

### 1. Configure Environment

> **Run the `/adk-init` workflow** to initialize the project.

Then see [configuration.md](./configuration.md) for specific settings.

### 2. Configure Thinking

> **Run the `/adk-advanced-thinking` workflow** to set up `ThinkingConfig` for all agents.

### 3. Define Agents

> See [agents.md](./agents.md) for each agent definition and its required workflows.

### 4. Create Project Structure

> See [project-structure.md](./project-structure.md) for the complete file layout.

### 5. Deploy

> **Run the `/adk-deploy-agent-engine` workflow** to deploy to Vertex AI Agent Engine.

See [deployment.md](./deployment.md) for commands.

---

## Prerequisites

- [ ] Google Cloud project with billing enabled
- [ ] `gcloud` CLI installed and authenticated
- [ ] ADK installed: `pip install google-adk`
- [ ] Cloud Storage bucket for staging: `gs://<bucket-name>`
- [ ] Environment variables configured

---

## Success Criteria

- [ ] `adk run adk_dev_system --verbose` executes without errors
- [ ] All agents show thinking output (ThinkingConfig working)
- [ ] System responds to: "Create a weather agent with google_search grounding"
- [ ] Generated code follows ADK conventions
- [ ] `adk deploy agent_engine ...` succeeds
