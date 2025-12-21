---
description: Configure ADK tracing with Cloud Trace, MLflow, AgentOps, and other observability platforms
---

# ADK Workflow: Agent Observability

Configure OpenTelemetry-based tracing for ADK agents to monitor, debug, and analyze agent performance in production environments.

---

## Prerequisites

- [ ] Google Cloud Project (for Cloud Trace)
- [ ] ADK installed: `pip install google-adk`
- [ ] OpenTelemetry packages: `pip install opentelemetry-sdk opentelemetry-exporter-otlp-proto-http`

---

## Step 1: Understand ADK's Tracing Architecture

ADK emits OpenTelemetry (OTel) spans for key agent operations:

| Span Name | Description |
|-----------|-------------|
| `invocation` | Root span for each agent invocation |
| `agent_run` | Span for individual agent execution |
| `call_llm` | Span for LLM API calls |
| `execute_tool` | Span for tool execution |

These spans enable end-to-end distributed tracing across your agent's workflow.

---

## Step 2: Cloud Trace Setup

### Option A: ADK CLI Deployment

Enable tracing with the `--trace_to_cloud` flag:

```bash
# For Agent Engine deployment
adk deploy agent_engine \
    --project=$GOOGLE_CLOUD_PROJECT \
    --region=$GOOGLE_CLOUD_LOCATION \
    --staging_bucket=$STAGING_BUCKET \
    --trace_to_cloud \
    $AGENT_PATH

# For Cloud Run deployment
adk deploy cloud_run \
    --project=$GOOGLE_CLOUD_PROJECT \
    --region=$GOOGLE_CLOUD_LOCATION \
    --trace_to_cloud \
    $AGENT_PATH
```

### Option B: Python SDK Deployment

Enable tracing programmatically with `enable_tracing=True`:

```python
from vertexai.preview import reasoning_engines
from vertexai import agent_engines
import vertexai

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)

adk_app = reasoning_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,  # Enable Cloud Trace
)

remote_app = agent_engines.create(
    agent_engine=adk_app,
    extra_packages=["./my_agent"],
    requirements=["google-cloud-aiplatform[adk,agent_engines]"],
)
```

### Option C: FastAPI Integration

Use the built-in FastAPI app with tracing enabled:

```python
import os
from google.adk.cli.fast_api import get_fast_api_app
from fastapi import FastAPI

os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "your-project-id")

app: FastAPI = get_fast_api_app(
    agents_dir=os.path.dirname(os.path.abspath(__file__)),
    web=True,
    trace_to_cloud=True,  # Enable Cloud Trace
)
```

### Option D: Custom OpenTelemetry Setup

For full control, configure the tracer provider manually:

```python
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace import export

provider = TracerProvider()
processor = export.BatchSpanProcessor(
    CloudTraceSpanExporter(project_id="your-project-id")
)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Now import and run your agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

runner = Runner(
    agent=your_agent,
    app_name="my_agent",
    session_service=InMemorySessionService()
)
```

---

## Step 3: Third-Party Integrations

### MLflow Tracing

MLflow 3.6.0+ supports OpenTelemetry trace ingestion:

```bash
# Install dependencies
pip install "mlflow>=3.6.0" opentelemetry-exporter-otlp-proto-http

# Start MLflow server with SQL backend
mlflow server --backend-store-uri sqlite:///mlflow.db --port 5000
```

Configure the OTLP exporter BEFORE importing ADK:

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

exporter = OTLPSpanExporter(
    endpoint="http://localhost:5000/v1/traces",
    headers={"x-mlflow-experiment-id": "123"}
)

provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(exporter))
trace.set_tracer_provider(provider)  # Set BEFORE importing ADK

# Now import your agent
from google.adk.agents import LlmAgent
```

### AgentOps

Two-line integration for session replays and metrics:

```python
import agentops

agentops.init(api_key="your-api-key")

# AgentOps automatically instruments ADK agents
from google.adk.agents import Agent

agent = Agent(
    name="my_agent",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant.",
    tools=[my_tool],
)
```

### Monocle

Open-source observability platform for LLM applications:

```python
from monocle_apptrace.instrumentor import setup_monocle_telemetry

setup_monocle_telemetry(
    workflow_name="my_adk_agent",
    span_processors=[your_span_processor],
)

# Your ADK agent code here
```

### Weave by WandB

Logging and visualization platform integration:

```python
import weave

weave.init(project_name="my-adk-project")

# Your ADK agent will be automatically traced
```

### Arize AX

Production-grade observability at scale - configures OpenTelemetry to send to Arize Phoenix.

---

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `--trace_to_cloud` | CLI flag to enable Cloud Trace | `False` |
| `enable_tracing` | Python SDK parameter for AdkApp | `False` |
| `trace_to_cloud` | FastAPI app parameter | `False` |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID for Cloud Trace |
| `GOOGLE_CLOUD_LOCATION` | GCP region |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Custom OTLP endpoint |
| `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` | Custom traces endpoint |

---

## Verification

### View Cloud Traces

1. Navigate to [console.cloud.google.com](https://console.cloud.google.com)
2. Open Trace Explorer in your project
3. Filter by span names: `invocation`, `agent_run`, `call_llm`, `execute_tool`

### View in ADK Web UI

```bash
adk web path/to/agent
```

Use the **Trace** tab to inspect execution flow:
- Hover over trace rows to highlight corresponding messages
- Click traces to see Event, Request, Response, and Graph tabs

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| No traces appearing | Tracer provider not set before ADK import | Configure OpenTelemetry BEFORE importing ADK components |
| Missing spans | File-based MLflow backend | Use SQL backend (SQLite, PostgreSQL, MySQL) |
| Cloud Trace permission denied | Missing IAM roles | Grant `roles/cloudtrace.agent` to service account |
| Spans not exported | Processor not connected | Ensure `add_span_processor()` is called before `set_tracer_provider()` |

---

## References

- [Cloud Trace Documentation](https://cloud.google.com/trace)
- [OpenTelemetry Python SDK](https://opentelemetry.io/docs/languages/python/)
- [MLflow Tracing Documentation](https://mlflow.org/docs/latest/genai/tracing/)
- [AgentOps Documentation](https://www.agentops.ai)
- [Monocle Documentation](https://github.com/monocle2ai/monocle)
- [Weave Documentation](https://weave-docs.wandb.ai/)
- [Arize AX Documentation](https://arize.com/docs/ax)
