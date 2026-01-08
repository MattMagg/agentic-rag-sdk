---
name: ADK Memory
description: This skill should be used when the user asks about "memory", "MemoryService", "long-term memory", "remember across sessions", "RAG", "retrieval augmented generation", "grounding", "knowledge base", "vector search", or needs guidance on implementing persistent memory or grounding agent responses in external knowledge.
version: 2.0.0
---

# ADK Memory

Guide for implementing memory and grounding in ADK agents. Enables agents to remember across sessions and ground responses in external knowledge.

## When to Use

- Persisting memories across conversations
- Grounding responses in knowledge bases (RAG)
- Building agents that learn user preferences
- Connecting to Vertex AI Search datastores

## When NOT to Use

- Within-session state only → Use `@adk-behavior` (session state) instead
- Agent creation → Use `@adk-agents` instead
- Tool integration → Use `@adk-tools` instead

## Key Concepts

**Session State** persists within a conversation but is lost when session ends. Use `ctx.state` for temporary data.

**MemoryService** provides long-term memory across sessions. Agents can remember facts, preferences, and context over time.

**Grounding (RAG)** connects agents to external knowledge bases. Use Vertex AI Search or custom vector stores to retrieve relevant context before responding.

**Knowledge Attribution** enables agents to cite sources when grounding responses, improving transparency and trust.

## References

Detailed guides with code examples:
- `references/memory-service.md` - Long-term memory patterns
- `references/grounding.md` - RAG and knowledge grounding
