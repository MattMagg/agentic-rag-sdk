---
description: Implement LLM-backed user simulation for dynamic agent evaluation and automated testing
---

# ADK Workflow: User Simulation for Agent Evaluation

Use LLM-backed user simulation to dynamically evaluate conversational agents with conversation scenarios instead of fixed test prompts.

> [!NOTE]
> **Version:** Requires ADK Python v1.18.0+

---

## Prerequisites

- [ ] ADK Python installed (`pip install google-adk`)
- [ ] Agent project exists with a root agent
- [ ] Model API access configured (Google AI or Vertex AI)

---

## Step 1: Understand User Simulation

ADK's user simulation dynamically generates user prompts using a generative AI model. Instead of fixed prompts, you define:

| Component | Purpose |
|-----------|---------|
| `starting_prompt` | Fixed initial prompt to begin the conversation |
| `conversation_plan` | Guidelines for how the LLM should continue the conversation |

The LLM uses the conversation plan and conversation history to generate prompts until it judges the conversation is complete.

---

## Step 2: Create Conversation Scenarios

Create a scenarios file defining test conversations:

```json
{
  "scenarios": [
    {
      "starting_prompt": "What can you do for me?",
      "conversation_plan": "Ask the agent to roll a 20-sided die. After you get the result, ask the agent to check if it is prime."
    },
    {
      "starting_prompt": "Hi, I'm running a tabletop RPG in which prime numbers are bad!",
      "conversation_plan": "Say that you don't care about the value; you just want the agent to tell you if a roll is good or bad. Once the agent agrees, ask it to roll a 6-sided die. Finally, ask the agent to do the same with 2 20-sided dice."
    }
  ]
}
```

Save as: `<agent_folder>/conversation_scenarios.json`

---

## Step 3: Create Session Input File

Define session context for evaluation:

```json
{
  "app_name": "your_agent_name",
  "user_id": "user"
}
```

Save as: `<agent_folder>/session_input.json`

---

## Step 4: Add Scenarios to an EvalSet

```bash
# Create a new EvalSet (optional if adding to existing)
adk eval_set create \
  <agent_folder> \
  eval_set_with_scenarios

# Add conversation scenarios as eval cases
adk eval_set add_eval_case \
  <agent_folder> \
  eval_set_with_scenarios \
  --scenarios_file <agent_folder>/conversation_scenarios.json \
  --session_input_file <agent_folder>/session_input.json
```

---

## Step 5: Configure Evaluation Metrics

Since user simulation doesn't have expected responses, use appropriate metrics:

```json
{
  "criteria": {
    "hallucinations_v1": {
      "threshold": 0.5,
      "evaluate_intermediate_nl_responses": true
    },
    "safety_v1": {
      "threshold": 0.8
    }
  }
}
```

Save as: `<agent_folder>/eval_config.json`

---

## Step 6: Configure User Simulator (Optional)

Override default user simulator behavior in your eval config:

```json
{
  "criteria": {
    "hallucinations_v1": { "threshold": 0.5 },
    "safety_v1": { "threshold": 0.8 }
  },
  "user_simulator_config": {
    "model": "gemini-3-flash-preview",
    "model_configuration": {
      "thinking_config": {
        "include_thoughts": true,
        "thinking_budget": 10240
      }
    },
    "max_allowed_invocations": 20
  }
}
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `model` | `gemini-3-flash-preview` | Model backing the simulator |
| `model_configuration` | See above | GenerateContentConfig for model behavior |
| `max_allowed_invocations` | `20` | Max user-agent interactions before forced termination |

---

## Step 7: Run Evaluation

```bash
adk eval \
    <agent_folder> \
    --config_file_path <agent_folder>/eval_config.json \
    eval_set_with_scenarios \
    --print_detailed_results
```

---

## Configuration Options

### ConversationScenario Structure

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `starting_prompt` | string | Yes | Fixed initial user message |
| `conversation_plan` | string | Yes | LLM instructions for conversation flow |

### Supported Evaluation Criteria

| Criterion | Purpose |
|-----------|---------|
| `hallucinations_v1` | Detect factual inaccuracies |
| `safety_v1` | Evaluate response safety |
| `per_turn_user_simulator_quality_v1` | Verify simulator follows scenario |

---

## Integration Points

- **With EvalSet:** Scenarios are stored as eval cases within EvalSets
- **With EvalConfig:** Simulator config and evaluation criteria
- **With adk web:** Run evaluations interactively via `adk web`

---

## Verification

```bash
# Run evaluation with detailed output
adk eval \
    <agent_folder> \
    --config_file_path <agent_folder>/eval_config.json \
    eval_set_with_scenarios \
    --print_detailed_results
```

**Expected behavior:**
- Simulator generates dynamic prompts following the conversation plan
- Agent responses are evaluated against configured criteria
- Detailed results show pass/fail for each scenario

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Conversation terminates early | `max_allowed_invocations` too low | Increase the value in `user_simulator_config` |
| Simulator goes off-topic | Vague `conversation_plan` | Make plan more specific and goal-oriented |
| Missing expected responses error | Using response-dependent metrics | Use `hallucinations_v1` or `safety_v1` instead |

---

## Example: Complete Workflow

```bash
# 1. Create scenario file
cat > my_agent/conversation_scenarios.json << 'EOF'
{
  "scenarios": [
    {
      "starting_prompt": "Hello, what can you help me with?",
      "conversation_plan": "Ask the agent to help you book a flight to Paris. Provide your travel dates when asked. Confirm the booking when offered."
    }
  ]
}
EOF

# 2. Create session input
cat > my_agent/session_input.json << 'EOF'
{
  "app_name": "my_agent",
  "user_id": "test_user"
}
EOF

# 3. Create eval config
cat > my_agent/eval_config.json << 'EOF'
{
  "criteria": {
    "hallucinations_v1": { "threshold": 0.5 },
    "safety_v1": { "threshold": 0.8 }
  }
}
EOF

# 4. Create EvalSet and add scenarios
adk eval_set create my_agent user_sim_tests
adk eval_set add_eval_case \
  my_agent \
  user_sim_tests \
  --scenarios_file my_agent/conversation_scenarios.json \
  --session_input_file my_agent/session_input.json

# 5. Run evaluation
adk eval my_agent --config_file_path my_agent/eval_config.json user_sim_tests --print_detailed_results
```

---

## References

- [ADK User Simulation Documentation](https://google.github.io/adk-docs/evaluate/user-sim/)
- [ADK Evaluation Guide](https://google.github.io/adk-docs/evaluate/)
- [ConversationScenario Source](https://github.com/google/adk-python/blob/main/src/google/adk/evaluation/conversation_scenarios.py)
- [LlmBackedUserSimulator Source](https://github.com/google/adk-python/blob/main/src/google/adk/evaluation/simulation/llm_backed_user_simulator.py)
- [Colab Notebook: User Simulation](https://github.com/google/adk-samples/blob/main/python/notebooks/evaluation/user_simulation_in_adk_evals.ipynb)
