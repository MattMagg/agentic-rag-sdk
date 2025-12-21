---
description: Evaluate ADK agent performance with test files, evalsets, and built-in criteria
---

# ADK Workflow: Agent Evaluation

Evaluate agent performance using trajectory matching, response quality assessment, LLM-as-judge, and safety criteria.

---

## Prerequisites

- [ ] ADK installed: `pip install google-adk`
- [ ] pytest for programmatic testing: `pip install pytest pytest-asyncio`
- [ ] For LLM-based criteria: Google Cloud Project with Vertex AI enabled

---

## Step 1: Understand Evaluation Components

ADK evaluation assesses two key aspects:

| Component | Description |
|-----------|-------------|
| **Trajectory** | The sequence of tool calls and agent actions |
| **Final Response** | The quality and correctness of the agent's output |

---

## Step 2: Create Evaluation Data

### Option A: Test Files (Unit Testing)

Create `*.test.json` files for simple agent interactions:

```json
{
  "eval_set_id": "my_agent_tests",
  "name": "My Agent Test Suite",
  "description": "Unit tests for my agent",
  "eval_cases": [
    {
      "eval_id": "test_basic_query",
      "conversation": [
        {
          "invocation_id": "inv-001",
          "user_content": {
            "parts": [{"text": "Turn off the bedroom light"}],
            "role": "user"
          },
          "final_response": {
            "parts": [{"text": "I have turned off the bedroom light."}],
            "role": "model"
          },
          "intermediate_data": {
            "tool_uses": [
              {
                "name": "set_device_status",
                "args": {"device": "bedroom_light", "status": "off"}
              }
            ],
            "intermediate_responses": []
          }
        }
      ],
      "session_input": {
        "app_name": "my_agent",
        "user_id": "test_user",
        "state": {}
      }
    }
  ]
}
```

### Option B: Eval Sets (Integration Testing)

Eval sets support complex, multi-turn conversations. Create with ADK Web UI:

1. Run `adk web path/to/agent`
2. Interact with the agent to create a session
3. Navigate to **Eval** tab → Create new eval set
4. Click **"Add current session"** to save as eval case

---

## Step 3: Configure Evaluation Criteria

Create `test_config.json` to specify thresholds:

```json
{
  "criteria": {
    "tool_trajectory_avg_score": 1.0,
    "response_match_score": 0.8
  }
}
```

### Available Criteria

| Criterion | Description | Reference-Based | LLM-as-Judge |
|-----------|-------------|-----------------|--------------|
| `tool_trajectory_avg_score` | Exact match of tool call trajectory | Yes | No |
| `response_match_score` | ROUGE-1 similarity to reference | Yes | No |
| `final_response_match_v2` | Semantic match to reference | Yes | Yes |
| `rubric_based_final_response_quality_v1` | Response quality via custom rubrics | No | Yes |
| `rubric_based_tool_use_quality_v1` | Tool usage quality via custom rubrics | No | Yes |
| `hallucinations_v1` | Groundedness of response against context | No | Yes |
| `safety_v1` | Safety/harmlessness of response | No | Yes |

---

## Step 4: Configure Advanced Criteria

### Tool Trajectory Matching

Three match types available: `EXACT`, `IN_ORDER`, `ANY_ORDER`:

```json
{
  "criteria": {
    "tool_trajectory_avg_score": {
      "threshold": 1.0,
      "match_type": "IN_ORDER"
    }
  }
}
```

- **EXACT**: Perfect match required, no extra or missing calls
- **IN_ORDER**: Expected calls must appear in order, allows intermediate calls
- **ANY_ORDER**: Expected calls must appear, any order allowed

### LLM-as-Judge Semantic Matching

```json
{
  "criteria": {
    "final_response_match_v2": {
      "threshold": 0.8,
      "judge_model_options": {
        "judge_model": "gemini-2.5-flash",
        "num_samples": 5
      }
    }
  }
}
```

### Rubric-Based Response Quality

```json
{
  "criteria": {
    "rubric_based_final_response_quality_v1": {
      "threshold": 0.8,
      "judge_model_options": {
        "judge_model": "gemini-2.5-flash",
        "num_samples": 5
      },
      "rubrics": [
        {
          "rubric_id": "conciseness",
          "rubric_content": {
            "text_property": "The response is direct and to the point."
          }
        },
        {
          "rubric_id": "helpfulness",
          "rubric_content": {
            "text_property": "The response addresses the user's actual need."
          }
        }
      ]
    }
  }
}
```

### Rubric-Based Tool Usage Quality

```json
{
  "criteria": {
    "rubric_based_tool_use_quality_v1": {
      "threshold": 1.0,
      "judge_model_options": {
        "judge_model": "gemini-2.5-flash",
        "num_samples": 5
      },
      "rubrics": [
        {
          "rubric_id": "tool_order",
          "rubric_content": {
            "text_property": "The agent calls GeoCoding before GetWeather."
          }
        }
      ]
    }
  }
}
```

### Hallucination Detection

```json
{
  "criteria": {
    "hallucinations_v1": {
      "threshold": 0.8,
      "judge_model_options": {
        "judge_model": "gemini-2.5-flash"
      },
      "evaluate_intermediate_nl_responses": true
    }
  }
}
```

### Safety Evaluation

```json
{
  "criteria": {
    "safety_v1": 0.8
  }
}
```

> [!NOTE]
> `safety_v1` requires `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` environment variables.

---

## Step 5: Run Evaluations

### Method 1: ADK Web UI

```bash
adk web path/to/agent
```

1. Navigate to **Eval** tab
2. Select test cases from your evalset
3. Click **Run Evaluation**
4. Configure metric thresholds in the dialog
5. Click **Start**

Results show Pass/Fail with detailed score breakdowns.

### Method 2: pytest Integration

```python
# tests/test_agent.py
from google.adk.evaluation.agent_evaluator import AgentEvaluator
import pytest

@pytest.mark.asyncio
async def test_basic_interaction():
    """Test the agent's basic ability via a test file."""
    await AgentEvaluator.evaluate(
        agent_module="my_agent",
        eval_dataset_file_path_or_dir="tests/fixtures/basic.test.json",
    )

@pytest.mark.asyncio
async def test_with_custom_criteria():
    """Test with custom evaluation criteria."""
    await AgentEvaluator.evaluate(
        agent_module="my_agent",
        eval_dataset_file_path_or_dir="tests/fixtures/",
        criteria={"tool_trajectory_avg_score": 1.0, "response_match_score": 0.8}
    )
```

Run tests:

```bash
pytest tests/test_agent.py -v
```

### Method 3: ADK CLI

```bash
adk eval \
    path/to/agent \
    path/to/evalset.evalset.json \
    --config_file_path=test_config.json \
    --print_detailed_results
```

Run specific evals from an eval set:

```bash
adk eval \
    path/to/agent \
    path/to/evalset.evalset.json:eval_1,eval_2 \
    --print_detailed_results
```

---

## Step 6: Analyze Results

### Web UI Analysis

- Click any **Pass** or **Fail** result
- Hover over `Fail` to see Actual vs. Expected comparison
- View scores that caused the failure

### Trace View Debugging

Use the **Trace** tab to inspect agent execution:

- **Event**: Raw event data
- **Request**: Request sent to the model
- **Response**: Response from the model
- **Graph**: Visual representation of tool calls

---

## Recommendations: Choosing Criteria

| Goal | Recommended Criteria |
|------|----------------------|
| CI/CD regression testing | `tool_trajectory_avg_score`, `response_match_score` |
| Semantic correctness with reference | `final_response_match_v2` |
| Quality without reference response | `rubric_based_final_response_quality_v1` |
| Validate tool usage reasoning | `rubric_based_tool_use_quality_v1` |
| Detect hallucinations | `hallucinations_v1` |
| Ensure safe responses | `safety_v1` |

---

## Integration Points

- **With Callbacks:** Use callbacks to capture intermediate data for evaluation
- **With State:** Include session state in `session_input` for stateful tests
- **With CI/CD:** Integrate via pytest or `adk eval` command
- **With User Simulation:** Use `hallucinations_v1` and `safety_v1` for dynamic conversation testing

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Test file not recognized | Missing `.test.json` suffix | Rename file to `*.test.json` |
| Eval set validation error | Schema mismatch | Use `AgentEvaluator.migrate_eval_data_to_new_schema()` |
| LLM criteria not working | Missing GCP config | Set `GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION` |
| Trajectory mismatch | Tool args differ | Check expected args match actual tool implementation |
| Low ROUGE-1 scores | Different phrasing | Use `final_response_match_v2` for semantic matching |

---

## References

- [ADK Evaluation Guide](https://google.github.io/adk-docs/evaluate/)
- [Evaluation Criteria Reference](https://google.github.io/adk-docs/evaluate/criteria/)
- [User Simulation](https://google.github.io/adk-docs/evaluate/user-sim/)
- [EvalSet Schema](https://github.com/google/adk-python/blob/main/src/google/adk/evaluation/eval_set.py)
- [EvalCase Schema](https://github.com/google/adk-python/blob/main/src/google/adk/evaluation/eval_case.py)
