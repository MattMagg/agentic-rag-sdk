# RAG Pipeline + ADK Agent Workflows

A **dual-purpose repository** providing:

1. **RAG Pipeline Infrastructure** – Drop-in, accuracy-first retrieval using Voyage AI embeddings and Qdrant vector DB
2. **ADK Development Workflows** – 43 grounded, RAG-informed workflows for building agentic systems with Google Agent Development Kit (ADK)

> **Note**: The ADK workflows are crafted for [Antigravity IDE](https://www.antigravity.dev/) but work with any IDE coding agent that supports workflow files.

---

## ✨ What This Repository Provides

### RAG Pipeline
End-to-end retrieval infrastructure optimized for accuracy:

- **Voyage AI Embeddings** – Context-aware embeddings for docs (`voyage-context-3`) and code (`voyage-code-3`)
- **Voyage Rerank** – Cross-encoder reranking with instruction-following (`rerank-2.5`)
- **Qdrant Vector DB** – Hybrid retrieval combining dense + sparse vectors with server-side RRF fusion
- **Drop-in Architecture** – Clone any repo, point to any docs folder, and ingest

### ADK Agent Workflows
Comprehensive **agent-optimized** workflows enabling IDE agents to autonomously build agentic systems:

| Category | Workflows | Coverage |
|----------|-----------|----------|
| **Foundation** | `adk-init`, `adk-agents-*`, `adk-master` | Project setup, LlmAgent, BaseAgent, multi-model |
| **Tools** | `adk-tools-*` | FunctionTool, MCP, OpenAPI, builtin, third-party |
| **Behavior** | `adk-behavior-*` | Callbacks, state, events, artifacts, plugins |
| **Multi-Agent** | `adk-multi-agent-*` | Delegation, orchestration, A2A protocol |
| **Memory** | `adk-memory-*` | Memory services, grounding tools |
| **Streaming** | `adk-streaming-*` | SSE, bidirectional, multimodal |
| **Deployment** | `adk-deploy-*` | Cloud Run, GKE, Vertex AI Agent Engine |
| **Security** | `adk-security-*` | Auth, guardrails, security plugins |
| **Quality** | `adk-quality-*` | Logging, tracing, observability, evals |
| **Advanced** | `adk-advanced-*` | ThinkingConfig, visual builder |
| **Meta** | `adk-master`, `adk-create-workflow` | Workflow orchestration and creation |

**Agent Infrastructure:** Workflows include machine-readable frontmatter with triggers, dependencies, and completion criteria for programmatic selection.

---

## 🎯 Use Cases

### RAG Pipeline
- **Ground AI coding agents** with official documentation and source code
- **Build internal knowledge bases** from company docs, wikis, and runbooks
- **Create documentation chatbots** with precise, citation-backed answers
- **Enable semantic code search** across large codebases

### ADK Workflows
- **Autonomous agent development** – IDE agents follow workflows to build ADK agents
- **Consistent implementation patterns** – Grounded in official ADK docs and SDK
- **Rapid prototyping** – From project init to multi-agent orchestration
- **Quality assurance** – Built-in evaluation and observability patterns

---

## 🏗️ Architecture Overview

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

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- [Voyage AI API Key](https://voyageai.com/)
- [Qdrant Cloud](https://cloud.qdrant.io/) cluster (or local Qdrant)

### 1. Clone and Install

```bash
git clone https://github.com/MattMagg/rag_qdrant_voyage.git
cd rag_qdrant_voyage
pip install -e .
```

### 2. Configure Credentials

Copy `.env.example` to `.env` and fill in your keys:

```bash
# Voyage AI
VOYAGE_API_KEY="your-voyage-api-key"

# Qdrant Cloud
QDRANT_URL="https://your-cluster.region.cloud.qdrant.io:6333"
QDRANT_API_KEY="your-qdrant-api-key"

# Collection name (customize per project)
QDRANT_COLLECTION="my_knowledge_base_v1"
```

### 3. Query the Pipeline

```bash
# Query Google ADK only
python -m src.grounding.query.query_adk "How to implement multi-agent orchestration?" --sdk adk

# Query OpenAI Agents SDK only  
python -m src.grounding.query.query_adk "How to create handoffs?" --sdk openai

# Query general agent development docs
python -m src.grounding.query.query_adk "Agent architectures" --sdk general

# With verbose output
python -m src.grounding.query.query_adk "your query" --sdk adk --verbose
```

**SDK Groups:**

| Flag | Corpora |
|------|---------|
| `--sdk adk` | `adk_docs`, `adk_python` |
| `--sdk openai` | `openai_agents_docs`, `openai_agents_python` |
| `--sdk general` | `agent_dev_docs` |

---

## 📁 Project Structure

```
rag_qdrant_voyage/
├── .agent/
│   ├── workflows/           # ADK DEVELOPMENT WORKFLOWS (43 files)
│   │   ├── _schema.yaml     # Agent-optimized frontmatter schema
│   │   ├── _manifest.json   # Workflow index with dependency graph
│   │   ├── adk-master.md    # Master orchestrator
│   │   ├── adk-init*.md     # Project initialization
│   │   ├── adk-agents-*.md  # Agent creation patterns
│   │   ├── adk-tools-*.md   # Tool integration
│   │   ├── adk-behavior-*.md    # Agent behavior
│   │   ├── adk-multi-agent-*.md # Multi-agent orchestration
│   │   ├── adk-memory-*.md      # Memory and grounding
│   │   ├── adk-streaming-*.md   # Streaming patterns
│   │   ├── adk-deploy-*.md      # Deployment workflows
│   │   ├── adk-security-*.md    # Security patterns
│   │   ├── adk-quality-*.md     # Quality assurance
│   │   └── adk-advanced-*.md    # Advanced features
│   ├── scripts/             # Workflow tooling
│   │   ├── validate_workflows.py  # Schema compliance checker
│   │   └── select_workflow.py     # Query-to-workflow router
│   └── tools/               # Non-workflow agent tools
├── config/
│   ├── settings.yaml        # Main configuration
│   └── logging.yaml         # Logging configuration
├── corpora/                 # YOUR CONTENT GOES HERE
│   ├── adk-docs/            # ADK documentation corpus
│   ├── adk-python/          # ADK Python SDK corpus
│   ├── openai-agents-python/# OpenAI Agents SDK corpus (docs + source)
│   └── agent-dev-docs/      # General agent development docs
├── src/grounding/
│   ├── clients/             # Qdrant + Voyage client wrappers
│   ├── contracts/           # Pydantic models for chunks, payloads
│   ├── chunking/            # AST-based code + heading-aware doc chunkers
│   ├── embedding/           # Dense (Voyage) + sparse (SPLADE) embedders
│   ├── query/               # Hybrid query + rerank pipeline
│   └── scripts/             # CLI commands (ingest, verify, query)
├── docs/spec/               # Detailed implementation specifications
└── tests/                   # Smoke tests + retrieval evaluation
```

---

## 🤖 Using the ADK Workflows

### With Antigravity IDE

The workflows are automatically detected. Use slash commands:

```
/adk-master          # Master orchestrator - routes to appropriate workflow
/adk-init            # Initialize new ADK project
/adk-agents-create   # Create LlmAgent with model and instructions
/adk-tools-function  # Add custom FunctionTool
/adk-multi-agent-delegation  # Implement multi-agent patterns
```

### With Other IDE Agents

Copy `.agent/workflows/` to your project and reference the workflows in your agent's system prompt or configuration.

### Workflow Categories

| Prefix | Purpose |
|--------|---------|
| `adk-init-*` | Project scaffolding and setup |
| `adk-agents-*` | LlmAgent, BaseAgent, multi-model config |
| `adk-tools-*` | FunctionTool, MCP, OpenAPI, builtin tools |
| `adk-behavior-*` | Callbacks, state management, events |
| `adk-multi-agent-*` | Delegation, orchestration, A2A protocol |
| `adk-memory-*` | Memory services and grounding |
| `adk-streaming-*` | SSE, bidirectional, multimodal |
| `adk-deploy-*` | Cloud Run, GKE, Agent Engine |
| `adk-security-*` | Auth, guardrails, security plugins |
| `adk-quality-*` | Logging, tracing, evals, observability |
| `adk-advanced-*` | ThinkingConfig, visual builder |

### Agent Tooling

The workflows include infrastructure for programmatic selection and validation:

```bash
# Find the right workflow for a task (with dependency chain)
python .agent/scripts/select_workflow.py "add a function tool to my agent"
# Output: adk-init → adk-agents-create → adk-tools-function

# Validate all workflows against schema
python .agent/scripts/validate_workflows.py --verbose

# List all workflow categories
python .agent/scripts/select_workflow.py --list-categories
```

**Manifest (`_manifest.json`):** Contains workflow index, dependency graph, and routing keywords for agent-based selection.

**Schema (`_schema.yaml`):** Defines frontmatter fields (triggers, dependencies, outputs, completion_criteria) for agent-optimized parsing.

---

## ⚙️ Configuration

### Core Settings (`config/settings.yaml`)

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
  fusion: "rrf"
  prefetch_limit_dense: 80
  prefetch_limit_sparse: 120
  final_limit: 40
  rerank_top_k: 12
```

---

## 🔍 Retrieval Deep Dive

### Hybrid Search Strategy

Every query triggers **3 parallel searches**:

| Search Type | Vector Space | Model | Purpose |
|-------------|--------------|-------|---------|
| Dense Docs | `dense_docs` | `voyage-context-3` | Semantic match for documentation |
| Dense Code | `dense_code` | `voyage-code-3` | Semantic match for code |
| Sparse | `sparse_lexical` | SPLADE++ | Exact keyword/identifier match |

Results are **fused server-side** using Reciprocal Rank Fusion (RRF), then **reranked** with Voyage `rerank-2.5`.

### Coverage Balancing

The pipeline enforces a balanced mix of documentation and code results before reranking to ensure grounded evidence from both sources.

---

## 📚 Specifications

| Spec | Topic |
|------|-------|
| [Foundation & Environment](docs/spec/Foundation_and_Environment.md) | Project setup, credentials, client wrappers |
| [Qdrant Schema](docs/spec/qdrant_schema_and_config.md) | Collection schema, HNSW config, payload indexes |
| [Ingestion Pipeline](docs/spec/ingestion_upsert.md) | Chunking, embedding, upsert workflow |
| [Hybrid Query](docs/spec/hybrid_query.md) | Prefetch, fusion, ADK tool interface |
| [Rerank Retrieval](docs/spec/rerank_retrieval.md) | Voyage rerank, evidence packs, evaluation |

---

## 🛠️ Development

### Prerequisites

```bash
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/
```

### Key Dependencies

| Package | Purpose |
|---------|---------|
| `qdrant-client` | Vector DB operations |
| `voyageai` | Embeddings + reranking |
| `fastembed` | SPLADE sparse embeddings |
| `pydantic` | Data contracts |

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions welcome! Please read the specs in `docs/spec/` before making changes to core retrieval logic.

For ADK workflow contributions, follow the structure in existing workflows and ensure examples are grounded in official ADK documentation.
