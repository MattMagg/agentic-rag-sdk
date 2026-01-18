"""
RAG MCP Server package.

Exposes the RAG grounding platform as MCP (Model Context Protocol) tools
for use by AI agents and Claude Code.

Provides:
- FastMCP server definition
- Tool implementations for retrieval, ingestion, discovery, diagnostics
- Background job management for long-running operations

Related files:
- src/grounding/ - Core RAG pipeline this package wraps
- src/grounding/query/query.py - search() function wrapped by retrieval tools
- src/grounding/scripts/03_ingest_corpus.py - ingestion logic wrapped by ingestion tools
"""

__version__ = "0.1.0"

from .server import main, mcp

__all__ = [
    "__version__",
    "main",
    "mcp",
]
