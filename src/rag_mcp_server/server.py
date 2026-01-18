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

import asyncio
from typing import Annotated, Any

from fastmcp import FastMCP

# Import the search function and corpus groups from grounding pipeline
from src.grounding.query.query import CORPUS_GROUPS, search as grounding_search

# Create the FastMCP server instance
mcp = FastMCP("rag-server")


# =============================================================================
# Preset Configurations
# =============================================================================

# Preset parameter mappings for different retrieval strategies
RETRIEVAL_PRESETS: dict[str, dict[str, Any]] = {
    "balanced": {
        # Default balanced retrieval
        "first_stage_k": 80,
        "rerank_candidates": 60,
        "rerank": True,
        "expand_context": True,
    },
    "precision": {
        # High precision: more candidates, stricter threshold
        "first_stage_k": 100,
        "rerank_candidates": 80,
        "rerank": True,
        "score_threshold": 0.3,
        "expand_context": True,
    },
    "recall": {
        # High recall: more results, RRF fusion
        "first_stage_k": 120,
        "rerank_candidates": 100,
        "rerank": True,
        "fusion_method": "rrf",
        "expand_context": True,
    },
    "speed": {
        # Fast retrieval: skip reranking, no expansion
        "first_stage_k": 60,
        "rerank_candidates": 40,
        "rerank": False,
        "expand_context": False,
    },
}


def _transform_result_to_evidence(result: dict[str, Any]) -> dict[str, Any]:
    """
    Transform a search result to the Evidence Pack format.

    Converts internal result format to agent-consumable evidence format.
    """
    # Build lines string from start_line and end_line
    start_line = result.get("start_line")
    end_line = result.get("end_line")
    if start_line is not None and end_line is not None:
        lines = f"{start_line}-{end_line}"
    elif start_line is not None:
        lines = str(start_line)
    else:
        lines = ""

    # Determine if this is an expanded chunk
    is_expanded = "expanded_from" in result

    # Get score (prefer rerank_score, fall back to rrf_score, then score)
    # Use explicit None checks to handle 0.0 scores correctly
    score = result.get("rerank_score")
    if score is None:
        score = result.get("rrf_score")
    if score is None:
        score = result.get("score", 0.0)

    return {
        "id": str(result.get("id", "")),
        "corpus": result.get("corpus", ""),
        "kind": result.get("kind", ""),
        "path": result.get("path", ""),
        "lines": lines,
        "text": result.get("text", ""),
        "score": score,
        "title": result.get("title"),  # May be None
        "is_expanded": is_expanded,
    }


def _build_corpus_filter(
    sdk: str | None,
    corpus: list[str] | None,
    kind: str | None,
) -> dict[str, Any] | None:
    """
    Build filter dict from SDK, corpus, and kind parameters.

    Args:
        sdk: SDK group name (e.g., "adk", "openai")
        corpus: List of specific corpus names
        kind: Content type ("doc" or "code")

    Returns:
        Filter dict for search(), or None if no filters
    """
    filters: dict[str, Any] = {}

    # SDK takes precedence over corpus
    if sdk and sdk in CORPUS_GROUPS:
        filters["corpus"] = CORPUS_GROUPS[sdk]
    elif corpus:
        if len(corpus) == 1:
            filters["corpus"] = corpus[0]
        else:
            filters["corpus"] = corpus

    # Add kind filter if specified
    if kind in ("doc", "code"):
        filters["kind"] = kind

    return filters if filters else None


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
    corpus: Annotated[
        list[str] | None,
        "Filter by specific corpus names (e.g., ['adk_docs', 'adk_python'])",
    ] = None,
    kind: Annotated[
        str | None,
        "Filter by content type: 'doc' for documentation, 'code' for source code",
    ] = None,
    preset: Annotated[
        str,
        "Retrieval preset: 'balanced' (default), 'precision', 'recall', 'speed'",
    ] = "balanced",
    top_k: Annotated[int, "Number of results to return"] = 12,
    mode: Annotated[
        str,
        "Search intent: 'build' (implementation), 'debug', 'explain', 'refactor'",
    ] = "build",
    expand_context: Annotated[
        bool, "Whether to fetch adjacent chunks for context"
    ] = True,
    verbose: Annotated[bool, "Include timing and debug info in response"] = False,
) -> dict[str, Any]:
    """
    Full RAG search with reranking and context expansion.

    Performs hybrid search across documentation and code using Voyage AI
    embeddings, applies cross-encoder reranking for relevance, and optionally
    expands results with adjacent chunks for better context.

    Returns an Evidence Pack with search results, coverage stats, and metadata.

    Use this for comprehensive searches where quality matters more than speed.
    For faster searches without reranking, use rag_search_quick.
    """
    warnings: list[str] = []

    # Validate preset
    if preset not in RETRIEVAL_PRESETS:
        warnings.append(f"Unknown preset '{preset}', using 'balanced'")
        preset = "balanced"

    # Validate SDK
    if sdk and sdk not in CORPUS_GROUPS:
        valid_sdks = list(CORPUS_GROUPS.keys())
        warnings.append(f"Unknown SDK '{sdk}', valid options: {valid_sdks}")
        sdk = None

    # Validate mode
    valid_modes = ("build", "debug", "explain", "refactor")
    if mode not in valid_modes:
        warnings.append(f"Unknown mode '{mode}', using 'build'")
        mode = "build"

    # Build filters
    filters = _build_corpus_filter(sdk, corpus, kind)

    # Get preset parameters
    preset_params = RETRIEVAL_PRESETS[preset].copy()

    # Override expand_context from explicit parameter
    preset_params["expand_context"] = expand_context

    try:
        # Run sync search in thread pool to avoid blocking
        loop = asyncio.get_running_loop()
        raw_result = await loop.run_in_executor(
            None,
            lambda: grounding_search(
                query=query,
                top_k=top_k,
                mode=mode,  # type: ignore
                filters=filters,
                verbose=verbose,
                **preset_params,
            ),
        )

        # Transform results to Evidence Pack format
        evidence = [
            _transform_result_to_evidence(r)
            for r in raw_result.get("results", [])
        ]

        # Build coverage info
        coverage_raw = raw_result.get("coverage", {})
        doc_count = sum(1 for e in evidence if e["kind"] == "doc")
        code_count = sum(1 for e in evidence if e["kind"] == "code")
        corpora_list = list(coverage_raw.keys())

        # Combine warnings
        all_warnings = warnings + raw_result.get("warnings", [])

        # Build response
        response: dict[str, Any] = {
            "query": query,
            "count": len(evidence),
            "evidence": evidence,
            "coverage": {
                "doc_count": doc_count,
                "code_count": code_count,
                "corpora": corpora_list,
            },
            "warnings": all_warnings,
        }

        # Include timing if verbose
        if verbose:
            response["timing"] = raw_result.get("timings", {})
            response["pipeline"] = raw_result.get("pipeline", {})

        return response

    except Exception as e:
        # Return error dict instead of raising
        return {
            "query": query,
            "count": 0,
            "evidence": [],
            "coverage": {
                "doc_count": 0,
                "code_count": 0,
                "corpora": [],
            },
            "error": str(e),
            "error_type": type(e).__name__,
            "warnings": warnings + [f"Search failed: {e}"],
        }


@mcp.tool
async def rag_search_quick(
    query: Annotated[str, "The search query to find relevant documents and code"],
    sdk: Annotated[
        str | None,
        "Filter by SDK: 'adk', 'openai', 'langchain', 'langgraph', 'anthropic', 'crewai'",
    ] = None,
    corpus: Annotated[
        list[str] | None,
        "Filter by specific corpus names (e.g., ['adk_docs', 'adk_python'])",
    ] = None,
    kind: Annotated[
        str | None,
        "Filter by content type: 'doc' for documentation, 'code' for source code",
    ] = None,
    top_k: Annotated[int, "Number of results to return"] = 20,
) -> dict[str, Any]:
    """
    Fast RAG search without reranking (3-5x faster than rag_search).

    Performs hybrid search across documentation and code but skips reranking
    and context expansion for faster response times. Results are ordered by
    hybrid search score only. Higher default top_k compensates for less
    precise ranking.

    Use this for quick lookups where speed matters more than optimal ranking.
    For comprehensive searches with reranking, use rag_search instead.
    """
    warnings: list[str] = []

    # Validate SDK
    if sdk and sdk not in CORPUS_GROUPS:
        valid_sdks = list(CORPUS_GROUPS.keys())
        warnings.append(f"Unknown SDK '{sdk}', valid options: {valid_sdks}")
        sdk = None

    # Build filters
    filters = _build_corpus_filter(sdk, corpus, kind)

    # Speed-optimized parameters: no reranking, no context expansion
    # Lower first_stage_k since we're not reranking anyway
    speed_params = {
        "rerank": False,
        "expand_context": False,
        "first_stage_k": 60,
        "rerank_candidates": 40,
    }

    try:
        # Run sync search in thread pool to avoid blocking
        loop = asyncio.get_running_loop()
        raw_result = await loop.run_in_executor(
            None,
            lambda: grounding_search(
                query=query,
                top_k=top_k,
                mode="build",  # Default mode
                filters=filters,
                verbose=False,  # Keep it fast
                **speed_params,
            ),
        )

        # Transform results to Evidence Pack format
        evidence = [
            _transform_result_to_evidence(r)
            for r in raw_result.get("results", [])
        ]

        # Build coverage info
        coverage_raw = raw_result.get("coverage", {})
        doc_count = sum(1 for e in evidence if e["kind"] == "doc")
        code_count = sum(1 for e in evidence if e["kind"] == "code")
        corpora_list = list(coverage_raw.keys())

        # Combine warnings
        all_warnings = warnings + raw_result.get("warnings", [])

        return {
            "query": query,
            "count": len(evidence),
            "evidence": evidence,
            "coverage": {
                "doc_count": doc_count,
                "code_count": code_count,
                "corpora": corpora_list,
            },
            "warnings": all_warnings,
        }

    except Exception as e:
        # Return error dict instead of raising
        return {
            "query": query,
            "count": 0,
            "evidence": [],
            "coverage": {
                "doc_count": 0,
                "code_count": 0,
                "corpora": [],
            },
            "error": str(e),
            "error_type": type(e).__name__,
            "warnings": warnings + [f"Search failed: {e}"],
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
