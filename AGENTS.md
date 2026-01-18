# AGENTS.md

Guidelines for AI coding agents working in this repository.

## Build & Test Commands

```bash
# Install in development mode
pip install -e .
pip install -e ".[dev]"  # includes pytest

# Run all tests
pytest tests/

# Run a single test file
pytest tests/test_config_loads.py

# Run a single test function
pytest tests/test_config_loads.py::test_function_name -v

# Run tests with verbose output
pytest tests/ -v

# Run tests matching a pattern
pytest tests/ -k "config" -v
```

## Pipeline Scripts

Run in order for fresh setup:

```bash
python -m src.grounding.scripts.00_smoke_test_connections  # Verify API connections
python -m src.grounding.scripts.01_print_effective_config  # Show loaded config
python -m src.grounding.scripts.02_ensure_collection_schema  # Create/update Qdrant schema
python -m src.grounding.scripts.03_ingest_corpus            # Ingest all corpora
python -m src.grounding.scripts.03_ingest_corpus --corpus adk_docs  # Single corpus
```

## Query Commands

```bash
# Basic query
python -m src.grounding.query.query "your query"

# SDK-specific queries
python -m src.grounding.query.query "query" --sdk adk       # Google ADK
python -m src.grounding.query.query "query" --sdk openai    # OpenAI Agents
python -m src.grounding.query.query "query" --sdk langchain # LangChain ecosystem
python -m src.grounding.query.query "query" --sdk langgraph # LangGraph + DeepAgents
python -m src.grounding.query.query "query" --sdk anthropic # Claude Agent SDK
python -m src.grounding.query.query "query" --sdk crewai    # CrewAI Framework

# Additional options
python -m src.grounding.query.query "query" --verbose --multi-query --top-k 12

# Context expansion (enabled by default, fetch adjacent chunks)
python -m src.grounding.query.query "query" --expand-context --expand-top-k 3 --expand-window 2
```

## Code Style Guidelines

### Python Version
- **Python 3.11+** required (uses `X | Y` union syntax, `list[T]` generics)

### Imports

Order imports as: stdlib, third-party, local. Use `from __future__ import annotations` for forward references:

```python
from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

from src.grounding.config import get_settings
```

### Type Hints

Always use type hints. Prefer modern syntax:

```python
# Good
def process(items: list[str], mapping: dict[str, int]) -> str | None:
    ...

# Good - use Literal for constrained values
SourceCorpus = Literal["adk_docs", "adk_python", "langchain_python"]
ContentKind = Literal["code", "doc"]

# Good - Optional via union
symbol: str | None = None
```

### Pydantic Models

Use Pydantic v2 with Field descriptions:

```python
class CorpusConfig(BaseModel):
    """Configuration for a single corpus."""
    root: str = Field(description="Path to corpus root directory")
    corpus: str = Field(description="Corpus identifier")
    kind: str = Field(description="Content kind: doc or code")
    include_globs: list[str] = Field(default_factory=list)
```

### Docstrings

Use Google-style docstrings with module-level related files:

```python
"""
Module description.

Related files:
- src/grounding/contracts/ids.py - ID generation functions
- docs/spec/qdrant_schema_and_config.md - Schema specification
"""

def function(param: str, count: int = 10) -> list[str]:
    """
    Brief description.

    Args:
        param: Description of param
        count: Description with default note

    Returns:
        Description of return value

    Raises:
        ValueError: When param is invalid
    """
```

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

### Error Handling

Prefer explicit checks over try/except for expected conditions:

```python
# Good
if not corpus_root.exists():
    console.print(f"[red]Corpus root not found: {corpus_root}[/red]")
    return {"files": 0, "chunks": 0}

# Use try/except for truly exceptional cases
try:
    result = api_client.call()
except APIError as e:
    console.print(f"[red]API error: {e}[/red]")
    raise
```

### Dataclasses vs Pydantic

- **Pydantic**: For external data (config, API payloads, storage schemas)
- **Dataclasses**: For internal data structures

```python
# Pydantic - external contract
class Chunk(BaseModel):
    chunk_id: str = Field(description="Stable unique ID")
    corpus: SourceCorpus

# Dataclass - internal structure
@dataclass
class ChunkData:
    text: str
    chunk_index: int
    title: str | None
```

### Caching

Use `@lru_cache` for expensive singleton operations:

```python
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings loader."""
    ...

@lru_cache(maxsize=1)
def get_voyage_client() -> VoyageClientWrapper:
    """Singleton client instance."""
    ...
```

### Console Output

Use `rich` for CLI output:

```python
from rich.console import Console
console = Console()

console.print(f"[green]Success[/green]")
console.print(f"[red]Error: {msg}[/red]")
console.print(f"[yellow]Warning[/yellow]")
console.print(f"[dim]Debug info[/dim]")
```

## Project Structure

```
src/grounding/
    config.py           # Settings loader (get_settings)
    clients/            # API client wrappers (Qdrant, Voyage, FastEmbed)
    contracts/          # Pydantic models (Chunk, Document, IDs)
    chunkers/           # Content chunkers (markdown, python_code)
    query/              # Query pipeline (search)
    scripts/            # CLI scripts (00-04)
    util/               # Helpers (hashing, time, fs_walk)
tests/                  # pytest tests
config/settings.yaml    # YAML config with ${VAR} substitution
.env                    # Environment variables (not committed)
```

## Key Patterns

1. **Config loading**: Always use `get_settings()` - it's cached and handles env substitution
2. **Client access**: Use `get_*_client()` functions for singleton instances
3. **Idempotent ingestion**: Chunks are deduplicated via `text_hash` comparison
4. **SDK groups**: Filter queries with `--sdk adk|openai|langchain|langgraph|anthropic|crewai|general`
