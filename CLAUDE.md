# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dual-purpose repository: (1) RAG pipeline with Voyage AI embeddings + Qdrant vector DB, and (2) 43 agent-optimized ADK workflows for building agentic systems with Google Agent Development Kit.

The RAG database contains documentation and source code from multiple SDK ecosystems:
- **Google ADK** - Agent Development Kit documentation and Python source
- **OpenAI Agents** - OpenAI Agents SDK documentation and Python source
- **LangChain Ecosystem** - LangGraph, LangChain core, and DeepAgents source code
- **Anthropic Claude** - Claude Agent SDK documentation and Python source
- **CrewAI** - CrewAI multi-agent framework documentation and Python source
- **General** - Agent development guides and notebooks

## Commands

```bash
# Install
pip install -e .
pip install -e ".[dev]"  # with dev dependencies

# Run tests
pytest tests/

# Query the RAG pipeline
python -m src.grounding.query.query "your query" --verbose
python -m src.grounding.query.query "your query" --multi-query --top-k 12

# With context expansion (enabled by default, fetch adjacent chunks)
python -m src.grounding.query.query "your query" --expand-context --expand-top-k 5
python -m src.grounding.query.query "your query" --expand-context --expand-window 2

# Query specific SDK groups
python -m src.grounding.query.query "your query" --sdk adk       # Google ADK
python -m src.grounding.query.query "your query" --sdk openai    # OpenAI Agents
python -m src.grounding.query.query "your query" --sdk langchain # LangChain ecosystem
python -m src.grounding.query.query "your query" --sdk langgraph # LangGraph + DeepAgents
python -m src.grounding.query.query "your query" --sdk anthropic # Claude Agent SDK
python -m src.grounding.query.query "your query" --sdk crewai    # CrewAI Framework

# Pipeline scripts (run in order for fresh setup)
python -m src.grounding.scripts.00_smoke_test_connections
python -m src.grounding.scripts.01_print_effective_config
python -m src.grounding.scripts.02_ensure_collection_schema
python -m src.grounding.scripts.03_ingest_corpus --corpus adk_docs
python -m src.grounding.scripts.03_ingest_corpus  # all corpora

# Workflow tooling
python .agent/scripts/validate_workflows.py --verbose
python .agent/scripts/select_workflow.py "add a function tool"
```

## Architecture

### RAG Pipeline (`src/grounding/`)

Multi-stage retrieval: Hybrid Search → Configurable Fusion (DBSF/RRF) → Deduplication → Coverage Balancing → Voyage Rerank → Context Expansion → Coverage Gates

- **Query entry point**: `src/grounding/query/query.py` - `search()` function
- **Config**: `src/grounding/config.py` loads `.env` + `config/settings.yaml` with `${VAR}` substitution
- **Clients**: `clients/` wraps Qdrant, Voyage AI, and FastEmbed (SPLADE)
- **Chunkers**: `chunkers/markdown.py` (heading-aware), `chunkers/python_code.py` (AST-based)
- **Contracts**: Pydantic models in `contracts/` for `Chunk`, `Document`, IDs

Vector spaces in Qdrant:
- `dense_docs` - voyage-context-3 (2048d) for documentation
- `dense_code` - voyage-code-3 (2048d) for Python code
- `sparse_lexical` - SPLADE++ for keyword matching

### ADK Workflows (`.agent/workflows/`)

Agent-optimized workflows with machine-readable frontmatter:

- **Schema**: `_schema.yaml` defines triggers, dependencies, outputs, completion_criteria
- **Manifest**: `_manifest.json` has dependency graph and routing keywords
- **Master**: `adk-master.md` routes to appropriate sub-workflow
- **Categories**: init, agents, tools, behavior, multi-agent, memory, security, streaming, deploy, quality, advanced

Frontmatter fields enable programmatic workflow selection:
```yaml
triggers: [keywords that route here]
dependencies: [required prior workflows]
completion_criteria: [how to verify success]
```

## Key Patterns

### Configuration
Settings loaded via `get_settings()` from `src/grounding/config.py`. Credentials in `.env`, structure in `config/settings.yaml`.

### Corpus Ingestion
Each corpus in `config/settings.yaml` under `ingestion.corpora` defines include/exclude globs, allowed extensions, and content kind (doc/code). Idempotent via text_hash comparison.

### Retrieval Flow
1. **Query Expansion (optional)**: Generate balanced code/docs query variations
2. **Hybrid Search**: Embed query with voyage-context-3 (docs) + voyage-code-3 (code) + SPLADE (sparse)
3. **Fusion & Deduplication**: Prefetch from 3 vector spaces with DBSF/RRF fusion, deduplicate by file path (one best chunk per source file) using query_points_groups
4. **Candidate Balancing**: Balance candidate pool to ensure docs/code mix before reranking
5. **Reranking**: Rerank top candidates with voyage rerank-2.5 cross-encoder
6. **Context Expansion (enabled by default)**: Fetch adjacent chunks (±N) around top-K reranked results for contextual continuity. Score inheritance: `adjacent_score = parent_score * (decay_factor ** distance)`
7. **Coverage Gates**: Apply final selection ensuring minimum docs/code representation

## Environment Variables

Required in `.env`:
- `VOYAGE_API_KEY`
- `QDRANT_URL`, `QDRANT_API_KEY`, `QDRANT_COLLECTION`

Optional retrieval tuning:
- `RETRIEVAL_PREFETCH_LIMIT_DENSE`, `RETRIEVAL_PREFETCH_LIMIT_SPARSE`
- `RETRIEVAL_FINAL_LIMIT`, `RERANK_TOP_K`
