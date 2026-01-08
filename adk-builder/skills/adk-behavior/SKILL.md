---
name: ADK Behavior
description: This skill should be used when the user asks about "callbacks", "lifecycle hooks", "before_model_call", "after_tool_call", "plugins", "session state", "state management", "artifacts", "file uploads", "events", "EventActions", "human-in-the-loop", "confirmation", or needs guidance on customizing agent behavior, intercepting execution, managing state across turns, or implementing approval workflows.
version: 2.0.0
---

# ADK Behavior

Guide for customizing agent behavior through callbacks, state, artifacts, and events. Enables interception of execution, state persistence, and human-in-the-loop workflows.

## When to Use

- Intercepting LLM calls or tool executions
- Persisting data across conversation turns
- Implementing human approval workflows
- Handling file uploads and artifacts
- Customizing event flow control

## When NOT to Use

- Creating agents from scratch → Use `@adk-agents` instead
- Adding tools → Use `@adk-tools` instead
- Multi-agent orchestration → Use `@adk-multi-agent` instead

## Key Concepts

**Callbacks** intercept lifecycle events: `before_model_callback`, `after_model_callback`, `before_tool_callback`, `after_tool_callback`. Return content to override default behavior.

**Session State** persists data across conversation turns via `ctx.state`. Access with `get()` and update with dictionary assignment.

**Plugins** bundle reusable callbacks. Create custom plugins for logging, security, or monitoring.

**Artifacts** handle binary data and file uploads. Store files via artifact service for multi-turn access.

**EventActions** control flow: skip steps, escalate to parent, terminate session.

**Human-in-the-Loop** requires confirmation before sensitive actions by returning confirmation prompts from callbacks.

## References

Detailed guides with code examples:
- `references/callbacks.md` - Lifecycle callback patterns
- `references/plugins.md` - Reusable callback bundles
- `references/state.md` - Session state management
- `references/artifacts.md` - File/binary handling
- `references/events.md` - EventActions and flow control
- `references/confirmation.md` - Human-in-the-loop patterns
