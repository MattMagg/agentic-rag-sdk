---
description: Add new corpus/corpora to the RAG database end-to-end
---

# Add Corpora Workflow

Add a new SDK or documentation source to the RAG pipeline with proper configuration, ingestion, and documentation updates.

---

## Overview

This workflow adds a new corpus (or pair of corpora) to the RAG database. Most SDKs require TWO corpora:

| Corpus Type | Embedding Model | Purpose |
|-------------|-----------------|---------|
| `{sdk}_docs` | `voyage-context-3` | Documentation (README, docs/, guides) |
| `{sdk}_python` | `voyage-code-3` | Source code (src/, lib/, examples/) |

The `kind` field in configuration determines which embedding model is used.

---

## Step 1: Clone Repository

```bash
cd /Users/mac-main/rag_qdrant_voyage/corpora/
git clone https://github.com/{org}/{repo}.git
```

After cloning, explore the repository to identify:

1. **Documentation locations**: Look for README.md, docs/, documentation/, guides/
2. **Source code locations**: Look for src/, lib/, {package_name}/, examples/
3. **Files to exclude**: tests/, __pycache__/, .git/, node_modules/, dist/

---

## Step 2: Update Configuration

**File:** `config/settings.yaml`

**Location:** Find the `ingestion:` → `corpora:` section. Add new entries at the END of the existing corpora list.

### Template for Documentation Corpus

```yaml
    # =========================================================================
    # {SDK Display Name}
    # =========================================================================

    # {SDK Display Name} - Documentation
    {sdk}_docs:
      root: "corpora/{cloned-directory-name}"
      corpus: "{sdk}_docs"
      repo: "{org}/{repo}"
      kind: "doc"
      ref: "main"
      include_globs:
        - "README.md"
        - "docs/**/*.md"
        - "docs/**/*.mdx"
      exclude_globs:
        - "**/.git/**"
        - "**/images/**"
        - "**/node_modules/**"
      allowed_exts: [".md", ".mdx", ".rst"]
      max_file_bytes: 500000
```

### Template for Code Corpus

```yaml
    # {SDK Display Name} - Python Source Code
    {sdk}_python:
      root: "corpora/{cloned-directory-name}"
      corpus: "{sdk}_python"
      repo: "{org}/{repo}"
      kind: "code"
      ref: "main"
      include_globs:
        - "src/**/*.py"
        - "lib/**/*.py"
        - "examples/**/*.py"
        - "pyproject.toml"
      exclude_globs:
        - "**/.git/**"
        - "**/__pycache__/**"
        - "**/tests/**"
        - "**/test_*.py"
        - "**/*_test.py"
      allowed_exts: [".py", ".toml"]
      max_file_bytes: 500000
```

**Customize `include_globs`** based on the actual repository structure you observed in Step 1.

---

## Step 3: Update Type Definitions

**File:** `src/grounding/contracts/chunk.py`

**Find:** The `SourceCorpus = Literal[...]` type definition (around lines 20-35).

**Add** your new corpus names at the end, before the closing bracket:

```python
SourceCorpus = Literal[
    "adk_docs",
    "adk_python",
    # ... existing entries ...
    # {SDK Display Name}
    "{sdk}_docs",
    "{sdk}_python",
]
```

---

## Step 4: Update Query Layer

**File:** `src/grounding/query/query.py`

### 4a. Find `CORPUS_GROUPS` Dictionary (around lines 119-135)

Add your SDK group at the end, before the closing brace:

```python
CORPUS_GROUPS = {
    "adk": ["adk_docs", "adk_python"],
    "openai": ["openai_agents_docs", "openai_agents_python"],
    # ... existing groups ...
    # {SDK Display Name}
    "{sdk}": ["{sdk}_docs", "{sdk}_python"],
}
```

### 4b. Find `ALL_CORPORA` List (around lines 138-155)

Add your corpus names at the end:

```python
ALL_CORPORA = [
    "adk_docs",
    "adk_python",
    # ... existing entries ...
    # {SDK Display Name}
    "{sdk}_docs",
    "{sdk}_python",
]
```

---

## Step 5: Update `.gitignore`

**File:** `.gitignore`

**Find:** The section with other `corpora/` entries (search for `corpora/`).

**Add** your new directory:

```
corpora/{cloned-directory-name}
```

---

## Step 6: Update Documentation Files

You MUST update ALL of these files. For each file, search for existing SDK patterns and follow the same format.

### 6a. README.md

**Update these sections:**

1. **Line ~5**: Update corpora count in intro paragraph
   - Find: `Currently indexes N corpora`
   - Change: Increment by 2

2. **Lines ~59-72**: Add query example in Quick Start
   - Find: `# Query LangChain ecosystem` or similar
   - Add after:
   ```bash
   # Query {SDK Display Name}
   python -m src.grounding.query.query "example query" --sdk {sdk}
   ```

3. **Lines ~149-157**: Add row to SDK Groups table
   - Find: `| SDK Flag | Corpora | Description |`
   - Add row: `| \`--sdk {sdk}\` | \`{sdk}_docs\`, \`{sdk}_python\` | {SDK Display Name} |`

4. **Lines ~409-418**: Add to project structure tree
   - Find: `├── corpora/`
   - Add: `│   ├── {cloned-directory-name}/  # {SDK Display Name}`

### 6b. GEMINI.md

**Update these sections:**

1. **Lines ~51-66**: Add query example
   - Find: `# Query only general agent development docs`
   - Add before:
   ```bash
   # Query {SDK Display Name}
   python -m src.grounding.query.query_adk "example query" --sdk {sdk}
   ```

2. **Lines ~68-77**: Add row to SDK Groups table
   - Find: `| SDK Flag | Corpora Included |`
   - Add row: `| \`--sdk {sdk}\` | \`{sdk}_docs\`, \`{sdk}_python\` |`

### 6c. CLAUDE.md

**Update these sections:**

1. **Lines ~9-16**: Add to SDK ecosystem list
   - Find: `The RAG database contains documentation`
   - Add bullet: `- **{SDK Display Name}** - Description`

2. **Lines ~33-39**: Add query example
   - Find: `# Query specific SDK groups`
   - Add: `python -m src.grounding.query.query "your query" --sdk {sdk}  # {SDK Display Name}`

### 6d. AGENTS.md

**Update these sections:**

1. **Lines ~46-50**: Add query example
   - Find: `# SDK-specific queries`
   - Add: `python -m src.grounding.query.query "query" --sdk {sdk}  # {SDK Display Name}`

2. **Line ~239**: Update SDK groups list
   - Find: `--sdk adk|openai|langchain|...`
   - Add `|{sdk}` to the list

### 6e. docs/rag-query.md

**Update these sections:**

1. **Line ~2**: Update description in frontmatter
   - Add your SDK name to the list

2. **Lines ~13-30**: Add query example
   - Add:
   ```bash
   # Query {SDK Display Name}
   python -m src.grounding.query.query "example query" --sdk {sdk}
   ```

3. **Lines ~34-43**: Add row to SDK Groups table
   - Add: `| \`--sdk {sdk}\` | \`{sdk}_docs\`, \`{sdk}_python\` |`

4. **Lines ~84-86**: Update `--sdk` flag description
   - Add `{sdk}` to the list of valid values

5. **Lines ~105-120**: Add rows to All Corpora table
   - Add two rows for `{sdk}_docs` and `{sdk}_python`

---

## Step 7: Verify Configuration

```bash
# Activate virtual environment
source .venv/bin/activate

# Validate configuration loads correctly
python -m src.grounding.scripts.01_print_effective_config 2>&1 | grep -A 15 "{sdk}_docs"

# Ensure collection schema is up-to-date
python -m src.grounding.scripts.02_ensure_collection_schema
```

**Expected:** Your new corpus configs should appear in the output. Schema script should report "verified".

**If config fails:** Check YAML indentation (must use 2 spaces, not tabs).

---

## Step 8: Ingest Corpora

```bash
# Ingest documentation corpus
python -m src.grounding.scripts.03_ingest_corpus --corpus {sdk}_docs

# Ingest code corpus
python -m src.grounding.scripts.03_ingest_corpus --corpus {sdk}_python
```

**Expected output:**
- `Files discovered: N`
- `Chunks created: M`
- `Ingestion complete`

**If ingestion fails with 502 error:** Retry the command. The ingestion is idempotent and will skip already-processed chunks.

**If zero files discovered:** Check your `include_globs` patterns match the actual repository structure.

---

## Step 9: Test Queries

```bash
# Test with new SDK flag - should return only your SDK's results
python -m src.grounding.query.query "example query relevant to {sdk}" --sdk {sdk} --verbose

# Verify coverage balance
python -m src.grounding.query.query "example query" --sdk {sdk} --top-k 6
```

**Expected:** 
- Results should come 100% from `{sdk}_docs` and `{sdk}_python`
- Coverage should show a mix of both corpora (e.g., docs=3, code=3)

**If results are empty:** Verify ingestion completed and check corpus names match exactly.

---

## Step 10: Run Test Suite

```bash
pytest tests/ -v
```

**Expected:** All tests pass.

---

## Step 11: Commit and Push

```bash
git add \
  config/settings.yaml \
  src/grounding/contracts/chunk.py \
  src/grounding/query/query.py \
  .gitignore \
  README.md \
  GEMINI.md \
  CLAUDE.md \
  AGENTS.md \
  docs/rag-query.md

git status  # Verify all expected files are staged

git commit -m "feat(corpora): add {SDK Display Name}

## Context
Added {SDK Display Name} to the RAG database with docs and code corpora.

## Changes
- config/settings.yaml: Added {sdk}_docs and {sdk}_python corpus configs
- chunk.py: Extended SourceCorpus Literal
- query.py: Added '{sdk}' SDK group to CORPUS_GROUPS and ALL_CORPORA
- .gitignore: Added corpora/{cloned-directory-name}
- Updated all documentation with new --sdk {sdk} flag

## New SDK Flag
--sdk {sdk} → {SDK Display Name}
"

git push origin main
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Config fails to load | Check YAML indentation (2 spaces, no tabs) |
| Zero files discovered | Adjust `include_globs` to match actual repo structure |
| Ingestion 502 error | Retry command (idempotent, skips processed chunks) |
| Query returns empty | Verify corpus names match in all 3 Python files |
| Tests fail | Check `SourceCorpus` Literal includes new names |
| Coverage gate warnings | Normal if only docs or only code ingested; complete both |

---

## Naming Conventions

| Element | Format | Example |
|---------|--------|---------|
| SDK flag | lowercase, no hyphens | `anthropic`, `crewai`, `openai` |
| Docs corpus | `{sdk}_docs` | `anthropic_docs`, `crewai_docs` |
| Code corpus | `{sdk}_python` | `anthropic_python`, `crewai_python` |
| Display name | Title case, full name | `Anthropic Claude Agent SDK` |
