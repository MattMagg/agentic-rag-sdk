---
name: adk-init
description: Initialize a new ADK project with intelligent authentication detection
argument-hint: Optional project name
allowed-tools: ["Read", "Write", "Bash", "Glob", "Grep", "AskUserQuestion"]
---

# Initialize ADK Project

Initialize a new Google ADK project with proper structure, dependencies, and authentication.

## Decision Logic

**Step 1: Check for existing ADK project**

```bash
# Check for existing agent.py or pyproject.toml with google-adk
```

If exists: Ask user if they want to reinitialize or abort.

**Step 2: Detect GCP environment**

Check for:
- `GOOGLE_CLOUD_PROJECT` environment variable
- `~/.config/gcloud/application_default_credentials.json`
- Existing `.env` with Vertex AI config

**Step 3: Recommend authentication method**

If GCP detected:
> "I detected GCP credentials. I recommend **Vertex AI** authentication for production-ready setup with access to all Vertex AI services.
>
> Alternatively, use **Google AI Studio** (API key) for simpler setup.
>
> Which would you prefer?"

If no GCP:
> "I recommend **Google AI Studio** (API key) for the quickest setup.
>
> Get your API key at: https://aistudio.google.com/apikey
>
> Or configure **Vertex AI** if you have a GCP project.
>
> Which would you prefer?"

**Step 4: Execute initialization**

Based on selection, follow the appropriate path from `@adk-getting-started` skill.

1. Create virtual environment (if not exists)
2. Install google-adk
3. Create `.env` with selected auth method
4. Scaffold project with `adk create` or create manually
5. Verify with `adk --version` and test run

**Step 5: Verify success**

```bash
adk --version
adk run <project_name>  # Quick test
```

## Usage Examples

```
/adk-init                    # Interactive, detects best auth
/adk-init my_agent          # Create project named my_agent
```

## References

Load `@adk-getting-started` skill for detailed initialization guidance.
