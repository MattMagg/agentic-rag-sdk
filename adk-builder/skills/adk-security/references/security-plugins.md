---
description: Create reusable security-focused plugins for access control, audit logging, and policy enforcement
---

# ADK Workflow: Security Plugins

Build security-focused plugins that intercept and control agent behavior across tool calls, model interactions, and agent execution.

---

## Prerequisites

- [ ] ADK v1.7.0+ (plugins support)
- [ ] Understanding of plugin callback lifecycle

```python
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from typing import Any, Optional
```

---

## Step 1: Understand Plugin Callback Points

Plugins provide hooks at these security-relevant points:

| Callback | Timing | Security Use Case |
|----------|--------|-------------------|
| `before_agent_callback` | Before agent runs | Session validation, rate limiting |
| `before_model_callback` | Before LLM call | Input sanitization, prompt injection defense |
| `after_model_callback` | After LLM response | Output filtering, content policy |
| `before_tool_callback` | Before tool execution | Authorization check, argument validation |
| `after_tool_callback` | After tool execution | Audit logging, result sanitization |
| `on_tool_error` | Tool error occurs | Error logging, alerting |

---

## Step 2: Create an Audit Logging Plugin

```python
import logging
from datetime import datetime

class AuditLoggingPlugin(BasePlugin):
    """Logs all tool invocations for security audit."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger("adk.audit")
    
    async def before_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
    ) -> Optional[dict]:
        """Log tool invocation before execution."""
        self.logger.info(
            "TOOL_INVOKE",
            extra={
                "timestamp": datetime.utcnow().isoformat(),
                "tool_name": tool.name,
                "args": self._sanitize_args(tool_args),
                "session_id": tool_context.session.id,
                "user_id": tool_context.user_id,
                "invocation_id": tool_context.invocation_id,
            }
        )
        return None  # Proceed normally
    
    async def after_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
        result: dict,
    ) -> Optional[dict]:
        """Log tool result after execution."""
        self.logger.info(
            "TOOL_RESULT",
            extra={
                "timestamp": datetime.utcnow().isoformat(),
                "tool_name": tool.name,
                "success": "error" not in result,
                "session_id": tool_context.session.id,
            }
        )
        return None
    
    async def on_tool_error(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
        error: Exception,
    ) -> Optional[dict]:
        """Log tool errors."""
        self.logger.error(
            "TOOL_ERROR",
            extra={
                "tool_name": tool.name,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "session_id": tool_context.session.id,
            }
        )
        return None  # Let error propagate
    
    def _sanitize_args(self, args: dict) -> dict:
        """Remove sensitive data from logged arguments."""
        sensitive_keys = {"password", "token", "secret", "api_key", "credential"}
        return {
            k: "[REDACTED]" if k.lower() in sensitive_keys else v
            for k, v in args.items()
        }
```

---

## Step 3: Create a Policy Enforcement Plugin

Implement centralized access control using a policy engine pattern.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

class PolicyDecision(Enum):
    ALLOW = "allow"
    DENY = "deny"
    

@dataclass
class PolicyContext:
    tool_name: str
    tool_args: dict
    user_id: str
    session_id: str
    

class BasePolicyEngine(ABC):
    """Abstract base for policy engines."""
    
    @abstractmethod
    async def evaluate(self, context: PolicyContext) -> PolicyDecision:
        """Evaluate policy and return decision."""
        pass


class RBACPolicyEngine(BasePolicyEngine):
    """Role-based access control policy engine."""
    
    def __init__(self, role_permissions: dict[str, set[str]]):
        # role -> set of allowed tool names
        self.role_permissions = role_permissions
        # user -> role (in practice, fetch from database)
        self.user_roles: dict[str, str] = {}
    
    def set_user_role(self, user_id: str, role: str):
        self.user_roles[user_id] = role
    
    async def evaluate(self, context: PolicyContext) -> PolicyDecision:
        role = self.user_roles.get(context.user_id, "guest")
        allowed_tools = self.role_permissions.get(role, set())
        
        if context.tool_name in allowed_tools or "*" in allowed_tools:
            return PolicyDecision.ALLOW
        return PolicyDecision.DENY


class SecurityPolicyPlugin(BasePlugin):
    """Enforces security policies on tool execution."""
    
    def __init__(self, policy_engine: BasePolicyEngine):
        self.policy_engine = policy_engine
    
    async def before_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
    ) -> Optional[dict]:
        """Check policy before tool execution."""
        context = PolicyContext(
            tool_name=tool.name,
            tool_args=tool_args,
            user_id=tool_context.user_id,
            session_id=tool_context.session.id,
        )
        
        decision = await self.policy_engine.evaluate(context)
        
        if decision == PolicyDecision.DENY:
            return {
                "error": f"Access denied: User lacks permission for tool '{tool.name}'"
            }
        
        return None  # Allow execution
```

---

## Step 4: Create a Rate Limiting Plugin

```python
from collections import defaultdict
from time import time

class RateLimitPlugin(BasePlugin):
    """Enforces rate limits on tool invocations."""
    
    def __init__(
        self,
        max_calls_per_minute: int = 60,
        max_calls_per_tool_per_minute: int = 10,
    ):
        self.max_calls = max_calls_per_minute
        self.max_per_tool = max_calls_per_tool_per_minute
        self.call_times: dict[str, list[float]] = defaultdict(list)
        self.tool_call_times: dict[str, dict[str, list[float]]] = defaultdict(
            lambda: defaultdict(list)
        )
    
    async def before_tool_callback(
        self,
        *,
        tool: BaseTool,
        tool_args: dict[str, Any],
        tool_context: ToolContext,
    ) -> Optional[dict]:
        """Check rate limits before execution."""
        user_id = tool_context.user_id
        tool_name = tool.name
        now = time()
        window_start = now - 60
        
        # Clean old entries
        self.call_times[user_id] = [
            t for t in self.call_times[user_id] if t > window_start
        ]
        self.tool_call_times[user_id][tool_name] = [
            t for t in self.tool_call_times[user_id][tool_name] if t > window_start
        ]
        
        # Check global rate limit
        if len(self.call_times[user_id]) >= self.max_calls:
            return {"error": "Rate limit exceeded. Please try again later."}
        
        # Check per-tool rate limit
        if len(self.tool_call_times[user_id][tool_name]) >= self.max_per_tool:
            return {"error": f"Rate limit for '{tool_name}' exceeded."}
        
        # Record this call
        self.call_times[user_id].append(now)
        self.tool_call_times[user_id][tool_name].append(now)
        
        return None
```

---

## Step 5: Create a Content Filtering Plugin

```python
class ContentFilterPlugin(BasePlugin):
    """Filters harmful content from model inputs and outputs."""
    
    def __init__(self, blocked_patterns: list[str]):
        self.blocked_patterns = [p.lower() for p in blocked_patterns]
    
    async def before_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_request: LlmRequest,
    ) -> Optional[LlmResponse]:
        """Check input for blocked patterns."""
        from google.genai import types
        
        if not llm_request.contents:
            return None
        
        last_content = llm_request.contents[-1]
        for part in last_content.parts:
            if hasattr(part, "text") and part.text:
                text_lower = part.text.lower()
                for pattern in self.blocked_patterns:
                    if pattern in text_lower:
                        return LlmResponse(
                            content=types.Content(
                                role="model",
                                parts=[types.Part.from_text(
                                    "I cannot process this request due to content policy."
                                )]
                            )
                        )
        
        return None
    
    async def after_model_callback(
        self,
        *,
        callback_context: CallbackContext,
        llm_response: LlmResponse,
    ) -> Optional[LlmResponse]:
        """Filter blocked patterns from output."""
        import re
        from google.genai import types
        
        if not llm_response.content or not llm_response.content.parts:
            return None
        
        modified = False
        new_parts = []
        
        for part in llm_response.content.parts:
            if hasattr(part, "text") and part.text:
                text = part.text
                for pattern in self.blocked_patterns:
                    if pattern in text.lower():
                        text = re.sub(
                            re.escape(pattern),
                            "[FILTERED]",
                            text,
                            flags=re.IGNORECASE
                        )
                        modified = True
                new_parts.append(types.Part.from_text(text))
            else:
                new_parts.append(part)
        
        if modified:
            return LlmResponse(
                content=types.Content(role="model", parts=new_parts)
            )
        
        return None
```

---

## Step 6: Register Plugins with Runner

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Configure policy engine
policy_engine = RBACPolicyEngine(
    role_permissions={
        "admin": {"*"},  # All tools
        "user": {"search", "read_file"},  # Limited tools
        "guest": set(),  # No tools
    }
)
policy_engine.set_user_role("user1", "admin")

# Create plugins
plugins = [
    AuditLoggingPlugin(),
    SecurityPolicyPlugin(policy_engine),
    RateLimitPlugin(max_calls_per_minute=100),
    ContentFilterPlugin(blocked_patterns=["jailbreak", "ignore instructions"]),
]

# Create runner with plugins
runner = Runner(
    agent=agent,
    session_service=InMemorySessionService(),
    plugins=plugins,
)
```

---

## Plugin Execution Order

Plugins execute in registration order. For security, register:

1. **Rate limiting** (first - fail fast on abuse)
2. **Content filtering** (block harmful input early)
3. **Policy enforcement** (check authorization)
4. **Audit logging** (log all attempts, including blocked ones)

```python
plugins = [
    RateLimitPlugin(),        # 1. Rate limit first
    ContentFilterPlugin(...), # 2. Filter content
    SecurityPolicyPlugin(...),# 3. Check permissions
    AuditLoggingPlugin(),     # 4. Log everything
]
```

---

## Verification

```bash
adk run your_agent_folder
```

Test each plugin:

1. **Audit**: Check logs for tool invocations
2. **Policy**: Try accessing a tool without permission
3. **Rate limit**: Make rapid requests to trigger limit
4. **Content filter**: Send blocked patterns

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Plugin not executing | Not registered with Runner | Add to `plugins=[]` parameter |
| Wrong execution order | Registration order matters | Reorder in plugins list |
| Async errors | Missing `async` keyword | All callbacks must be `async def` |
| Blocking not working | Wrong return type | Return `{"error": ...}` for tools, `LlmResponse` for model |

---

## References

- ADK Plugins Guide
- ADK Multi-Agent: SecurityPlugin Pattern
- ADK Callbacks Design Patterns
