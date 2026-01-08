---
name: ADK Security
description: This skill should be used when the user asks about "guardrails", "safety", "content filtering", "input validation", "output validation", "authentication", "OAuth", "API keys", "credentials", "security plugins", or needs guidance on implementing safety measures, access control, or secure authentication in ADK agents.
version: 2.0.0
---

# ADK Security

Guide for implementing security features in ADK agents. Covers input/output guardrails, authentication, and security plugins.

## When to Use

- Validating or filtering user input
- Filtering agent responses before delivery
- Implementing OAuth or API key authentication
- Creating reusable security plugins
- Blocking unsafe topics or content

## When NOT to Use

- General callbacks → Use `@adk-behavior` instead
- Agent creation → Use `@adk-agents` instead
- Tool integration → Use `@adk-tools` instead

## Key Concepts

**Input Guardrails** validate user input before processing. Use `before_model_callback` to block or modify unsafe requests.

**Output Guardrails** filter agent responses before returning to users. Use `after_model_callback` to redact PII, profanity, or sensitive data.

**Authentication** secures tool access. Configure OAuth credentials for Google APIs or custom authentication for third-party services.

**Security Plugins** bundle reusable security callbacks. Create plugins for logging, rate limiting, or content moderation.

**Credential Management** uses environment variables and secure storage. Never hardcode secrets in agent code.

## References

Detailed guides with code examples:
- `references/guardrails.md` - Input/output validation
- `references/auth.md` - Authentication patterns
- `references/security-plugins.md` - Reusable security bundles
