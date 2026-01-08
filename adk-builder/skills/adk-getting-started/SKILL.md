---
name: ADK Getting Started
description: This skill should be used when the user asks about "creating a new ADK project", "initializing ADK", "setting up Google ADK", "adk create command", "ADK project structure", "YAML agent configuration", or needs guidance on bootstrapping an ADK development environment, authentication setup, or choosing between Python code and YAML-based agent definitions.
version: 2.0.0
---

# ADK Getting Started

Guide for initializing and setting up Google Agent Development Kit (ADK) projects. Covers installation, authentication, and project scaffolding.

## When to Use

- Starting a new ADK project from scratch
- Setting up authentication (API key or Vertex AI)
- Understanding ADK project structure
- Choosing between Python and YAML configuration
- Running agents locally for development

## When NOT to Use

- Adding tools to existing agent → Use `@adk-tools` instead
- Deploying to production → Use `@adk-deployment` instead
- Agent configuration details → Use `@adk-agents` instead

## Key Concepts

**Installation**: `pip install google-adk` in Python 3.10+ virtual environment. Verify with `adk --version`.

**Project Creation**: `adk create <name>` scaffolds a new agent project with `agent.py`, `__init__.py`, and `.env`.

**Authentication Options**: Google AI Studio (GOOGLE_API_KEY) for prototyping, Vertex AI (GOOGLE_CLOUD_PROJECT) for production.

**Running Agents**: `adk run` for CLI, `adk web` for development UI, `adk api_server` for HTTP API.

**YAML Configuration**: Declarative agent definition without Python code. Quick prototyping for simple agents.

**Project Structure**: `agent.py` exports `root_agent`. ADK CLI discovers and runs the exported agent.

## References

Detailed guides with code examples:
- `references/init.md` - Complete initialization workflow
- `references/create-project.md` - Python project scaffolding
- `references/yaml-config.md` - YAML-based configuration
