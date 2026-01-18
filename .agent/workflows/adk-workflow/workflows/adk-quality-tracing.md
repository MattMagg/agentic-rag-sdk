---
description: Enable OpenTelemetry tracing with Cloud Trace and third-party platforms for ADK agents
---

# ADK Workflow: Quality Tracing

Enable distributed tracing for your ADK agents using OpenTelemetry (OTel). ADK emits OTel spans for LLM calls, tool executions, and agent interactions, which can be exported to Google Cloud Trace or third-party platforms like MLflow, Weave, AgentOps, and Monocle.

---

## Prerequisites

- [ ] Google Cloud project (for Cloud Trace)
- [ ] ADK Python v0.1.0+
- [ ] Required packages installed

```bash
pip install google-adk
# For Cloud Trace
pip install opentelemetry-exporter-gcp-trace
# For MLflow
pip install mlflow>=2.17
# For Weave
pip install weave
```

---

## Step 1: Enable Cloud Trace (ADK CLI)

### Option A: Development Server

Start the ADK development server with Cloud Trace enabled:

```bash
adk web --trace_to_cloud your_agent_folder
```

### Option B: Agent Engine Deployment

Deploy to Vertex AI Agent Engine with tracing:

```bash
adk deploy agent_engine --trace_to_cloud your_agent_folder \
    --project YOUR_PROJECT_ID \
    --region us-central1
```

---

## Step 2: Programmatic Tracing Setup

For custom applications, configure tracing programmatically:

```python
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.telemetry.google_cloud import get_gcp_exporters
from google.adk.telemetry.setup import maybe_set_otel_providers

from your_agent import root_agent

# Get Cloud Trace exporters
otel_hooks = get_gcp_exporters(
    enable_cloud_tracing=True,
    enable_cloud_metrics=False,
    enable_cloud_logging=False,
)

# Initialize the OTel provider
maybe_set_otel_providers(
    otel_hooks_to_setup=[otel_hooks],
)

# Create runner and execute
runner = Runner(
    agent=root_agent,
    session_service=InMemorySessionService(),
    app_name="my-traced-agent",
)
```

---

## Step 3: Third-Party Integrations

### MLflow Tracing

MLflow's tracing system ingests OpenTelemetry traces emitted by ADK:

```python
import mlflow

# Enable MLflow tracing
mlflow.set_experiment("adk-agent-traces")

# ADK spans are automatically exported when MLflow tracing is active
# Use @mlflow.trace decorator for additional spans
```

### Weave by WandB

```python
import weave

# Initialize Weave
weave.init("your-wandb-project")

# ADK traces are automatically captured
```

### AgentOps

AgentOps provides session replays and metrics with minimal setup:

```python
import agentops

# Initialize AgentOps (neutralizes ADK's native telemetry)
agentops.init()

# AgentOps instruments ADK automatically
```

### Monocle

Monocle is an open-source observability platform:

```python
from monocle_apptrace.instrumentation import setup_monocle_telemetry

# Setup Monocle telemetry
setup_monocle_telemetry(
    workflow_name="adk-weather-agent"
)
```

---

## Step 4: Environment Variable Configuration

Configure tracing via environment variables:

```bash
# Enable OTLP exporter
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
export OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="http://localhost:4318/v1/traces"

# Set service name
export OTEL_SERVICE_NAME="my-adk-agent"
```

---

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_cloud_tracing` | bool | False | Export spans to Cloud Trace |
| `enable_cloud_metrics` | bool | False | Export metrics to Cloud Monitoring |
| `enable_cloud_logging` | bool | False | Export logs to Cloud Logging |
| `google_auth` | tuple | None | Custom credentials (Credentials, project_id) |

---

## What Gets Traced

ADK automatically traces:

| Span Type | Description |
|-----------|-------------|
| LLM Calls | Requests and responses to the model |
| Tool Executions | Function tool invocations and results |
| Agent Interactions | Parent-child agent communication |
| Data Sending | Content sent to the agent |

---

## Verification

### View in Google Cloud Console

1. Navigate to **Trace Explorer** in Cloud Console
2. Filter by `AGENT_APP.my-traced-agent` (your app name)
3. View span hierarchy and timing

### Test locally

```bash
# Start with tracing enabled
adk web --trace_to_cloud your_agent_folder

# Make requests and check Cloud Trace Explorer
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| No traces in Cloud Console | Missing permissions | Grant `roles/cloudtrace.agent` to service account |
| OTLP export fails | Endpoint not reachable | Check `OTEL_EXPORTER_OTLP_ENDPOINT` value |
| Third-party not capturing | Initialization order | Initialize third-party SDK before ADK agent |

---

## References

- [Cloud Trace Documentation](https://cloud.google.com/trace/docs)
- [MLflow Tracing](https://mlflow.org/docs/latest/genai/tracing/)
- [Weave Documentation](https://weave-docs.wandb.ai/)
- [AgentOps Documentation](https://www.agentops.ai)
- [Monocle Repository](https://github.com/monocle2ai/monocle)
