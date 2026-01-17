---
description: Query the RAG database for grounding information (supports Google ADK, OpenAI Agents SDK, LangChain/LangGraph, and general agent docs)
---

# RAG Query Tool

Query the grounding database for documentation and code examples. Use `--sdk` to isolate queries to a specific SDK.

---

## SDK-based Filtering (Recommended)

```bash
source .venv/bin/activate

# Query Google ADK only
python -m src.grounding.query.query_adk "how to use ToolContext" --sdk adk

# Query OpenAI Agents SDK only
python -m src.grounding.query.query_adk "how to create handoffs" --sdk openai

# Query LangChain ecosystem (includes LangGraph + DeepAgents)
python -m src.grounding.query.query_adk "ChatOpenAI model" --sdk langchain

# Query LangGraph-specific (includes DeepAgents)
python -m src.grounding.query.query_adk "StateGraph checkpoint" --sdk langgraph

# Query general agent development docs
python -m src.grounding.query.query_adk "agent architectures" --sdk general
```

### SDK Groups

| Flag | Corpora Included |
|------|------------------|
| `--sdk adk` | `adk_docs`, `adk_python` |
| `--sdk openai` | `openai_agents_docs`, `openai_agents_python` |
| `--sdk langchain` | `langgraph_python`, `langchain_python`, `deepagents_python`, `deepagents_docs` |
| `--sdk langgraph` | `langgraph_python`, `deepagents_python`, `deepagents_docs` |
| `--sdk general` | `agent_dev_docs` |

---

## Additional Options

```bash
# Verbose output with timing
python -m src.grounding.query.query_adk "your query" --sdk adk --verbose

# Multi-query expansion (better recall, slower)
python -m src.grounding.query.query_adk "your query" --sdk adk --multi-query

# Filter by specific corpus (multiple allowed)
python -m src.grounding.query.query_adk "your query" --corpus adk_docs --corpus adk_python
```

---

## Python Usage

```python
from src.grounding.query.query_adk import search_adk, SDK_GROUPS

# Query with SDK filter
results = search_adk(
    query="how to use ToolContext",
    top_k=12,
    filters={"corpus": SDK_GROUPS["adk"]}
)

# Access results
for r in results["results"]:
    print(f"{r['corpus']} | {r['path']}")
    print(r['text'][:200])
```

---

## Options Reference

| Flag | Default | Description |
|------|---------|-------------|
| `--sdk` | none | SDK group: `adk`, `openai`, `langchain`, `langgraph`, `general` |
| `--corpus` | all | Filter by specific corpus (repeatable) |
| `--top-k` | 12 | Number of results |
| `--mode` | build | Retrieval mode: build, debug, explain, refactor |
| `--multi-query` | off | Enable query expansion (+15% recall, slower) |
| `--verbose` | off | Show timing breakdown |
| `--no-rerank` | off | Disable VoyageAI reranking |

---

## All Corpora

| Corpus | SDK | Type | Description |
|--------|-----|------|-------------|
| `adk_docs` | adk | doc | Official ADK documentation |
| `adk_python` | adk | code | ADK Python source code |
| `openai_agents_docs` | openai | doc | OpenAI Agents SDK documentation |
| `openai_agents_python` | openai | code | OpenAI Agents SDK source code |
| `langgraph_python` | langchain, langgraph | code | LangGraph source code |
| `langchain_python` | langchain | code | LangChain core + key partners source |
| `deepagents_docs` | langchain, langgraph | doc | DeepAgents documentation |
| `deepagents_python` | langchain, langgraph | code | DeepAgents source code |
| `agent_dev_docs` | general | doc | Agent development PDFs & notebooks |

---

## Pipeline

1. **Query Expansion** (optional) — Generate variations
2. **Hybrid Search** — Dense docs + dense code + sparse (RRF fusion)
3. **Candidate Balancing** — Ensure docs/code mix before rerank
4. **VoyageAI Rerank** — Cross-encoder refinement  
5. **Coverage Gates** — Enforce minimum docs/code in output
