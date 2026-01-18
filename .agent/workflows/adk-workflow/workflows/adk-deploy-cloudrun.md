---
description: Deploy ADK agents to Cloud Run using adk CLI or gcloud CLI
---

# ADK Workflow: Deploy to Cloud Run

Deploy your ADK agent to Cloud Run for fully managed, auto-scaling serverless execution.

---

## Prerequisites

- [ ] Google Cloud project created with billing enabled
- [ ] `gcloud` CLI installed and authenticated (`gcloud auth login`)
- [ ] Project configured: `gcloud config set project <your-project-id>`
- [ ] ADK installed: `pip install google-adk`

### Required APIs

Enable the necessary APIs:

```bash
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    aiplatform.googleapis.com
```

### Environment Variables

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
export GOOGLE_GENAI_USE_VERTEXAI=True
```

---

## Step 1: Prepare Agent Code Structure

Organize your agent directory:

```
capital_agent/
├── __init__.py      # Contains: from . import agent
├── agent.py         # Your agent code with root_agent variable
└── requirements.txt # Dependencies including google-adk
```

**Critical Requirements:**
- Agent variable must be named `root_agent`
- `__init__.py` must import the agent module

---

## Step 2: Deploy Using ADK CLI (Recommended)

### Minimal Deployment

```bash
adk deploy cloud_run \
    --project=$GOOGLE_CLOUD_PROJECT \
    --region=$GOOGLE_CLOUD_LOCATION \
    ./capital_agent
```

### Full Deployment with Options

```bash
adk deploy cloud_run \
    --project=$GOOGLE_CLOUD_PROJECT \
    --region=$GOOGLE_CLOUD_LOCATION \
    --service_name=my-agent-service \
    --app_name=my-agent \
    --with_ui \
    --port=8000 \
    ./capital_agent
```

---

## Step 3: Alternative - Deploy Using gcloud CLI

For custom FastAPI applications or more control:

### 3a. Create FastAPI Entry Point

```python
# main.py
import os
import uvicorn
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app

AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_SERVICE_URI = "sqlite+aiosqlite:///./sessions.db"
ALLOWED_ORIGINS = ["http://localhost", "http://localhost:8080", "*"]
SERVE_WEB_INTERFACE = True

app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    session_service_uri=SESSION_SERVICE_URI,
    allow_origins=ALLOWED_ORIGINS,
    web=SERVE_WEB_INTERFACE,
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
```

### 3b. Create Dockerfile

```dockerfile
FROM python:3.13-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN adduser --disabled-password --gecos "" myuser && \
    chown -R myuser:myuser /app

COPY . .

USER myuser

ENV PATH="/home/myuser/.local/bin:$PATH"

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
```

### 3c. Deploy with gcloud

```bash
gcloud run deploy my-agent-service \
    --source . \
    --region=$GOOGLE_CLOUD_LOCATION \
    --project=$GOOGLE_CLOUD_PROJECT \
    --allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION,GOOGLE_GENAI_USE_VERTEXAI=$GOOGLE_GENAI_USE_VERTEXAI"
```

---

## Configuration Options

### ADK CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--project` | Google Cloud project ID | Required |
| `--region` | Deployment region | Required |
| `--service_name` | Cloud Run service name | `adk-default-service-name` |
| `--app_name` | Application name | Agent directory name |
| `--port` | Container port | `8000` |
| `--with_ui` | Deploy ADK dev UI | Disabled |
| `--agent_engine_id` | Vertex AI Agent Engine ID for sessions | None |

### Authentication Options

During deployment you'll be prompted:
- **`y`**: Allow unauthenticated (public) access
- **`N`**: Require authentication via identity tokens

---

## Secrets Management

### Store API Key in Secret Manager

```bash
# Create secret
echo "your-api-key" | gcloud secrets create GOOGLE_API_KEY \
    --project=$GOOGLE_CLOUD_PROJECT \
    --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding GOOGLE_API_KEY \
    --member="serviceAccount:$PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --project=$GOOGLE_CLOUD_PROJECT
```

---

## Verification

### Test Deployed Agent

```bash
# Set service URL
export APP_URL="https://your-service-name-abc123.a.run.app"

# Get identity token (for authenticated services)
export TOKEN=$(gcloud auth print-identity-token)

# List apps
curl -X GET -H "Authorization: Bearer $TOKEN" $APP_URL/list-apps

# Run agent
curl -X POST -H "Authorization: Bearer $TOKEN" \
    $APP_URL/run_sse \
    -H "Content-Type: application/json" \
    -d '{
      "app_name": "capital_agent",
      "user_id": "user_123",
      "session_id": "session_abc",
      "new_message": {
        "role": "user",
        "parts": [{"text": "What is the capital of Canada?"}]
      },
      "streaming": false
    }'
```

### UI Testing

If deployed with `--with_ui`, navigate to the Cloud Run service URL in your browser.

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| 403 Permission Denied | Missing Vertex AI permissions | Ensure service account has `roles/aiplatform.user` |
| 401 Unauthorized | Missing identity token | Run `gcloud auth print-identity-token` |
| 404 Not Found | Invalid endpoint or app name | Check `/list-apps` for available apps |
| Connection refused | Wrong port configuration | Verify PORT environment variable |

---

## Multi-Agent Deployment

Deploy multiple agents in a single Cloud Run instance:

```
your-project/
├── capital_agent/
│   ├── __init__.py
│   └── agent.py       # root_agent definition
├── weather_agent/
│   ├── __init__.py
│   └── agent.py       # root_agent definition
├── main.py
├── requirements.txt
└── Dockerfile
```

Each agent folder with a `root_agent` is automatically discovered.

---

## References

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [ADK Deploy Reference](https://google.github.io/adk-docs/deploy/cloud-run/)
- [gcloud run deploy Reference](https://cloud.google.com/sdk/gcloud/reference/run/deploy)
