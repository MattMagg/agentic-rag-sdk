---
name: adk-secure
description: Add security features to an ADK agent
argument-hint: Optional security type
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Secure ADK Agent

Add security features to an existing agent.

## Decision Logic

Ask user:
> "What security features do you need?
>
> 1. **Input Guardrails** (Recommended) - Filter/validate user input
> 2. **Output Guardrails** - Filter agent responses
> 3. **Authentication** - Secure API access (OAuth, API keys)
> 4. **All of the above**"

**Recommendation:** Start with input guardrails - they're the first line of defense.

Based on selection, load appropriate section from `@adk-security` skill.

## References

Load `@adk-security` skill for detailed implementation.
