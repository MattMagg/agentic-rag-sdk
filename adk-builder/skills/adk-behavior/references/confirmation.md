---
description: Implement human-in-the-loop confirmation for ADK tool execution
---

# ADK Workflow: Tool Confirmation (Human-in-the-Loop)

Tool confirmation enables human oversight of agent tool execution. Use this pattern for high-risk operations, financial transactions, data modifications, or any action requiring explicit user approval before execution.

> [!NOTE]
> This feature is supported in **ADK Python v1.14.0+**

---

## Prerequisites

- [ ] ADK Python >= 1.14.0
- [ ] FunctionTool or MCPTool usage
- [ ] Client capable of capturing confirmation responses
- [ ] Imports ready:

```python
from google.adk.tools import FunctionTool
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
```

---

## Step 1: Enable Confirmation on a Tool

Set `require_confirmation=True` when creating a FunctionTool:

### Static Confirmation (Always Require)

```python
from google.adk.tools import FunctionTool

def delete_user(user_id: str) -> dict:
    """Delete a user account permanently."""
    # This will only execute if user confirms
    return {"status": "deleted", "user_id": user_id}

delete_user_tool = FunctionTool(
    delete_user,
    require_confirmation=True,  # Always require confirmation
)
```

### Dynamic Confirmation (Conditional)

Use a function to determine whether confirmation is needed based on arguments:

```python
def should_require_confirmation(amount: float, **kwargs) -> bool:
    """Only require confirmation for large amounts."""
    return amount >= 1000.0

def transfer_money(amount: float, to_account: str) -> dict:
    """Transfer money to another account."""
    return {"status": "transferred", "amount": amount, "to": to_account}

transfer_tool = FunctionTool(
    transfer_money,
    require_confirmation=should_require_confirmation,
)
```

The confirmation function receives the same arguments as the tool function.

---

## Step 2: Handle Confirmation in Client

When a tool requires confirmation, the agent pauses execution and emits an event requesting confirmation. Your client must intercept this and prompt the user.

### Confirmation Flow

```
1. Agent decides to call tool with require_confirmation=True
2. Runner emits event with confirmation request
3. Client prompts user for approval
4. Client sends confirmation response back to Runner
5. Tool executes (if approved) or returns rejection message (if denied)
```

### Example: CLI Confirmation Handler

```python
from google.adk.runners import Runner
from google import genai

async def run_with_confirmation(runner: Runner, session, user_message: str):
    """Run agent with confirmation handling."""
    
    content = genai.types.Content(
        role="user",
        parts=[genai.types.Part(text=user_message)]
    )
    
    pending_confirmation = None
    
    async for event in runner.run_async(
        session=session,
        user_id="user123",
        new_message=content,
    ):
        # Check for confirmation request in event
        if event.actions and event.actions.requested_auth_configs:
            # Has pending confirmation request
            tool_name = extract_tool_name(event)
            tool_args = extract_tool_args(event)
            
            print(f"\n⚠️  Confirmation Required")
            print(f"   Tool: {tool_name}")
            print(f"   Args: {tool_args}")
            
            user_response = input("   Approve? (y/n): ").strip().lower()
            
            if user_response == "y":
                # Resume with approval
                await send_confirmation(runner, session, approved=True)
            else:
                # Resume with rejection
                await send_confirmation(runner, session, approved=False)
        
        # Normal event processing
        elif event.get_text():
            print(f"[{event.author}] {event.get_text()}")
```

---

## Step 3: Remote Confirmation via REST API

For headless environments without an interactive UI, use REST API endpoints:

### Runner with Resumable Sessions

```python
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService

# Use a persistent session service for resumable operations
session_service = DatabaseSessionService(db_url="sqlite:///sessions.db")

runner = Runner(
    agent=my_agent,
    app_name="my_app",
    session_service=session_service,
)
```

### CLI Tool for Confirmation

```bash
# Check pending confirmations
curl http://localhost:8000/api/confirmations

# Approve a confirmation
curl -X POST http://localhost:8000/api/confirm \
  -H "Content-Type: application/json" \
  -d '{"confirmation_id": "abc123", "approved": true}'

# Reject a confirmation  
curl -X POST http://localhost:8000/api/confirm \
  -H "Content-Type: application/json" \
  -d '{"confirmation_id": "abc123", "approved": false}'
```

---

## Step 4: Advanced Patterns

### SecurityPlugin for Policy-Based Confirmation

Use `SecurityPlugin` with `BasePolicyEngine` for centralized confirmation logic:

```python
from google.adk.plugins import SecurityPlugin
from google.adk.plugins.security import BasePolicyEngine, PolicyDecision

class MyPolicyEngine(BasePolicyEngine):
    """Custom policy engine for tool confirmation."""
    
    async def evaluate(
        self,
        tool_name: str,
        tool_args: dict,
        context: dict,
    ) -> PolicyDecision:
        # High-risk tools always require confirmation
        high_risk_tools = {"delete_user", "transfer_money", "modify_database"}
        
        if tool_name in high_risk_tools:
            return PolicyDecision.REQUIRE_CONFIRMATION
        
        # Amount-based rules
        if "amount" in tool_args and tool_args["amount"] >= 500:
            return PolicyDecision.REQUIRE_CONFIRMATION
        
        # Default: allow without confirmation
        return PolicyDecision.ALLOW

# Attach to runner
runner = Runner(
    agent=my_agent,
    app_name="my_app",
    plugins=[SecurityPlugin(policy_engine=MyPolicyEngine())],
)
```

### Multi-Agent Confirmation

In multi-agent systems, confirmation can span agent handoffs:

```python
from google.adk.agents import LlmAgent, SequentialAgent

# Agent that requests human approval
approval_agent = LlmAgent(
    name="approval_requester",
    model="gemini-3-flash-preview",
    instruction="""You request approval for high-value operations.
    Use the request_approval tool with the operation details.""",
    tools=[request_approval_tool],
)

# Main agent that performs operations after approval
executor_agent = LlmAgent(
    name="executor", 
    model="gemini-3-flash-preview",
    instruction="""You execute approved operations.
    Check state for 'approved' before proceeding.""",
    tools=[execute_operation_tool],
)

# Sequential workflow: request → approve → execute
workflow = SequentialAgent(
    name="approval_workflow",
    sub_agents=[approval_agent, executor_agent],
)
```

---

## Step 5: Testing Confirmation Flows

### Unit Test Example

```python
import pytest
from google.adk.tools import FunctionTool, ToolContext

@pytest.fixture
def confirmation_tool():
    def risky_operation(action: str) -> dict:
        return {"executed": action}
    
    return FunctionTool(risky_operation, require_confirmation=True)

async def test_confirmation_required(confirmation_tool, mock_tool_context):
    """Test that confirmation is required before execution."""
    
    # Without confirmation, tool should not execute
    mock_tool_context.confirmation = None
    
    result = await confirmation_tool.run_async(
        args={"action": "delete_everything"},
        tool_context=mock_tool_context,
    )
    
    assert result.get("confirmation_required") == True
    assert result.get("executed") is None

async def test_confirmation_approved(confirmation_tool, mock_tool_context):
    """Test tool executes when confirmation is approved."""
    
    mock_tool_context.confirmation = {"approved": True}
    
    result = await confirmation_tool.run_async(
        args={"action": "delete_everything"},
        tool_context=mock_tool_context,
    )
    
    assert result.get("executed") == "delete_everything"
```

---

## Verification

```bash
adk run agent_folder
```

1. Trigger a tool with `require_confirmation=True`
2. Verify confirmation prompt appears
3. Test approval → tool executes
4. Test rejection → tool returns rejection message
5. Verify state is preserved across confirmation pause

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Confirmation not requested | `require_confirmation` not set | Add `require_confirmation=True` to FunctionTool |
| Tool executes without confirmation | Confirmation handler bypassed | Ensure client properly handles confirmation events |
| Session lost after confirmation | Non-persistent session service | Use `DatabaseSessionService` or similar |
| Dynamic confirmation always triggers | Condition function always returns True | Check confirmation function logic |

---

## Best Practices

- **Use for high-risk operations only**: Don't over-confirm, it degrades UX
- **Provide clear context**: Show users exactly what will happen if they approve
- **Use dynamic confirmation**: Confirm only when necessary (e.g., high amounts)
- **Persist sessions**: Use database-backed sessions for resumable confirmation flows
- **Log confirmations**: Maintain audit trail of approved/rejected actions
- **Set timeouts**: Don't leave confirmations pending indefinitely
- **Test both paths**: Always test approval AND rejection handling
