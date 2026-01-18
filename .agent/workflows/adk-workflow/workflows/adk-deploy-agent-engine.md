---
description: Deploy ADK agent to Vertex AI Agent Engine for production use
---

# ADK Workflow: Deploy to Vertex AI Agent Engine

Deploy your ADK agent to **Vertex AI Agent Engine** for scalable, managed production use. Agent Engine provides serverless hosting, built-in session management, and full Vertex AI integration.

> [!NOTE]
> Agent Engine currently supports **Python only**.

---

## Prerequisites

- [ ] Google Cloud project with billing enabled
- [ ] `gcloud` CLI installed and authenticated
- [ ] ADK project with properly structured agent folder
- [ ] Google Cloud Storage bucket for staging artifacts

---

## Step 1: Set Up Google Cloud Project

### 1.1 Sign into Google Cloud

```bash
# Sign in and set your project
gcloud auth login
gcloud config set project <your-project-id>
```

### 1.2 Enable Required APIs

```bash
# Enable Vertex AI and related APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
```

### 1.3 Create Staging Bucket

Create a Cloud Storage bucket for staging deployment artifacts:

```bash
# Create bucket (choose a unique name)
gcloud storage buckets create gs://<your-staging-bucket> \
  --location=<your-region>
```

---

## Step 2: Configure Application Default Credentials

Authenticate your coding environment:

```bash
# Set up ADC for local development
gcloud auth application-default login

# Set quota project if needed
gcloud auth application-default set-quota-project <your-project-id>
```

---

## Step 3: Verify Project Structure

Ensure your ADK project follows the required structure:

```
my_agent/
├── __init__.py     # Exports 'root_agent' or 'agent'
├── agent.py        # Agent definition with LlmAgent
└── requirements.txt  # Optional: additional dependencies
```

The `__init__.py` must export the root agent:

```python
# my_agent/__init__.py
from .agent import root_agent

# Or with explicit naming
agent = root_agent
```

---

## Step 4: Deploy with ADK CLI

### Basic Deployment

```bash
adk deploy agent_engine \
  --project=<your-gcp-project-id> \
  --region=<your-gcp-region> \
  --staging_bucket=gs://<your-staging-bucket> \
  my_agent
```

### Deployment with Cloud Tracing

Enable observability with Cloud Trace:

```bash
adk deploy agent_engine \
  --project=<your-gcp-project-id> \
  --region=<your-gcp-region> \
  --staging_bucket=gs://<your-staging-bucket> \
  --trace_to_cloud \
  my_agent
```

### Update Existing Deployment

To update an existing Agent Engine deployment:

```bash
adk deploy agent_engine \
  --project=<your-gcp-project-id> \
  --region=<your-gcp-region> \
  --staging_bucket=gs://<your-staging-bucket> \
  --agent_engine_id=<existing-agent-engine-id> \
  my_agent
```

---

## CLI Options Reference

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `--project` | string | Yes | Google Cloud project ID |
| `--region` | string | Yes | Deployment region (e.g., `us-central1`) |
| `--staging_bucket` | string | Yes | GCS bucket for staging (`gs://...`) |
| `--agent_engine_id` | string | No | Existing Agent Engine ID (for updates) |
| `--trace_to_cloud` | flag | No | Enable Cloud Trace integration |
| `--adk_app` | string | No | Custom app entry point |

---

## Step 5: Query the Deployed Agent

### Using Vertex AI SDK

```python
from vertexai import agent_engines

# Get the deployed agent by resource name
remote_app = agent_engines.get("<your-agent-resource-name>")

# Create a session
session = remote_app.create_session(user_id="user_123")

# Send a message and get response
response = remote_app.stream_query(
    session_id=session.session_id,
    message="Hello, how can you help me?",
)

for chunk in response:
    print(chunk.content, end="")
```

### Using Async API

```python
from vertexai import agent_engines
import asyncio

async def query_agent():
    remote_app = agent_engines.get("<your-agent-resource-name>")
    
    # Create session asynchronously
    session = await remote_app.async_create_session(user_id="user_456")
    
    # Stream response
    async for chunk in remote_app.async_stream_query(
        session_id=session.session_id,
        message="Explain quantum computing",
    ):
        print(chunk.content, end="")

asyncio.run(query_agent())
```

### Using REST API (curl)

```bash
# Get access token
ACCESS_TOKEN=$(gcloud auth print-access-token)

# Query the agent
curl -X POST \
  "https://<region>-aiplatform.googleapis.com/v1beta1/projects/<project>/locations/<region>/agents/<agent-id>:streamQuery" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "<session-id>",
    "message": "Your query here"
  }'
```

---

## Step 6: Session Management

For deployed agents, use `VertexAiSessionService` to manage sessions:

```python
from google.adk.sessions import VertexAiSessionService

# Initialize service
session_service = VertexAiSessionService(
    project="<your-project-id>",
    location="<your-region>",
    agent_engine_id="<your-agent-engine-id>",
)

# Create session
session = await session_service.create_session(
    app_name="my_agent",
    user_id="user_123",
)

# List sessions
sessions = await session_service.list_sessions(
    app_name="my_agent",
    user_id="user_123",
)
```

---

## Verification

After deployment, verify your agent:

```bash
# 1. Check the deployment output for the Agent Engine resource name
# Example: projects/<project>/locations/<region>/agents/<agent-id>

# 2. Test with Python SDK
python -c "
from vertexai import agent_engines
app = agent_engines.get('<your-agent-resource-name>')
print('Agent found:', app)
"

# 3. Or use gcloud to list agents
gcloud ai agent-engines list --location=<your-region>
```

**Expected behavior**: The agent should be listed and respond to queries.

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `Permission denied` | Missing IAM roles | Grant `roles/aiplatform.user` to your account |
| `Bucket not found` | Invalid staging bucket | Verify bucket exists with `gcloud storage ls gs://...` |
| `Module not found` | Missing `__init__.py` | Ensure agent folder has proper exports |
| `API not enabled` | Required API disabled | Run `gcloud services enable aiplatform.googleapis.com` |
| `Quota exceeded` | Project quota limits | Request quota increase in Cloud Console |

---

## Integration Points

- **With Cloud Trace**: Add `--trace_to_cloud` for observability
- **With Session Service**: Use `VertexAiSessionService` for state management
- **With Memory Service**: Configure Vertex AI memory for long-term persistence
- **With Callbacks**: All ADK callbacks work in deployed agents

---

## References

> [!TIP]
> For the most current documentation, consult the official ADK and Vertex AI documentation.

**Documentation Topics:**
- Deploy to Vertex AI Agent Engine (setup, authentication, deployment commands)
- Agent Engine deployment prerequisites and Google Cloud project configuration
- Querying deployed agents using Vertex AI SDK and REST API
- VertexAiSessionService for production session management
- Cloud Trace integration for Agent Engine deployments
- Agent Starter Pack (ASP) alternative deployment method

**Code References:**
- ADK CLI `deploy agent_engine` command implementation
- `to_agent_engine()` deployment function with all parameters
- VertexAiSessionService class for remote session management
