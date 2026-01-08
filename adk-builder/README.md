# ADK Builder Plugin

Autonomous Google ADK development with specialized agents for planning, coding, debugging, and verification.

## Overview

ADK Builder is a Claude Code plugin that provides an intelligent, multi-agent workflow for building Google Agent Development Kit (ADK) applications. Instead of manually coding agents, the plugin guides you through a deliberate process:

1. **Plan** - Understand requirements, clarify ambiguity, present options
2. **Execute** - Implement step by step with verification
3. **Debug** - Diagnose and fix issues systematically
4. **Verify** - Validate completion against requirements

## Installation

### Option 1: Marketplace (Recommended)

```bash
/plugin marketplace add https://github.com/MattMagg/adk-workflow-rag.git
/plugin install adk-builder@adk-workflow-rag
```

### Option 2: Plugin Directory (Local Development)

```bash
claude --plugin-dir /path/to/rag_qdrant_voyage/adk-builder
```

## Agents

The plugin provides four specialized agents:

| Agent | Color | Purpose |
|-------|-------|---------|
| **adk-planner** | Cyan | Contemplates, clarifies, plans implementation |
| **adk-executor** | Green | Implements plans step by step |
| **adk-debugger** | Red | Diagnoses and fixes issues |
| **adk-verifier** | Yellow | Validates completion |

### Workflow

```
User Request → adk-planner (contemplate, clarify, plan)
                    ↓
              User Approval
                    ↓
            adk-executor (implement step-by-step)
                    ↓
            adk-verifier (validate completion)
                    ↓
              [If errors: adk-debugger]
```

## Commands

| Command | Description |
|---------|-------------|
| `/adk-init` | Initialize new ADK project |
| `/adk-create-agent` | Create agent with type selection |
| `/adk-add-tool` | Add tool to existing agent |
| `/adk-deploy` | Deploy to production |
| `/adk-add-behavior` | Add callbacks, state, events |
| `/adk-multi-agent` | Set up multi-agent system |
| `/adk-add-memory` | Add memory or grounding |
| `/adk-secure` | Add security features |
| `/adk-streaming` | Enable streaming responses |
| `/adk-test` | Create tests and evaluations |

## Skills

The plugin includes 11 ADK domain skills:

| Skill | Triggers |
|-------|----------|
| `@adk-getting-started` | project setup, initialization |
| `@adk-agents` | LlmAgent, BaseAgent, models |
| `@adk-tools` | FunctionTool, MCP, OpenAPI |
| `@adk-behavior` | callbacks, state, events |
| `@adk-multi-agent` | delegation, orchestration |
| `@adk-memory` | MemoryService, RAG, grounding |
| `@adk-security` | guardrails, authentication |
| `@adk-streaming` | SSE, bidirectional, Live API |
| `@adk-deployment` | Agent Engine, Cloud Run, GKE |
| `@adk-quality` | evals, tracing, logging |
| `@adk-advanced` | visual builder, ThinkingConfig |

## Usage Examples

### Create a New Agent

```
> I want to build a customer support agent

[adk-planner activates]
"I'll help you plan this. What should the agent handle?
1. General inquiries
2. Billing questions
3. Technical support
4. All of the above"

> All of the above

"I recommend a multi-agent delegation pattern with specialized sub-agents..."
[presents plan]

> Proceed

[adk-executor implements]
[adk-verifier validates]
```

### Add a Tool

```
> /adk-add-tool weather lookup

[adk-planner activates]
"For weather lookup, I recommend a FunctionTool that calls a weather API..."
```

### Debug an Issue

```
> My agent won't start - "tool not found" error

[adk-debugger activates]
"Let me diagnose this. The error 'tool not found' typically means..."
[provides fix]
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Follow the existing patterns
4. Submit a pull request

## License

MIT
