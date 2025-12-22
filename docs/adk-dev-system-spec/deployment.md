# Deployment

Deploy the ADK Development System to Vertex AI Agent Engine.

> **Run the `/adk-deploy-agent-engine` workflow** for complete deployment instructions.

---

## Prerequisites

- [ ] Google Cloud project with billing enabled
- [ ] Required APIs enabled
- [ ] Staging bucket created
- [ ] Environment configured (see [configuration.md](./configuration.md))

### Enable APIs

```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
```

### Create Staging Bucket

```bash
gcloud storage buckets create gs://${ADK_STAGING_BUCKET} \
  --location=${GOOGLE_CLOUD_LOCATION}
```

### Authenticate

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project ${GOOGLE_CLOUD_PROJECT}
```

---

## Deploy

### Basic Deployment

```bash
adk deploy agent_engine \
  --project=${GOOGLE_CLOUD_PROJECT} \
  --region=${GOOGLE_CLOUD_LOCATION} \
  --staging_bucket=${ADK_STAGING_BUCKET} \
  adk_dev_system
```

### With Cloud Tracing

> **Run the `/adk-quality-tracing` workflow** to understand tracing options.

```bash
adk deploy agent_engine \
  --project=${GOOGLE_CLOUD_PROJECT} \
  --region=${GOOGLE_CLOUD_LOCATION} \
  --staging_bucket=${ADK_STAGING_BUCKET} \
  --trace_to_cloud \
  adk_dev_system
```

---

## Verify Deployment

### List Deployed Agents

```bash
gcloud ai agent-engines list --location=${GOOGLE_CLOUD_LOCATION}
```

### Query via Python SDK

```python
from vertexai import agent_engines

# Get deployed agent
remote_app = agent_engines.get("<your-agent-resource-name>")

# Create session
session = remote_app.create_session(user_id="test_user")

# Query
response = remote_app.stream_query(
    session_id=session.session_id,
    message="Create a weather agent with google_search grounding"
)

for chunk in response:
    print(chunk.content, end="")
```

---

## Update Existing Deployment

```bash
adk deploy agent_engine \
  --project=${GOOGLE_CLOUD_PROJECT} \
  --region=${GOOGLE_CLOUD_LOCATION} \
  --staging_bucket=${ADK_STAGING_BUCKET} \
  --agent_engine_id=<existing-agent-engine-id> \
  adk_dev_system
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Permission denied` | Grant `roles/aiplatform.user` to your account |
| `Bucket not found` | Verify bucket: `gcloud storage ls gs://${ADK_STAGING_BUCKET}` |
| `Module not found` | Ensure `__init__.py` exports `root_agent` or `agent` |
| `API not enabled` | Run `gcloud services enable aiplatform.googleapis.com` |
