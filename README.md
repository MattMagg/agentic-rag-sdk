# RAG Pipeline: Voyage AI + Qdrant

A **drop-in, accuracy-first RAG solution** for grounding AI agents and LLMs in your own knowledge base. Ingest any corpus—documentation, code, PDFs, or custom content—into a hybrid vector database with state-of-the-art retrieval.

## ✨ What This Is

This pipeline provides **end-to-end RAG infrastructure** optimized for retrieval accuracy:

- **Voyage AI Embeddings** – Context-aware embeddings for docs (`voyage-context-3`) and code (`voyage-code-3`)
- **Voyage Rerank** – Cross-encoder reranking with instruction-following (`rerank-2.5`)
- **Qdrant Vector DB** – Hybrid retrieval combining dense + sparse vectors with server-side RRF fusion
- **Drop-in Architecture** – Clone any repo, point to any docs folder, and ingest

## 🎯 Use Cases

- **Ground AI coding agents** with official documentation and source code
- **Build internal knowledge bases** from company docs, wikis, and runbooks  
- **Create documentation chatbots** with precise, citation-backed answers
- **Enable semantic code search** across large codebases

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
git clone https://github.com/YOUR_ORG/rag_qdrant_voyage.git
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

### 3. Add Your Corpus

Drop your content into the `corpora/` directory:

```bash
mkdir -p corpora/my-docs
# Copy or clone your content
cp -r /path/to/your/docs corpora/my-docs/
# Or clone a repo
git clone https://github.com/org/repo.git corpora/my-repo
```

### 4. Ingest

```bash
# Ingest everything
python -m src.grounding.scripts.ingest all

# Or selectively
python -m src.grounding.scripts.ingest docs
python -m src.grounding.scripts.ingest code
```

### 5. Query

```python
from src.grounding.retrieval import retrieve_evidence

results = retrieve_evidence(
    query="How do I implement multi-agent orchestration?",
    intent="HOW_TO_IMPLEMENT",
    top_k=12
)

for item in results["evidence"]:
    print(f"[{item['rank']}] {item['path']}")
    print(f"    Score: {item['rerank_score']:.3f}")
    print(f"    {item['text'][:200]}...")
```

---

## 📁 Project Structure

```
rag_qdrant_voyage/
├── config/
│   ├── settings.yaml       # Main configuration (models, limits, defaults)
│   └── logging.yaml        # Logging configuration
├── corpora/                 # YOUR CONTENT GOES HERE
│   ├── my-docs/            # Documentation corpus
│   └── my-code/            # Code corpus  
├── manifests/
│   ├── corpus_manifest.json       # Corpus metadata + commit SHAs
│   └── ingestion_runs/            # Run history for reproducibility
├── src/grounding/
│   ├── clients/            # Qdrant + Voyage client wrappers
│   ├── contracts/          # Pydantic models for chunks, payloads
│   ├── chunking/           # AST-based code + heading-aware doc chunkers
│   ├── embedding/          # Dense (Voyage) + sparse (SPLADE) embedders
│   ├── retrieval/          # Hybrid query + rerank pipeline
│   └── scripts/            # CLI commands (ingest, verify, query)
├── tests/                  # Smoke tests + retrieval evaluation
└── docs/spec/              # Detailed implementation specifications
```

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
  docs_model: "voyage-context-3"    # Contextualized embeddings for docs
  code_model: "voyage-code-3"       # Code-optimized embeddings
  output_dimension: 2048            # Maximum for highest accuracy
  output_dtype: "float"             # Float32 for precision
  rerank_model: "rerank-2.5"        # Instruction-following reranker

vectors:
  dense_docs: "dense_docs"          # Named vector space for docs
  dense_code: "dense_code"          # Named vector space for code
  sparse_lexical: "sparse_lexical"  # Sparse vector for hybrid

retrieval_defaults:
  fusion: "rrf"                     # Reciprocal Rank Fusion
  prefetch_limit_dense: 80          # Candidates per dense search
  prefetch_limit_sparse: 120        # Candidates from sparse search
  final_limit: 40                   # After fusion, before rerank
  rerank_top_k: 12                  # Final returned results
```

### Ingestion Settings

```yaml
ingestion:
  chunking:
    docs:
      target_chunk_chars: 4500      # Target chunk size
      overlap_chars: 300            # Context overlap
    code:
      max_symbol_chunk_chars: 9000  # Max per function/class
  
  lexical:
    sparse_model: "prithivida/Splade_PP_en_v1"
    code_identifier_expansion: true  # Split snake_case, camelCase
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

### Query Intent Classification

The pipeline adapts retrieval based on intent:

| Intent | Description | Behavior |
|--------|-------------|----------|
| `HOW_TO_IMPLEMENT` | "How do I build X?" | Mixed docs + code |
| `API_LOOKUP` | "What are the params for X?" | Code-heavy |
| `CODE_EXAMPLE` | "Show me an example of X" | Code-focused |
| `DEBUG_ERROR` | Stack traces, errors | Code-focused |
| `CONCEPTUAL` | Architecture, concepts | Docs-heavy |

### Accuracy-First HNSW Configuration

The Qdrant collection is configured for **maximum retrieval accuracy**:

- `m = 64` (high connectivity graph)
- `ef_construct = 512` (thorough index building)
- `hnsw_ef = 256` at query time (broad search before fusion)
- No quantization (preserves full precision)

---

## 📊 Adding Your Own Corpus

### Supported File Types

**Documentation:**
- Markdown: `.md`, `.mdx`
- reStructuredText: `.rst`
- Plain text: `.txt`
- AsciiDoc: `.adoc`

**Code:**
- Python: `.py` (AST-parsed for symbol chunks)
- Config: `.yaml`, `.yml`, `.toml`, `.json`
- Any text file with explicit include

### Corpus Configuration

Define your corpus in `config/settings.yaml`:

```yaml
ingestion:
  corpora:
    my_docs:
      root: "corpora/my-docs"
      corpus: "my_docs"
      kind: "doc"
      allowed_exts: [".md", ".mdx", ".rst", ".txt"]
      exclude_globs:
        - "**/.git/**"
        - "**/node_modules/**"

    my_code:
      root: "corpora/my-repo"
      corpus: "my_code"
      kind: "code"
      allowed_exts: [".py", ".md", ".yaml"]
      exclude_globs:
        - "**/.git/**"
        - "**/__pycache__/**"
        - "**/.venv/**"
```

### Chunk Text Format

Every chunk includes a **provenance header** for traceability:

```
[CORPUS=my_docs] [REPO=my-org/my-docs] [COMMIT=abc123]
[PATH=guides/getting-started.md]
[HEADINGS=Getting Started > Installation]
---
To install the package, run pip install...
```

---

## 🧪 Verification

### Smoke Tests

```bash
# Test all connections
python -m src.grounding.scripts.00_smoke_test_connections

# Verify Qdrant collection schema
python -m src.grounding.scripts.verify
```

### Ingestion Verification

After ingestion, verify counts:

```bash
python -m src.grounding.scripts.verify

# Expected output:
# ✓ Collection exists with correct schema
# ✓ Docs chunks: 1,234
# ✓ Code chunks: 5,678
# ✓ Sample payloads validated
```

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

## 📚 Detailed Specifications

For implementation details, see the spec documents:

| Spec | Topic |
|------|-------|
| [Foundation & Environment](docs/spec/Foundation_and_Environment.md) | Project setup, credentials, client wrappers |
| [Qdrant Schema](docs/spec/qdrant_schema_and_config.md) | Collection schema, HNSW config, payload indexes |
| [Ingestion Pipeline](docs/spec/ingestion_upsert.md) | Chunking, embedding, upsert workflow |
| [Hybrid Query](docs/spec/hybrid_query.md) | Prefetch, fusion, ADK tool interface |
| [Rerank Retrieval](docs/spec/rerank_retrieval.md) | Voyage rerank, evidence packs, evaluation |

---

## 🔑 Key Design Decisions

### Why Voyage AI?

- **Contextualized embeddings** (`voyage-context-3`) preserve document-level context across chunks
- **Code-specific model** (`voyage-code-3`) understands programming semantics
- **Instruction-following reranker** (`rerank-2.5`) can be steered for your use case

### Why Qdrant?

- **Named vector spaces** allow different embedding models in one collection
- **Sparse vector support** enables hybrid search in a single DB
- **Server-side fusion** (RRF/DBSF) eliminates client-side merging
- **Query API with prefetch** runs multiple searches + fusion in one request

### Why Hybrid (Dense + Sparse)?

- Dense vectors capture **semantic meaning** ("similar concepts")
- Sparse vectors capture **exact terms** (identifiers, API names, error codes)
- Combined via RRF, you get the best of both worlds

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Contributions welcome! Please read the specs in `docs/spec/` before making changes to core retrieval logic.
