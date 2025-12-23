---
description: Query the ADK RAG database for grounding information
---

# RAG Query Workflow

Query the ADK grounding database for documentation and code examples.

---

## CLI Usage

```bash
# Activate venv first
source .venv/bin/activate

# Basic query (12 results)
python -m src.grounding.query.query_adk "your query" --top-k 12

# Verbose output with timing breakdown
python -m src.grounding.query.query_adk "your query" --verbose

# Multi-query expansion (better recall, slower)
python -m src.grounding.query.query_adk "your query" --multi-query --verbose

# Filter by corpus
python -m src.grounding.query.query_adk "your query" --corpus adk_docs
python -m src.grounding.query.query_adk "your query" --corpus adk_python
python -m src.grounding.query.query_adk "your query" --corpus agent_dev_docs
```

---

## Python Usage

```python
from src.grounding.query.query_adk import search_adk

# Basic search
results = search_adk("how to use ToolContext", top_k=12)

# With options
results = search_adk(
    query="callbacks in ADK",
    top_k=12,
    mode="build",           # build, debug, explain, refactor
    multi_query=True,       # Enable query expansion
    verbose=True            # Print timing breakdown
)

# Access results
for r in results["results"]:
    print(f"{r['corpus']} | {r['path']}")
    print(r['text'][:200])
```

---

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--top-k` | 12 | Number of results |
| `--mode` | build | Retrieval mode: build, debug, explain, refactor |
| `--multi-query` | off | Enable query expansion (slower, +15% recall) |
| `--corpus` | all | Filter by corpus (see below) |
| `--verbose` | off | Show timing breakdown |
| `--no-rerank` | off | Disable VoyageAI reranking |

---

## Corpora

| Corpus | Description |
|--------|-------------|
| `adk_docs` | Official ADK documentation (guides, API ref) |
| `adk_python` | ADK Python source code (src/, tests/) |
| `agent_dev_docs` | Agent development PDFs & notebook examples |

---

## Pipeline

1. **Query Expansion** (optional) — Generate variations
2. **Hybrid Search** — Dense docs + dense code + sparse (RRF fusion)
3. **Candidate Balancing** — Ensure docs/code mix before rerank
4. **VoyageAI Rerank** — Cross-encoder refinement  
5. **Coverage Gates** — Enforce minimum docs/code in output
