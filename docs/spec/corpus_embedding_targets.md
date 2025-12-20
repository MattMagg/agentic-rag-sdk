# SPEC 0/5 — Corpus Content Analysis & Embedding Target Specification

**Document ID:** `SPEC-00-corpus-embedding-targets`
**Depends on:** None (foundational spec)
**Required by:** SPEC-03 (Ingestion Pipeline)

---

## Purpose

Define exactly **what content** from each corpus should be embedded, what should be excluded, and the rationale for each decision. This specification ensures deterministic, reproducible ingestion with maximum retrieval utility.

---

## 1) Corpus Overview

### 1.1 `corpora/adk-docs` (Documentation Corpus)

**Purpose:** Official ADK documentation and examples for `voyage-context-3` embeddings.

| Directory | Item Count | Content Type | Embedding Decision |
|-----------|------------|--------------|-------------------|
| `docs/` | 129 markdown files | Conceptual docs, API guides, tutorials | ✅ **INCLUDE ALL** |
| `examples/python/` | 60 Python files | Code snippets, sample agents | ✅ **INCLUDE** (as docs-style code examples) |
| `examples/go/` | ~36 files | Go examples | ⏸️ **EXCLUDE** (Python-focused corpus) |
| `examples/java/` | ~39 files | Java examples | ⏸️ **EXCLUDE** (Python-focused corpus) |
| `examples/typescript/` | ~37 files | TypeScript examples | ⏸️ **EXCLUDE** (Python-focused corpus) |
| `api-reference/` | 636 files | Auto-generated API docs | ⚠️ **SELECTIVE** (see §3.1) |
| `site/` | Build artifacts | Generated HTML | ❌ **EXCLUDE** |
| `overrides/` | MkDocs theme | Template files | ❌ **EXCLUDE** |
| `tools/` | Build scripts | CI/tooling | ❌ **EXCLUDE** |

### 1.2 `corpora/adk-python` (Code Corpus)

**Purpose:** Official ADK Python SDK source code for `voyage-code-3` embeddings.

| Directory | Item Count | Content Type | Embedding Decision |
|-----------|------------|--------------|-------------------|
| `src/google/adk/` | 96+ Python files | Core SDK implementation | ✅ **INCLUDE ALL** |
| `tests/unittests/` | ~309 files | Unit tests | ✅ **INCLUDE** (pattern examples) |
| `tests/integration/` | ~73 files | Integration tests | ✅ **INCLUDE** (usage patterns) |
| `contributing/` | ~443 files | Dev samples/tests | ⏸️ **EXCLUDE** (redundant with tests/) |
| `.github/` | CI files | Workflow configs | ❌ **EXCLUDE** |
| Root config files | pyproject.toml, etc. | Package config | ⏸️ **PARTIAL** (see §3.2) |

---

## 2) Target File Specifications

### 2.1 Documentation Corpus (`adk-docs`) - voyage-context-3

**Include Patterns:**

```yaml
include_globs:
  - "docs/**/*.md"
  - "docs/**/*.mdx"
  - "examples/python/**/*.py"
  - "examples/python/**/*.md"
  - "README.md"
  - "CONTRIBUTING.md"
```

**Exclude Patterns:**

```yaml
exclude_globs:
  # Build artifacts
  - "**/site/**"
  - "**/.git/**"
  - "**/node_modules/**"
  - "**/__pycache__/**"
  
  # Auto-generated API reference (too verbose, low semantic value)
  - "docs/api-reference/java/**"
  - "docs/api-reference/go/**"
  - "docs/api-reference/rest/**"
  
  # Non-Python examples
  - "examples/go/**"
  - "examples/java/**"
  - "examples/typescript/**"
  
  # Theme/tooling
  - "overrides/**"
  - "tools/**"
  - "docs/stylesheets/**"
```

**File Extensions:**

```yaml
allowed_exts:
  - ".md"
  - ".mdx"
  - ".py"   # Python examples only
  - ".txt"  # Any text readmes
```

### 2.2 Code Corpus (`adk-python`) - voyage-code-3

**Include Patterns:**

```yaml
include_globs:
  - "src/**/*.py"
  - "tests/**/*.py"
  - "README.md"
  - "AGENTS.md"
  - "pyproject.toml"
```

**Exclude Patterns:**

```yaml
exclude_globs:
  - "**/.git/**"
  - "**/__pycache__/**"
  - "**/.venv/**"
  - "**/*.pyc"
  - "**/contributing/**"  # Redundant dev samples
  - ".github/**"
  - "scripts/**"
  - "assets/**"
```

**File Extensions:**

```yaml
allowed_exts:
  - ".py"
  - ".md"    # README files
  - ".toml"  # pyproject.toml (dependency/config info)
```

---

## 3) Content-Specific Decisions

### 3.1 API Reference Handling

The `docs/api-reference/` directory (636 files) requires special handling:

| Subdirectory | Decision | Rationale |
|--------------|----------|-----------|
| `api-reference/index.md` | ✅ Include | Entry point, overview |
| `api-reference/java/**` | ❌ Exclude | Non-Python, auto-generated |
| `api-reference/go/**` | ❌ Exclude | Non-Python, auto-generated |
| `api-reference/rest/**` | ⚠️ Conditional | Include only if REST API is relevant to Python usage |

**Recommendation:** Exclude all auto-generated API reference initially. The `src/google/adk/` code with docstrings provides superior code-level documentation for retrieval.

### 3.2 Configuration Files

| File | Decision | Rationale |
|------|----------|-----------|
| `pyproject.toml` | ✅ Include | Dependencies, package config, version info |
| `pylintrc` | ❌ Exclude | Linter config, no semantic value |
| `.gitignore` | ❌ Exclude | No semantic value |
| `mkdocs.yml` | ❌ Exclude | Build config only |
| `requirements.txt` | ⏸️ Optional | Minimal info, covered by pyproject.toml |

### 3.3 Test Files Strategy

**Include tests because:**
1. Tests demonstrate canonical usage patterns
2. Tests show expected inputs/outputs
3. Tests cover edge cases and error handling
4. Test docstrings often explain intent

**Chunking consideration:** Tests should be chunked by test class/function, not by file, to preserve test-level semantics.

### 3.4 LLM Context Files

Both repos contain `llms.txt` and `llms-full.txt`:

| File | Size | Decision | Rationale |
|------|------|----------|-----------|
| `llms.txt` | ~600B / 10KB | ⏸️ Optional | Summary context |
| `llms-full.txt` | 598B / 1.2MB | ❌ Exclude | Concatenated dump, redundant |

**Recommendation:** The full LLM context files are concatenated versions of other files—embedding them would create massive duplicates. Exclude.

---

## 4) Estimated Embedding Volume

### 4.1 Documentation Corpus

| Category | Est. Files | Est. Chunks (4K chars avg) |
|----------|-----------|---------------------------|
| Core docs (`docs/**/*.md`) | ~129 | ~400-600 |
| Python examples | ~60 | ~150-250 |
| **Total** | ~189 | **~550-850 chunks** |

### 4.2 Code Corpus

| Category | Est. Files | Est. Chunks (symbol-based) |
|----------|-----------|---------------------------|
| SDK source (`src/`)| ~96 | ~500-800 |
| Unit tests | ~309 | ~600-1000 |
| Integration tests | ~73 | ~150-250 |
| **Total** | ~478 | **~1250-2050 chunks** |

### 4.3 Combined Estimate

| Corpus | Chunks | Vectors (2048 dim, float32) | Est. Storage |
|--------|--------|------------------------------|--------------|
| Docs (adk-docs) | ~700 | 700 × 2048 × 4 bytes | ~5.7 MB |
| Code (adk-python) | ~1650 | 1650 × 2048 × 4 bytes | ~13.5 MB |
| Sparse (both) | ~2350 | Variable | ~2-5 MB |
| **Total** | ~2350 points | | **~21-25 MB** |

---

## 5) Priority Content (High Retrieval Value)

### 5.1 Documentation - Highest Priority

These docs should be embedded with extra care (accurate chunking, preserved headings):

1. **`docs/get-started/`** - Installation, quickstart, basics
2. **`docs/agents/`** - Agent types, multi-agent, workflow agents
3. **`docs/tools/`** and **`docs/tools-custom/`** - Tool creation patterns
4. **`docs/callbacks/`** - Callback patterns
5. **`docs/sessions/`** - State management
6. **`docs/streaming/`** - Streaming patterns
7. **`docs/deploy/`** - Deployment guides

### 5.2 Code - Highest Priority

These source files are most likely to be retrieved:

1. **`src/google/adk/agents/*.py`** - All agent implementations
2. **`src/google/adk/tools/*.py`** - Tool base classes and builtins
3. **`src/google/adk/sessions/*.py`** - Session/state management
4. **`src/google/adk/events/*.py`** - Event system
5. **`src/google/adk/runners/*.py`** - Execution runners

---

## 6) Chunking Requirements

### 6.1 Documentation Chunking

| Content Type | Chunking Strategy | Target Size |
|--------------|-------------------|-------------|
| Markdown docs | Heading-based (H2/H3 splits) | 3000-5000 chars |
| Python examples | Function/class-based | 2000-4000 chars |
| README files | Section-based | 3000-5000 chars |

**Context header required:**
```
[CORPUS=adk_docs] [REPO=google/adk-docs] [COMMIT=<sha>]
[PATH=<path>] [HEADINGS=H1 > H2 > H3]
---
<chunk content>
```

### 6.2 Code Chunking

| Content Type | Chunking Strategy | Target Size |
|--------------|-------------------|-------------|
| Module-level | Imports + module docstring | 1000-3000 chars |
| Classes | Full class with methods | 3000-9000 chars |
| Functions | Full function with docstring | 1000-4000 chars |
| Tests | Test class/function | 2000-5000 chars |

**Context header required:**
```
[CORPUS=adk_python] [REPO=google/adk-python] [COMMIT=<sha>]
[PATH=<path>] [SYMBOL=<class.method or function>] [LINES=<start>-<end>]
---
<code chunk>
```

---

## 7) Exclusion Justifications

| Excluded Content | Justification |
|------------------|---------------|
| Java/Go/TS examples | Python-only corpus focus; these would pollute code retrieval |
| Auto-generated API docs | Low semantic density, better coverage from source docstrings |
| Build artifacts (`site/`) | HTML/JS build output, no value |
| CI configs (`.github/`) | No semantic value for code assistance |
| `llms-full.txt` | 1.2MB concatenated dump would dominate embedding space |
| `contributing/` | Overlaps with tests/; would create duplicates |

---

## 8) Final Ingestion Configuration

```yaml
# Add to config/settings.yaml

ingestion:
  corpora:
    adk_docs:
      root: "corpora/adk-docs"
      corpus: "adk_docs"
      repo: "google/adk-docs"
      kind: "doc"
      include_globs:
        - "docs/**/*.md"
        - "docs/**/*.mdx"
        - "examples/python/**/*.py"
        - "examples/python/**/*.md"
        - "README.md"
        - "CONTRIBUTING.md"
      exclude_globs:
        - "**/site/**"
        - "**/.git/**"
        - "**/node_modules/**"
        - "**/__pycache__/**"
        - "docs/api-reference/java/**"
        - "docs/api-reference/go/**"
        - "docs/api-reference/rest/**"
        - "examples/go/**"
        - "examples/java/**"
        - "examples/typescript/**"
        - "overrides/**"
        - "tools/**"
        - "docs/stylesheets/**"
        - "llms-full.txt"
      allowed_exts: [".md", ".mdx", ".py", ".txt"]
      max_file_bytes: 500000

    adk_python:
      root: "corpora/adk-python"
      corpus: "adk_python"
      repo: "google/adk-python"
      kind: "code"
      include_globs:
        - "src/**/*.py"
        - "tests/**/*.py"
        - "README.md"
        - "AGENTS.md"
        - "pyproject.toml"
      exclude_globs:
        - "**/.git/**"
        - "**/__pycache__/**"
        - "**/.venv/**"
        - "**/*.pyc"
        - "**/contributing/**"
        - ".github/**"
        - "scripts/**"
        - "assets/**"
        - "llms-full.txt"
      allowed_exts: [".py", ".md", ".toml"]
      max_file_bytes: 500000
```

---

## 9) Acceptance Criteria

- [ ] All 129 core docs markdown files are discovered
- [ ] All 60 Python example files are discovered
- [ ] All 96+ SDK source files are discovered
- [ ] All 382 test files are discovered
- [ ] No Java/Go/TypeScript files are included
- [ ] No build artifacts (`site/`) are included
- [ ] No `llms-full.txt` is included
- [ ] Chunk counts are within estimated ranges

---

## 10) Cross-Spec References

| Spec | Dependency |
|------|------------|
| **SPEC-01** (Foundation) | Uses `corpus` field values defined here |
| **SPEC-03** (Ingestion) | Implements include/exclude patterns from §8 |
| **SPEC-04** (Retrieval) | Filters by `corpus` values `adk_docs` / `adk_python` |
