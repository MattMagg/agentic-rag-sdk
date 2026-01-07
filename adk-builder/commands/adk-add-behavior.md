---
name: adk-add-behavior
description: Add behavior customization (callbacks, state, events) to an ADK agent
argument-hint: Optional behavior type
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Add Behavior to Agent

Add behavior customization to an existing ADK agent.

## Decision Logic

Ask user:
> "What behavior do you want to add?
>
> 1. **Callbacks** - Intercept lifecycle events (logging, validation)
> 2. **State Management** - Store data across turns
> 3. **Artifacts** - Handle file uploads/downloads
> 4. **Events** - Custom event handling
> 5. **Human-in-the-Loop** - Require confirmation for actions"

Based on selection, load appropriate section from `@adk-behavior` skill and implement.

## References

Load `@adk-behavior` skill for detailed implementation.
