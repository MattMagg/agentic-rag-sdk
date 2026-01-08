---
name: ADK Advanced
description: This skill should be used when the user asks about "visual builder", "no-code agent builder", "drag and drop", "ThinkingConfig", "extended thinking", "chain of thought", "reasoning", or needs guidance on using ADK's visual development tools or configuring advanced reasoning capabilities.
version: 2.0.0
---

# ADK Advanced Features

Guide for advanced ADK features including visual building and extended thinking. Covers no-code development and enhanced reasoning capabilities.

## When to Use

- Building agents with drag-and-drop visual tools
- Enabling chain-of-thought reasoning
- Complex multi-step problem solving
- Prototyping without writing code
- Tasks requiring explicit reasoning steps

## When NOT to Use

- Standard agent creation → Use `@adk-agents` instead
- Tool integration → Use `@adk-tools` instead
- Multi-agent systems → Use `@adk-multi-agent` instead

## Key Concepts

**Visual Builder** provides drag-and-drop agent design via `adk web --builder`. Create agents visually and export to Python code.

**ThinkingConfig** enables extended reasoning with configurable token budgets. The model explicitly works through problems before answering.

**Thinking Budget** controls how many tokens the model uses for reasoning. Higher budgets enable deeper analysis but increase latency and cost.

**Chain-of-Thought** prompting combined with ThinkingConfig improves performance on complex reasoning tasks.

**Visual-to-Code Export** generates Python from visual designs, enabling no-code prototyping with full code control later.

## References

Detailed guides with code examples:
- `references/visual-builder.md` - Visual development tools
- `references/thinking.md` - Extended thinking configuration
