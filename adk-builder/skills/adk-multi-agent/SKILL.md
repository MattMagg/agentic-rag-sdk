---
name: ADK Multi-Agent
description: This skill should be used when the user asks about "multi-agent systems", "sub-agents", "delegation", "agent routing", "orchestration", "SequentialAgent", "ParallelAgent", "LoopAgent", "agent-to-agent", "A2A protocol", "agent hierarchy", or needs guidance on building systems with multiple specialized agents working together.
version: 2.0.0
---

# ADK Multi-Agent Systems

Guide for building multi-agent systems with delegation, orchestration, and inter-agent communication. Enables specialized agents to collaborate on complex tasks.

## When to Use

- Routing requests to specialized sub-agents
- Building agent pipelines (sequential execution)
- Running agents concurrently (parallel execution)
- Creating hierarchical agent teams
- Cross-system agent communication (A2A)

## When NOT to Use

- Single agent with tools → Use `@adk-agents` and `@adk-tools` instead
- Callbacks and state → Use `@adk-behavior` instead
- Agent deployment → Use `@adk-deployment` instead

## Key Concepts

**Delegation** routes requests to sub-agents based on their descriptions. The parent agent decides which child handles each request.

**SequentialAgent** executes sub-agents in order (A → B → C). Each agent receives the previous agent's output.

**ParallelAgent** runs sub-agents concurrently. Results are aggregated when all complete.

**LoopAgent** repeats execution until a condition is met. Useful for iterative refinement.

**Hierarchy** nests agent teams for complex organizations. Parent agents coordinate child teams.

**A2A Protocol** enables cross-system agent communication. Agents can call agents in other deployments.

## References

Detailed guides with code examples:
- `references/delegation.md` - Sub-agent routing patterns
- `references/orchestration.md` - Sequential, Parallel, Loop agents
- `references/advanced.md` - Hierarchical and complex patterns
- `references/a2a.md` - Agent-to-Agent protocol
