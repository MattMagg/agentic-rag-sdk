---
name: adk-create-agent
description: Create a new ADK agent with intelligent type selection
argument-hint: Optional agent name and purpose
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Create ADK Agent

Create a new agent with intelligent selection of agent type and configuration.

## Decision Logic

**Step 1: Understand requirements**

Ask user:
> "What should this agent do? (Brief description)"

**Step 2: Recommend agent type**

Based on description:

If requires LLM reasoning (conversation, analysis, decisions):
> "I recommend **LlmAgent** because your use case requires AI reasoning.
>
> - Uses Gemini 3 Flash by default (fast, cost-effective)
> - Can use tools and have conversations
>
> Proceed with LlmAgent?"

If purely programmatic (API calls, calculations, orchestration):
> "I recommend **Custom Agent (BaseAgent)** because your use case is deterministic without LLM reasoning.
>
> - Full control over execution
> - No LLM costs
> - Best for orchestration logic
>
> Proceed with BaseAgent?"

**Step 3: Configure agent**

For LlmAgent:
1. Ask for agent name (or use provided)
2. Ask for model preference (default: gemini-3-flash)
3. Generate instruction based on purpose
4. Create agent.py

For BaseAgent:
1. Ask for agent name
2. Create agent.py with run_async skeleton

**Step 4: Create the agent file**

Use `@adk-agents` skill for implementation details.

**Step 5: Verify**

```bash
adk run <agent_name>
```

## Usage Examples

```
/adk-create-agent                           # Interactive
/adk-create-agent customer_support         # Named agent
/adk-create-agent "handles billing questions"  # With purpose
```

## References

Load `@adk-agents` skill for detailed agent configuration.
