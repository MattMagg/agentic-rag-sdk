## SPEC 1/5 — Foundation & Environment Bootstrap (VoyageAI → Qdrant Cloud → Hybrid Retrieval + Rerank)

**Document ID:** `SPEC-01-foundation-bootstrap`
**Applies to:** Your fork-based grounding corpus built from:

* `google/adk-docs` (documentation corpus) ([GitHub][1])
* `google/adk-python` (code corpus) ([GitHub][2])

**Primary goal of this spec:**
Create a *reproducible*, *credentialed*, *testable* baseline environment that a coding agent can immediately use to:

1. connect to **Qdrant Cloud**,
2. call **VoyageAI embeddings** (docs + code),
3. call **Voyage rerank-2.5**,
4. prepare the configuration and “contracts” needed for later specs (collection schema, ingestion, retrieval).

This spec intentionally **does not** create the Qdrant collection or ingest data yet (that begins in Spec 2/5 and 3/5). This spec makes sure every later step is deterministic and fails fast if misconfigured.

---

# 1) Fixed Decisions (Locked for Highest Retrieval Accuracy)

These decisions are **already made** in this spec to avoid ambiguity and maximize retrieval quality.

## 1.1 One Qdrant collection, multiple named vector spaces (recommended)

We will use **one** Qdrant collection with:

* `dense_docs` vector space for docs embeddings
* `dense_code` vector space for code embeddings
* `sparse_lexical` sparse vector space for lexical hybrid

Rationale:

* Qdrant supports **multiple named vectors of different sizes and types** in the same collection ([Qdrant][3]).
* Named vectors are **optional per point**, so docs points can carry `dense_docs` while code points carry `dense_code` (and both can carry `sparse_lexical`). ([Qdrant][4])
* Qdrant’s **Query API + prefetch + fusion** is explicitly designed to combine results across representations (dense + sparse and multiple vector spaces) ([Qdrant][5]), which is exactly what we need for “docs + code as complementary grounding.”

This is the cleanest way to get:

* high recall across both corpora
* unified filtering/faceting
* a single retrieval tool endpoint for your IDE agents

## 1.2 Embedding models & dimensions (accuracy-first)

You specified:

* **Docs:** `voyage-context-3` via *contextualized chunk embeddings* ([Voyage AI][6])
* **Code:** `voyage-code-3` via *text embeddings* ([Voyage AI][7])
* **Rerank:** `rerank-2.5` ([Voyage AI][8])

For “highest possible retrieval accuracy,” we will set:

* `output_dimension = 2048` for dense vectors where supported ([Voyage AI][7])
* `output_dtype = "float"` (Voyage explicitly states float provides highest precision / retrieval accuracy) ([Voyage AI][7])

> Note: `voyage-code-3` supports flexible dimensions up to 2048 ([Voyage AI][7]).
> `voyage-context-3` is used through the contextualized embeddings endpoint; we will keep floats (default/explicit) ([Voyage AI][6]).

## 1.3 Hybrid retrieval method in Qdrant

We will use:

* Qdrant **Query API**
* `prefetch` sub-queries
* **Fusion = RRF** (Reciprocal Rank Fusion) as default

Qdrant documents that hybrid/multi-stage queries use `prefetch` and that hybrid fusion supports `rrf` and `dbsf` ([Qdrant][5]). We’ll start with **RRF** because it’s robust when mixing heterogeneous rankers (sparse lexical + two dense spaces), then evaluate DBSF later (Spec 5).

---

# 2) Requirements & Preconditions

## 2.1 Python version

If you plan to run ADK tooling in the same workspace, note the ADK docs site indicates **ADK Python v1.19.0 requires Python 3.10+** ([Google GitHub Page][9]).

**Spec decision:** Use **Python 3.11 or 3.12** (safe, modern, widely supported).

> **Note:** Python 3.14+ is too new for the `voyageai` package (as of v0.3.7). If your system Python is 3.14, create a venv with an older Python: `/opt/homebrew/bin/python3.12 -m venv .venv`

## 2.2 Accounts / credentials required

You must have:

1. **VoyageAI API Key**
2. **Qdrant Cloud cluster URL + API key**

   * Qdrant client connects to cloud via `url=...` and `api_key=...` ([GitHub][10])

---

# 3) Project Layout (Canonical, Agent-Friendly)

This is the filesystem contract your coding agent will implement. Keep it stable across specs.

```
adk-grounding/
  README.md
  pyproject.toml
  .env.example
  .gitignore

  config/
    settings.yaml
    logging.yaml

  corpora/
    adk-python/        # git clone (your fork or upstream mirror)
    adk-docs/          # git clone

  manifests/
    corpus_manifest.json
    ingestion_runs/
      YYYYMMDD-HHMMSS-run.json

  src/
    grounding/
      __init__.py

      clients/
        qdrant_client.py
        voyage_client.py

      contracts/
        document.py
        chunk.py
        ids.py

      util/
        hashing.py
        time.py
        fs_walk.py
        mime.py

      scripts/
        00_smoke_test_connections.py
        01_print_effective_config.py

  tests/
    test_config_loads.py
    test_voyage_smoke.py
    test_qdrant_smoke.py
```

**Notes**

* `corpora/` contains *cloned git repos* as the raw source-of-truth.
* `manifests/` makes ingestion reproducible: every ingestion run writes exactly what commit SHAs were used.
* `src/grounding/contracts/` will define strict payload schemas so later ingestion/retrieval is deterministic.

---

# 4) Repo Acquisition (Reproducible Clones)

You can use your fork(s). The only requirement is: **record commit SHAs**.

## 4.1 Clone corpora

Example commands (use your fork URLs as desired):

```bash
mkdir -p corpora
cd corpora

git clone https://github.com/google/adk-python.git
git clone https://github.com/google/adk-docs.git
```

(Repos: ([GitHub][2]))

## 4.2 Pin exact commits into a corpus manifest

Create `manifests/corpus_manifest.json`:

```json
{
  "adk_python": {
    "repo_path": "corpora/adk-python",
    "remote": "https://github.com/<YOU>/adk-python.git",
    "ref": "main",
    "commit": "<TO_BE_FILLED_BY_SCRIPT>"
  },
  "adk_docs": {
    "repo_path": "corpora/adk-docs",
    "remote": "https://github.com/<YOU>/adk-docs.git",
    "ref": "main",
    "commit": "<TO_BE_FILLED_BY_SCRIPT>"
  }
}
```

**Rule:** The ingestion pipeline must refuse to run unless both commits are resolved to concrete SHAs and written into the run manifest.

---

# 5) Secrets & Configuration (No Surprises)

## 5.1 Environment variables

Create `.env.example`:

```bash
# Voyage
VOYAGE_API_KEY="..."

# Qdrant Cloud
QDRANT_URL="https://xxxxxx-xxxxx-xxxxx-xxxx-xxxxxxxxx.<region>.<provider>.cloud.qdrant.io:6333"
QDRANT_API_KEY="..."

# Names (keep stable across runs)
QDRANT_COLLECTION="adk_grounding_v1"

# Retrieval tuning defaults (used later; define now so behavior is consistent)
RETRIEVAL_PREFETCH_LIMIT_DENSE="60"
RETRIEVAL_PREFETCH_LIMIT_SPARSE="80"
RETRIEVAL_FINAL_LIMIT="30"
RERANK_TOP_K="12"
```

### Why the Qdrant URL looks like that

The official qdrant-client README shows the cloud URL format includes `:6333` and uses `api_key` in the client constructor ([GitHub][10]).

## 5.2 `config/settings.yaml` (single source of truth)

Create `config/settings.yaml`:

```yaml
qdrant:
  url: ${QDRANT_URL}
  api_key: ${QDRANT_API_KEY}
  collection: ${QDRANT_COLLECTION}

voyage:
  api_key: ${VOYAGE_API_KEY}

  # Dense models
  docs_model: "voyage-context-3"
  code_model: "voyage-code-3"
  output_dimension: 2048
  output_dtype: "float"

  # Reranker
  rerank_model: "rerank-2.5"

vectors:
  dense_docs: "dense_docs"
  dense_code: "dense_code"
  sparse_lexical: "sparse_lexical"

retrieval_defaults:
  fusion: "rrf"
  prefetch_limit_dense: ${RETRIEVAL_PREFETCH_LIMIT_DENSE}
  prefetch_limit_sparse: ${RETRIEVAL_PREFETCH_LIMIT_SPARSE}
  final_limit: ${RETRIEVAL_FINAL_LIMIT}
  rerank_top_k: ${RERANK_TOP_K}
```

**Model grounding (official):**

* Voyage text embeddings models include `voyage-code-3` and support `output_dimension` up to 2048 with `output_dtype="float"` ([Voyage AI][7]).
* Voyage reranker includes `rerank-2.5` ([Voyage AI][8]).
* Contextualized chunk embeddings endpoint supports `model: "voyage-context-3"` ([Voyage AI][6]).

---

# 6) Dependency Setup (Pinned Enough to Reproduce)

## 6.1 Python dependencies

Minimum required libraries:

* `qdrant-client>=1.12.0` (cloud connection + query API)
* `voyageai>=0.3.0` (embeddings + reranking; requires Python <3.14)
* `pydantic>=2.0.0` (data contracts)
* `pydantic-settings>=2.0.0` (BaseSettings for config)
* `python-dotenv>=1.0.0` (local env loading)
* `pyyaml>=6.0.0` (YAML config parsing)
* `rich>=13.0.0` (logging and output formatting)

**Suggested install**

```bash
pip install qdrant-client voyageai pydantic pydantic-settings python-dotenv pyyaml rich
```

**Why qdrant-client**
The official qdrant-client repository documents cloud connection via `QdrantClient(url=..., api_key=...)` ([GitHub][10]) and supports Query API usage patterns that we’ll rely on in later specs (prefetch/fusion are part of Qdrant’s Query API design) ([Qdrant][5]).

---

# 7) Client Implementations (Thin, Deterministic)

## 7.1 Qdrant client wrapper (`src/grounding/clients/qdrant_client.py`)

Implement a minimal wrapper that:

* reads config
* instantiates `QdrantClient`
* exposes:

  * `healthcheck()`
  * `collection_exists(name)`
  * `get_collection_info(name)`
  * (later) `create_collection(...)`, `upsert_points(...)`, `query(...)`

**Cloud connection contract** (official):

```python
from qdrant_client import QdrantClient

client = QdrantClient(url="https://....cloud.qdrant.io:6333", api_key="...")  # :contentReference[oaicite:22]{index=22}
```

## 7.2 Voyage client wrapper (`src/grounding/clients/voyage_client.py`)

Expose three calls:

1. `embed_code(texts: list[str], input_type: "query"|"document") -> list[list[float]]`

   * Use `voyageai.Client.embed()`
   * Must pass:

     * `model="voyage-code-3"` ([Voyage AI][7])
     * `output_dimension=2048` ([Voyage AI][7])
     * `output_dtype="float"` ([Voyage AI][7])

2. `embed_docs_contextualized(inputs: list[list[str]], input_type: "query"|"document") -> list[list[float]]`

   * Use `voyageai.Client.contextualized_embed(...)`
   * Must pass: `model="voyage-context-3"`, `output_dimension=2048`, `output_dtype="float"`
   * **Return structure:** Returns a `ContextualizedEmbeddingsObject` with `.results` attribute. Each result has `.embeddings` (list of vectors for that document's chunks). Flatten via:
     ```python
     all_embeddings = []
     for doc_result in result.results:
         all_embeddings.extend(doc_result.embeddings)
     return all_embeddings
     ```

3. `rerank(query: str, docs: list[str], top_k: int) -> reranked`

   * Use `voyageai.Client.rerank(model="rerank-2.5")` ([Voyage AI][8])

---

# 8) Data Contracts (Defined Now, Used Everywhere Later)

These contracts ensure later ingestion/retrieval/reranking are consistent.

## 8.1 Canonical “Chunk” payload contract

Create `src/grounding/contracts/chunk.py` as a Pydantic model with fields like:

* `chunk_id` (string; globally unique)
* `source_corpus` (`"adk_docs"` | `"adk_python"`)
* `repo` (string; e.g., `google/adk-docs`)
* `ref` (branch/tag)
* `commit` (sha)
* `path` (file path inside repo)
* `language` (derived or null)
* `content_type` (e.g., `text/markdown`, `text/x-python`)
* `chunk_index` (int)
* `chunk_text` (string)
* `chunk_char_start` / `chunk_char_end` (int)
* `parent_doc_id` (stable id for the file)
* `title_hint` (optional; extracted from headings, filename, etc.)
* `created_at` (iso string)
* `hash` (sha256 of normalized chunk text)
* `metadata` (dict; flexible)

**Important:** Qdrant supports storing payload alongside vectors (we’ll use this heavily for filtering and debugging in later specs).

## 8.2 ID strategy (`src/grounding/contracts/ids.py`)

Define stable IDs:

* `parent_doc_id = sha1(corpus + ":" + commit + ":" + path)`
* `chunk_id = sha1(parent_doc_id + ":" + chunk_index + ":" + hash(chunk_text))`

**Rule:** If content changes, chunk_id must change, enabling safe upserts and deletes-by-parent later.

---

# 9) Smoke Tests (Must Pass Before Any Ingestion)

These scripts are required deliverables in this spec. A coding agent should run them before moving to Spec 2.

## 9.1 `00_smoke_test_connections.py`

**Checks**

1. Load config (env var substitution works)
2. Instantiate Voyage client
3. Instantiate Qdrant client
4. Qdrant: list collections (or get cluster info)
5. Voyage: embed a tiny string and rerank a 3-doc list

### Voyage requirements grounded in docs

* `voyage-code-3` exists and is intended for code retrieval ([Voyage AI][7])
* `rerank-2.5` exists and `voyageai.Client.rerank()` signature is documented ([Voyage AI][8])
* contextualized embeddings endpoint exists for `voyage-context-3` ([Voyage AI][6])

## 9.2 `01_print_effective_config.py`

Print fully resolved config, **redacting** secrets.

---

# 10) Acceptance Criteria (Spec 1 is “Done” Only If…)

You do **not** proceed to Spec 2 unless all are true:

1. ✅ **Repos present**: `corpora/adk-python` and `corpora/adk-docs` exist and are valid git repos ([GitHub][2])
2. ✅ **Manifest written**: a script resolves and writes commit SHAs into `manifests/ingestion_runs/<run>.json`
3. ✅ **Secrets configured**: `.env` created from `.env.example`
4. ✅ **Qdrant Cloud connectivity succeeds** using `QdrantClient(url=..., api_key=...)` ([GitHub][10])
5. ✅ **Voyage calls succeed**:

   * `embed(model="voyage-code-3", output_dimension=2048, output_dtype=float)` ([Voyage AI][7])
   * `contextualized_embed(model="voyage-context-3")` ([Voyage AI][6])
   * `rerank(model="rerank-2.5")` ([Voyage AI][8])
6. ✅ **Config is stable**: `config/settings.yaml` and vector-space names are defined and will not change across later specs.

---

# 11) Explicit Handoff to Spec 2/5 (What This Spec Produces)

After Spec 1, the coding agent will have:

* A working project skeleton
* Resolved corpus commit manifests
* Verified Qdrant Cloud connection
* Verified Voyage embeddings + contextualized embeddings + rerank
* Stable configuration names for:

  * Qdrant collection
  * vector space names
  * default retrieval knobs

**Spec 2 will assume all of this exists** and will proceed to:
✅ create the Qdrant collection with named vectors + sparse vectors, plus payload index strategy.

---

If you say **“Proceed to Spec 2”**, I’ll produce **SPEC 2/5 — Qdrant Collection Schema + Indexing + Hybrid Vector Space Setup** (fully detailed, implementation-ready).

[1]: https://github.com/google/adk-docs?utm_source=chatgpt.com "GitHub - google/adk-docs: An open-source, code-first toolkit for building, evaluating, and deploying sophisticated AI agents with flexibility and control."
[2]: https://github.com/google/adk-python?utm_source=chatgpt.com "GitHub - google/adk-python: An open-source, code-first Python toolkit for building, evaluating, and deploying sophisticated AI agents with flexibility and control."
[3]: https://qdrant.tech/documentation/concepts/vectors/ "Vectors - Qdrant"
[4]: https://qdrant.tech/documentation/concepts/points/ "Points - Qdrant"
[5]: https://qdrant.tech/documentation/concepts/hybrid-queries/ "Hybrid Queries - Qdrant"
[6]: https://docs.voyageai.com/docs/contextualized-chunk-embeddings "Contextualized Chunk Embeddings"
[7]: https://docs.voyageai.com/docs/embeddings "Text Embeddings"
[8]: https://docs.voyageai.com/docs/reranker "Rerankers"
[9]: https://google.github.io/adk-docs/?utm_source=chatgpt.com "Index - Agent Development Kit"
[10]: https://github.com/qdrant/qdrant-client "GitHub - qdrant/qdrant-client: Python client for Qdrant vector search engine"
