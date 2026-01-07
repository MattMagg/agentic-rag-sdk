---
name: adk-multi-agent
description: Set up a multi-agent system with intelligent pattern selection
argument-hint: Optional pattern type
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Set Up Multi-Agent System

Create a multi-agent system with appropriate orchestration pattern.

## Decision Logic

Ask user:
> "What multi-agent pattern do you need?
>
> 1. **Delegation** (Recommended) - Route to specialized sub-agents
> 2. **Sequential** - Pipeline of agents in order
> 3. **Parallel** - Run agents concurrently
> 4. **A2A** - Cross-system agent communication"

**Recommendation:** Start with delegation - it's the most flexible and covers most use cases.

Based on selection, load appropriate section from `@adk-multi-agent` skill.

## References

Load `@adk-multi-agent` skill for detailed implementation.
