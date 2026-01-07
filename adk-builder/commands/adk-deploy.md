---
name: adk-deploy
description: Deploy an ADK agent to production with intelligent platform selection
argument-hint: Optional target (agent-engine, cloudrun, gke)
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Deploy ADK Agent

Deploy an agent to production with intelligent platform selection.

## Decision Logic

**Step 1: Analyze project**

Check for:
- Dockerfile (suggests Cloud Run/GKE preference)
- Vertex AI dependencies (suggests Agent Engine)
- GCP project configuration

**Step 2: Recommend platform**

> "I recommend **Agent Engine** for deployment because:
>
> - Managed hosting with auto-scaling
> - Built-in session management
> - Integrated Vertex AI services (Search, Memory)
> - No infrastructure to manage
>
> Alternatives:
> - **Cloud Run** - More container control
> - **GKE** - Full Kubernetes for enterprise
>
> Proceed with Agent Engine?"

**Step 3: Execute deployment**

Based on selection, follow deployment steps from `@adk-deployment` skill.

For Agent Engine:
```bash
adk deploy --project=PROJECT_ID --region=us-central1
```

**Step 4: Verify**

Confirm deployment successful and provide endpoint URL.

## Usage Examples

```
/adk-deploy                    # Interactive, recommends Agent Engine
/adk-deploy agent-engine      # Direct to Agent Engine
/adk-deploy cloudrun          # Direct to Cloud Run
```

## References

Load `@adk-deployment` skill for detailed deployment guides.
