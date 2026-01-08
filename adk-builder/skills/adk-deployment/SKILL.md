---
name: ADK Deployment
description: This skill should be used when the user asks about "deploying", "production", "Agent Engine", "Vertex AI", "Cloud Run", "GKE", "Kubernetes", "hosting", "scaling", or needs guidance on deploying ADK agents to production environments.
version: 2.0.0
---

# ADK Deployment

Guide for deploying ADK agents to production. Covers Agent Engine (managed), Cloud Run (containers), and GKE (Kubernetes).

## When to Use

- Deploying agents to production
- Choosing between hosting options
- Configuring auto-scaling
- Setting up CI/CD for agents
- Integrating with Vertex AI services

## When NOT to Use

- Local development → Use `@adk-getting-started` instead
- Agent creation → Use `@adk-agents` instead
- Testing and evaluation → Use `@adk-quality` instead

## Key Concepts

**Agent Engine** is the recommended managed deployment. Auto-scales, integrates with Vertex AI services, no infrastructure management.

**Cloud Run** offers container control with serverless scaling. Build custom Docker images for more control over the runtime.

**GKE (Kubernetes)** provides enterprise-scale deployment. Full control over infrastructure, networking, and scaling policies.

**Deployment CLI**: `adk deploy` handles Agent Engine deployment. For Cloud Run/GKE, containerize with `adk api_server`.

**Environment Configuration**: Use environment variables for credentials. Never commit secrets to source control.

## References

Detailed guides with code examples:
- `references/agent-engine.md` - Vertex AI Agent Engine
- `references/cloudrun.md` - Cloud Run deployment
- `references/gke.md` - Kubernetes deployment
