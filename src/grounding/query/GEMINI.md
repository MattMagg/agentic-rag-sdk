# Query Module for Agents

This directory contains the retrieval logic for the ADK grounding system.

## Primary Entry Point

**File**: `query_adk.py` → `search_adk()`

```bash
# CLI usage
python -m src.grounding.query.query_adk "your query" --verbose

# Python usage
from src.grounding.query.query_adk import search_adk
results = search_adk("how to use tool context", top_k=12)
```

**Features:**
- Hybrid search (dense docs + dense code + sparse with RRF fusion)
- Coverage-aware candidate balancing (ensures docs/code mix)
- Voyage `rerank-2.5` cross-encoder reranking
- Per-stage timing breakdown
- Multi-query expansion (optional, `--multi-query`)
