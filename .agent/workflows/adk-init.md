---
description: Initialize new ADK project with proper structure and dependencies
---

# ADK Workflow: Project Initialization

Bootstrap a new Google ADK (Agent Development Kit) project with proper structure, dependencies, and environment configuration.

---

## Scope

This parent workflow routes to child workflows based on your needs:

| Task | Child Workflow |
|------|----------------|
| Scaffold Python project with `adk create` | `/adk-init-create-project` |
| Configure agent via YAML (no-code) | `/adk-init-yaml-config` |

---

## Prerequisites

Before starting any ADK project:

- [ ] **Python 3.10+** installed (Python 3.11+ recommended for best performance)
- [ ] **Virtual environment** created and activated
- [ ] **ADK installed** via `pip install google-adk`
- [ ] **Authentication configured** (API key or GCP credentials)

---

## Step 1: Verify Installation

Confirm ADK is properly installed:

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate.bat  # Windows CMD
# .venv\Scripts\Activate.ps1  # Windows PowerShell

# Install ADK
pip install google-adk

# Verify installation
adk --version
pip show google-adk
```

---

## Step 2: Choose Project Type

| Approach | When to Use | Workflow |
|----------|-------------|----------|
| **Python Code** | Full flexibility, custom tools, advanced patterns | `/adk-init-create-project` |
| **YAML Config** | Quick setup, no-code agents, declarative definition | `/adk-init-yaml-config` |

---

## Step 3: Configure Authentication

Choose your platform and set environment variables in `.env`:

### Option A: Google AI Studio (Simplest)

```env
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
```

Get API key from: https://aistudio.google.com/apikey

### Option B: Google Cloud Vertex AI

```env
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GOOGLE_CLOUD_LOCATION=us-central1
```

Also run:
```bash
gcloud auth application-default login
```

### Option C: Vertex AI Express Mode

```env
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_API_KEY=YOUR_EXPRESS_MODE_API_KEY
```

---

## Step 4: Run Local Development

Once your project is created, test it:

```bash
# Navigate to parent directory of your agent folder
cd parent_folder/

# Interactive browser UI (recommended for development)
adk web

# Terminal CLI interaction
adk run my_agent

# Local FastAPI server (for testing API calls)
adk api_server
```

**Dev UI access:** http://localhost:8000

---

## Verification

- [ ] `adk --version` returns installed version
- [ ] Agent folder contains `agent.py`, `__init__.py`, `.env`
- [ ] `adk run my_agent` starts without authentication errors
- [ ] `adk web` opens dev UI at http://localhost:8000
- [ ] Agent responds to test prompts

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `adk` command not found | Virtual env not active | Run `source .venv/bin/activate` |
| Agent not in dropdown | Wrong directory | Run `adk web` from parent of agent folder |
| 401 Unauthorized | Missing/invalid API key | Check `.env` file, verify key is valid |
| 429 RESOURCE_EXHAUSTED | Rate limit exceeded | Add retry options or request quota increase |
| Windows `NotImplementedError` | Reload issue | Use `adk web --no-reload` |

---

## References

- [ADK Quickstart](https://google.github.io/adk-docs/get-started/quickstart/)
- [Python Quickstart](https://google.github.io/adk-docs/get-started/python/)
- [Installation Guide](https://google.github.io/adk-docs/get-started/installation/)
- [Models & Authentication](https://google.github.io/adk-docs/agents/models/)

---

## Next Workflows

After initialization:
- `/adk-agents-create` — Create LlmAgent with model, name, instructions
- `/adk-tools-function` — Add FunctionTool capabilities
- `/adk-behavior-state` — Configure session state
