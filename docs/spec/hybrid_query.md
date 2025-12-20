## Spec 4 of 5 — Runtime Retrieval: Hybrid Querying in Qdrant (Voyage dense + SPLADE sparse), Evidence Packs, and ADK Tool Interface

### 0) Purpose and scope (what this spec *fully* defines)

This spec defines the **entire runtime retrieval workflow** for your IDE coding agents:

* How a user/developer question becomes a **hybrid Qdrant query** (dense + sparse).
* How you run **parallel prefetch searches** and fuse them **server-side** using Qdrant’s **Universal Query API** (prefetch → fusion) in **one request**. ([Qdrant][1])
* How you apply **filters** (global + prefetch-specific), and how those filters are represented. ([Qdrant][1])
* How you parse results into a deterministic **Evidence Pack** format suitable for grounding an implementation agent.
* How you expose this as an **ADK Function Tool** (schema-driven, strongly typed signature, docstring contract) that your agents can call reliably. ([Google GitHub Page][2])

**Explicit non-scope:** ingestion, chunking, collection creation, payload indexing, upserts (covered by earlier specs). This spec assumes the Qdrant collection(s) already exist and contain points for:

* **Docs chunks** embedded with `voyage-context-3` (dense named vector field)
* **Code chunks** embedded with `voyage-code-3` (dense named vector field)
* **Lexical/sparse chunks** embedded with SPLADE++ (sparse named vector field)

---

### 1) Ground-truth primitives and constraints (must be true before implementing this spec)

#### 1.1 Qdrant supports multi-vector fields and selecting a vector field at query time

At query time, if your collection has multiple vector fields, you select which one to search with `using`. ([Qdrant][3])

#### 1.2 Qdrant Universal Query API structure you will use

You will use the **prefetch stage** to run multiple searches in parallel, then fuse results via **RRF** (or DBSF, but this spec standardizes on RRF), returning a final top-K list—**all in one request**. ([Qdrant][1])

#### 1.3 Filters are first-class and can be global or prefetch-specific

* Qdrant filtering uses `filter: { must: [...], should: [...], must_not: [...] }` with conditions like `match` and `range`. ([Qdrant][4])
* In Universal Query API, **global filters propagate** to all prefetches unless overridden, and individual prefetches can add extra constraints. ([Qdrant][1])

---

### 2) Retrieval design goals (hard requirements)

Your runtime retrieval must satisfy these requirements:

1. **Highest retrieval accuracy** (priority)
2. **Deterministic evidence formatting** for an implementation agent (stable structure, predictable quotas, deduping)
3. **Hybrid recall**: semantic + lexical must both contribute
4. **Code+Docs complementarity**: answers should incorporate both when relevant (unless the intent is explicitly code-only or docs-only)
5. **One call to Qdrant per user query** for candidate generation (prefetch + fusion server-side), minimizing glue logic. ([Qdrant][1])

---

### 3) Input → intent classification (deterministic, no “maybe”)

Your retrieval tool will accept an explicit `intent` parameter, and if the caller doesn’t provide it, your tool will classify using the rules below and then **set** it.

#### 3.1 Intent enum (canonical)

Use exactly these values:

* `HOW_TO_IMPLEMENT` — “How do I build X with ADK?”, “show me the pattern”, “how do I wire tools/state”
* `API_LOOKUP` — “What does class/method X do?”, “params for Y”
* `CODE_EXAMPLE` — “Find an example of Z”, “where is X used”
* `DEBUG_ERROR` — stacktrace/error text; find relevant source + docs
* `CONCEPTUAL` — architecture/concepts; docs-heavy but still code grounded
* `MIGRATION_OR_VERSION` — “what changed”, “deprecated”, “v0.x behavior”
* `TARGETED_FILE` — caller provides a path/module target
* `CODE_ONLY` / `DOCS_ONLY` — forced scope

#### 3.2 Intent classifier (rules)

If `intent` absent:

* If query contains stack trace markers (`Traceback`, `Exception`, `Error:`) → `DEBUG_ERROR`
* If query contains “parameter”, “signature”, “return type”, “what does X do” → `API_LOOKUP`
* If query contains “example”, “sample”, “where is”, “used in” → `CODE_EXAMPLE`
* If query contains “implement”, “build”, “create agent”, “multi-agent workflow” → `HOW_TO_IMPLEMENT`
* If query contains “concept”, “overview”, “difference between”, “when to use” → `CONCEPTUAL`
* If query contains “deprecated”, “changed”, “version”, “release” → `MIGRATION_OR_VERSION`
* If query includes an explicit path-like token (`/`, `.py`, `src/`, `google/adk/...`) → `TARGETED_FILE`

This classifier is intentionally simple because the **accuracy driver is retrieval + rerank**, not sophisticated intent ML.

---

### 4) Query embedding generation (dense + sparse) — exact runtime contract

You will compute **three** query representations for every query unless intent forces a narrower scope:

1. `q_dense_docs` — Voyage **context** embedding (semantic match to docs chunks)
2. `q_dense_code` — Voyage **code** embedding (semantic match to code chunks)
3. `q_sparse` — SPLADE++ sparse vector (lexical/keyword match across both)

#### 4.1 `q_dense_docs` (Voyage)

* Model: `voyage-context-3`
* Use the Voyage contextualized embedding API in “query mode” (the docs show using `input_type="query"` in their embedding examples; follow that pattern for query embeddings). ([Voyage AI][5])

**Runtime requirement:** store/query dimension must match the vector field dimension configured in Qdrant (you standardized on 2048 + float32 earlier).

#### 4.2 `q_dense_code` (Voyage)

* Model: `voyage-code-3`
* Use `input_type="query"` for best retrieval behavior per Voyage embedding usage patterns. ([Voyage AI][6])

#### 4.3 `q_sparse` (SPLADE++)

* Use FastEmbed SPLADE++ to create sparse representations (indices + values) as required by Qdrant sparse vectors. ([Qdrant][7])
* SPLADE embeddings produce a `SparseEmbedding` object containing `indices` and `values`. ([Qdrant][7])
* Qdrant represents sparse vectors as `indices` + `values` arrays. ([Qdrant][8])

**Runtime requirement:** you must produce a sparse vector for the *query string* (you can do so by embedding the query as a one-item list, same mechanism shown for documents). ([Qdrant][7])

---

### 5) Qdrant query strategy (the canonical “one request” hybrid plan)

#### 5.1 Why this exact plan (no alternatives in implementation)

You will use:

* **prefetch** for: docs-dense, code-dense, sparse
* **fusion** for: RRF
* **limit** for: final top-K candidates for reranking (Spec 5)

This is directly aligned with the Universal Query API model: run retrieval sources in parallel, fuse, return. ([Qdrant][1])

#### 5.2 Canonical Qdrant REST request (POST /points/query)

Base endpoint for Qdrant query is `POST /collections/{collection_name}/points/query`. ([Qdrant][3])

You will send a **single** JSON request structured like:

* `prefetch`: list of retrieval sources (each has `query`, `using`, `limit`, optional `filter`)
* `query`: fusion selector (RRF)
* optional `filter`: global constraints (propagate to all prefetches)
* `params`: HNSW runtime parameters (accuracy tuning)
* `limit`: final number of results returned
* `with_payload`: include the payload fields needed for Evidence Packs
* `with_vector`: false (not needed at runtime)

> Qdrant’s Python client example shows this structure explicitly using `prefetch=[Prefetch(...), ...]` with `query=FusionQuery(fusion=RRF)` and `limit=...`. ([Qdrant][1])

#### 5.3 Prefetch limits (standardized defaults)

These defaults are tuned for *accuracy first* candidate recall before rerank:

* `prefetch.docs_dense.limit = 80`
* `prefetch.code_dense.limit = 80`
* `prefetch.sparse.limit = 120`
* `final.limit = 40`

Rationale (fixed): sparse retrieval often contributes high-signal identifiers; giving it a slightly larger candidate pool improves recall for symbol-heavy queries.

#### 5.4 HNSW parameters (accuracy-first)

Qdrant query params support `hnsw_ef` (and `exact`) in the query request. ([Qdrant][3])

Set:

* `params.hnsw_ef = 256` (or 384 if latency is acceptable)
* `params.exact = false` (keep HNSW for speed; rerank handles precision)

**Rule:** if you later detect you’re missing exact matches in evaluation (Spec 5), you adjust `hnsw_ef` upward before enabling `exact=true`. You do **not** start with exact search globally.

---

### 6) Filters: global + prefetch-specific (exact behavior)

#### 6.1 Filter syntax (payload conditions)

Qdrant filtering supports:

* `match` conditions (`key`, `match.value`) ([Qdrant][4])
* `range` and `datetime range` conditions ([Qdrant][4])

#### 6.2 Global filters propagate to prefetch

Universal Query API supports query-level filters that apply automatically to all prefetches; prefetches can additionally add constraints. ([Qdrant][1])

#### 6.3 Standard payload fields used for filtering (assumed present)

Your ingestion specs should have stored at least these payload keys for every point:

* `corpus`: `"docs"` or `"code"`
* `repo`: `"google/adk-docs"` or `"google/adk-python"`
* `path`: file path
* `lang`: `"py" | "md" | "rst" | ...`
* `chunk_kind`: `"doc" | "code" | "config" | "test" | "example"`
* `symbol`: optional (for code chunks when extracted)
* `commit`: commit SHA
* `start_line`, `end_line`: integers
* `text`: chunk content (or `content`)

(If your earlier ingestion specs named these differently, you must map them—**the runtime tool depends on stable names**.)

#### 6.4 Default filter policy (deterministic)

Unless intent is `CODE_ONLY` or `DOCS_ONLY`, apply **no corpus filter** globally.

If `intent == CODE_ONLY`:

* global filter includes `{"key":"corpus","match":{"value":"code"}}` ([Qdrant][4])

If `intent == DOCS_ONLY`:

* global filter includes `{"key":"corpus","match":{"value":"docs"}}` ([Qdrant][4])

If `intent == TARGETED_FILE`:

* global filter includes `path` constraint:

  * exact match if caller provides full path
  * otherwise prefix match implemented as text index or keyword strategy (your indexing spec decides). If you use keyword only, enforce exact. (Do not invent a partial-match filter unless you created a text index for it.)

---

### 7) Canonical Query API request templates (drop-in)

Below are **templates** you will implement and fill at runtime. They are consistent with Qdrant Query API concepts and parameters. ([Qdrant][3])

#### 7.1 Template A — Standard hybrid (docs + code + sparse), fused with RRF

```json
{
  "prefetch": [
    { "query": "<q_dense_docs>", "using": "dense_docs", "limit": 80 },
    { "query": "<q_dense_code>", "using": "dense_code", "limit": 80 },
    {
      "query": { "indices": "<q_sparse.indices>", "values": "<q_sparse.values>" },
      "using": "sparse_lexical",
      "limit": 120
    }
  ],
  "query": { "fusion": "rrf" },
  "params": { "hnsw_ef": 256, "exact": false },
  "limit": 40,
  "with_payload": true,
  "with_vector": false
}
```

**Notes that are required by spec:**

* The sparse vector structure is `indices` + `values`, matching Qdrant sparse vectors. ([Qdrant][8])
* Multi-vector selection uses `using` (named vector fields). ([Qdrant][3])
* Prefetch + fusion is the Universal Query API pattern. ([Qdrant][1])

#### 7.2 Template B — Code-only hybrid (code dense + sparse), fused with RRF

```json
{
  "prefetch": [
    { "query": "<q_dense_code>", "using": "dense_code", "limit": 100 },
    {
      "query": { "indices": "<q_sparse.indices>", "values": "<q_sparse.values>" },
      "using": "sparse_lexical",
      "limit": 150
    }
  ],
  "query": { "fusion": "rrf" },
  "filter": { "must": [{ "key": "corpus", "match": { "value": "code" } }] },
  "params": { "hnsw_ef": 256, "exact": false },
  "limit": 50,
  "with_payload": true,
  "with_vector": false
}
```

#### 7.3 Template C — Docs-only hybrid (docs dense + sparse), fused with RRF

```json
{
  "prefetch": [
    { "query": "<q_dense_docs>", "using": "dense_docs", "limit": 100 },
    {
      "query": { "indices": "<q_sparse.indices>", "values": "<q_sparse.values>" },
      "using": "sparse_lexical",
      "limit": 150
    }
  ],
  "query": { "fusion": "rrf" },
  "filter": { "must": [{ "key": "corpus", "match": { "value": "docs" } }] },
  "params": { "hnsw_ef": 256, "exact": false },
  "limit": 50,
  "with_payload": true,
  "with_vector": false
}
```

#### 7.4 Template D — Targeted symbol lookup (boost exact symbol matches)

For symbol-heavy API lookups, you constrain at least one prefetch to symbol matches *if your payload contains `symbol`*.

* Global filter: none (unless code-only)
* Prefetch-specific filter on the dense_code prefetch: `symbol == <symbol>` (exact)

This mirrors the “prefetch-specific filter” pattern Qdrant documents. ([Qdrant][1])

---

### 8) Evidence Pack construction (what your retrieval tool returns)

Your retrieval tool does **not** return raw Qdrant points. It returns a curated **Evidence Pack**: a list of evidence items with deterministic ordering, de-duplication, and minimal formatting surprises.

#### 8.1 Evidence item schema (mandatory fields)

Every evidence item returned must include:

* `evidence_id`: stable ID you generate (e.g., `{point_id}:{start_line}:{end_line}`)
* `score`: Qdrant returned score (note: with RRF fusion, scores are fusion-derived; treat as *ranking signal*, not similarity)
* `rank`: 1..N in returned order
* `corpus`: `"code"` or `"docs"`
* `repo`: repo identifier
* `path`: file path
* `commit`: commit SHA (or tag)
* `start_line`, `end_line`: line numbers (or null for docs without line mapping)
* `chunk_kind`: `"code" | "doc" | ...`
* `text`: the chunk content
* `retrieval_route`: one of `"dense_docs" | "dense_code" | "sparse_lexical" | "fusion_rrf"`
* `highlights`: optional short list of matched tokens/symbols (derived locally; never rely on Qdrant highlights)

#### 8.2 Deterministic post-processing rules

After receiving Qdrant results:

1. **Hard dedupe:**
   If two evidence items share the same `(repo, path, start_line, end_line)`, keep the higher-ranked one.

2. **Soft dedupe (near duplicates):**
   If two items share `(repo, path)` and overlap lines by ≥ 60%, keep the higher-ranked one.

3. **Quota mix (unless forced intent):**
   If `intent` is not `CODE_ONLY` / `DOCS_ONLY`, enforce:

   * at least **30%** items from `corpus=code`
   * at least **30%** items from `corpus=docs`
   * remaining 40% can be whichever ranks higher
     This prevents “all docs” for implementation questions and “all code” for conceptual questions—because the repos are complementary.

4. **Evidence window expansion (optional but recommended):**
   For code chunks only: if chunk is < 25 lines and you have `start_line/end_line`, expand by ±10 lines (bounded by file limits) *only if your payload stores file text or you have a file fetcher*. If you don’t have a safe file fetcher, skip expansion; do not fabricate lines.

5. **Stable sort key:**
   Primary: `rank` (as returned)
   Secondary: `corpus` (“code” before “docs” only for `HOW_TO_IMPLEMENT`, otherwise no secondary)
   Tertiary: `(repo, path, start_line)`

#### 8.3 “Usable information” guarantee

Your retrieval tool must ensure `text` is always present. Qdrant query results omit payload by default unless you request it; so you must set `with_payload` appropriately. ([Qdrant][3])

---

### 9) Tool interface exposed to ADK (Function Tool contract)

#### 9.1 Why ADK Function Tool (and what ADK expects)

In ADK, assigning a Python function to an agent’s `tools` list automatically wraps it as a FunctionTool; ADK inspects signature + docstring + type hints to build the tool schema that the LLM uses. ([Google GitHub Page][2])

A parameter is required if it has a type hint and **no default value**. ([Google GitHub Page][2])

Tools can accept `ToolContext` (ADK passes it automatically when declared as the last argument), enabling access to session state if you need caching or storing last evidence pack. ([Google GitHub Page][9])

#### 9.2 Canonical tool signature (what you implement)

You will implement a single retrieval tool function that the agent calls:

**Name:** `retrieve_adk_evidence`

**Required params (no defaults):**

* `query: str`
* `intent: str` (must be one of the enum values in §3.1)
* `top_k: int` (final evidence pack size after post-processing; typical 12–20)

**Optional params (must be explicitly Optional; default None allowed):**

* `repo_scope: list[str] | None` (e.g., `["google/adk-python"]`, `["google/adk-docs"]`)
* `path_scope: list[str] | None` (exact paths only unless your indexing supports partial)
* `commit: str | None`
* `include_tests: bool | None`
* `min_rank_fusion: int | None` (rare; default None)
* `tool_context: ToolContext` (last arg only; optional usage)

**Docstring requirements (mandatory):**

* Clearly define each parameter, allowed intent values, and exact output schema.
* Include a “When to call this tool” description for the LLM.

(You will implement in Python for ADK Python; if you later mirror in TS, you follow TS ADK patterns—but Python is canonical here.)

---

### 10) End-to-end runtime sequence (exact steps, no ambiguity)

This is the exact order your tool must follow on every call:

#### Step 1 — Validate inputs

* Ensure `intent` is valid; else set via classifier in §3.2.
* Ensure `top_k` is within bounds:

  * hard min 5, hard max 30 (beyond that you’re overfeeding the model)
* If `repo_scope` present, verify values are known; if unknown, error loudly (don’t silently ignore).

#### Step 2 — Build query embeddings

Compute:

* `q_dense_docs` (voyage-context-3 query embedding) ([Voyage AI][5])
* `q_dense_code` (voyage-code-3 query embedding) ([Voyage AI][6])
* `q_sparse` (SPLADE++ indices/values) ([Qdrant][7])

**Hard rule:** If any embedding fails:

* If one dense embedding fails, proceed with the other dense + sparse.
* If sparse fails, proceed with dense only.
* If both dense fail, return error (no retrieval possible).

#### Step 3 — Construct global filter (if any)

* Build Qdrant `filter` JSON using `must` conditions (match/range) per Qdrant filtering docs. ([Qdrant][4])
* Apply corpus constraints for `CODE_ONLY` / `DOCS_ONLY`.
* Apply `repo_scope`, `path_scope`, `commit` as exact `match` conditions.

#### Step 4 — Construct prefetch list

* Use Template A/B/C/D depending on intent.
* If `TARGETED_FILE`, add `filter` forcing `path == ...` globally.
* If `API_LOOKUP` and you extracted a likely symbol token, add a **prefetch-specific** filter on code dense: `symbol == token`.

#### Step 5 — Issue exactly one Qdrant request

Send `POST /collections/{collection}/points/query` with:

* `prefetch`
* `query` fusion selector
* `filter` global
* `params` (hnsw_ef)
* `limit` (candidate pool, fixed at 40–50)
* `with_payload` = include required payload fields ([Qdrant][3])

#### Step 6 — Parse results into raw evidence list

For each result:

* Read payload keys: `corpus`, `repo`, `path`, `commit`, `start_line`, `end_line`, `text`, etc.
* Create `evidence_id`, assign `rank` in returned order.

#### Step 7 — Post-process (dedupe + quotas)

Apply §8.2 rules.

#### Step 8 — Return Evidence Pack

Return exactly:

```json
{
  "intent": "<final_intent>",
  "query": "<original_query>",
  "evidence": [ ...evidence items... ],
  "stats": {
    "candidates_received": 40,
    "returned": <top_k>,
    "corpus_mix": {"code": n1, "docs": n2},
    "routes_used": ["dense_code","dense_docs","sparse_lexical","fusion_rrf"],
    "qdrant_params": {"hnsw_ef": 256, "exact": false}
  }
}
```

---

### 11) Acceptance tests (retrieval correctness checks you must implement now)

You will implement these tests as part of bringing the tool up (even before Spec 5 rerank). Each test asserts that evidence includes the right *type* of sources.

1. **Implementation question** (`HOW_TO_IMPLEMENT`)
   Query: “build a sequential multi-agent workflow with tools and state”
   Pass criteria:

* Evidence includes ≥ 1 item from docs about tools or workflows
* Evidence includes ≥ 1 item from code showing actual agent/tool usage

2. **API lookup** (`API_LOOKUP`)
   Query: “FunctionTool required parameters and schema generation”
   Pass:

* Evidence includes doc chunk describing signature inspection / required params ([Google GitHub Page][2])

3. **Filtering sanity**
   Query includes explicit constraints: “only show code from adk-python”
   Pass:

* Every evidence item has `corpus=code` and `repo=google/adk-python`

4. **Lexical win case**
   Query: “output_key not automatically read state sequential agent”
   Pass:

* Evidence includes at least one code or issue/doc mention referencing this behavior (lexical should help).

---

### 12) What changes in Spec 5 (so you don’t accidentally implement it here)

This spec ends at **candidate generation + evidence pack**.

**Spec 5 will add:**

* Voyage `rerank-2.5` integration over candidates (and the exact input formatting)
* rerank-aware truncation strategies (token budgeting)
* evaluation harness, regression queries, and tuning knobs (ef, limits, quotas)
* caching strategy finalized (embedding cache + result cache) with correctness constraints

---

## To continue

If you want me to generate **Spec 5 of 5**, reply **“proceed”**.

[1]: https://qdrant.tech/course/essentials/day-5/universal-query-api/ "The Universal Query API - Qdrant"
[2]: https://google.github.io/adk-docs/tools-custom/function-tools/ "Overview - Agent Development Kit"
[3]: https://qdrant.tech/documentation/search/?utm_source=chatgpt.com "Search - Qdrant"
[4]: https://qdrant.tech/documentation/concepts/filtering/?utm_source=chatgpt.com "Filtering - Qdrant"
[5]: https://docs.voyageai.com/docs/contextualized-chunk-embeddings?utm_source=chatgpt.com "Contextualized Chunk Embeddings"
[6]: https://docs.voyageai.com/docs/embeddings?utm_source=chatgpt.com "Text Embeddings"
[7]: https://qdrant.tech/documentation/fastembed/fastembed-splade/?utm_source=chatgpt.com "Working with SPLADE - Qdrant"
[8]: https://qdrant.tech/documentation/concepts/vectors/ "Vectors - Qdrant"
[9]: https://google.github.io/adk-docs/tutorials/agent-team/?utm_source=chatgpt.com "Agent team - Agent Development Kit"
