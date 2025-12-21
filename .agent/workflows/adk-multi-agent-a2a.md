---
description: Implement Agent-to-Agent (A2A) protocol for inter-agent communication across network boundaries
---

# ADK Workflow: Agent-to-Agent (A2A) Protocol

Connect agents across network boundaries using the standardized A2A protocol. This workflow covers exposing agents as A2A servers and consuming remote agents via `RemoteA2aAgent`.

---

## When to Use A2A

**Use A2A when:**
- The agent is a **separate, standalone service** (e.g., a specialized domain agent)
- The agent is maintained by a **different team or organization**
- Connecting agents written in **different languages or frameworks**
- Enforcing a **formal API contract** between agent systems

**Use local sub-agents instead when:**
- Agents run **within the same process** (internal modules)
- Performance-critical operations with shared memory
- Simple helper functions or code organization

---

## Prerequisites

- [ ] ADK with A2A support installed: `pip install google-adk[a2a]`
- [ ] Python 3.10+ with async support
- [ ] Network connectivity between agent hosts (for remote communication)

---

## Part A: Exposing an Agent via A2A

Make your existing ADK agent available for remote consumption.

### Step 1: Create the Agent

Define your agent with tools and instructions as usual:

```python
from google.adk.agents import Agent

root_agent = Agent(
    model='gemini-2.0-flash',
    name='my_service_agent',
    instruction="""You are a specialized service agent.
    Handle requests using your available tools.""",
    tools=[my_tool_function],
)
```

### Step 2: Wrap with `to_a2a()`

Convert the agent to an A2A-compatible Starlette application:

```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a

# Basic usage - auto-generates agent card
a2a_app = to_a2a(root_agent, host="localhost", port=8001)
```

**`to_a2a()` function signature:**

```python
def to_a2a(
    agent: BaseAgent,
    *,
    host: str = "localhost",
    port: int = 8000,
    protocol: str = "http",
    agent_card: Optional[Union[AgentCard, str]] = None,  # Custom card or path
    runner: Optional[Runner] = None,  # Custom runner configuration
) -> Starlette:
```

### Step 3: Serve with Uvicorn

```bash
uvicorn your_module.agent:a2a_app --host localhost --port 8001
```

### Step 4: Verify Agent Card

Check the auto-generated agent card at the well-known endpoint:

```bash
curl http://localhost:8001/.well-known/agent-card.json
```

---

## Part B: Consuming a Remote Agent

Connect to and use a remote A2A agent from your local agent.

### Step 1: Create RemoteA2aAgent

```python
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH

# Connect to remote agent via agent card URL
remote_agent = RemoteA2aAgent(
    name="remote_service",
    description="Remote service agent for specialized tasks",
    agent_card=f"http://localhost:8001{AGENT_CARD_WELL_KNOWN_PATH}",
)
```

**`RemoteA2aAgent` constructor parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Unique agent identifier |
| `agent_card` | `AgentCard \| str` | AgentCard object, URL, or file path |
| `description` | `str` | Agent description (auto-populated from card if empty) |
| `httpx_client` | `httpx.AsyncClient` | Optional shared HTTP client |
| `timeout` | `float` | HTTP timeout in seconds (default: 600.0) |

### Step 2: Use as Sub-Agent

Add the remote agent to your root agent's sub-agents:

```python
from google.adk.agents import Agent

root_agent = Agent(
    model="gemini-2.0-flash",
    name="orchestrator_agent",
    instruction="""You orchestrate tasks between local and remote agents.
    Delegate specialized tasks to the remote_service agent.""",
    sub_agents=[remote_agent],  # Include remote agent
    tools=[local_tool],
)
```

### Step 3: Run the Consuming Agent

```bash
# Start consuming agent on different port than the exposed agent
adk web your_agent_folder
```

---

## Part C: Using ADK CLI for A2A

Alternative approach using the ADK command line.

### Expose with `adk api_server`

```bash
# Expose agent with A2A protocol
adk api_server --a2a --port 8001 path/to/agent_folder
```

> [!NOTE]
> When using `adk api_server --a2a`, you need to provide an `agent.json` file in your agent folder with the agent card definition.

### Agent Card File Structure

Create `agent.json` in your agent folder:

```json
{
  "name": "my_agent",
  "description": "Agent that performs specialized tasks",
  "version": "1.0.0",
  "url": "http://localhost:8001/a2a/my_agent",
  "capabilities": {},
  "skills": [
    {
      "id": "main_skill",
      "name": "Main Skill",
      "description": "Primary capability of this agent",
      "tags": ["domain", "specific"]
    }
  ],
  "defaultInputModes": ["text/plain"],
  "defaultOutputModes": ["application/json"]
}
```

---

## Custom Agent Card Configuration

### Programmatic AgentCard

```python
from a2a.types import AgentCard, AgentSkill
from google.adk.a2a.utils.agent_to_a2a import to_a2a

custom_card = AgentCard(
    name="custom_agent",
    url="http://localhost:8001",
    description="Custom configured agent",
    version="1.0.0",
    capabilities={},
    skills=[
        AgentSkill(
            id="primary_skill",
            name="Primary Skill",
            description="Main agent capability",
            tags=["custom"]
        )
    ],
    defaultInputModes=["text/plain"],
    defaultOutputModes=["text/plain"],
)

a2a_app = to_a2a(root_agent, port=8001, agent_card=custom_card)
```

### Load from JSON File

```python
a2a_app = to_a2a(
    root_agent,
    port=8001,
    agent_card="/path/to/custom-agent-card.json"
)
```

---

## Complete Example: Multi-Agent System

### 1. Remote Prime Checker Agent (`remote_agent/agent.py`)

```python
from google.adk.agents import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

def check_prime(nums: list[int]) -> str:
    """Check if numbers are prime."""
    results = []
    for n in nums:
        is_prime = n > 1 and all(n % i != 0 for i in range(2, int(n**0.5) + 1))
        results.append(f"{n}: {'prime' if is_prime else 'not prime'}")
    return "\n".join(results)

root_agent = Agent(
    model='gemini-2.0-flash',
    name='prime_checker_agent',
    instruction="Check if numbers are prime using the check_prime tool.",
    tools=[check_prime],
)

# Expose as A2A server
a2a_app = to_a2a(root_agent, port=8001)
```

### 2. Main Orchestrator Agent (`main_agent/agent.py`)

```python
from google.adk.agents import Agent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent, AGENT_CARD_WELL_KNOWN_PATH

# Connect to remote prime checker
prime_agent = RemoteA2aAgent(
    name="prime_agent",
    description="Checks if numbers are prime",
    agent_card=f"http://localhost:8001{AGENT_CARD_WELL_KNOWN_PATH}",
)

def roll_die(sides: int) -> int:
    """Roll a die with given number of sides."""
    import random
    return random.randint(1, sides)

root_agent = Agent(
    model="gemini-2.0-flash",
    name="orchestrator",
    instruction="""You coordinate dice rolling and prime checking.
    1. Use roll_die for dice operations
    2. Delegate prime checking to prime_agent""",
    tools=[roll_die],
    sub_agents=[prime_agent],
)
```

### 3. Run the System

```bash
# Terminal 1: Start remote agent
uvicorn remote_agent.agent:a2a_app --host localhost --port 8001

# Terminal 2: Start main agent
adk web main_agent
```

---

## Integration Points

- **With State:** Session state is passed through A2A requests via `ClientCallContext`
- **With Callbacks:** Standard ADK callbacks work on both exposed and consuming agents
- **With Artifacts:** Artifacts can be exchanged through A2A message parts

---

## Verification

1. **Check remote agent is running:**
   ```bash
   curl http://localhost:8001/.well-known/agent-card.json
   ```

2. **Test in ADK Web UI:**
   ```bash
   adk web your_agent_folder
   ```
   Navigate to `http://localhost:8000` and test interactions.

3. **Enable debug logging:**
   ```bash
   adk api_server --a2a --port 8001 agent_folder --log_level debug
   ```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `AgentCardResolutionError` | Cannot fetch agent card | Verify URL and that remote server is running |
| `A2AClientHTTPError` | Network or authentication failure | Check connectivity, ports, and firewall rules |
| Port conflict | Same port for exposed and consuming agent | Use different ports (e.g., 8001 for exposed, 8000 for consuming) |
| Empty response | No message parts to send | Ensure session has content before delegation |
| Timeout errors | Remote agent slow or unresponsive | Increase `timeout` parameter in `RemoteA2aAgent` |

---

## References

- A2A Protocol: https://a2a-protocol.org
- ADK A2A Introduction: `docs/a2a/intro.md`
- Quickstart Consuming: `docs/a2a/quickstart-consuming.md`
- Quickstart Exposing: `docs/a2a/quickstart-exposing.md`
- RemoteA2aAgent: `src/google/adk/agents/remote_a2a_agent.py`
- to_a2a utility: `src/google/adk/a2a/utils/agent_to_a2a.py`
- AgentCardBuilder: `src/google/adk/a2a/utils/agent_card_builder.py`
