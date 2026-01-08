---
name: ADK Quality
description: This skill should be used when the user asks about "testing agents", "evaluation", "evals", "benchmarks", "tracing", "Cloud Trace", "logging", "observability", "AgentOps", "LangSmith", "user simulation", or needs guidance on testing, debugging, monitoring, or evaluating ADK agent quality.
version: 2.0.0
---

# ADK Quality

Guide for testing, evaluating, and monitoring ADK agents. Covers evals, tracing, logging, observability, and user simulation.

## When to Use

- Creating test suites for agents
- Evaluating agent responses against criteria
- Debugging execution with tracing
- Setting up production monitoring
- Automated testing with synthetic users

## When NOT to Use

- Agent creation → Use `@adk-agents` instead
- Deployment → Use `@adk-deployment` instead
- Runtime callbacks → Use `@adk-behavior` instead

## Key Concepts

**Evaluations (Evals)** test agent behavior against expected outputs. Define test cases with inputs and expected results, measure pass rates.

**Tracing** captures execution flow for debugging. Cloud Trace integration shows LLM calls, tool executions, and timing.

**Logging** provides structured event capture. Use LoggingPlugin for consistent log formatting and levels.

**Observability** integrates with third-party platforms (AgentOps, LangSmith) for production monitoring and analytics.

**User Simulation** automates testing with synthetic conversations. Generate diverse test scenarios without manual testing.

## References

Detailed guides with code examples:
- `references/evals.md` - Evaluation framework
- `references/tracing.md` - Cloud Trace integration
- `references/logging.md` - Structured logging
- `references/observability.md` - Third-party integrations
- `references/user-sim.md` - Synthetic user testing
