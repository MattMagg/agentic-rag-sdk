---
name: ADK Tools
description: This skill should be used when the user asks about "adding a tool", "FunctionTool", "creating tools", "MCP integration", "OpenAPI tools", "built-in tools", "google_search tool", "code_execution tool", "long-running tools", "async tools", "third-party tools", "LangChain tools", "computer use", or needs guidance on extending agent capabilities with custom functions, API integrations, or external tool frameworks.
version: 2.0.0
---

# ADK Tools

Guide for adding tools to ADK agents. Tools extend agent capabilities beyond LLM reasoning to interact with external systems, APIs, and services.

## When to Use

- Adding custom Python functions as agent tools
- Integrating REST APIs via OpenAPI specs
- Connecting MCP (Model Context Protocol) servers
- Using built-in tools (Google Search, Code Execution)
- Wrapping LangChain or CrewAI tools

## When NOT to Use

- Creating the base agent → Use `@adk-agents` instead
- Multi-agent routing → Use `@adk-multi-agent` instead
- Callbacks and state → Use `@adk-behavior` instead

## Key Concepts

**FunctionTool** wraps Python functions. Requires type hints for schema generation and docstrings for LLM understanding. Return JSON-serializable data.

**Built-in Tools**: `google_search` for web search, `code_execution` for sandboxed Python execution.

**OpenAPI/MCP**: For external APIs, use OpenAPIToolset (REST specs) or MCPToolset (Model Context Protocol servers).

**Long-Running Tools**: For operations >30s, use async patterns with progress callbacks.

**Computer Use**: Browser and desktop automation for complex UI interactions.

## References

Detailed guides with code examples:
- `references/function-tools.md` - Custom Python functions
- `references/builtin-tools.md` - Google Search, Code Execution
- `references/openapi-tools.md` - REST API integration
- `references/mcp-tools.md` - MCP server integration
- `references/third-party-tools.md` - LangChain, CrewAI
- `references/long-running-tools.md` - Async operations
- `references/computer-use.md` - Browser/desktop automation
