# Project Context for Agents

This repository implements a **RAG (Retrieval Augmented Generation)** system using **Qdrant** (Vector DB) and **Voyage AI** (Embedding & Reranking).

## Core Purpose

The system provides grounded evidence from:
1.  **ADK Documentation** (`google/adk-docs`)
2.  **ADK Python SDK** (`google/adk-python`)

## Key Architecture

### Specs
*   [Retrieval Spec](docs/spec/rerank_retrieval.md): Defines the hybrid search and reranking logic.
*   [Embedding Targets](docs/spec/corpus_embedding_targets.md): Defines what files are ingested.

### Retrieval Logic
*   **Entry Point**: `src/grounding/query/query_adk.py` -> `search_adk()`
*   **Hybrid Query**: Uses Qdrant `prefetch` (Dense Docs + Dense Code + Sparse) with `RRF` fusion.
*   **Coverage Balancing**: Ensures balanced docs/code mix before reranking.
*   **Reranking**: Uses Voyage `rerank-2.5`.

### Configuration
*   **Settings**: `config/settings.yaml`
*   **Secrets**: `.env` (managed via `src/grounding/config.py`)

## Development Workflow
*   **Run Query**: `python -m src.grounding.query.query_adk "your query" --verbose`
*   **Run Demo**: `python -m src.grounding.scripts.04_query_demo "your query"`
*   **Ingest Data**: `python -m src.grounding.scripts.03_ingest_corpus`

## Important Context
*   **Voyage API**: `voyage-context-3` requires the `contextualized_embed` endpoint even for queries.
*   **Coverage Gates**: Retrieval enforces a mix of Docs and Code files in the final results.
*   **Multi-Query**: Off by default for speed. Enable with `--multi-query` flag.
