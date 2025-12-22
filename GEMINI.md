# Repository Guidelines

This repository provides **ADK workflow templates** for building agentic systems with Google Agent Development Kit (ADK). The RAG pipeline grounds workflow creation in official ADK documentation and source code.

## Project Structure

```
.agent/workflows/     # 44 ADK workflow templates (adk-*.md)
src/grounding/        # RAG pipeline (Qdrant + Voyage embeddings)
corpora/              # Ingested ADK docs and Python source
config/               # Settings and environment config
```

## ADK Workflow System

**Entry Point**: Always start with [adk-master.md](.agent/workflows/adk-master.md) to route to the appropriate workflow.

**Development Pattern**:
1. Invoke the relevant workflow(s) from `adk-master`
2. Chain multiple workflows if the task spans categories (e.g., init → agents → tools → deploy)
3. Conduct additional RAG queries as needed for implementation details

| Category | Prefix | Example Workflows |
|----------|--------|-------------------|
| Foundation | `adk-init` | `adk-init`, `adk-init-create-project`, `adk-init-yaml-config` |
| Agents | `adk-agents` | `adk-agents-create`, `adk-agents-custom`, `adk-agents-multi-model` |
| Tools | `adk-tools` | `adk-tools-function`, `adk-tools-mcp`, `adk-tools-openapi` |
| Behavior | `adk-behavior` | `adk-behavior-callbacks`, `adk-behavior-state`, `adk-behavior-plugins` |
| Multi-Agent | `adk-multi-agent` | `adk-multi-agent-delegation`, `adk-multi-agent-orchestration` |
| Memory | `adk-memory` | `adk-memory-service`, `adk-memory-grounding` |
| Security | `adk-security` | `adk-security-guardrails`, `adk-security-auth` |
| Streaming | `adk-streaming` | `adk-streaming-sse`, `adk-streaming-bidi`, `adk-streaming-multimodal` |
| Deployment | `adk-deploy` | `adk-deploy-agent-engine`, `adk-deploy-cloudrun`, `adk-deploy-gke` |
| Quality | `adk-quality` | `adk-quality-evals`, `adk-quality-tracing`, `adk-quality-observability` |

### Creating New Workflows

Use `/adk-create-workflow` to generate new workflows via RAG-grounded research against the ADK corpus.

## Querying the RAG Pipeline

Query results return a balanced mix of **adk_docs** (official documentation) and **adk_python** (source code examples).

```bash
# Basic query
python -m src.grounding.query.query_adk "your query" --top-k 12

# With verbose timing breakdown
python -m src.grounding.query.query_adk "your query" --verbose

# Multi-query expansion for better recall
python -m src.grounding.query.query_adk "your query" --multi-query --verbose

# Filter by corpus (adk_docs or adk_python)
python -m src.grounding.query.query_adk "your query" --corpus adk_python
```

**Python usage:**
```python
from src.grounding.query.query_adk import search_adk
results = search_adk("how to use ToolContext", top_k=12)
```

## Build & Test Commands

```bash
pip install -e .              # Install package in dev mode
pytest tests/                 # Run test suite
python -m src.grounding.scripts.03_ingest_corpus  # Re-ingest corpora
```

## Coding Style

- Python 3.11+, PEP 8
- Type hints required
- Docstrings: Google style
- Linting: `ruff`
