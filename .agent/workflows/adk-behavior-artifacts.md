---
description: Save and load binary data/files as artifacts in ADK agents
---

# ADK Workflow: Artifacts

Artifacts provide a mechanism for ADK agents to save, load, and manage binary data (files) tied to sessions or users. Use artifacts for file outputs, processed documents, generated images, and persistent binary data.

---

## Prerequisites

- [ ] ADK project initialized (`adk init` or manual setup)
- [ ] Artifact service configured in `Runner`
- [ ] Imports ready:

```python
from google.adk.runners import Runner
from google.adk.agents import LlmAgent
from google.adk.artifacts import (
    InMemoryArtifactService,
    FileArtifactService,
    GcsArtifactService,
)
from google import genai
```

---

## Step 1: Configure an Artifact Service

Choose the appropriate artifact service implementation for your use case:

| Service | Use Case | Persistence |
|---------|----------|-------------|
| `InMemoryArtifactService` | Testing, prototyping | None (memory only) |
| `FileArtifactService` | Local development | Local filesystem |
| `GcsArtifactService` | Production, cloud | Google Cloud Storage |

### InMemoryArtifactService (Testing)

```python
from google.adk.artifacts import InMemoryArtifactService

artifact_service = InMemoryArtifactService()
```

### FileArtifactService (Local Storage)

```python
from google.adk.artifacts import FileArtifactService

artifact_service = FileArtifactService(base_path="./artifacts")
```

### GcsArtifactService (Cloud Storage)

```python
from google.adk.artifacts import GcsArtifactService

artifact_service = GcsArtifactService(bucket_name="my-artifacts-bucket")
```

---

## Step 2: Attach Artifact Service to Runner

```python
runner = Runner(
    agent=my_agent,
    app_name="my_app",
    artifact_service=artifact_service,  # Required for artifacts
    session_service=session_service,
)
```

---

## Step 3: Save Artifacts

Access artifact methods via `ToolContext` (in tools) or `CallbackContext` (in callbacks).

### From a Tool (ToolContext)

```python
from google.adk.tools import FunctionTool, ToolContext
from google import genai

async def generate_report(topic: str, tool_context: ToolContext) -> dict:
    """Generate and save a report as an artifact."""
    
    # Create report content
    report_content = f"# Report on {topic}\n\nGenerated report content..."
    report_bytes = report_content.encode("utf-8")
    
    # Create Part object with inline_data
    artifact = genai.types.Part(
        inline_data=genai.types.Blob(
            mime_type="text/markdown",
            data=report_bytes,
        )
    )
    
    # Save artifact - returns version number
    version = await tool_context.save_artifact(
        filename=f"report_{topic}.md",
        artifact=artifact,
    )
    
    return {"status": "saved", "filename": f"report_{topic}.md", "version": version}

generate_report_tool = FunctionTool(generate_report)
```

### From a Callback (CallbackContext)

```python
from google.adk.agents import CallbackContext
from google import genai

async def after_agent_callback(callback_context: CallbackContext):
    """Save summary after agent completes."""
    
    summary_data = b"Agent completed successfully"
    artifact = genai.types.Part(
        inline_data=genai.types.Blob(
            mime_type="text/plain",
            data=summary_data,
        )
    )
    
    version = await callback_context.save_artifact(
        filename="session_summary.txt",
        artifact=artifact,
    )
    print(f"Saved summary as version {version}")
```

---

## Step 4: Load Artifacts

### Load Latest Version

```python
async def read_report(filename: str, tool_context: ToolContext) -> dict:
    """Load an artifact by filename."""
    
    artifact = await tool_context.load_artifact(filename=filename)
    
    if artifact is None:
        return {"error": f"Artifact '{filename}' not found"}
    
    # Access the data
    if artifact.inline_data:
        content = artifact.inline_data.data.decode("utf-8")
        mime_type = artifact.inline_data.mime_type
        return {"content": content, "mime_type": mime_type}
    
    return {"error": "Artifact has no inline data"}
```

### Load Specific Version

```python
# Load a specific version (0-indexed)
artifact = await tool_context.load_artifact(filename="report.md", version=0)
```

---

## Step 5: List and Manage Artifacts

### List All Artifacts

```python
async def list_all_artifacts(tool_context: ToolContext) -> dict:
    """List all artifacts in the session."""
    
    filenames = await tool_context.list_artifacts()
    return {"artifacts": filenames}
```

### List Artifact Versions

```python
async def list_versions(filename: str, tool_context: ToolContext) -> dict:
    """List all versions of a specific artifact."""
    
    versions = await tool_context.list_artifact_versions(filename=filename)
    return {
        "filename": filename,
        "versions": [
            {"version": v.version_number, "timestamp": str(v.timestamp)}
            for v in versions
        ]
    }
```

### Delete Artifact

```python
async def delete_artifact(filename: str, tool_context: ToolContext) -> dict:
    """Delete an artifact and all its versions."""
    
    await tool_context.delete_artifact(filename=filename)
    return {"deleted": filename}
```

---

## Artifact Scoping

Artifacts can be scoped to either the **session** or the **user**:

| Scope | Accessible By | Use Case |
|-------|---------------|----------|
| Session | Same session only | Conversation-specific files |
| User | Any session for user | Persistent user documents |

### Session-Scoped (Default)

```python
# Accessible only within the current session
await tool_context.save_artifact(filename="session_file.txt", artifact=part)
```

### User-Scoped

```python
# Configure via Artifact Service - accessible across all user sessions
# User scoping is controlled at the service level via app_name + user_id
```

---

## Artifact Data Format

Artifacts use `google.genai.types.Part` for content representation:

```python
from google import genai

# Text/Binary via inline_data (Blob)
artifact = genai.types.Part(
    inline_data=genai.types.Blob(
        mime_type="application/pdf",
        data=pdf_bytes,
    )
)

# Common MIME types:
# - text/plain, text/markdown, text/html
# - application/json, application/pdf
# - image/png, image/jpeg, image/webp
# - audio/mp3, audio/wav
# - application/octet-stream (generic binary)
```

---

## SaveFilesAsArtifactsPlugin

Automatically save files uploaded by users as artifacts:

```python
from google.adk.plugins import SaveFilesAsArtifactsPlugin

# Add to agent plugins
agent = LlmAgent(
    name="document_processor",
    model="gemini-2.0-flash",
    instruction="Process uploaded documents.",
    plugins=[SaveFilesAsArtifactsPlugin()],
)
```

When a user uploads a file, it is automatically saved as an artifact and replaced with a placeholder in the message.

---

## Verification

```bash
adk run agent_folder
```

1. Send a message that triggers artifact creation
2. Check runner output for artifact save confirmation
3. Verify artifact retrieval in subsequent tool calls
4. For `FileArtifactService`, check the `base_path` directory

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `artifact_service not available` | No service configured in Runner | Add `artifact_service=` to Runner |
| `Artifact not found` | Wrong filename or session | Verify filename, check session scope |
| `Permission denied` (GCS) | Missing credentials | Configure GCP auth, check bucket permissions |
| Version returns -1 | Save failed | Check artifact service logs |

---

## Best Practices

- **Choose the right service**: Use `InMemoryArtifactService` for testing, `FileArtifactService` for local dev, `GcsArtifactService` for production
- **Use meaningful filenames**: Include context like timestamps or topic names
- **Set proper MIME types**: Enables correct handling/display of artifacts
- **Handle missing artifacts gracefully**: Always check for `None` return values
- **Consider versioning**: Each save creates a new version, load supports version parameter
