## SPEC 5/5 — Runtime Retrieval + Voyage Re-rank + Grounded “Evidence Pack” for IDE Coding Agents (Qdrant Cloud)

### 0) Purpose (what this spec guarantees)

This spec defines the **end-to-end runtime retrieval workflow** your coding agent will use to reliably ground implementation work in:

* **ADK docs** (embedded with `voyage-context-3`)
* **ADK Python code** (embedded with `voyage-code-3`)
* **Hybrid retrieval** (dense + sparse) in **Qdrant Cloud**
* **Cross-encoder re-ranking** with **Voyage `rerank-2.5`** (plus instruction-following)

The output is a structured, deterministic **Evidence Pack** that the coding agent uses to (1) plan work, (2) write correct code, and (3) cite the exact sources (doc URL anchors and repo file/line spans).

---

### 1) Assumptions / Preconditions (must already be true)

You already completed (from prior specs in this chain):

1. **Qdrant Cloud is provisioned** and reachable.
2. You created **two collections** (recommended for accuracy):

   * `adk_docs` (dense vectors from `voyage-context-3` + sparse vectors)
   * `adk_code` (dense vectors from `voyage-code-3` + sparse vectors)
3. Each point payload includes the minimum provenance required for citations:

   * `source_type`: `"docs"` or `"code"`
   * `repo`: e.g. `"google/adk-docs"` or `"google/adk-python"`
   * `ref`: immutable identifier (commit SHA strongly recommended)
   * `path`: file path in repo (or URL for docs)
   * `chunk_id`: stable chunk identifier
   * `text`: the chunk text (the thing you re-rank)
   * For code chunks: `start_line`, `end_line` (strongly recommended)
4. Sparse vectors exist and your query-time sparse generator matches ingestion.
5. You have Voyage API access for `rerank-2.5` (and embeddings already used in ingestion).

---

### 2) Why two collections (final decision for this build)

**This build uses two collections** for maximum retrieval accuracy because:

* Qdrant requires a fixed vector size per named vector field inside a collection; different embedding models can produce different dimensionality (and even if they happened to match, the spaces are not interchangeable for similarity search).
* Keeping docs and code dense embeddings separate prevents “semantic drift” and makes tuning per-domain retrieval parameters easier.
* The agent still retrieves from **both collections**, merges candidates, and uses **a single `rerank-2.5` step** to produce one unified ranked list.

This answers your earlier question: yes, docs and code are complementary, and the runtime should treat most developer tasks as **mixed grounding** (docs explain usage patterns; code shows real implementations). The agent will retrieve from both by default and only narrow when it has a strong reason to. (That’s a runtime rule, not “agreeing with you.”)

---

### 3) Runtime inputs / outputs

#### 3.1 Inputs

At runtime, the retrieval subsystem is called with:

* `user_query: str` — the agent’s current question/task (e.g. “build a multi-agent workflow with ADK sessions/state and tool calling”)
* `task_mode: Literal["build", "debug", "explain", "refactor"]` — used only to steer rerank instruction
* Optional constraints:

  * `repo_ref_hint` (commit SHA / tag)
  * `path_allowlist` / `path_blocklist` (you said you’ll define later; this system supports it)
  * `max_results_final` (default 12)
  * `time_budget_ms` (soft budget; used for early stops and batching)

#### 3.2 Outputs — Evidence Pack (the only thing the agent needs)

A structured object:

```json
{
  "query": "...",
  "retrieval_plan": {
    "collections_queried": ["adk_docs", "adk_code"],
    "hybrid_fusion": "rrf",
    "prefetch_limits": {"dense": 80, "sparse": 120},
    "qdrant_search_params": {"hnsw_ef": 256, "exact": false}
  },
  "candidates": [
    {
      "rank": 1,
      "rerank_score": 0.93,
      "collection": "adk_docs",
      "source_type": "docs",
      "repo": "google/adk-docs",
      "ref": "COMMIT_SHA",
      "path_or_url": "https://google.github.io/adk-docs/tools-custom/function-tools/",
      "chunk_id": "docs:tools-custom:function-tools:0007",
      "text": "…",
      "citation": "adk-docs@COMMIT_SHA:tools-custom/function-tools#Lxx-Lyy"
    }
  ],
  "coverage": {
    "docs_in_top_k": 8,
    "code_in_top_k": 4
  },
  "warnings": [],
  "debug": {
    "qdrant": {...},
    "voyage": {...}
  }
}
```

---

### 4) Retrieval strategy (hybrid + two-collection + rerank)

#### 4.1 Overview

1. **Normalize + expand** the query (lightweight, deterministic).
2. Create **two dense query embeddings**:

   * docs query vector using docs model
   * code query vector using code model
3. Create **one sparse query representation** (same method you used at ingestion).
4. For each collection:

   * Run **Qdrant Query API** using `prefetch` for dense + sparse and fuse with RRF/DBSF.
   * Return top **M candidates** with payload text + provenance.
5. Merge candidates across both collections.
6. Send candidates to **Voyage `rerank-2.5`** with an instruction-steered query.
7. Emit a final ranked Evidence Pack.

Qdrant’s Query API supports `prefetch` and fusion (RRF/DBSF) in one request, eliminating client-side merging for hybrid search. ([Qdrant][1])
Voyage rerankers are designed to re-rank a candidate list from embedding-based retrieval, and `rerank-2.5` supports instruction-following. ([Voyage AI][2])

---

### 5) Step 1 — Query normalization + deterministic expansion

This is not “LLM query rewriting.” It’s a simple deterministic enhancement to improve recall and reduce misses.

#### 5.1 Normalize

* Trim whitespace, collapse internal whitespace.
* Preserve casing (code identifiers can be case-sensitive).
* Extract **identifier-like tokens** (regex `\b[A-Za-z_][A-Za-z0-9_]*\b`) for optional “lexical emphasis” (used only in sparse generation if supported).

#### 5.2 Expand into 2–4 sub-queries (deterministic templates)

Generate a small set of parallel queries:

* `Q0`: original user query
* `Q1`: “ADK Python official usage: {user_query}”
* `Q2`: “Agent Development Kit tool calling sessions state: {user_query}”
* Optional `Q3` if code-heavy signals (detect `snake_case`, `.py`, `FunctionTool`, etc.):

  * “In code: {identifiers} {user_query}”

**Why**: This helps both dense and sparse branches retrieve anchored docs pages and canonical implementations.

Runtime rule: You do **not** embed 4× and explode cost; you embed **Q0** by default, and only embed secondary queries when:

* The first pass yields too few candidates, or
* Scores are weak / below threshold, or
* The agent is failing a grounding quality gate (Section 10).

---

### 6) Step 2 — Build query vectors (docs + code + sparse)

#### 6.1 Dense query vectors (two embeddings)

* `docs_query_vector = embed(user_query, model="voyage-context-3")`
* `code_query_vector = embed(user_query, model="voyage-code-3")`

Each is used only against its matching collection.

#### 6.2 Sparse query representation (must match ingestion)

Qdrant sparse vectors are represented as `indices` + `values` arrays in query payload. ([Qdrant][3])
Your sparse encoder must output:

* `sparse_indices: List[int]`
* `sparse_values: List[float]`

> If you used SPLADE at ingestion, your runtime must run the same SPLADE query encoder and post-process the sparse vector the same way (pruning, normalization, top-n nonzeros).

---

### 7) Step 3 — Qdrant hybrid retrieval per collection (single call with prefetch + fusion)

#### 7.1 Use Qdrant Query API with `prefetch`

Qdrant’s Query API supports:

* `prefetch` (sub-requests)
* `using` (named vector selection)
* `filter`
* `params` / `search_params` including `hnsw_ef` and `exact` ([Qdrant][4])

#### 7.2 Recommended defaults for accuracy-first hybrid

* `fusion`: start with **RRF** (robust when score scales differ between sparse/dense)
* `dense_prefetch_limit`: 80
* `sparse_prefetch_limit`: 120
* `final_limit_per_collection`: 60
* `hnsw_ef`: 256 (increase if needed; Qdrant explicitly documents `hnsw_ef` as accuracy vs speed knob) ([Qdrant][5])
* `exact`: false (use true only for evaluation comparisons; can be slow) ([Qdrant][5])

#### 7.3 Python client call shape (authoritative interface)

The Qdrant Python client exposes `query_points(...)` with `prefetch`, `using`, `query_filter`, `search_params`, `with_payload`, etc. ([python-client.qdrant.tech][6])

**Docs collection** (dense uses docs_query_vector):

```python
from qdrant_client import models

docs_resp = client.query_points(
    collection_name="adk_docs",
    prefetch=[
        models.Prefetch(
            query=docs_query_vector,
            using="dense",
            limit=80,
        ),
        models.Prefetch(
            query=models.SparseVector(indices=sparse_indices, values=sparse_values),
            using="sparse",
            limit=120,
        ),
    ],
    query=models.FusionQuery(fusion=models.Fusion.RRF),
    search_params=models.SearchParams(hnsw_ef=256, exact=False),
    with_payload=True,
    with_vectors=False,
    limit=60,
)
```

**Code collection** (dense uses code_query_vector):

```python
code_resp = client.query_points(
    collection_name="adk_code",
    prefetch=[
        models.Prefetch(
            query=code_query_vector,
            using="dense",
            limit=80,
        ),
        models.Prefetch(
            query=models.SparseVector(indices=sparse_indices, values=sparse_values),
            using="sparse",
            limit=120,
        ),
    ],
    query=models.FusionQuery(fusion=models.Fusion.RRF),
    search_params=models.SearchParams(hnsw_ef=256, exact=False),
    with_payload=True,
    with_vectors=False,
    limit=60,
)
```

Notes:

* The “fusion query” pattern is shown in Qdrant hybrid Query API examples. ([Qdrant][7])
* If you later choose DBSF, Qdrant documents it as `"fusion": "dbsf"` for hybrid `prefetch` fusion. ([Qdrant][3])

#### 7.4 Filtering (optional but supported)

Qdrant filtering supports `must`, `should`, `must_not` logic over payload fields. ([Qdrant][8])
Typical filters you’ll add later:

* `source_type == "docs"` / `"code"` (if you ever query a combined collection)
* `path` allowlist/blocklist
* `repo_ref` pinning (if you store it as payload)

---

### 8) Step 4 — Candidate canonicalization + merge (cross-collection)

After you receive 2× results:

#### 8.1 Canonical candidate object

Normalize each hit into:

* `candidate_id`: stable unique ID for merging/dedup
  Recommended: `{repo}@{ref}:{path}:{chunk_id}` (not Qdrant point ID, since you have two collections)
* `collection`: `adk_docs` / `adk_code`
* `text`: payload chunk text
* `provenance`: repo/ref/path/start_line/end_line/url
* `qdrant_score`: the returned score (for debugging only; rerank will decide)

#### 8.2 Dedup rules (strict)

You want rerank to compare distinct evidence, not repeated slices.

Dedup in this order:

1. Exact match of `candidate_id`
2. Exact match of `(repo, ref, path, start_line, end_line)` for code
3. Near-duplicate text hash (normalize whitespace, hash) — keep the one with richer provenance fields

#### 8.3 Candidate pool size for rerank

Target **120–180 total candidates** combined.

Default:

* take up to 90 from docs + 90 from code
* if one side is weak, borrow slots from the other

---

### 9) Step 5 — Voyage `rerank-2.5` (instruction-following, token-safe, batched)

#### 9.1 Authoritative API contract

Voyage rerank is called as `voyageai.Client.rerank(query, documents, model, top_k, truncation)` and is explicitly designed to re-rank preliminary embedding search results. ([Voyage AI][2])
`rerank-2.5` supports a 32K context per query+doc pair and instruction-following appended to the query. ([Voyage AI][2])
You must also respect rate limits. ([Voyage AI][9])

#### 9.2 Build rerank “documents” (critical for accuracy)

Rerank input is a list of strings. You must present each candidate in a way that helps a cross-encoder judge usefulness.

**Doc format template (use exactly this ordering):**

1. Source header line (short, consistent)
2. Provenance (repo/ref/path/url)
3. Optional “symbol” fields if you store them (class/function names)
4. The chunk text

Example doc string:

```
SOURCE: docs
REPO: google/adk-docs
REF: <commit_sha>
LOC: https://google.github.io/adk-docs/tools-custom/function-tools/
CHUNK: docs:tools-custom:function-tools:0007

<chunk text here…>
```

For code:

```
SOURCE: code
REPO: google/adk-python
REF: <commit_sha>
PATH: adk/agents/.../some_file.py
LINES: 120-185
CHUNK: code:adk/agents/...:0012

<chunk text here…>
```

Why this matters:

* You’re not only ranking “semantic similarity.” You’re ranking “utility for correct implementation,” and provenance improves that discrimination.

#### 9.3 Rerank query instruction (accuracy-first)

Because `rerank-2.5` supports instructions appended/prepended to the query, you should steer it to prefer canonical sources and implementation-ready guidance. ([Voyage AI][2])

Use this instruction wrapper:

```
You are ranking evidence to help implement a correct solution using Google ADK.
Prefer: official ADK docs that describe the exact API and constraints, and ADK Python source that demonstrates real patterns.
Prefer: content that directly answers the question and includes concrete parameters, function/class names, and usage patterns.
Deprioritize: tangential mentions, outdated references, or generic LLM commentary.
Question: {user_query}
```

(Yes, this is “prompting a reranker.” It is explicitly supported by `rerank-2.5` instruction-following.) ([Voyage AI][10])

#### 9.4 Token safety: enforce with Voyage tokenizer + truncation

Voyage provides a tokenizer helper: `voyageai.Client.tokenize(texts, model=...)`. ([Voyage AI][11])
Rerank supports `truncation=True` to auto-truncate to context limits. ([Voyage AI][2])

**Hard rules:**

* Keep candidate count ≤ 250 by default.
* If candidate text is long, pre-trim before rerank:

  * Keep header/provenance always
  * Keep first N tokens of chunk body (N=1200 tokens recommended)
* Always call rerank with `truncation=True` as the final guardrail. ([Voyage AI][2])

Also respect global rerank token budgeting constraints from Voyage docs (query/document limits and total token budgeting). ([Voyage AI][2])

#### 9.5 Batching strategy (no ambiguity)

Even though Voyage supports up to 1000 docs per request, you should batch to:

* reduce chance of hitting token ceilings
* reduce retry blast radius

**Batch size defaults:**

* `rerank_batch_size = 60` documents per request
* `rerank_top_k_per_batch = None` (return all scores), then merge scores
* OR set `top_k` only on the final merged request if you rerank once

**Recommended:** rerank once with 120–180 docs (often fits comfortably). Use batching only if token estimator says you might exceed.

#### 9.6 Expected output shape and mapping

Voyage rerank returns relevance scores aligned to input documents; you must preserve original candidate ordering to map back to provenance. ([Voyage AI][2])

Implementation requirement:

* maintain `doc_index -> candidate_id` mapping
* store rerank score as `rerank_score`

---

### 10) Step 6 — Evidence Pack finalization (grounding quality gates)

After rerank, you select final K (default 12) and enforce deterministic grounding quality gates.

#### 10.1 Select top K

* `top_k_final = 12` (default)
* keep `top_k_buffer = 20` for internal checks and fallback

#### 10.2 Coverage gate (docs + code complementarity)

For `task_mode in {"build","debug","refactor"}`:

* Require at least:

  * `min_docs = 3` in top 12
  * `min_code = 3` in top 12
    If gate fails:
* Expand pool from the missing side:

  * increase that collection’s `final_limit_per_collection` from 60 → 90
  * rerank again
    If still failing:
* allow override but emit a warning.

This is the concrete, verifiable answer to “docs and code are complementary”:

* In implementation modes, the system **forces mixed grounding** unless it is genuinely unavailable.

#### 10.3 Provenance completeness gate

Before a candidate can be included in the final Evidence Pack:

* If `source_type=="docs"`: must include a stable URL.
* If `source_type=="code"`: must include `path` and ideally `start_line/end_line`.
  If line spans are missing, you still include the chunk but set:

  * `citation_confidence = "medium"`
  * and add a warning: “line spans unavailable”

#### 10.4 Citation formatting (deterministic)

Emit citations in a consistent format so the coding agent can drop them into final responses.

* Docs: `adk-docs@<commit_sha>:<url>`
* Code: `adk-python@<commit_sha>:<path>#L<start>-L<end>`

Even if you can’t fetch line numbers at runtime, do not invent them. Only emit what’s in payload.

---

### 11) Step 7 — Tool interface for ADK agent (how the coding agent calls retrieval)

You’ll expose the retrieval module to ADK as a tool function.

ADK wraps Python functions in `FunctionTool` by inspecting signature, docstring, and type hints. ([Google GitHub Page][12])
Return should be a `dict` with descriptive keys; including a `status` key is recommended. ([Google GitHub Page][13])

**Tool contract:**

```python
def retrieve_adk_evidence(
    query: str,
    task_mode: str = "build",
    max_results_final: int = 12,
) -> dict:
    """
    Retrieve and rerank official ADK docs + ADK python code evidence for grounding implementation work.

    Args:
      query: The developer question or task request.
      task_mode: One of build|debug|explain|refactor. Used to steer reranking.
      max_results_final: Number of final reranked items to return.

    Returns:
      A dict with keys:
        status: success|no_results|error
        evidence_pack: {...}  # structured as in this spec
        warnings: [...]
        debug: {...}
    """
```

---

### 12) Observability (implementation-level, accuracy-driven; not “governance”)

For accuracy tuning, you must log enough to reproduce any miss.

Log event schema per retrieval call:

* `query_id` (uuid)
* `query_text`
* `collections_queried`
* `qdrant_request_params` (prefetch limits, fusion, hnsw_ef)
* `qdrant_result_ids` (top 200 candidate_ids + scores)
* `rerank_model`, `rerank_instruction_hash`, `rerank_batching`
* `final_top_k candidate_ids + rerank_scores`
* `coverage metrics` (docs/code counts)
* `warnings`

Do **not** log full chunk text by default (too noisy); log chunk_id + provenance and keep text only in Evidence Pack output.

---

### 13) Evaluation harness (how you *prove* retrieval accuracy is optimal)

This is how you tune the system without guesswork.

#### 13.1 Build a small “golden set”

Create 30–80 queries across categories:

* tool calling / FunctionTools
* sessions/state/memory
* multi-agent orchestration patterns
* deployment topics if present in docs
* common code-level tasks (add tool, create agent, use callbacks, etc.)

For each query:

* store 3–8 “expected” evidence items (by `candidate_id`), not just “expected answer text.”

#### 13.2 Metrics to compute per run

Compute:

* `Recall@K` (K=20, 50) before rerank and after rerank
* `MRR@12` (Mean Reciprocal Rank)
* `nDCG@12` (if you add graded relevance later)

#### 13.3 Tuning knobs (in decreasing order of impact)

1. Candidate pool sizes:

   * per-collection final limit (60→90)
   * dense/sparse prefetch limits (80/120 → 120/160)
2. Fusion method:

   * RRF vs DBSF (Qdrant documents both) ([Qdrant][3])
3. `hnsw_ef`:

   * 128 → 256 → 512 for dense queries (accuracy improves with higher ef; Qdrant documents this tradeoff) ([Qdrant][5])
4. Query expansion:

   * enable Q1/Q2 fallback embedding when low results
5. Rerank instruction:

   * small edits only; keep stable for reproducibility

#### 13.4 “Exact mode” spot-check

Use `exact=True` on a small evaluation sample to compare ANN misses (Qdrant documents `exact` as full scan). ([Qdrant][14])
You do not run exact in production; it’s an evaluation lens.

---

### 14) Rate limits + retries (deterministic behavior under failure)

Voyage publishes RPM/TPM limits by model; `rerank-2.5` has specific TPM/RPM tiers. ([Voyage AI][9])

#### 14.1 Retry policy

* Qdrant:

  * retry on 429/503 with exponential backoff (max 3 tries)
* Voyage rerank:

  * retry on 429/503 with exponential backoff (max 3 tries)
  * if still failing: fall back to Qdrant fused order and emit warning `"rerank_unavailable"`

#### 14.2 Timeouts

* Qdrant query timeout: 8–12 seconds
* Voyage rerank timeout: 20 seconds (rerank is heavier)

---

### 15) Implementation checklist (what the coding agent must build)

**A. Retrieval Core**

* [ ] Query normalization + deterministic expansion
* [ ] Dense embedder wrappers (docs + code) (already exist if you did ingestion; reuse)
* [ ] Sparse query generator matching ingestion
* [ ] Qdrant hybrid query function per collection using Query API `prefetch` + fusion ([Qdrant][1])
* [ ] Candidate canonicalization + dedup

**B. Reranking**

* [ ] Build rerank documents with provenance headers
* [ ] Implement token-safe trimming + truncation=True ([Voyage AI][2])
* [ ] Call `voyageai.Client.rerank(..., model="rerank-2.5")` ([Voyage AI][2])
* [ ] Map results back to candidate_ids

**C. Evidence Pack**

* [ ] Coverage gate enforcement
* [ ] Citation formatting rules
* [ ] Debug payload + warning emission

**D. ADK Tool**

* [ ] Expose as a typed Python function tool with strong docstring and dict return ([Google GitHub Page][12])

**E. Evaluation harness**

* [ ] Golden set format
* [ ] Metrics runner (Recall@K, MRR, nDCG)
* [ ] Config sweep runner for fusion/limits/ef

---

If you want to proceed cleanly from here, your next message should be: **“Spec 6 isn’t needed—now generate the implementation plan as tasks/issues for the coding agent”** (or tell me your preferred repo structure), and I’ll translate these specs into a stepwise build queue with acceptance criteria.

[1]: https://qdrant.tech/course/essentials/day-5/universal-query-api/?utm_source=chatgpt.com "The Universal Query API - Qdrant"
[2]: https://docs.voyageai.com/docs/reranker?utm_source=chatgpt.com "Rerankers"
[3]: https://qdrant.tech/blog/qdrant-1.11.x/?utm_source=chatgpt.com "Qdrant 1.11 - The Vector Stronghold: Optimizing Data Structures for Scale and Efficiency - Qdrant"
[4]: https://api.qdrant.tech/master/api-reference/search/query-points?utm_source=chatgpt.com "Query points | Qdrant | API Reference"
[5]: https://qdrant.tech/documentation/guides/optimize/?utm_source=chatgpt.com "Optimize Performance - Qdrant"
[6]: https://python-client.qdrant.tech/qdrant_client.qdrant_client?utm_source=chatgpt.com "qdrant_client.qdrant_client module — Qdrant Client documentation"
[7]: https://qdrant.tech/articles/hybrid-search/?utm_source=chatgpt.com "Hybrid Search Revamped - Building with Qdrant's Query API - Qdrant"
[8]: https://qdrant.tech/documentation/concepts/filtering/?utm_source=chatgpt.com "Filtering - Qdrant"
[9]: https://docs.voyageai.com/docs/rate-limits?utm_source=chatgpt.com "Rate Limits"
[10]: https://blog.voyageai.com/2025/08/11/rerank-2-5/?utm_source=chatgpt.com "rerank-2.5 and rerank-2.5-lite: instruction-following rerankers – Voyage AI"
[11]: https://docs.voyageai.com/docs/tokenization?utm_source=chatgpt.com "Tokenization"
[12]: https://google.github.io/adk-docs/tools-custom/function-tools/?utm_source=chatgpt.com "Overview - Agent Development Kit"
[13]: https://google.github.io/adk-docs/tools-custom/?utm_source=chatgpt.com "Custom Tools for ADK - Agent Development Kit"
[14]: https://qdrant.tech/documentation/search/?utm_source=chatgpt.com "Search - Qdrant"
