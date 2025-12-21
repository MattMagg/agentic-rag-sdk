# Scripts Usage for Agents

This directory contains operational scripts for the RAG pipeline.

## Query Demo
**File**: `04_query_demo.py`

Simple demo script for quick testing.

```bash
python -m src.grounding.scripts.04_query_demo "your query here"
```

## Ingestion
**File**: `03_ingest_corpus.py`

Ingest document and code corpora into Qdrant.

```bash
python -m src.grounding.scripts.03_ingest_corpus
```

---

## Production Query (Recommended)

For production use, prefer the optimized query module:

**File**: `src/grounding/query/query_adk.py`

```bash
# Basic usage
python -m src.grounding.query.query_adk "your query" --top-k 12

# With verbose output
python -m src.grounding.query.query_adk "your query" --verbose

# With multi-query expansion (slower but better recall)
python -m src.grounding.query.query_adk "your query" --multi-query --verbose

# Filter by corpus
python -m src.grounding.query.query_adk "your query" --corpus adk_python
```

**Features:**
- Hybrid search (dense docs + dense code + sparse)
- Coverage-aware candidate balancing
- Voyage rerank-2.5
- Per-stage timing breakdown
