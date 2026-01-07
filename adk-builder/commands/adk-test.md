---
name: adk-test
description: Create tests and evaluations for an ADK agent
argument-hint: Optional test type
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Test ADK Agent

Create tests and evaluations for agent quality assurance.

## Decision Logic

Ask user:
> "What testing do you need?
>
> 1. **Evaluations** (Recommended) - Test agent behavior with eval sets
> 2. **Tracing** - Debug execution flow with Cloud Trace
> 3. **Logging** - Add structured logging
> 4. **User Simulation** - Automated testing with synthetic users"

**Recommendation:** Start with evaluations - they're the foundation of agent testing.

Based on selection, load appropriate section from `@adk-quality` skill.

## References

Load `@adk-quality` skill for detailed testing guidance.
