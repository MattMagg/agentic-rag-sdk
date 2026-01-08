---
name: ADK Agents
description: This skill should be used when the user asks about "creating an agent", "LlmAgent", "BaseAgent", "custom agent", "agent with different model", "Claude with ADK", "OpenAI with ADK", "LiteLLM", "multi-model agent", or needs guidance on agent configuration, model selection, system instructions, or extending the base agent class for non-LLM logic.
version: 2.0.0
---

# ADK Agents

Guide for creating and configuring agents in Google ADK. Covers LlmAgent for AI reasoning and BaseAgent for custom non-LLM logic.

## When to Use

- Creating a new ADK agent from scratch
- Configuring agent parameters (model, name, instruction, description)
- Using non-Gemini models (Claude, OpenAI via LiteLLM)
- Building custom agents without LLM reasoning

## When NOT to Use

- Adding tools to agents → Use `@adk-tools` instead
- Multi-agent orchestration → Use `@adk-multi-agent` instead
- Callbacks and state management → Use `@adk-behavior` instead

## Key Concepts

**LlmAgent** is the standard agent type for AI reasoning, conversation, and tool use. Requires `model` and `name` parameters. Use `instruction` for system prompts and `description` for routing in multi-agent systems.

**BaseAgent** is for custom non-LLM logic. Extend it and implement `run_async()` to yield responses. Use when you need deterministic behavior or external API orchestration.

**Model Selection**: Default to `gemini-3-flash-preview`. Use LiteLLM prefix for other providers (e.g., `anthropic/claude-sonnet-4`).

## References

Detailed guides with code examples:
- `references/llm-agent.md` - Complete LlmAgent configuration and parameters
- `references/custom-agent.md` - BaseAgent extension patterns
- `references/multi-model.md` - LiteLLM setup and model switching
