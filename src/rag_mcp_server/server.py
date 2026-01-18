"""
FastMCP server definition for the RAG MCP Server.

This module defines the main MCP server that exposes RAG pipeline functionality
as agent-consumable tools. Uses FastMCP framework for Python MCP servers.

Tools exposed:
- rag_search: Full retrieval with reranking and context expansion
- rag_search_quick: Fast retrieval without reranking
- rag_ingest_start: Start background corpus ingestion
- rag_ingest_status: Check ingestion job status
- rag_corpus_list: List available corpora
- rag_corpus_info: Get corpus details and statistics
- rag_diagnose: Run diagnostic checks on RAG platform
- rag_config_show: Display current configuration

Related files:
- src/rag_mcp_server/tools/ - Tool implementations (future)
- src/rag_mcp_server/config.py - Server configuration (future)
- src/grounding/ - Core RAG pipeline
"""

from __future__ import annotations

from typing import Annotated

from fastmcp import FastMCP

# Create the FastMCP server instance
mcp = FastMCP("rag-server")


# =============================================================================
# Retrieval Tools
# =============================================================================


@mcp.tool
async def rag_search(
    query: Annotated[str, "The search query to find relevant documents and code"],
    sdk: Annotated[
        str | None,
        "Filter by SDK: 'adk', 'openai', 'langchain', 'langgraph', 'anthropic', 'crewai'",
    ] = None,
    top_k: Annotated[int, "Number of results to return"] = 10,
    expand_context: Annotated[
        bool, "Whether to fetch adjacent chunks for context"
    ] = True,
) -> dict:
    """
    Full RAG search with reranking and context expansion.

    Performs hybrid search across documentation and code, applies Voyage AI
    reranking for relevance, and optionally expands results with adjacent
    chunks for better context.

    Use this for comprehensive searches where quality matters more than speed.
    """
    return {
        "status": "not_implemented",
        "tool": "rag_search",
        "params": {
            "query": query,
            "sdk": sdk,
            "top_k": top_k,
            "expand_context": expand_context,
        },
    }


@mcp.tool
async def rag_search_quick(
    query: Annotated[str, "The search query to find relevant documents and code"],
    sdk: Annotated[
        str | None,
        "Filter by SDK: 'adk', 'openai', 'langchain', 'langgraph', 'anthropic', 'crewai'",
    ] = None,
    top_k: Annotated[int, "Number of results to return"] = 5,
) -> dict:
    """
    Fast RAG search without reranking.

    Performs hybrid search across documentation and code but skips the
    reranking step for faster response times. Use when speed is more
    important than optimal ranking.
    """
    return {
        "status": "not_implemented",
        "tool": "rag_search_quick",
        "params": {
            "query": query,
            "sdk": sdk,
            "top_k": top_k,
        },
    }


# =============================================================================
# Ingestion Tools
# =============================================================================


@mcp.tool
async def rag_ingest_start(
    corpus: Annotated[
        str | None, "Corpus name to ingest, or None to ingest all corpora"
    ] = None,
) -> dict:
    """
    Start background corpus ingestion.

    Initiates ingestion of documents and code into the vector database.
    Returns a job ID that can be used to check status with rag_ingest_status.

    Ingestion is idempotent - unchanged files are skipped based on content hash.
    """
    return {
        "status": "not_implemented",
        "tool": "rag_ingest_start",
        "params": {
            "corpus": corpus,
        },
    }


@mcp.tool
async def rag_ingest_status(
    job_id: Annotated[
        str | None, "Job ID from rag_ingest_start, or None for all jobs"
    ] = None,
) -> dict:
    """
    Check ingestion job status.

    Returns the current state of an ingestion job including progress,
    files processed, and any errors encountered.
    """
    return {
        "status": "not_implemented",
        "tool": "rag_ingest_status",
        "params": {
            "job_id": job_id,
        },
    }


# =============================================================================
# Discovery Tools
# =============================================================================


@mcp.tool
async def rag_corpus_list() -> dict:
    """
    List all available corpora.

    Returns the names and basic info for all configured corpora that can
    be searched or ingested. Useful for discovering what content is available.
    """
    return {
        "status": "not_implemented",
        "tool": "rag_corpus_list",
    }


@mcp.tool
async def rag_corpus_info(
    corpus: Annotated[str, "Name of the corpus to get info about"],
) -> dict:
    """
    Get detailed corpus information.

    Returns statistics about a specific corpus including document count,
    chunk count, last ingestion time, and configured paths/extensions.
    """
    return {
        "status": "not_implemented",
        "tool": "rag_corpus_info",
        "params": {
            "corpus": corpus,
        },
    }


# =============================================================================
# Diagnostic Tools
# =============================================================================


@mcp.tool
async def rag_diagnose() -> dict:
    """
    Run diagnostic checks on the RAG platform.

    Verifies connectivity to Qdrant and Voyage AI, checks collection schema,
    and reports on system health. Use when troubleshooting issues.
    """
    return {
        "status": "not_implemented",
        "tool": "rag_diagnose",
    }


@mcp.tool
async def rag_config_show(
    include_secrets: Annotated[
        bool, "Whether to include API keys (masked) in output"
    ] = False,
) -> dict:
    """
    Display current RAG configuration.

    Shows the active configuration including Qdrant URL, collection name,
    retrieval settings, and ingestion paths. Secrets are masked by default.
    """
    return {
        "status": "not_implemented",
        "tool": "rag_config_show",
        "params": {
            "include_secrets": include_secrets,
        },
    }


# =============================================================================
# CLI Entry Point
# =============================================================================


def main() -> None:
    """
    CLI entry point for the RAG MCP server.

    Supports two transport modes:
    - stdio (default): For local integration with Claude Code and other MCP clients
    - http: For remote access via HTTP transport

    Usage:
        rag-mcp-server                              # Run with stdio (default)
        rag-mcp-server --transport http --port 8080 # Run with HTTP
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="rag-mcp-server",
        description="RAG MCP Server - Expose RAG pipeline as MCP tools",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for HTTP transport (default: 8080)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host for HTTP transport (default: 127.0.0.1)",
    )

    args = parser.parse_args()

    if args.transport == "http":
        mcp.run(transport="http", host=args.host, port=args.port)
    else:
        mcp.run()  # stdio is the default


if __name__ == "__main__":
    main()
