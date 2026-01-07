---
name: adk-streaming
description: Enable streaming responses for an ADK agent
argument-hint: Optional streaming type
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Enable Streaming

Enable real-time streaming responses for an agent.

## Decision Logic

Ask user:
> "What streaming capability do you need?
>
> 1. **SSE** (Recommended) - Stream text responses progressively
> 2. **Bidirectional** - Real-time two-way communication
> 3. **Voice/Video** - Live API for audio/video streaming"

**Recommendation:** Start with SSE - it covers most chat use cases.

Based on selection, load appropriate section from `@adk-streaming` skill.

## References

Load `@adk-streaming` skill for detailed implementation.
