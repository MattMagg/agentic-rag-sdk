# Voyage + Qdrant RAG Pipeline

**Accuracy-first retrieval infrastructure for grounding AI coding agents.**

A production-ready RAG pipeline using Voyage AI embeddings, Qdrant vector database, and hybrid retrieval with cross-encoder reranking. Currently indexes 9 corpora (~14,700 vectors) across major agentic AI SDKs.

**Secondary feature**: 44 IDE-agnostic workflows for building agents with Google ADK.

---

## Quick Start

### Prerequisites

- Python 3.11+
- [Voyage AI API Key](https://dash.voyageai.com/)
- [Qdrant Cloud](https://cloud.qdrant.io/) cluster (free tier works)

### 1. Clone and Install

```bash
git clone https://github.com/MattMagg/adk-workflow-rag.git
cd adk-workflow-rag
pip install -e .
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required variables:
```bash
VOYAGE_API_KEY="your-voyage-api-key"
QDRANT_URL="https://your-cluster.region.cloud.qdrant.io:6333"
QDRANT_API_KEY="your-qdrant-api-key"
QDRANT_COLLECTION="agentic_grounding_v1"
```

### 3. Initialize Pipeline

```bash
# Verify API connections
python -m src.grounding.scripts.00_smoke_test_connections

# Create Qdrant collection with schema
python -m src.grounding.scripts.02_ensure_collection_schema

# Ingest a corpus (e.g., ADK docs)
python -m src.grounding.scripts.03_ingest_corpus --corpus adk_docs
```

### 4. Query

```bash
# Query Google ADK
python -m src.grounding.query.query_adk "How to implement multi-agent orchestration?" --sdk adk

# Query OpenAI Agents SDK
python -m src.grounding.query.query_adk "How to create handoffs?" --sdk openai

# Query LangChain ecosystem
python -m src.grounding.query.query_adk "How to use LangGraph checkpoints?" --sdk langchain

# With verbose output
python -m src.grounding.query.query_adk "your query" --verbose --multi-query
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           YOUR CORPUS                                   │
│   repos, docs, markdown, code, PDFs, text files, configs...            │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │    DISCOVERY & CHUNK    │
                    │  • Smart file walking   │
                    │  • AST-based code split │
                    │  • Heading-aware docs   │
                    └────────────┬────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          ▼                      ▼                      ▼
   ┌─────────────┐       ┌─────────────┐       ┌─────────────┐
   │  Dense Vec  │       │  Dense Vec  │       │ Sparse Vec  │
   │voyage-ctx-3 │       │voyage-code-3│       │   SPLADE++  │
   │   (docs)    │       │   (code)    │       │  (lexical)  │
   └──────┬──────┘       └──────┬──────┘       └──────┬──────┘
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                ▼
                    ┌────────────────────────┐
                    │    QDRANT CLOUD        │
                    │  Named vector spaces:  │
                    │  • dense_docs (2048d)  │
                    │  • dense_code (2048d)  │
                    │  • sparse_lexical      │
                    │  + Rich payload index  │
                    └────────────┬───────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
       ┌───────────┐      ┌───────────┐      ┌───────────┐
       │  Prefetch │      │  Prefetch │      │  Prefetch │
       │dense_docs │      │dense_code │      │  sparse   │
       └─────┬─────┘      └─────┬─────┘      └─────┬─────┘
             └──────────────────┼──────────────────┘
                                ▼
                    ┌────────────────────────┐
                    │   RRF / DBSF FUSION    │
                    │   (server-side)        │
                    └────────────┬───────────┘
                                 ▼
                    ┌────────────────────────┐
                    │  VOYAGE RERANK-2.5     │
                    │  instruction-following │
                    └────────────┬───────────┘
                                 ▼
                    ┌────────────────────────┐
                    │    EVIDENCE PACK       │
                    │  ranked, cited, ready  │
                    └────────────────────────┘
```

---

## SDK Groups & Corpora

| SDK Flag | Corpora | Description |
|----------|---------|-------------|
| `--sdk adk` | `adk_docs`, `adk_python` | Google Agent Development Kit |
| `--sdk openai` | `openai_agents_docs`, `openai_agents_python` | OpenAI Agents SDK |
| `--sdk langchain` | `langgraph_python`, `langchain_python`, `deepagents_python`, `deepagents_docs` | LangChain ecosystem |
| `--sdk langgraph` | `langgraph_python`, `deepagents_python`, `deepagents_docs` | LangGraph + DeepAgents |
| `--sdk general` | `agent_dev_docs` | General agent development |

**Current stats**: 9 corpora, ~14,700 vectors, 5 SDK filter groups

---

## Adding Your Own Corpora

### Step 1: Clone the Repository

```bash
cd corpora/
git clone https://github.com/your-org/your-repo.git
```

### Step 2: Add Configuration

Edit `config/settings.yaml` and add an entry under `ingestion.corpora`:

```yaml
your_corpus_name:
  root: "corpora/your-repo"
  corpus: "your_corpus_name"
  repo: "your-org/your-repo"
  kind: "doc"  # or "code"
  ref: "main"
  include_globs:
    - "docs/**/*.md"
    - "src/**/*.py"
  exclude_globs:
    - "**/.git/**"
    - "**/tests/**"
  allowed_exts: [".md", ".py"]
  max_file_bytes: 500000
```

**Kind determines embedding model**:
- `doc` → `voyage-context-3` (optimized for documentation)
- `code` → `voyage-code-3` (optimized for source code)

### Step 3: Update Type Definition

Edit `src/grounding/contracts/chunk.py` and add to `SourceCorpus`:

```python
SourceCorpus = Literal[
    "adk_docs",
    "adk_python",
    # ... existing corpora ...
    "your_corpus_name",  # Add here
]
```

### Step 4: Update Query Module

Edit `src/grounding/query/query_adk.py`:

```python
# Add to ALL_CORPORA list
ALL_CORPORA = [
    # ... existing corpora ...
    "your_corpus_name",
]

# Optionally add to SDK_GROUPS for --sdk filtering
SDK_GROUPS = {
    # ... existing groups ...
    "your_sdk": ["your_corpus_name"],
}
```

### Step 5: Ingest

```bash
python -m src.grounding.scripts.03_ingest_corpus --corpus your_corpus_name
```

---

## Switching Embedding Models

### Why This Repo Uses Voyage 3 Family

This pipeline uses `voyage-context-3` (docs) and `voyage-code-3` (code) because they are purpose-built for their respective content types. The specialized models provide better retrieval quality for code and documentation compared to general-purpose models.

### Available Voyage Models

**Voyage 3 family** (used in this repo):
- `voyage-context-3` - Optimized for long-context documents (2048d)
- `voyage-code-3` - Optimized for source code (2048d)

**Voyage 4 family** (general-purpose, if you prefer):
- `voyage-4-large` - Highest quality general model (1024d)
- `voyage-4` - Balanced quality/speed (1024d)
- `voyage-4-lite` - Faster, smaller (512d)
- `voyage-4-nano` - Fastest, smallest (512d)

### How to Switch to Voyage 4

1. **Update `config/settings.yaml`**:
   ```yaml
   voyage:
     docs_model: "voyage-4-large"  # or voyage-4, voyage-4-lite
     code_model: "voyage-4-large"  # Voyage 4 doesn't have specialized code model
     output_dimension: 1024        # Voyage 4 uses 1024d (not 2048d)
   ```

2. **Re-create Qdrant collection** (dimensions must match):
   ```bash
   # Delete existing collection first (via Qdrant console or API)
   python -m src.grounding.scripts.02_ensure_collection_schema
   ```

3. **Re-ingest all corpora**:
   ```bash
   python -m src.grounding.scripts.03_ingest_corpus
   ```

---

## Configuration Reference

### `config/settings.yaml`

```yaml
qdrant:
  url: ${QDRANT_URL}
  api_key: ${QDRANT_API_KEY}
  collection: ${QDRANT_COLLECTION}

voyage:
  api_key: ${VOYAGE_API_KEY}
  docs_model: "voyage-context-3"
  code_model: "voyage-code-3"
  output_dimension: 2048
  rerank_model: "rerank-2.5"

retrieval_defaults:
  fusion: "rrf"                    # Reciprocal Rank Fusion
  prefetch_limit_dense: 80         # Candidates per dense search
  prefetch_limit_sparse: 120       # Candidates from sparse search
  final_limit: 40                  # Candidates sent to reranker
  rerank_top_k: 12                 # Final results returned
```

Environment variable substitution (`${VAR}`) is supported throughout.

---

## Hybrid Retrieval Strategy

Every query executes **3 parallel searches**:

| Search | Vector Space | Model | Purpose |
|--------|--------------|-------|---------|
| Dense Docs | `dense_docs` | `voyage-context-3` | Semantic match for documentation |
| Dense Code | `dense_code` | `voyage-code-3` | Semantic match for code |
| Sparse | `sparse_lexical` | SPLADE++ | Exact keyword/identifier match |

Results are **fused server-side** using Reciprocal Rank Fusion (RRF), then **reranked** with `rerank-2.5`.

### Coverage Balancing

Before reranking, the pipeline ensures a balanced mix of documentation and code results. This prevents the reranker from seeing only one content type and ensures grounded evidence from both sources.

---

## Coding Agent Workflows

This repository includes **44 ADK development workflows** in `.agent/workflows/` for building agentic systems with Google Agent Development Kit.

### Quick Usage

With [Antigravity IDE](https://www.antigravity.dev/), workflows are auto-detected:
```
/adk-master          # Master orchestrator
/adk-init            # Initialize new project
/adk-agents-create   # Create LlmAgent
/adk-tools-function  # Add FunctionTool
```

For other IDEs, copy `.agent/workflows/` to your project and reference in your agent's system prompt.

### Workflow Categories

| Prefix | Purpose |
|--------|---------|
| `adk-init-*` | Project scaffolding |
| `adk-agents-*` | Agent creation (LlmAgent, BaseAgent) |
| `adk-tools-*` | Tool integration (FunctionTool, MCP, OpenAPI) |
| `adk-behavior-*` | Callbacks, state, events |
| `adk-multi-agent-*` | Delegation, orchestration, A2A |
| `adk-memory-*` | Memory services, grounding |
| `adk-streaming-*` | SSE, bidirectional, multimodal |
| `adk-deploy-*` | Cloud Run, GKE, Agent Engine |
| `adk-security-*` | Auth, guardrails |
| `adk-quality-*` | Logging, tracing, evals |
| `adk-advanced-*` | ThinkingConfig, visual builder |

See `.agent/workflows/adk-workflow/` for detailed workflow creation specs.

---

## Project Structure

```
adk-workflow-rag/
├── .agent/
│   ├── workflows/           # 44 ADK development workflows
│   │   ├── _schema.yaml     # Frontmatter schema
│   │   ├── _manifest.json   # Workflow index + dependencies
│   │   └── adk-*.md         # Individual workflows
│   └── scripts/             # Workflow tooling
├── config/
│   ├── settings.yaml        # Main configuration
│   └── logging.yaml         # Logging configuration
├── corpora/                 # Git-cloned source repositories
│   ├── adk-docs/            # Google ADK documentation
│   ├── adk-python/          # Google ADK Python SDK
│   ├── openai-agents-python/# OpenAI Agents SDK
│   ├── langgraph/           # LangGraph source
│   ├── langchain/           # LangChain source
│   ├── deepagents/          # DeepAgents source
│   └── agent-dev-docs/      # General agent docs
├── src/grounding/
│   ├── clients/             # Qdrant + Voyage client wrappers
│   ├── contracts/           # Pydantic models (Chunk, Document)
│   ├── chunkers/            # AST-based code + heading-aware docs
│   ├── query/               # Hybrid query + rerank pipeline
│   └── scripts/             # CLI commands (00-03)
├── docs/
│   ├── voyage-qdrant-rag-spec/  # 6 detailed spec files
│   └── rag-query.md             # Query tool documentation
└── tests/                   # pytest tests
```

---

## Documentation

| Document | Topic |
|----------|-------|
| [Foundation & Environment](docs/voyage-qdrant-rag-spec/Foundation_and_Environment.md) | Setup, credentials, client wrappers |
| [Qdrant Schema](docs/voyage-qdrant-rag-spec/qdrant_schema_and_config.md) | Collection schema, HNSW config |
| [Ingestion Pipeline](docs/voyage-qdrant-rag-spec/ingestion_upsert.md) | Chunking, embedding, upsert |
| [Hybrid Query](docs/voyage-qdrant-rag-spec/hybrid_query.md) | Prefetch, fusion, tool interface |
| [Rerank Retrieval](docs/voyage-qdrant-rag-spec/rerank_retrieval.md) | Voyage rerank, evidence packs |
| [Corpus Targets](docs/voyage-qdrant-rag-spec/corpus_embedding_targets.md) | Corpus configuration |

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run single test
pytest tests/test_config_loads.py -v
```

### Key Dependencies

| Package | Purpose |
|---------|---------|
| `qdrant-client` | Vector DB operations |
| `voyageai` | Embeddings + reranking |
| `fastembed` | SPLADE sparse embeddings |
| `pydantic` | Data contracts |

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Contributing

Contributions welcome! Please read the specs in `docs/voyage-qdrant-rag-spec/` before modifying core retrieval logic.

For workflow contributions, follow existing patterns in `.agent/workflows/` and ensure examples are grounded in official ADK documentation.
