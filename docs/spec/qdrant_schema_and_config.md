## SPEC 2/5 — Qdrant Cloud Collection Schema, Indexing, and Hybrid Vector Space Configuration (Accuracy-First)

**Document ID:** `SPEC-02-qdrant-schema-indexing`
**Depends on:** `SPEC-01-foundation-bootstrap` (config + Voyage/Qdrant connectivity verified)

**Primary goal of this spec:**
Define and implement the **exact Qdrant Cloud collection schema** that will support **highest-accuracy hybrid retrieval** across:

* **Docs corpus** embedded with `voyage-context-3` (dense docs vector space) ([Voyage AI][1])
* **Code corpus** embedded with `voyage-code-3` (dense code vector space) ([Voyage AI][2])
* **Lexical hybrid** using **sparse vectors** (single sparse vector space shared across corpora) with Qdrant’s sparse vector support ([Qdrant][3])

This spec creates:

1. One Qdrant collection with **named dense vectors** + **named sparse vectors** (schema locked) ([Qdrant][3])
2. Payload index strategy for fast, accurate filtering (commit pinning, corpus filters, etc.) ([Qdrant][4])
3. Accuracy-first HNSW defaults and search parameter guidance (for later retrieval spec) ([Qdrant][5])

**Out of scope for this spec:** Chunking, embeddings generation, ingestion (Spec 3), query logic + fusion + rerank (Spec 5).

---

# 1) Locked Design Decisions (No Ambiguity)

## 1.1 One collection, multi-vector (dense-docs + dense-code) + sparse lexical

We create **one** collection: `${QDRANT_COLLECTION}`.

It contains:

* `vectors`:

  * `dense_docs` → cosine, size **2048**
  * `dense_code` → cosine, size **2048**
* `sparse_vectors`:

  * `sparse_lexical` → sparse index (in-RAM for accuracy/latency)

Qdrant supports storing **multiple vectors of different sizes and types in the same point** via **named vectors**, useful for “different embedding models / modalities.” ([Qdrant][3])
Qdrant also supports **sparse vectors** as a separate named storage/index and querying with them via the Query API using `using`. ([Qdrant][3])

## 1.2 Dense vector dimensionality (2048) for both corpora

Voyage supports:

* `voyage-code-3`: output dimensions include **2048** ([Voyage AI][2])
* `voyage-context-3`: contextualized output dimensions include **2048** ([Voyage AI][1])

Therefore, Qdrant vector size for both named dense vector spaces will be set to **2048**.

> This avoids dimension mismatch and enables uniform operational handling while still keeping *separate vector spaces* (`dense_docs` vs `dense_code`) so we never mix embedding spaces incorrectly.

## 1.3 Distance function

Set `distance = Cosine` for both dense vectors.

Cosine is the standard for modern embedding retrieval and is the default in most official examples for named text vectors. ([Qdrant][6])

## 1.4 Accuracy-first indexing posture (no quantization, keep vectors in RAM)

This system prioritizes **retrieval accuracy** over cost/latency optimizations. Therefore:

* **No quantization** (quantization can trade accuracy for memory/speed; we will not introduce any compression in the baseline). Qdrant’s optimization guide explicitly positions quantization as a memory/speed optimization lever rather than an accuracy baseline. ([Qdrant][5])
* Keep vectors in RAM (do not set `on_disk: true` at the vector level).

---

# 2) Qdrant Cloud Collection Contract

## 2.1 Collection name (stable)

Use `${QDRANT_COLLECTION}` from `config/settings.yaml` (Spec 1).

Example:

* `adk_grounding_v1`

**Rule:** The collection name is immutable once ingestion begins. If you need a new schema later, you create a new collection name (e.g., `adk_grounding_v2`).

## 2.2 Named dense vectors (two independent spaces)

Per Qdrant named vector concept: define each vector space during collection creation and manage independently. ([Qdrant][3])

* `dense_docs`: `size=2048`, `distance=Cosine`
* `dense_code`: `size=2048`, `distance=Cosine`

## 2.3 Named sparse vector space (lexical hybrid)

Sparse vectors:

* have no fixed length; defined by `(indices, values)` pairs ([Qdrant][3])
* require separate configuration under `sparse_vectors` ([Qdrant][3])
* can be queried using Query API with `using: "<sparse_name>"` and a sparse query object ([Qdrant][3])

We define:

* `sparse_lexical` with sparse index `on_disk=false` (accuracy/latency baseline; also aligns with Qdrant’s guidance that sparse index is built as part of optimization and is efficient for dense+sparse collections). ([Qdrant][4])

---

# 3) HNSW Configuration (Accuracy-First Defaults)

Qdrant’s optimization guide is explicit:

* Increase `m` and `ef_construct` to improve precision ([Qdrant][5])
* Adjust `hnsw_ef` at query time for precision vs speed ([Qdrant][5])

## 3.1 Collection-level HNSW defaults

Set:

* `m = 64`
* `ef_construct = 512`

These values are deliberately high to bias toward recall/precision.

> This increases build time and memory usage. That is acceptable in this project because the stated priority is retrieval accuracy.

## 3.2 Query-time search params (baseline guidance)

Even though query-time configuration is Spec 5, you must lock the baseline now so everyone implements consistently:

Default query params for dense searches:

* `hnsw_ef = 256` (increase to 512 when evaluating “hard” queries)
* `exact = false` (use `exact=true` only for debugging/evaluation comparisons against brute force) ([Qdrant][5])

---

# 4) Payload Schema (Stored on every point)

This spec defines the *minimum required payload fields* that later ingestion (Spec 3) must supply, so indexing can be created now and used consistently.

## 4.1 Required payload fields (must exist on every point)

All are stored as payload values in Qdrant:

**Identity & provenance**

* `chunk_id` (string) — stable unique ID (also used as point ID)
* `corpus` (keyword) — `adk_docs` | `adk_python`
* `repo` (keyword) — e.g., `google/adk-docs` or `google/adk-python`
* `commit` (keyword) — pinned SHA for that ingestion run
* `ref` (keyword) — branch/tag (optional but recommended; indexable)

**Location**

* `path` (keyword) — repo-relative file path (or doc path)
* `uri` (keyword) — optional canonical URI (useful for docs)
* `symbol` (keyword) — optional (best-effort for code chunks)

**Chunk boundaries**

* `chunk_index` (integer)
* `start_line` (integer, nullable for docs)
* `end_line` (integer, nullable for docs)

**Content**

* `text` (string) — the chunk text used for embedding + rerank candidates
* `text_hash` (keyword) — hash of normalized text (dedupe / change detect)

**Type flags**

* `kind` (keyword) — `code` | `doc`
* `lang` (keyword) — `py` | `md` | `rst` | etc. (best-effort)

**Timestamps**

* `ingested_at` (datetime string) — ISO8601

> Qdrant payload indexing supports keyword/integer/datetime/text etc. ([Qdrant][4])

---

# 5) Payload Indexing Strategy (Filter Accuracy + Performance)

Qdrant recommends indexing fields used for filtering, prioritizing those that constrain results the most. ([Qdrant][7])

Because this system will frequently filter by corpus/commit/path/kind, create indexes for those fields.

## 5.1 Create keyword indexes (in-memory)

Create indexes for:

* `corpus` (keyword)
* `repo` (keyword)
* `commit` (keyword)
* `ref` (keyword)
* `path` (keyword)
* `kind` (keyword)
* `lang` (keyword)
* `symbol` (keyword)
* `text_hash` (keyword)

Keyword indexing supports efficient `match` filters. ([Qdrant][4])

## 5.2 Create integer indexes

* `chunk_index`
* `start_line`
* `end_line`

Integer indexing improves range filters and match/range logic. ([Qdrant][4])

## 5.3 Create datetime index

* `ingested_at`

Datetime indexing supports range filtering and temporal constraints. ([Qdrant][4])

## 5.4 Text (full-text) index: DO NOT create in baseline

Although Qdrant supports full-text indexes for string payload, this pipeline will use:

* sparse lexical vectors for lexical retrieval (hybrid)
* Voyage rerank-2.5 for final semantic ordering

Full-text payload indexes are not needed for baseline accuracy and add complexity/memory; the indexing docs recommend being selective. ([Qdrant][4])

(If you later want additional “exact phrase within payload field” filtering, you can add a text index, but not in this baseline spec.)

---

# 6) Qdrant Collection Creation (Authoritative Implementation)

This section is fully implementable as a script (e.g., `src/grounding/scripts/02_create_collection.py`).

## 6.1 REST API schema (canonical)

Qdrant docs show collection creation with multiple named vectors and sparse vectors. ([Qdrant][3])

**HTTP:**
`PUT /collections/{collection_name}`

**Body (schema):**

```json
{
  "vectors": {
    "dense_docs": { "size": 2048, "distance": "Cosine" },
    "dense_code": { "size": 2048, "distance": "Cosine" }
  },
  "sparse_vectors": {
    "sparse_lexical": {
      "index": { "on_disk": false }
    }
  },
  "hnsw_config": {
    "m": 64,
    "ef_construct": 512
  }
}
```

Sparse vector indexing configuration uses the documented `sparse_vectors` structure with `index.on_disk`. ([Qdrant][4])

## 6.2 Python qdrant-client implementation (required)

Use QdrantClient with cloud URL and api_key as per official client docs.

**Create (idempotent) behavior:**

* If collection does not exist → create it
* If collection exists:

  * Validate schema matches (vector names, sizes, distances, sparse vector name exists)
  * If mismatch → fail hard with a detailed diff (do not auto-migrate in baseline)

**Python code (collection creation):**

```python
from qdrant_client.models import (
    Distance,
    VectorParams,
    SparseVectorParams,
    SparseIndexParams,
    HnswConfigDiff,
)

client.create_collection(
    collection_name=collection_name,
    vectors_config={
        "dense_docs": VectorParams(size=2048, distance=Distance.COSINE),
        "dense_code": VectorParams(size=2048, distance=Distance.COSINE),
    },
    sparse_vectors_config={
        "sparse_lexical": SparseVectorParams(
            index=SparseIndexParams(on_disk=False)
        ),
    },
    hnsw_config=HnswConfigDiff(m=64, ef_construct=512),
)
```

> **Note:** Named vectors use a dict for `vectors_config` where keys are vector names. Sparse vectors require `SparseIndexParams` nested inside `SparseVectorParams`.

**Schema validation (for existing collections):**

Query collection info and validate:

```python
info = client.get_collection(collection_name)
vectors = info.config.params.vectors  # dict of {name: VectorParams}
sparse = info.config.params.sparse_vectors  # dict of {name: SparseVectorParams}
hnsw = info.config.hnsw_config  # HnswConfig with m, ef_construct
```

Validation must check:
* Dense vector names exist with correct `size` and `distance`
* Sparse vector name exists
* `hnsw.m == 64` and `hnsw.ef_construct == 512`

---

# 7) Post-Creation: Payload Index Creation (Required Step)

Qdrant payload indexing is done via:
`PUT /collections/{collection_name}/index` or client helper functions. ([Qdrant][7])

## 7.1 Create indexes (Python)

For each field above, create the index using the proper schema types:

* `keyword` for categorical string fields
* `integer` for integer fields
* `datetime` for timestamp

**Python code (payload indexing):**

```python
from qdrant_client.models import PayloadSchemaType

# Check existing indexes first for idempotency
info = client.get_collection(collection_name)
existing_indexes = set(info.payload_schema.keys()) if info.payload_schema else set()

# Create keyword indexes
for field in ["corpus", "repo", "commit", "ref", "path", "kind", "lang", "symbol", "text_hash"]:
    if field not in existing_indexes:
        client.create_payload_index(
            collection_name=collection_name,
            field_name=field,
            field_schema=PayloadSchemaType.KEYWORD,
        )

# Create integer indexes
for field in ["chunk_index", "start_line", "end_line"]:
    if field not in existing_indexes:
        client.create_payload_index(
            collection_name=collection_name,
            field_name=field,
            field_schema=PayloadSchemaType.INTEGER,
        )

# Create datetime index
if "ingested_at" not in existing_indexes:
    client.create_payload_index(
        collection_name=collection_name,
        field_name="ingested_at",
        field_schema=PayloadSchemaType.DATETIME,
    )
```

**Rule:** Index creation should be re-runnable:

* Query `info.payload_schema.keys()` to get existing index names before creation
* If an index exists, skip (no-op)
* If an index exists with different type/options, fail (schema drift)

---

# 8) Schema Validation Checklist (Hard Requirements)

After running the schema script, you must verify:

## 8.1 Collection has required vector spaces

* Dense:

  * `dense_docs` size=2048 distance=Cosine
  * `dense_code` size=2048 distance=Cosine
* Sparse:

  * `sparse_lexical` exists

Named vectors capability is part of Qdrant’s core vectors concept. ([Qdrant][3])
Sparse vectors querying uses `using` to select the sparse vector name. ([Qdrant][3])

## 8.2 Query API supports `prefetch` + `using`

This system will rely on Qdrant Query API later. The API reference explicitly includes:

* `prefetch`
* `using`
* `query`
* `params` ([Qdrant][8])

## 8.3 Indexes exist

At minimum:

* keyword: `corpus`, `repo`, `commit`, `path`, `kind`
* integer: `chunk_index`
* datetime: `ingested_at`

Qdrant explicitly recommends indexing fields used to constrain/filter results. ([Qdrant][7])

---

# 9) Implementation Deliverables (Spec 2 Output)

Your coding agent must produce:

1. `src/grounding/scripts/02_ensure_collection_schema.py`

   * Connects to Qdrant Cloud (from config)
   * Ensures collection exists (create if not)
   * Validates vector-space schema (dense + sparse)
   * Applies (and verifies) HNSW defaults
   * Creates payload indexes idempotently

2. `tests/test_collection_schema.py`

   * Asserts collection exists
   * Asserts required named vectors exist + correct sizes
   * Asserts sparse vector name exists
   * Asserts a representative payload index exists (at least the core ones)

---

# 10) Acceptance Criteria (Spec 2 is “Done” Only If…)

1. ✅ Qdrant Cloud collection exists with:

   * named dense vectors (`dense_docs`, `dense_code`) configured as above ([Qdrant][6])
   * named sparse vectors (`sparse_lexical`) configured as above ([Qdrant][3])
2. ✅ HNSW config set to accuracy-first defaults and retrievable via collection info ([Qdrant][5])
3. ✅ Payload indexes created for all required fields using correct schema types ([Qdrant][4])
4. ✅ All scripts are idempotent and safe (no silent migrations)

---

# 11) Explicit Handoff to Spec 3/5

**Spec 3 will assume:**

* The collection exists and is correct
* Vector names are locked:

  * `dense_docs`, `dense_code`, `sparse_lexical`
* Payload schema requirements are known and enforceable
* Ingestion can now upsert points that include:

  * one of the dense vectors (docs or code)
  * the sparse lexical vector
  * payload fields

If you say **“Proceed to Spec 3”**, I will produce:

## SPEC 3/5 — Ingestion Pipeline (Discover → Chunk → Embed with Voyage → Sparse embed → Upsert → Verification)

It will include:

* exact embedding calls for `voyage-context-3` contextualized embeddings and `voyage-code-3` text embeddings (both at 2048 float) ([Voyage AI][1])
* sparse vector generation method using Qdrant’s SPLADE guidance via FastEmbed ([Qdrant][9])
* deterministic point construction that satisfies the schema from this spec

[1]: https://docs.voyageai.com/docs/contextualized-chunk-embeddings?utm_source=chatgpt.com "Contextualized Chunk Embeddings"
[2]: https://docs.voyageai.com/docs/embeddings?utm_source=chatgpt.com "Text Embeddings"
[3]: https://qdrant.tech/documentation/concepts/vectors/?utm_source=chatgpt.com "Vectors - Qdrant"
[4]: https://qdrant.tech/documentation/concepts/indexing/?utm_source=chatgpt.com "Indexing - Qdrant"
[5]: https://qdrant.tech/documentation/guides/optimize/?utm_source=chatgpt.com "Optimize Performance - Qdrant"
[6]: https://qdrant.tech/documentation/concepts/collections/?utm_source=chatgpt.com "Collections - Qdrant"
[7]: https://qdrant.tech/documentation/concepts/payload/?utm_source=chatgpt.com "Payload - Qdrant"
[8]: https://api.qdrant.tech/v-1-13-x/api-reference/search/query-points?utm_source=chatgpt.com "Query points | Qdrant | API Reference"
[9]: https://qdrant.tech/documentation/fastembed/fastembed-splade/?utm_source=chatgpt.com "Working with SPLADE - Qdrant"
