## SPEC 3/5 — Ingestion Pipeline (Discover → Chunk → Voyage Embed → SPLADE Sparse → Qdrant Upsert → Verify)

**Document ID:** `SPEC-03-ingestion-pipeline`
**Depends on:**

* **SPEC 1** (project bootstrap; Voyage + Qdrant Cloud connectivity verified)
* **SPEC 2** (Qdrant collection exists with named vectors: `dense_docs`, `dense_code`, `sparse_lexical`)

**Primary goal:**
Implement a deterministic ingestion pipeline that loads **all usable text-based information** from:

* `corpora/adk-docs` → **docs corpus** → dense embeddings via **Voyage contextualized chunk embeddings** (`voyage-context-3`) ([Voyage AI][1])
* `corpora/adk-python` → **code corpus** → dense embeddings via **Voyage text embeddings** (`voyage-code-3`) ([Voyage AI][2])

…and produces **hybrid** points in **Qdrant Cloud** by attaching:

* one dense vector per chunk (`dense_docs` OR `dense_code`)
* one sparse vector per chunk (`sparse_lexical`) generated via **SPLADE** using **FastEmbed** ([Qdrant][3])
* rich payload metadata for filtering and debugging

This spec is written so a coding agent can implement it without needing any additional external references.

---

# 0) Non-negotiable behavior (accuracy + determinism)

1. **Every ingested chunk must be reproducible** from:

   * corpus name (`adk_docs` vs `adk_python`)
   * repo commit SHA
   * path
   * chunking algorithm version
2. **Chunk ordering is stable** (same inputs → same chunk list in the same order).
3. **Point IDs are globally unique** across both corpora (so upserts can’t accidentally null out vectors due to ID collisions).
4. **No “whole repo as one blob.”** Chunking is mandatory.
5. **Hybrid is mandatory**: every point includes `sparse_lexical` plus exactly one dense vector.
6. **Payload always includes the chunk text** (`text`) to support:

   * immediate grounding
   * Voyage rerank candidate text (Spec 5)
   * human debugging and quick spot checks

---

# 1) Inputs, outputs, and “what counts as usable information”

## 1.1 Inputs (runtime)

* Local filesystem:

  * `corpora/adk-docs/` (git repo clone)
  * `corpora/adk-python/` (git repo clone)
* `manifests/corpus_manifest.json` or a run manifest that includes commit SHAs (from Spec 1)
* `config/settings.yaml` (from Spec 1)
* Include/exclude patterns (you will define exact folders later; pipeline must accept them now)

## 1.2 Output (Qdrant)

For every chunk, create one Qdrant point with:

* **ID**: `chunk_id` (string UUID or sha1 hex; must be stable)
* **Vectors**:

  * `dense_docs` (docs chunks only) OR `dense_code` (code chunks only)
  * `sparse_lexical` (all chunks)
* **Payload**: full metadata + `text`

Qdrant supports:

* **named vectors** uploaded per point via a dict ([Qdrant][4])
* **sparse vectors** represented by `indices` + `values` (same length, unique indices) ([Qdrant][5])
* idempotent upsert semantics: same ID overwritten consistently ([Qdrant][4])

## 1.3 Definition: “all usable information”

“Usable” = **text-bearing, retrieval-relevant content** that can be represented as a string chunk and legally stored in your DB for internal RAG.

### 1.3.1 Usable file categories (handled)

* docs: `.md`, `.mdx`, `.rst`, `.txt`, `.adoc`
* code: `.py`, plus any embedded docs/config you choose (e.g., `.yaml`, `.yml`, `.toml`, `.json`) **if** you include them in patterns
* Any other extensions are supported **only if** they can be decoded to text reliably

### 1.3.2 Not usable (skipped by default)

* binary files (images, pdf, videos, fonts, archives, compiled artifacts)
* extremely large files beyond size cap (see §2.4)
* generated caches: `.git/`, `node_modules/`, `.venv/`, `__pycache__/`, etc.

This spec does not mandate your folder list; it mandates the **mechanism** to accept a folder list and safely interpret content.

---

# 2) Configuration contract (must implement exactly)

Add an ingestion section to `config/settings.yaml` (or `config/ingestion.yaml`), with defaults chosen for accuracy and safety.

```yaml
ingestion:
  run_mode: "all"   # "docs" | "code" | "all"

  corpora:
    adk_docs:
      root: "corpora/adk-docs"
      corpus: "adk_docs"
      repo: "google/adk-docs"
      kind: "doc"
      include_globs: []     # user-supplied later
      exclude_globs:
        - "**/.git/**"
        - "**/node_modules/**"
        - "**/__pycache__/**"
      allowed_exts: [".md",".mdx",".rst",".txt",".adoc"]
      max_file_bytes: 2000000

    adk_python:
      root: "corpora/adk-python"
      corpus: "adk_python"
      repo: "google/adk-python"
      kind: "code"
      include_globs: []     # user-supplied later
      exclude_globs:
        - "**/.git/**"
        - "**/node_modules/**"
        - "**/__pycache__/**"
        - "**/.venv/**"
      allowed_exts: [".py",".md",".txt",".yaml",".yml",".toml",".json"]
      max_file_bytes: 2000000

  chunking:
    # Hard caps to keep payload sizes reasonable and avoid huge embedding calls
    max_chunk_chars: 12000
    min_chunk_chars: 400

    docs:
      # target chunk sizing for heading blocks + paragraphs
      target_chunk_chars: 4500
      overlap_chars: 300

    code:
      # chunking by symbol is primary; these are fallback/limits
      max_symbol_chunk_chars: 9000
      overlap_chars: 200

  lexical:
    # Used to generate sparse vectors; always applied to BOTH docs and code
    sparse_model: "prithivida/Splade_PP_en_v1"
    sparse_batch_size: 32

    # Code lexical augmentation improves exact match for identifiers
    code_identifier_expansion: true
    include_path_tokens: true
    include_symbol_tokens: true

  batching:
    voyage_dense_max_items: 256
    voyage_dense_max_chars_total: 240000   # conservative safety limit
    voyage_retry_max_attempts: 6
    voyage_retry_backoff_seconds: [1,2,4,8,16,32]

  qdrant_upload:
    parallel: 6
    max_retries: 5
    wait: true
```

Why these parameters exist:

* Voyage embed API supports up to **1000 texts** per call and has a **token budget** per request for `voyage-code-3` (and other models). ([Voyage AI][2])
* Contextualized embeddings support `output_dimension` up to 2048 for `voyage-context-3` and `output_dtype="float"`. ([Voyage AI][1])
* SPLADE sparse generation is explicitly documented via FastEmbed with `prithivida/Splade_PP_en_v1`. ([Qdrant][3])

---

# 3) Data contracts (payload + internal objects)

You already defined a `Chunk` contract in Spec 1. Here we lock the exact fields for ingestion.

## 3.1 `ChunkRecord` (internal)

Each produced chunk must include:

* `chunk_id` (stable string)
* `corpus` (`adk_docs` | `adk_python`)
* `repo` (`google/adk-docs` | `google/adk-python`)
* `commit` (sha)
* `ref` (branch name or tag; optional)
* `path` (repo-relative)
* `uri` (optional; for docs you may compute a GitHub URL, but not required)
* `kind` (`doc` | `code`)
* `lang` (`md`/`rst`/`py`/etc.)
* `symbol` (optional; for code)
* `chunk_index` (int; stable ordering within a file)
* `start_line`, `end_line` (optional for docs)
* `text` (string; what you will store in Qdrant payload and what will be presented to the LLM as evidence)
* `lexical_text` (string; used ONLY for sparse embedding generation; may differ from `text`)
* `text_hash` (sha256 of normalized `text`)
* `created_at` (ISO8601)
* `chunker_version` (string; bump this if algorithm changes)

## 3.2 Qdrant payload (stored)

Payload must contain at least:

* all provenance and location fields above
* `text` (full chunk text)
* `text_hash`
* `chunker_version`

These payload fields are used by later retrieval filters and debugging.

---

# 4) Discovery phase (walk repos deterministically)

## 4.1 Repository root validation

For each corpus:

1. Confirm `root` exists
2. Confirm it’s a git repo
3. Resolve commit SHA:

   * `git rev-parse HEAD`
4. Write `manifests/ingestion_runs/<run_id>.json` early (before embedding), including:

   * corpus roots
   * commits
   * include/exclude patterns
   * ingestion config snapshot

## 4.2 Deterministic file listing

Implementation requirements:

* Walk filesystem in a stable order:

  * list directories and files sorted lexicographically
* Apply filters in this order:

  1. exclude globs
  2. include globs (if provided; empty means “all under root”)
  3. allowed extensions
  4. max file size
  5. binary detection (heuristic)

## 4.3 Binary detection heuristic (implementation)

Given bytes from file head (e.g., first 4096 bytes):

* If contains `\x00`, treat as binary
* If decoding as UTF-8 fails and fallback encodings fail, treat as binary
* Otherwise treat as text

## 4.4 Text decoding rules

* Attempt UTF-8 strict
* If fails, attempt UTF-8 with replacement (ONLY if replacement ratio < 0.5%)
* Normalize newlines to `\n`

Record a `decode_warnings` array in the run manifest for transparency.

---

# 5) Chunking phase (high-accuracy chunk semantics)

Your chunker must produce chunks that are:

* semantically coherent (not arbitrary fixed windows)
* small enough for embedding + payload storage
* stable across runs

You do **not** need to decide which folders—this chunker operates on whatever files are passed to it.

## 5.1 Docs chunking (Markdown/RST/etc.)

**Goal:** preserve heading structure + paragraph boundaries.

### 5.1.1 Markdown chunk algorithm (required)

For each markdown-like file:

1. Parse headings (`^#{1,6}\s+...`) and build a **heading stack**.
2. Create sections at H2/H3 boundaries (configurable; default: split at H2).
3. Within each section:

   * accumulate paragraphs until `target_chunk_chars` is reached
   * if a paragraph would exceed `max_chunk_chars`, split by sentences (fallback)
4. Overlap:

   * carry last `overlap_chars` from previous chunk into the next chunk as a “context tail”
5. Each chunk’s `text` should begin with a deterministic context header:

Example header (must be consistent; use it verbatim):

```
[CORPUS=adk_docs] [REPO=google/adk-docs] [COMMIT=<sha>]
[PATH=<path>]
[HEADINGS=H1 > H2 > H3]
---
<chunk body...>
```

Why: storing `PATH` + heading lineage in the chunk improves both lexical matching (sparse) and human/LLM grounding, without relying on external file lookup later.

### 5.1.2 RST/Plaintext chunk algorithm

* Split by blank lines into paragraphs
* Group paragraphs to target size
* Apply overlap similarly
* Use same standardized header (without headings if not available)

## 5.2 Code chunking (Python)

**Goal:** chunk by symbol (module + class/function) for maximal retrieval precision.

### 5.2.1 Primary method: AST-based symbol chunking

For each `.py` file:

1. Parse via Python `ast.parse`.

2. Identify:

   * module-level docstring + imports = “module header chunk” (chunk_index 0)

3. For each top-level:

   * `class` definition:

     * chunk includes: class signature line, class docstring, and full body up to `max_symbol_chunk_chars`
     * optionally split large classes by method blocks if too large
   * `def` function:

     * chunk includes: signature, docstring, and body

4. Capture exact `start_line` and `end_line`.

### 5.2.2 Fallback method: robust text splitter

If AST parse fails:

* Split by `^class\s` and `^def\s` regex boundaries
* If still too large: split by blank lines into logical blocks

### 5.2.3 Code chunk header (required)

Every code chunk must begin with:

```
[CORPUS=adk_python] [REPO=google/adk-python] [COMMIT=<sha>]
[PATH=<path>] [SYMBOL=<symbol_or_module>] [LINES=<start>-<end>]
---
<code chunk...>
```

This provides deterministic citations and helps lexical match.

---

# 6) Lexical sparse text construction (for hybrid accuracy)

Sparse embeddings will be generated from `lexical_text`, not necessarily `text`. This is intentional.

## 6.1 Docs lexical text

For docs:

* `lexical_text = normalize(text)` where normalize:

  * lowercase
  * collapse whitespace
  * keep punctuation minimal (do not strip periods inside tokens like `v1.2.3`)
* Prepend path tokens if enabled:

  * split path into components, add as space-separated tokens:

    * `adk-docs docs guides ...`

## 6.2 Code lexical text (critical)

For code, lexical matching for identifiers is a major win.

Construct `lexical_text` from:

1. `PATH` tokens (if enabled)
2. `SYMBOL` tokens (if enabled)
3. Extracted identifiers from the code chunk:

   * snake_case split: `my_function` → `my function my_function`
   * camelCase split: `ToolContext` → `tool context toolcontext`
   * dotted names preserved: `client.upsert` kept as `client.upsert client upsert`
4. Extracted string literals and comments (optional but recommended)

Then append a normalized version of the code chunk itself (without the structured header).

This “expansion” improves SPLADE’s ability to surface exact-ish matches even for code-ish queries, while dense code embeddings do the semantic heavy lifting.

---

# 7) Dense embedding generation (Voyage)

You will generate dense embeddings separately for docs and code because they use different Voyage models/spaces.

## 7.1 Docs dense embeddings: contextualized chunk embeddings (`voyage-context-3`)

Voyage contextualized chunk embeddings:

* `voyage-context-3` supports output dimensions up to **2048**
* available via `voyageai.Client.contextualized_embed(inputs: List[List[str]], ...)` ([Voyage AI][1])

### 7.1.1 Why contextualized embeddings are used here

You want each chunk embedding to incorporate broader document context (within the model’s context limits). This increases retrieval quality for docs where meaning is spread across sections.

### 7.1.2 Required call pattern

For each docs file:

1. Produce chunk list in stable order: `[chunk0_text, chunk1_text, ...]`
2. Call:

* `model = "voyage-context-3"`
* `input_type = "document"` (so the “document retrieval” prompt is applied)
* `output_dimension = 2048`
* `output_dtype = "float"`

This matches the documented parameters and ranges. ([Voyage AI][1])

### 7.1.3 Context window management

If a single file produces too many chunks to fit comfortably in one contextualized call:

* partition chunk list into **context batches** that remain under `voyage_dense_max_chars_total`
* use **overlapping batches** to preserve context for boundary chunks:

  * batch A: chunks 0–N
  * batch B: chunks N-k … 2N-k (overlap k chunks)
* ensure each chunk gets exactly one embedding output; choose the embedding from the batch where that chunk is “most central” (to maximize contextual coverage)

This is deterministic and improves embedding quality versus non-overlapping splits.

## 7.2 Code dense embeddings: text embeddings (`voyage-code-3`)

Voyage text embeddings are produced with `voyageai.Client.embed(texts, model, ...)` ([Voyage AI][2])

You must use:

* `model="voyage-code-3"`
* `input_type="document"`
* `output_dimension=2048` (supported by `voyage-code-3`) ([Voyage AI][2])
* `output_dtype="float"` (highest precision) ([Voyage AI][2])

### 7.2.1 Batching constraints (must implement)

Voyage embed:

* max list length = 1000
* token budget exists per request, and differs by model; `voyage-code-3` has a stated total token limit per batch ([Voyage AI][2])

Implement conservative batching using:

* `voyage_dense_max_items`
* `voyage_dense_max_chars_total`

If either limit would be exceeded, flush the batch.

---

# 8) Sparse embedding generation (FastEmbed + SPLADE)

You will generate sparse vectors for **every chunk** using FastEmbed’s SPLADE pipeline, as documented by Qdrant. ([Qdrant][3])

## 8.1 Model selection (locked)

Use:

* `model_name = "prithivida/Splade_PP_en_v1"` ([Qdrant][3])

## 8.2 Implementation (required)

1. Install:

   * `pip install fastembed` ([Qdrant][3])
2. Initialize:

   * `SparseTextEmbedding(model_name=model_name)` ([Qdrant][3])
3. Embed `lexical_text` strings in batches:

   * `model.embed(documents, batch_size=...)` ([Qdrant][3])
4. Convert to Qdrant sparse vectors:

   * Qdrant expects sparse vectors as `indices` + `values` of equal length, unique indices ([Qdrant][5])

---

# 9) Point construction (Qdrant-ready)

## 9.1 Qdrant vector field rules (mandatory)

For each chunk:

* If `kind == "doc"`:

  * include `dense_docs` dense vector
  * do not include `dense_code`
* If `kind == "code"`:

  * include `dense_code` dense vector
  * do not include `dense_docs`
* Always include `sparse_lexical` as a sparse vector

Qdrant allows named vectors per point and vectors can be omitted. ([Qdrant][4])

## 9.2 Qdrant PointStruct format (mandatory)

Construct each point using `PointStruct` with:

* `id = chunk_id`
* `payload = { ... }`
* `vector = { "dense_docs": [...], "sparse_lexical": SparseVector(...)}`
  OR
  `vector = { "dense_code": [...], "sparse_lexical": SparseVector(...)}`

Qdrant docs show:

* uploading named vectors via dict ([Qdrant][4])
* sparse vectors via `SparseVector(indices=[...], values=[...])` in PointStruct ([Qdrant][5])

## 9.3 ID collision avoidance (critical)

Because upserting an existing ID **replaces the whole point** and unspecified vectors become null, you must ensure IDs never collide across corpora. ([Qdrant][4])

Requirement:

* `chunk_id` MUST include the corpus in its hash material:

  * `sha1(f"{corpus}:{commit}:{path}:{chunk_index}:{text_hash}")`

---

# 10) Upload strategy (fast + safe)

## 10.1 Use `upload_points` with parallelism and retries

Qdrant’s points documentation provides `upload_points(... parallel=..., max_retries=...)` ([Qdrant][4])

Implement:

* batch points into chunks of 128–512 points (configurable)
* `client.upload_points(collection_name, points=[...], parallel=N, max_retries=M)`

### 10.1.1 Idempotence and safe retry

Qdrant point loading is idempotent: re-uploading same IDs overwrites consistently. ([Qdrant][4])
So:

* on transient failures you can safely retry the batch
* on partial success, you can re-run the entire ingestion without corrupting state (assuming stable IDs)

---

# 11) Verification (must be automated)

You must produce automated verification outputs **as part of ingestion**, not as a manual step.

## 11.1 Qdrant count checks

After ingestion:

* count points for each corpus using a filter.
  Qdrant’s API and Python client support `client.count(...)` with a filter and `exact=True`. ([Qdrant][6])

Minimum checks:

* `count(corpus="adk_docs", commit=<sha>) == docs_chunks_ingested`
* `count(corpus="adk_python", commit=<sha>) == code_chunks_ingested`
* `count(commit=<sha>) == total_chunks_ingested`

## 11.2 Scroll sample checks

Use Scroll API to retrieve a small sample and confirm payload + vector presence.
Qdrant supports `client.scroll(... with_payload=True, with_vectors=False)` for page-by-page results. ([Qdrant][4])

Checks on random sample:

* payload includes required fields
* `text` is present and non-empty
* `kind` matches expected
* `commit` matches run commit

(Optionally scroll with vectors enabled for a few points in a debug mode, but not required for baseline.)

---

# 12) Operational artifacts (must write these files)

Each run writes:

## 12.1 Run manifest: `manifests/ingestion_runs/<run_id>.json`

Contains:

* run_id, timestamps
* config snapshot (effective resolved config)
* commits for both repos
* counts:

  * files discovered / skipped (by reason)
  * chunks produced (docs, code)
  * points uploaded (docs, code)
  * Qdrant counts after ingest
* warnings/errors
* chunker_version
* sparse model name

## 12.2 Failure report (if any)

If ingestion fails mid-run, write:

* which stage failed (discover/chunk/embed/sparse/upsert/verify)
* last successful batch cursor
* list of files that failed parsing

This enables resume behavior.

---

# 13) CLI workflows (what the coding agent must implement)

Provide scripts (or a single CLI with subcommands). Minimum required commands:

1. `ingest docs`

   * reads docs repo
   * chunks docs
   * contextualized embeds with `voyage-context-3` ([Voyage AI][1])
   * sparse embeds with SPLADE ([Qdrant][3])
   * upserts into Qdrant with vectors in correct fields ([Qdrant][7])

2. `ingest code`

   * reads code repo
   * chunks code by symbol
   * embeds with `voyage-code-3` with `output_dimension=2048` + `output_dtype=float` ([Voyage AI][2])
   * sparse embeds with SPLADE ([Qdrant][3])
   * upserts

3. `ingest all`

   * runs docs then code (or interleaves, but must remain deterministic)

4. `verify`

   * runs the count + scroll checks (without ingest)

---

# 14) Hard acceptance criteria (Spec 3 is “done” only if)

1. ✅ The pipeline can run `ingest all` end-to-end without manual intervention.
2. ✅ Every ingested chunk in Qdrant has:

   * exactly one of `dense_docs` / `dense_code`
   * `sparse_lexical`
   * payload including `text`, `path`, `commit`, `corpus`, `kind`
3. ✅ Verification passes:

   * Qdrant `count` matches local produced chunk counts ([Qdrant][6])
   * Scroll samples show correct payloads ([Qdrant][4])
4. ✅ Re-running ingestion with the same commits is idempotent (counts remain stable) ([Qdrant][4])

---

# 15) Handoff to Spec 4/5

After Spec 3, you have a fully populated Qdrant Cloud collection with:

* docs dense vectors in `dense_docs` (Voyage contextualized embeddings) ([Voyage AI][1])
* code dense vectors in `dense_code` (Voyage code embeddings) ([Voyage AI][2])
* sparse lexical vectors in `sparse_lexical` (SPLADE via FastEmbed) ([Qdrant][3])

**Spec 4 will define the runtime retrieval tool interface and query construction** (hybrid prefetch + fusion + filters), returning an “evidence pack” for your coding agents.

If you say **“Proceed to Spec 4”**, I’ll produce:

## SPEC 4/5 — Retrieval Tool API + Hybrid Query Construction (Qdrant Query API prefetch + fusion) + Evidence Packing

…and it will be implementation-ready (exact JSON query shapes, filter rules, and return schemas), grounded in Qdrant’s Query API/fusion mechanics. ([Qdrant][8])

[1]: https://docs.voyageai.com/docs/contextualized-chunk-embeddings?utm_source=chatgpt.com "Contextualized Chunk Embeddings"
[2]: https://docs.voyageai.com/docs/embeddings?utm_source=chatgpt.com "Text Embeddings"
[3]: https://qdrant.tech/documentation/fastembed/fastembed-splade/?utm_source=chatgpt.com "Working with SPLADE - Qdrant"
[4]: https://qdrant.tech/documentation/concepts/points/?utm_source=chatgpt.com "Points - Qdrant"
[5]: https://qdrant.tech/course/essentials/day-3/sparse-vectors/?utm_source=chatgpt.com "Sparse Vectors and Inverted Indexes - Qdrant"
[6]: https://api.qdrant.tech/api-reference/points/count-points?utm_source=chatgpt.com "Count points | Qdrant | API Reference"
[7]: https://qdrant.tech/documentation/concepts/vectors/?utm_source=chatgpt.com "Vectors - Qdrant"
[8]: https://qdrant.tech/course/essentials/day-5/universal-query-api/?utm_source=chatgpt.com "The Universal Query API - Qdrant"
