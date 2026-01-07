---
name: adk-add-memory
description: Add memory capabilities to an ADK agent
argument-hint: Optional memory type
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Add Memory to Agent

Add memory or grounding capabilities to an existing agent.

## Decision Logic

Ask user:
> "What memory capability do you need?
>
> 1. **Long-term Memory** - Remember facts across sessions (MemoryService)
> 2. **Knowledge Grounding** - Search documents/knowledge base (RAG)"

Based on selection, load appropriate section from `@adk-memory` skill.

## References

Load `@adk-memory` skill for detailed implementation.
