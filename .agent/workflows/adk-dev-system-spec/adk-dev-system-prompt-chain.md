# ADK Development System — Prompt Chain

Sequential prompts for building the 4-agent ADK Dev System. Each prompt references the spec files and invokes ADK workflows.

> [!IMPORTANT]
> The spec lives at `docs/adk-dev-system-spec/`. Read it before and during execution.

---

## Spec Files

| File | Read For |
|------|----------|
| [GEMINI.md](file:///Users/mac-main/rag_qdrant_voyage/docs/adk-dev-system-spec/GEMINI.md) | Overview, architecture, features |
| [configuration.md](file:///Users/mac-main/rag_qdrant_voyage/docs/adk-dev-system-spec/configuration.md) | Models, ThinkingConfig, services |
| [agents.md](file:///Users/mac-main/rag_qdrant_voyage/docs/adk-dev-system-spec/agents.md) | Agent definitions, instructions |
| [project-structure.md](file:///Users/mac-main/rag_qdrant_voyage/docs/adk-dev-system-spec/project-structure.md) | File layout, code |
| [deployment.md](file:///Users/mac-main/rag_qdrant_voyage/docs/adk-dev-system-spec/deployment.md) | Deploy commands |

---

## Prompt 1: Project Initialization

### Spec Reference
- `docs/adk-dev-system-spec/GEMINI.md` → Prerequisites section
- `docs/adk-dev-system-spec/project-structure.md` → Directory Layout

### Workflows
`/adk-init`, `/adk-init-create-project`

### Prompt

```
Read docs/adk-dev-system-spec/GEMINI.md for prerequisites and project-structure.md for the directory layout.

Invoke /adk-init and /adk-init-create-project to scaffold the adk_dev_system project following the spec.

Ensure .env exists with the required environment variables per the spec.

STOP after scaffolding. Report what was created.
```

---

## Prompt 2: Configure Thinking and Services

### Spec Reference
- `docs/adk-dev-system-spec/configuration.md` → Full file

### Workflows
`/adk-advanced-thinking`, `/adk-behavior-artifacts`, `/adk-behavior-state`

### Prompt

```
Read docs/adk-dev-system-spec/configuration.md completely.

Invoke /adk-advanced-thinking to configure ThinkingConfig and BuiltInPlanner as specified.

Invoke /adk-behavior-artifacts for ArtifactService setup.

Invoke /adk-behavior-state to understand output_key and state flow.

Create config.py exactly as specified in configuration.md.

STOP after config.py is complete. Report exports.
```

---

## Prompt 3: Create Architect Agent

### Spec Reference
- `docs/adk-dev-system-spec/agents.md` → Agent 2: Architect section

### Workflows
`/adk-agents-create`, `/adk-tools-builtin`, `/adk-memory-grounding`

### Prompt

```
Read docs/adk-dev-system-spec/agents.md, specifically the "Agent 2: Architect" section.

Invoke /adk-agents-create to create the architect agent.

Invoke /adk-tools-builtin for google_search setup. Follow the AgentTool wrapper pattern exactly as shown in the spec.

Invoke /adk-memory-grounding for grounding context.

Write to specialists.py following the spec code exactly.

STOP after Architect is complete.
```

---

## Prompt 4: Create Developer Agent

### Spec Reference
- `docs/adk-dev-system-spec/agents.md` → Agent 3: Developer section

### Workflows
`/adk-agents-create`, `/adk-tools-function`, `/adk-multi-agent-orchestration`

### Prompt

```
Read docs/adk-dev-system-spec/agents.md, specifically the "Agent 3: Developer" section.

Invoke /adk-agents-create to create the developer agent.

Review /adk-tools-function for FunctionTool patterns the Developer will generate.

Review /adk-multi-agent-orchestration for multi-agent patterns.

Add developer_agent to specialists.py following the spec.

STOP after Developer is complete.
```

---

## Prompt 5: Create Ops Agent

### Spec Reference
- `docs/adk-dev-system-spec/agents.md` → Agent 4: Ops section

### Workflows
`/adk-agents-create`, `/adk-quality-evals`, `/adk-behavior-confirmation`

### Prompt

```
Read docs/adk-dev-system-spec/agents.md, specifically the "Agent 4: Ops" section.

Invoke /adk-agents-create to create the ops agent.

Review /adk-quality-evals for testing patterns.

Review /adk-behavior-confirmation for human-in-the-loop confirmation.

Add ops_agent to specialists.py following the spec.

STOP after all specialists are complete.
```

---

## Prompt 6: Create Orchestrator and Wire System

### Spec Reference
- `docs/adk-dev-system-spec/agents.md` → Agent 1: Orchestrator section
- `docs/adk-dev-system-spec/project-structure.md` → agent.py and __init__.py

### Workflows
`/adk-agents-create`, `/adk-multi-agent-delegation`

### Prompt

```
Read docs/adk-dev-system-spec/agents.md for the Orchestrator definition.
Read docs/adk-dev-system-spec/project-structure.md for agent.py and __init__.py code.

Invoke /adk-agents-create for the orchestrator.

Invoke /adk-multi-agent-delegation to wire sub_agents.

Create agent.py and update __init__.py exactly as specified.

STOP after wiring is complete.
```

---

## Prompt 7: Validation

### Spec Reference
- `docs/adk-dev-system-spec/GEMINI.md` → Success Criteria
- `docs/adk-dev-system-spec/project-structure.md` → Verification section

### Workflows
`/adk-quality-logging`, `/adk-quality-tracing`

### Prompt

```
Read docs/adk-dev-system-spec/GEMINI.md for success criteria.
Read docs/adk-dev-system-spec/project-structure.md verification section.

Invoke /adk-quality-logging for debugging setup.

Run all validation steps from the spec:
- adk run adk_dev_system --verbose
- Test: "Create a weather agent with google_search grounding"

Report results. Fix any issues.
```

---

## Prompt 8: Deployment

### Spec Reference
- `docs/adk-dev-system-spec/deployment.md` → Full file

### Workflows
`/adk-deploy-agent-engine`, `/adk-quality-tracing`

### Prompt

```
Read docs/adk-dev-system-spec/deployment.md completely.

Follow all prerequisites in the spec.

Invoke /adk-deploy-agent-engine following the deployment commands exactly.

Enable --trace_to_cloud as specified.

Report deployment status and agent resource name.
```

---

## Usage

Each prompt:
1. **Reads the spec** — Agent loads the referenced documentation
2. **Invokes workflows** — ADK workflows provide implementation patterns
3. **Produces output** — Matches what the spec defines

The prompts don't embed the answers—they point to where the answers live.
