---
description: Query the RAG database for grounding information (supports Google ADK, OpenAI Agents SDK, LangChain/LangGraph, Anthropic Claude SDK, CrewAI, and general agent docs)
---

# RAG Query Tool

Query the grounding database for documentation and code examples. Use `--sdk` to isolate queries to a specific SDK.

---

## SDK-based Filtering (Recommended)

```bash
source .venv/bin/activate

# Query Google ADK only
python -m src.grounding.query.query "how to use ToolContext" --sdk adk

# Query OpenAI Agents SDK only
python -m src.grounding.query.query "how to create handoffs" --sdk openai

# Query LangChain ecosystem (includes LangGraph + DeepAgents)
python -m src.grounding.query.query "ChatOpenAI model" --sdk langchain

# Query LangGraph-specific (includes DeepAgents)
python -m src.grounding.query.query "StateGraph checkpoint" --sdk langgraph

# Query Anthropic Claude Agent SDK
python -m src.grounding.query.query "create Claude agent" --sdk anthropic

# Query CrewAI Framework
python -m src.grounding.query.query "define a crew" --sdk crewai

# Query general agent development docs
python -m src.grounding.query.query "agent architectures" --sdk general
```

### SDK Groups

| Flag | Corpora Included |
|------|------------------|
| `--sdk adk` | `adk_docs`, `adk_python` |
| `--sdk openai` | `openai_agents_docs`, `openai_agents_python` |
| `--sdk langchain` | `langgraph_python`, `langchain_python`, `deepagents_python`, `deepagents_docs` |
| `--sdk langgraph` | `langgraph_python`, `deepagents_python`, `deepagents_docs` |
| `--sdk anthropic` | `claude_sdk_docs`, `claude_sdk_python` |
| `--sdk crewai` | `crewai_docs`, `crewai_python` |
| `--sdk general` | `agent_dev_docs` |

---

## Additional Options

```bash
# Verbose output with timing
python -m src.grounding.query.query "your query" --sdk adk --verbose

# Multi-query expansion (better recall, slower)
python -m src.grounding.query.query "your query" --sdk adk --multi-query

# Context expansion (enabled by default, fetch adjacent chunks)
python -m src.grounding.query.query "your query" --sdk adk --expand-context --expand-top-k 3

# Filter by specific corpus (multiple allowed)
python -m src.grounding.query.query "your query" --corpus adk_docs --corpus adk_python
```

---

## Python Usage

```python
from src.grounding.query.query import search, CORPUS_GROUPS

# Query with SDK filter
results = search(
    query="how to use ToolContext",
    top_k=12,
    filters={"corpus": CORPUS_GROUPS["adk"]}
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
| `--sdk` | none | SDK group: `adk`, `openai`, `langchain`, `langgraph`, `anthropic`, `crewai`, `general` |
| `--corpus` | all | Filter by specific corpus (repeatable) |
| `--top-k` | 12 | Number of final results |
| `--fusion` | dbsf | Fusion method: `dbsf` (Distribution-Based) or `rrf` (Reciprocal Rank) |
| `--score-threshold` | 0.0 | Filter results below this score (0 = disabled) |
| `--first-stage-k` | 80 | Candidates per prefetch lane |
| `--rerank-candidates` | 60 | Candidates sent to reranker |
| `--mode` | build | Retrieval mode: build, debug, explain, refactor |
| `--multi-query` | off | Enable query expansion (+15% recall, slower) |
| `--expand-context` | **on** | **Fetch adjacent chunks around top results (enabled by default)** |
| `--expand-top-k` | 5 | Number of top results to expand |
| `--expand-window` | 1 | Window size for adjacent chunks (±N) |
| `--verbose` | off | Show timing breakdown and stage info |
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
| `claude_sdk_docs` | anthropic | doc | Anthropic Claude Agent SDK documentation |
| `claude_sdk_python` | anthropic | code | Anthropic Claude Agent SDK source code |
| `crewai_docs` | crewai | doc | CrewAI framework documentation |
| `crewai_python` | crewai | code | CrewAI framework source code |
| `agent_dev_docs` | general | doc | Agent development PDFs & notebooks |

---

## Pipeline

1. **Query Expansion** (optional) — Generate balanced query variations
2. **Hybrid Search** — Dense docs + dense code + sparse (DBSF/RRF fusion)
3. **Deduplication** — Group by file path (one best chunk per source file)
4. **Candidate Balancing** — Ensure docs/code mix before rerank
5. **VoyageAI Rerank** — Cross-encoder refinement with large candidate pool
6. **Context Expansion** (enabled by default) — Fetch adjacent chunks (±N) around top-K results for contextual continuity
7. **Coverage Gates** — Enforce minimum docs/code in final output
