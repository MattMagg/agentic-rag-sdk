## SPEC 5/5 — Runtime Retrieval + Hybrid Fusion (Qdrant) + Voyage `rerank-2.5` + ADK Evidence Pack

### 0) Purpose

Implement the runtime retrieval layer that your IDE coding agent will call to ground development work in:

* **Hybrid retrieval** (dense + sparse) from **Qdrant Cloud**
* **Cross-encoder reranking** using **Voyage `rerank-2.5`**

Output is a deterministic **Evidence Pack** that the agent uses to:

1. pick correct ADK patterns and APIs,
2. implement code grounded in official sources,
3. cite exact provenance (repo/ref/path/lines or URL anchors).

---

### 1) Preconditions (must already be true)

This spec assumes Specs 1–4 already delivered:

1. Qdrant Cloud endpoint and API key are available.
2. Collection `adk_grounding_v1` exists with:

   * named dense vectors `dense_docs` and `dense_code` (2048, Cosine)
   * named sparse vector `sparse_lexical` ([Qdrant][1])
3. Points are ingested such that:

   * docs points include `dense_docs` and omit `dense_code`
   * code points include `dense_code` and omit `dense_docs`
   * both include `sparse_lexical`
   * payload contains `text` + provenance
4. Voyage API key is configured for reranking and embeddings.
5. The agent runtime can call a Python function tool in ADK. ([Google GitHub][6])

---

### 2) Interfaces: Inputs → Evidence Pack Output

#### 2.1 Tool function signature (ADK)

Expose one function to ADK tools:

```python
def retrieve_adk_evidence(
    query: str,
    mode: str = "build",
    top_k_final: int = 12,
    filter_spec: dict | None = None,
) -> dict:
    """
    Retrieve and rerank official ADK evidence from Qdrant (hybrid) and Voyage rerank-2.5.

    Args:
      query: Developer request/question.
      mode: build|debug|explain|refactor (steers rerank instruction only).
      top_k_final: final number of evidence items to return.
      filter_spec: optional payload filter constraints (repo/path/ref allowlists, etc).

    Returns:
      dict with keys:
        status: success|no_results|error
        evidence_pack: {...}
        warnings: [...]
        debug: {...}
    """
```

ADK will wrap this automatically as a FunctionTool, deriving schema from signature + docstring + type hints/defaults; required parameters are those with type hints and no defaults. ([Google GitHub][6])

#### 2.2 Evidence Pack schema

Return an object shaped like:

```json
{
  "query": "...",
  "mode": "build",
  "retrieval": {
    "collection": "adk_grounding_v1",
    "fusion": "rrf",
    "prefetch_limits": {
      "dense_docs": 80,
      "dense_code": 80,
      "sparse_lexical": 120
    },
    "final_candidate_limit": 80
  },
  "evidence": [
    {
      "rank": 1,
      "rerank_score": 0.93,
      "source_type": "adk_docs",
      "repo": "google/adk-docs",
      "ref": "COMMIT_SHA",
      "path_or_url": "https://…",
      "chunk_id": "…",
      "text": "…",
      "citation": "adk-docs@COMMIT_SHA:https://…#…",
      "citation_confidence": "high"
    }
  ],
  "coverage": { "adk_docs": 8, "adk_python": 4 },
  "warnings": [],
  "debug": { "qdrant": {...}, "voyage": {...} }
}
```

---

### 3) Runtime Flow (deterministic sequence)

**Step A — Normalize query** (deterministic, no LLM rewrite)
**Step B — Compute query vectors**

* `q_dense_docs`: Voyage `voyage-context-3` (query mode)
* `q_dense_code`: Voyage `voyage-code-3` (query mode)
* `q_sparse`: sparse encoder → `indices` + `values`

**Step C — Qdrant hybrid query** (one request):

* `prefetch`: dense_docs + dense_code + sparse_lexical
* `query`: `fusion="rrf"` baseline (or optional `dbsf`)
* `limit`: candidates (80)

**Step D — Candidate normalization/dedup**
**Step E — Voyage rerank-2.5** (single merged list, truncation on)
**Step F — Coverage gates + finalize top K**
**Step G — Emit Evidence Pack** with citations and debug metadata

Hybrid query structure is officially documented with `prefetch` and RRF fusion. ([Qdrant][3])

---

### 4) Query normalization (minimal but useful)

Do:

* trim whitespace, collapse internal whitespace
* extract identifier-like tokens for optional lexical emphasis (regex `\b[A-Za-z_][A-Za-z0-9_]*\b`)

Don’t:

* paraphrase
* “rewrite” semantics
* inject assumptions

---

### 5) Qdrant Hybrid Query (single collection, three lanes)

#### 5.1 Baseline knobs (accuracy-first)

* `prefetch_dense_docs_limit = 80`
* `prefetch_dense_code_limit = 80`
* `prefetch_sparse_limit = 120`
* `candidate_limit = 80`
* Fusion: `rrf` baseline (robust across different score scales)
* Optional: switch to `dbsf` after evaluation; Qdrant explicitly documents DBSF as a hybrid fusion mode. ([Qdrant][7])

#### 5.2 Canonical request shape (REST)

Hybrid Queries doc gives the exact pattern: `prefetch` array + `query: { fusion: "rrf" }`. ([Qdrant][3])

Conceptual JSON:

```json
{
  "prefetch": [
    { "query": [ ... ], "using": "dense_docs", "limit": 80 },
    { "query": [ ... ], "using": "dense_code", "limit": 80 },
    {
      "query": { "indices": [ ... ], "values": [ ... ] },
      "using": "sparse_lexical",
      "limit": 120
    }
  ],
  "query": { "fusion": "rrf" },
  "limit": 80,
  "with_payload": true,
  "with_vector": false
}
```

Sparse vectors are represented as non-zero indices + values in Qdrant docs. ([Qdrant][2])

#### 5.3 Filtering (optional)

If `filter_spec` exists, translate it to Qdrant filter clauses (`must`, `must_not`, `should`) over payload fields and attach at top-level in the query request. (This is standard Qdrant behavior described in their concepts docs; keep it payload-only and deterministic.)

---

### 6) Candidate normalization + dedup

Normalize each hit into:

* `candidate_id`: `{repo}@{ref}:{path_or_url}:{chunk_id}`
* `source_type`: `adk_docs` or `adk_python` (from `corpus` payload field)
* `repo`, `ref`, `path_or_url`, `chunk_id`
* `start_line/end_line` if code
* `text` (the chunk)
* `qdrant_score` (debug only)

Dedup rules:

1. exact `candidate_id`
2. exact `(repo, ref, path, start_line, end_line)` for code
3. normalized text hash fallback

---

### 7) Voyage `rerank-2.5` (official behavior + token constraints)

#### 7.1 Why rerank

Voyage reranker docs explicitly describe reranking as the second stage after embedding retrieval, improving ranking accuracy. ([Voyage AI][5])

#### 7.2 Official API contract

Use:
`Client.rerank(query: str, documents: List[str], model: str, top_k: Optional[int] = None, truncation: bool = True)` ([Voyage AI][5])

Rules from the official docs that your implementation must enforce:

* max documents ≤ 1000
* query token limit and pairwise context length limit
* total token budget constraints
* set `truncation=True` to avoid hard errors ([Voyage AI][5])

#### 7.3 Construct rerank “documents” (string format matters)

Each candidate passed to rerank should be a single string:

```
SOURCE_TYPE: adk_docs|adk_python
REPO: google/adk-docs|google/adk-python
REF: <sha>
PATH_OR_URL: <...>
LINES: <start-end or null>
CHUNK_ID: <...>

<chunk text>
```

This improves reranker discrimination because it sees provenance + content together.

#### 7.4 Instruction wrapper (supported)

For `rerank-2.5`, Voyage explicitly supports adding instructions alongside the query to guide relevance. ([Voyage AI][5])

Example wrapper (deterministic, short):

```
Rank evidence for correct Google ADK implementation. Prefer official ADK docs and official ADK Python source. Prefer concrete APIs, parameters, and canonical patterns. Deprioritize tangential mentions.
QUERY: {query}
```

---

### 8) Coverage gates (docs + code complementarity enforced)

Default `top_k_final=12`.

Unless user explicitly requests docs-only or code-only:

* require at least **3 docs** and **3 code** in final 12.

If gate fails:

1. raise `candidate_limit` to 120 and rerun (Qdrant + rerank once)
2. if still failing, return best effort and add warning `coverage_gate_failed`

This operationalizes “docs and code are complementary” without assuming it always happens automatically.

---

### 9) Citation formatting (machine + human usable)

* Docs:

  * `adk-docs@{ref}:{url}#{chunk_id}`
* Code:

  * if line spans exist: `adk-python@{ref}:{path}#L{start}-L{end}`
  * else: `adk-python@{ref}:{path}#{chunk_id}` + `citation_confidence="medium"`

---

### 10) Failure handling (deterministic fallbacks)

1. **Voyage rerank failure**

   * fallback ordering: Qdrant fused ordering
   * warning: `rerank_unavailable_fallback_to_qdrant`

2. **Sparse encoder failure**

   * drop sparse prefetch lane, query only dense lanes, keep fusion (RRF over two lanes)
   * warning: `sparse_unavailable_dense_only`

3. **One dense embedding failure**

   * drop that lane, keep the other + sparse
   * warning: `dense_docs_unavailable` or `dense_code_unavailable`

Named vectors being optional per point makes this safe (points without that vector simply aren’t comparable in that lane). ([Qdrant][4])

---

### 11) Evaluation harness hooks (so “optimal config” is not guesswork)

Record per retrieval call:

* candidate counts per lane (docs dense / code dense / sparse)
* fusion mode
* limits
* rerank token truncation events
* final coverage stats
* top-K candidate IDs

Tune in this order:

1. prefetch limits
2. candidate_limit
3. fusion method (RRF → DBSF)
4. sparse encoder pruning/normalization
5. rerank doc formatting + instruction

Hybrid fusion options are documented by Qdrant (RRF, DBSF). ([Qdrant][3])
