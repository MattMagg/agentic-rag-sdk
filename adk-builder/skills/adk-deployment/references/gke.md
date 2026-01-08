---
description: Deploy ADK agents to Google Kubernetes Engine (GKE) with adk CLI or kubectl
---

# ADK Workflow: Deploy to GKE

Deploy your ADK agent to Google Kubernetes Engine for container orchestration with full Kubernetes control.

---

## Prerequisites

- [ ] Google Cloud project with billing enabled
- [ ] `gcloud` CLI installed and authenticated
- [ ] `kubectl` CLI installed ([installation guide](https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-access-for-kubectl))
- [ ] ADK installed: `pip install google-adk`

### Enable Required APIs

```bash
gcloud services enable \
    container.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    aiplatform.googleapis.com
```

### Environment Variables

```bash
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="us-central1"
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT_NUMBER=$(gcloud projects describe --format json $GOOGLE_CLOUD_PROJECT | jq -r ".projectNumber")
```

---

## Option 1: Automated Deployment with ADK CLI

### Step 1: Create GKE Cluster (if needed)

```bash
gcloud container clusters create-auto adk-cluster \
    --location=$GOOGLE_CLOUD_LOCATION \
    --project=$GOOGLE_CLOUD_PROJECT

# Get cluster credentials
gcloud container clusters get-credentials adk-cluster \
    --location=$GOOGLE_CLOUD_LOCATION \
    --project=$GOOGLE_CLOUD_PROJECT
```

### Step 2: Deploy with ADK CLI

```bash
adk deploy gke \
    --project=$GOOGLE_CLOUD_PROJECT \
    --cluster_name=adk-cluster \
    --region=$GOOGLE_CLOUD_LOCATION \
    --with_ui \
    --log_level=info \
    ./capital_agent
```

### ADK CLI Options

| Option | Description | Required |
|--------|-------------|----------|
| `--project` | Google Cloud project ID | Yes |
| `--cluster_name` | GKE cluster name | Yes |
| `--region` | Cluster region | Yes |
| `--with_ui` | Deploy ADK dev UI | No |
| `--log_level` | Logging level (debug/info/warning/error) | No |

---

## Option 2: Manual Deployment with kubectl

### Step 1: Prepare Agent Code Structure

```
your-project/
├── capital_agent/
│   ├── __init__.py
│   └── agent.py
├── main.py
├── requirements.txt
└── Dockerfile
```

### Step 2: Create FastAPI Entry Point

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

### Step 3: Create Dockerfile

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

### Step 4: Build and Push Container Image

```bash
# Create Artifact Registry repository
gcloud artifacts repositories create adk-repo \
    --repository-format=docker \
    --location=$GOOGLE_CLOUD_LOCATION \
    --description="ADK repository"

# Build and push image
gcloud builds submit \
    --tag $GOOGLE_CLOUD_LOCATION-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/adk-repo/adk-agent:latest \
    --project=$GOOGLE_CLOUD_PROJECT \
    .
```

### Step 5: Configure Kubernetes Service Account

Required for Vertex AI access:

```bash
kubectl create serviceaccount adk-agent-sa

gcloud projects add-iam-policy-binding projects/${GOOGLE_CLOUD_PROJECT} \
    --role=roles/aiplatform.user \
    --member=principal://iam.googleapis.com/projects/${GOOGLE_CLOUD_PROJECT_NUMBER}/locations/global/workloadIdentityPools/${GOOGLE_CLOUD_PROJECT}.svc.id.goog/subject/ns/default/sa/adk-agent-sa \
    --condition=None
```

### Step 6: Create Kubernetes Manifests

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: adk-agent
spec:
  replicas: 1
  selector:
    matchLabels:
      app: adk-agent
  template:
    metadata:
      labels:
        app: adk-agent
    spec:
      serviceAccount: adk-agent-sa
      containers:
      - name: adk-agent
        imagePullPolicy: Always
        image: $GOOGLE_CLOUD_LOCATION-docker.pkg.dev/$GOOGLE_CLOUD_PROJECT/adk-repo/adk-agent:latest
        resources:
          limits:
            memory: "128Mi"
            cpu: "500m"
          requests:
            memory: "128Mi"
            cpu: "500m"
        ports:
        - containerPort: 8080
        env:
          - name: PORT
            value: "8080"
          - name: GOOGLE_CLOUD_PROJECT
            value: $GOOGLE_CLOUD_PROJECT
          - name: GOOGLE_CLOUD_LOCATION
            value: $GOOGLE_CLOUD_LOCATION
          - name: GOOGLE_GENAI_USE_VERTEXAI
            value: "true"
---
apiVersion: v1
kind: Service
metadata:
  name: adk-agent
spec:       
  type: LoadBalancer
  ports:
    - port: 80
      targetPort: 8080
  selector:
    app: adk-agent
```

### Step 7: Deploy to Cluster

```bash
kubectl apply -f deployment.yaml
```

---

## Verification

### Check Deployment Status

```bash
# Check pods are running
kubectl get pods -l=app=adk-agent

# Check service has external IP
kubectl get service adk-agent

# Get external IP
export APP_URL=$(kubectl get service adk-agent -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
```

### Test the Agent

```bash
# List apps
curl -X GET http://$APP_URL/list-apps

# Run agent
curl -X POST http://$APP_URL/run_sse \
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

### Check Logs

```bash
kubectl logs -l app=adk-agent
```

---

## IAM Permissions

### For Cloud Build (manual deployment)

Grant to default compute service account:

```bash
ROLES_TO_ASSIGN=(
    "roles/artifactregistry.writer"
    "roles/storage.objectViewer"
    "roles/logging.viewer"
    "roles/logging.logWriter"
)

for ROLE in "${ROLES_TO_ASSIGN[@]}"; do
    gcloud projects add-iam-policy-binding "${GOOGLE_CLOUD_PROJECT}" \
        --member="serviceAccount:${GOOGLE_CLOUD_PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
        --role="${ROLE}"
done
```

### For ADK CLI Deployment

Required roles for the user or service account:

| Role | Purpose |
|------|---------|
| `roles/container.developer` | Interact with GKE cluster |
| `roles/storage.objectViewer` | Download source from Cloud Storage |
| `roles/artifactregistry.createOnPushWriter` | Push container images |
| `roles/logging.logWriter` | Write build logs |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| 403 Permission Denied for Gemini | Missing Vertex AI permissions | Create service account with `roles/aiplatform.user` |
| Pods not starting | Image pull error | Check Artifact Registry permissions and image path |
| No external IP | LoadBalancer pending | Wait a few minutes for IP allocation |
| Readonly database error | SQLite copied into container | Add `sessions.db` to `.dockerignore` |
| Websocket failures for voice | Model doesn't support Live API | Use a Live API compatible model |

---

## Cleanup

```bash
# Delete deployment
kubectl delete -f deployment.yaml

# Delete cluster
gcloud container clusters delete adk-cluster \
    --location=$GOOGLE_CLOUD_LOCATION \
    --project=$GOOGLE_CLOUD_PROJECT

# Delete Artifact Registry repository
gcloud artifacts repositories delete adk-repo \
    --location=$GOOGLE_CLOUD_LOCATION \
    --project=$GOOGLE_CLOUD_PROJECT
```

---

## References

- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [ADK GKE Deploy Reference](https://google.github.io/adk-docs/deploy/gke/)
- [Workload Identity Configuration](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity)
