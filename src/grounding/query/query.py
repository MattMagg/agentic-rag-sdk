#!/usr/bin/env python3
"""
Optimal RAG Grounding Query Script

Multi-Stage Retrieval Pipeline:
1. Multi-Query Expansion (optional, off by default for speed)
   - Generates balanced code/docs query variations
   - 14-20% improvement in retrieval quality

2. Hybrid Search (Dense Docs + Dense Code + Sparse)
   - Dense: semantic understanding via Voyage AI
   - Sparse: keyword/lexical matching via SPLADE
   - RRF/DBSF fusion built into Qdrant

3. Coverage-Aware Candidate Pool
   - Ensures balanced code/docs mix BEFORE reranking
   - Prevents reranker from seeing only one type

4. VoyageAI Reranking (Cross-encoder)
   - Final refinement with rerank-2.5
   - Large candidate pool (60+) for best results

4b. Context-Aware Expansion (enabled by default)
   - Fetches adjacent chunks (±N) around top-K reranked results
   - Provides contextual continuity for better comprehension
   - Score inheritance: adjacent_score = parent_score * (decay_factor ** distance)
   - ~3-4% overhead, 50-70ms additional latency

5. Coverage Gates
   - Final selection ensuring minimum docs/code representation
   - Guarantees diverse result set across content types

Usage:
    from src.grounding.query.query import search

    results = search(
        query="how to use tool context",
        top_k=12
    )

    # With context expansion (enabled by default)
    results = search(
        query="LoopAgent implementation",
        top_k=12,
        expand_context=True,  # Explicit (default: True from config)
        expand_top_k=5,       # Expand top 5 results
        expand_window=1       # Fetch ±1 adjacent chunks
    )

Command line:
    python -m src.grounding.query.query "how to use tool context" --top-k 12
    python -m src.grounding.query.query "LoopAgent" --multi-query --verbose
    python -m src.grounding.query.query "agent patterns" --expand-context --expand-top-k 3
"""

import os
import sys
import time
from collections import defaultdict
from typing import Any, Dict, List, Literal, Optional

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
except ImportError:
    print(
        "ERROR: qdrant-client not installed. Run: pip install qdrant-client",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    import voyageai
except ImportError:
    print("ERROR: voyageai not installed. Run: pip install voyageai", file=sys.stderr)
    sys.exit(1)

try:
    from fastembed import SparseTextEmbedding
except ImportError:
    print("ERROR: fastembed not installed. Run: pip install fastembed", file=sys.stderr)
    sys.exit(1)

from src.grounding.config import get_settings


# Type aliases
RetrievalMode = Literal["build", "debug", "explain", "refactor"]

# Client cache for performance (avoid re-initialization)
_client_cache: Optional[Dict[str, Any]] = None


def _get_clients() -> Dict[str, Any]:
    """
    Get cached clients or initialize them if not cached.

    Returns a dict with: qdrant, voyage, sparse_model
    """
    global _client_cache
    if _client_cache is None:
        settings = get_settings()
        _client_cache = {
            "qdrant": QdrantClient(
                url=settings.qdrant.url, api_key=settings.qdrant.api_key, timeout=120
            ),
            "voyage": voyageai.Client(api_key=settings.voyage.api_key),
            "sparse_model": SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1"),
        }
    return _client_cache


def _clear_client_cache():
    """Clear client cache (useful for testing or config changes)."""
    global _client_cache
    _client_cache = None

# Corpus groupings for convenient filtering
CORPUS_GROUPS = {
    "adk": ["adk_docs", "adk_python"],
    "openai": ["openai_agents_docs", "openai_agents_python"],
    "general": ["agent_dev_docs"],
    # LangChain ecosystem
    "langchain": [
        "langgraph_python",
        "langchain_python",
        "deepagents_python",
        "deepagents_docs",
    ],
    "langgraph": ["langgraph_python", "deepagents_python", "deepagents_docs"],
    # Anthropic Claude Agent SDK
    "anthropic": ["claude_sdk_docs", "claude_sdk_python"],
    # CrewAI Framework
    "crewai": ["crewai_docs", "crewai_python"],
}

# All known corpora (for validation)
ALL_CORPORA = [
    "adk_docs",
    "adk_python",
    "agent_dev_docs",
    "openai_agents_docs",
    "openai_agents_python",
    # LangChain ecosystem
    "langgraph_python",
    "langchain_python",
    "deepagents_docs",
    "deepagents_python",
    # Anthropic Claude Agent SDK
    "claude_sdk_docs",
    "claude_sdk_python",
    # CrewAI Framework
    "crewai_docs",
    "crewai_python",
]


def generate_query_variations(
    original_query: str, num_variations: int = 3
) -> List[str]:
    """
    Generate balanced code/docs query perspectives for multi-query expansion.

    Args:
        original_query: User's original search query
        num_variations: Number of additional variations to generate

    Returns:
        List of query strings including original + variations
    """
    queries = [original_query]

    # Balanced templates: 1 code-specific, 1 neutral, 1 docs-specific
    templates = [
        f"Python source code class: {original_query}",  # code-specific
        f"ADK implementation pattern: {original_query}",  # neutral
        f"ADK documentation guide: {original_query}",  # docs-specific
    ]

    return queries + templates[:num_variations]


def embed_query_dense_docs(
    query: str, voyage_client: voyageai.Client, settings
) -> List[float]:
    """
    Embed query with voyage-context-3 for document matching.

    NOTE: voyage-context-3 requires the contextualized_embed endpoint.
    """
    result = voyage_client.contextualized_embed(
        inputs=[[query]],
        model=settings.voyage.docs_model,
        input_type="query",
        output_dimension=settings.voyage.output_dimension,
        output_dtype=settings.voyage.output_dtype,
    )
    return result.results[0].embeddings[0]


def embed_query_dense_code(
    query: str, voyage_client: voyageai.Client, settings
) -> List[float]:
    """Embed query with voyage-code-3 for code matching."""
    result = voyage_client.embed(
        texts=[query],
        model=settings.voyage.code_model,
        input_type="query",
        output_dimension=settings.voyage.output_dimension,
        output_dtype=settings.voyage.output_dtype,
    )
    return result.embeddings[0]


def embed_query_sparse(
    query: str, sparse_model: SparseTextEmbedding
) -> models.SparseVector:
    """Embed query with SPLADE (sparse vector)."""
    embeddings = list(sparse_model.query_embed([query]))
    emb = embeddings[0]
    return models.SparseVector(indices=list(emb.indices), values=list(emb.values))


def reciprocal_rank_fusion(results_lists: List[List[Dict]], k: int = 60) -> List[Dict]:
    """
    Fuse multiple result lists using Reciprocal Rank Fusion.

    RRF formula: score(d) = Σ 1 / (k + rank(d))
    """
    scores = defaultdict(float)
    doc_map = {}

    for results in results_lists:
        for rank, doc in enumerate(results, start=1):
            doc_id = doc["id"]
            scores[doc_id] += 1.0 / (k + rank)
            if doc_id not in doc_map:
                doc_map[doc_id] = doc

    ranked_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

    fused_results = []
    for doc_id in ranked_ids:
        doc = doc_map[doc_id].copy()
        doc["rrf_score"] = scores[doc_id]
        fused_results.append(doc)

    return fused_results


def balance_candidate_pool(
    candidates: List[Dict], target_size: int, min_per_type: int = 10
) -> List[Dict]:
    """
    Create a balanced candidate pool BEFORE reranking.

    This ensures the reranker sees both docs and code candidates.
    """
    doc_candidates = [c for c in candidates if c.get("kind") == "doc"]
    code_candidates = [c for c in candidates if c.get("kind") == "code"]

    # Calculate how many of each to include
    docs_to_take = max(min_per_type, target_size // 2)
    code_to_take = max(min_per_type, target_size // 2)

    # Take from each pool
    balanced = []
    balanced.extend(doc_candidates[:docs_to_take])
    balanced.extend(code_candidates[:code_to_take])

    # If we still have room and one pool is exhausted, fill from the other
    remaining = target_size - len(balanced)
    if remaining > 0:
        all_remaining = [
            c for c in candidates if c["id"] not in {b["id"] for b in balanced}
        ]
        balanced.extend(all_remaining[:remaining])

    return balanced


def apply_coverage_gates(
    candidates: List[Dict], top_k: int, min_docs: int = 3, min_code: int = 3
) -> tuple[List[Dict], List[str]]:
    """
    Apply coverage gates to ensure balanced docs/code mix in final output.
    """
    warnings = []

    doc_candidates = [c for c in candidates if c.get("kind") == "doc"]
    code_candidates = [c for c in candidates if c.get("kind") == "code"]

    selected = []
    selected_ids = set()

    # Force include top min_docs from docs
    for c in doc_candidates[:min_docs]:
        if c["id"] not in selected_ids:
            selected.append(c)
            selected_ids.add(c["id"])

    # Force include top min_code from code
    for c in code_candidates[:min_code]:
        if c["id"] not in selected_ids:
            selected.append(c)
            selected_ids.add(c["id"])

    # Fill remaining slots by score
    remaining = top_k - len(selected)
    for c in candidates:
        if remaining <= 0:
            break
        if c["id"] not in selected_ids:
            selected.append(c)
            selected_ids.add(c["id"])
            remaining -= 1

    # Sort by score
    selected.sort(
        key=lambda x: x.get("rerank_score", x.get("rrf_score", 0)), reverse=True
    )

    # Check coverage
    final_docs = sum(1 for c in selected if c.get("kind") == "doc")
    final_code = sum(1 for c in selected if c.get("kind") == "code")

    if final_docs < min_docs or final_code < min_code:
        warnings.append(
            f"Coverage gate: docs={final_docs}, code={final_code} (wanted {min_docs}/{min_code})"
        )

    return selected, warnings


def expand_context_around_chunks(
    candidates: List[Dict],
    qdrant: QdrantClient,
    collection_name: str,
    expand_top_k: int,
    window_size: int,
    score_decay_factor: float,
    max_expanded_chunks: int,
    verbose: bool = False,
) -> tuple[List[Dict], List[str]]:
    """
    Expand context by fetching adjacent chunks for top-K results.

    Strategy:
    1. Select top expand_top_k candidates (sorted by rerank_score)
    2. Build batch OR filter for all adjacent chunks (path + chunk_index)
    3. Execute single scroll() call
    4. Match fetched chunks to parents, compute inherited scores
    5. Deduplicate against existing candidates
    6. Merge and return

    Args:
        candidates: Reranked candidates with scores
        qdrant: Qdrant client instance
        collection_name: Qdrant collection name
        expand_top_k: Number of top candidates to expand (default: 5)
        window_size: How many chunks on each side (±N, default: 1)
        score_decay_factor: Score multiplier (default: 0.85)
        max_expanded_chunks: Safety limit on total expanded (default: 20)
        verbose: Print debug info

    Returns:
        Tuple of (expanded_candidates_list, warnings_list)

    Score Inheritance:
        adjacent_score = parent_rerank_score * (decay_factor ** abs(relative_position))

        Example (decay=0.85):
        Parent (N):   score = 0.900
        Adjacent N±1: score = 0.900 * 0.85¹ = 0.765
        Adjacent N±2: score = 0.900 * 0.85² = 0.650
    """
    warnings = []

    # 1. Select top-K candidates to expand
    sorted_candidates = sorted(
        candidates, key=lambda x: x.get("rerank_score", 0), reverse=True
    )
    expand_targets = sorted_candidates[:expand_top_k]

    # 2. Build batch OR filter for adjacent chunks
    fetch_targets = []
    for chunk in expand_targets:
        path = chunk["path"]
        chunk_idx = chunk.get("chunk_index")

        # Skip if chunk_index is missing
        if chunk_idx is None:
            continue

        for offset in range(-window_size, window_size + 1):
            if offset == 0:
                continue  # Skip parent chunk
            target_idx = chunk_idx + offset
            if target_idx < 0:
                continue  # No negative chunk indices

            fetch_targets.append(
                {
                    "path": path,
                    "chunk_index": target_idx,
                    "parent_id": chunk["id"],
                    "parent_score": chunk.get("rerank_score", 0),
                    "relative_position": offset,
                }
            )

    if not fetch_targets:
        return candidates, warnings

    # 3. Build OR filter conditions
    conditions = []
    for target in fetch_targets:
        conditions.append(
            models.Filter(
                must=[
                    models.FieldCondition(
                        key="path", match=models.MatchValue(value=target["path"])
                    ),
                    models.FieldCondition(
                        key="chunk_index",
                        match=models.MatchValue(value=target["chunk_index"]),
                    ),
                ]
            )
        )

    # 4. Single scroll call to fetch all adjacent chunks
    combined_filter = models.Filter(should=conditions)
    try:
        records, _ = qdrant.scroll(
            collection_name=collection_name,
            scroll_filter=combined_filter,
            limit=len(fetch_targets),
            with_payload=True,
        )
    except Exception as e:
        warnings.append(f"context_expansion_failed: {str(e)}")
        return candidates, warnings

    # 5. Match fetched to parents, compute scores
    existing_ids = {c["id"] for c in candidates}
    expanded_chunks = []

    for record in records:
        chunk_id = str(record.id)
        if chunk_id in existing_ids:
            continue  # Deduplicate

        # Find parent from fetch_targets
        chunk_path = record.payload.get("path")
        chunk_idx = record.payload.get("chunk_index")

        parent_info = next(
            (
                t
                for t in fetch_targets
                if t["path"] == chunk_path and t["chunk_index"] == chunk_idx
            ),
            None,
        )

        if not parent_info:
            continue

        # Compute inherited score
        decay = score_decay_factor ** abs(parent_info["relative_position"])
        inherited_score = parent_info["parent_score"] * decay

        expanded_chunks.append(
            {
                "id": chunk_id,
                "text": record.payload.get("text", ""),
                "corpus": record.payload.get("corpus", ""),
                "kind": record.payload.get("kind", ""),
                "repo": record.payload.get("repo", ""),
                "path": record.payload.get("path", ""),
                "commit": record.payload.get("commit", ""),
                "chunk_id": record.payload.get("chunk_id", ""),
                "chunk_index": record.payload.get("chunk_index"),
                "start_line": record.payload.get("start_line"),
                "end_line": record.payload.get("end_line"),
                "score": inherited_score,
                "rerank_score": inherited_score,
                "reranked": False,
                # Expansion metadata
                "expanded_from": parent_info["parent_id"],
                "relative_position": parent_info["relative_position"],
            }
        )

    # 6. Apply max_expanded_chunks limit
    if len(expanded_chunks) > max_expanded_chunks:
        warnings.append(
            f"context_expansion: truncated to {max_expanded_chunks} "
            f"(would have added {len(expanded_chunks)})"
        )
        expanded_chunks = expanded_chunks[:max_expanded_chunks]

    # 7. Merge and return
    all_candidates = candidates + expanded_chunks

    if verbose and len(expanded_chunks) > 0:
        expected = len(fetch_targets)
        actual = len(expanded_chunks)
        if actual < expected:
            warnings.append(
                f"context_expansion: fetched {actual}/{expected} "
                f"adjacent chunks (some missing)"
            )

    return all_candidates, warnings


def search(
    query: str,
    top_k: Optional[int] = None,  # None = use config
    mode: RetrievalMode = "build",
    multi_query: bool = False,  # Off by default for speed
    num_query_variations: int = 3,
    rerank: bool = True,
    first_stage_k: Optional[int] = None,  # None = use config
    rerank_candidates: Optional[int] = None,  # None = use config
    fusion_method: Optional[str] = None,  # None = use config
    score_threshold: Optional[float] = None,  # None = use config
    filters: Optional[Dict[str, Any]] = None,
    expand_context: Optional[bool] = None,  # None = use config
    expand_top_k: Optional[int] = None,  # None = use config
    expand_window: Optional[int] = None,  # None = use config
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Optimal RAG query with multi-stage retrieval pipeline.

    Pipeline:
    1. Multi-query expansion (optional, off by default)
    2. Hybrid search (dense docs + dense code + sparse with configurable fusion)
    3. Coverage-aware candidate balancing
    4. VoyageAI reranking with large candidate pool
    4b. Context expansion (optional, fetch adjacent chunks for top-K results)
    5. Coverage gates for final selection

    Args:
        query: Natural language search query
        top_k: Number of final results (default: 12)
        mode: Retrieval mode (build/debug/explain/refactor)
        multi_query: Enable query expansion (default: False for speed)
        num_query_variations: Number of query variations
        rerank: Enable VoyageAI reranking (default: True)
        first_stage_k: Candidates per prefetch lane (default: 80)
        rerank_candidates: Candidates to send to reranker (default: 60)
        fusion_method: Fusion strategy - "dbsf" (default) or "rrf"
        score_threshold: Filter results below this score (0 = disabled)
        filters: Payload filters (e.g., {"corpus": "adk_docs"})
        expand_context: Enable context-aware expansion (default: from config, enabled by default)
        expand_top_k: Number of top results to expand (default: from config, 5)
        expand_window: Window size for adjacent chunks (±N, default: from config, 1)
        verbose: Print debug info

    Returns:
        Evidence pack with results, coverage, timings, and warnings
    """
    start_time = time.time()
    timings = {}
    warnings = []

    settings = get_settings()

    # Load defaults from config for parameters not explicitly provided
    top_k = top_k if top_k is not None else settings.retrieval_defaults.top_k
    first_stage_k = (
        first_stage_k if first_stage_k is not None else settings.retrieval_defaults.first_stage_k
    )
    rerank_candidates = (
        rerank_candidates
        if rerank_candidates is not None
        else settings.retrieval_defaults.rerank_candidates
    )
    fusion_method = (
        fusion_method if fusion_method is not None else settings.retrieval_defaults.fusion_method
    )
    score_threshold = (
        score_threshold
        if score_threshold is not None
        else settings.retrieval_defaults.score_threshold
    )

    # Map fusion method string to Fusion enum
    fusion_map = {
        "dbsf": models.Fusion.DBSF,
        "rrf": models.Fusion.RRF,
    }
    fusion_enum = fusion_map.get(fusion_method.lower(), models.Fusion.DBSF)
    if fusion_method.lower() not in fusion_map:
        warnings.append(f"Unknown fusion method '{fusion_method}', defaulting to DBSF")

    # Get cached clients (or initialize if not cached)
    clients = _get_clients()
    qdrant = clients["qdrant"]
    voyage = clients["voyage"]
    sparse_model = clients["sparse_model"]

    # Stage 1: Multi-query expansion (optional)
    t0 = time.time()
    if multi_query:
        query_variations = generate_query_variations(query, num_query_variations)
        if verbose:
            print(f"\n[1/6] Query Expansion: {len(query_variations)} variations")
            for i, q in enumerate(query_variations):
                print(f"      {i + 1}. {q}")
    else:
        query_variations = [query]
        if verbose:
            print(f"\n[1/6] Query Expansion: disabled (single query)")
    timings["query_expansion"] = time.time() - t0

    # Build filter if provided
    query_filter = None
    if filters:
        conditions = []
        for key, value in filters.items():
            if isinstance(value, dict):
                if any(k in value for k in ["gte", "lte", "gt", "lt"]):
                    conditions.append(
                        models.FieldCondition(
                            key=key,
                            range=models.Range(
                                gte=value.get("gte"),
                                lte=value.get("lte"),
                                gt=value.get("gt"),
                                lt=value.get("lt"),
                            ),
                        )
                    )
            elif isinstance(value, list):
                # Multi-value filter (e.g., corpus in ["adk_docs", "adk_python"])
                conditions.append(
                    models.FieldCondition(key=key, match=models.MatchAny(any=value))
                )
            else:
                conditions.append(
                    models.FieldCondition(key=key, match=models.MatchValue(value=value))
                )
        if conditions:
            query_filter = models.Filter(must=conditions)

    # Stage 2: Hybrid search for each query variation
    t0 = time.time()
    all_results = []

    for i, query_var in enumerate(query_variations):
        t_embed = time.time()
        q_dense_docs = embed_query_dense_docs(query_var, voyage, settings)
        q_dense_code = embed_query_dense_code(query_var, voyage, settings)

        # Try sparse embedding with fallback
        q_sparse = None
        try:
            q_sparse = embed_query_sparse(query_var, sparse_model)
        except Exception as e:
            if i == 0:  # Only warn once
                warnings.append(f"sparse_unavailable: {str(e)}")
            # Continue without sparse - will only use dense vectors

        if i == 0:
            timings["embedding"] = time.time() - t_embed

        # Build prefetch list - conditionally include sparse
        prefetch_list = [
            models.Prefetch(
                query=q_dense_docs,
                using=settings.vectors.dense_docs,
                limit=first_stage_k,
                filter=query_filter,
            ),
            models.Prefetch(
                query=q_dense_code,
                using=settings.vectors.dense_code,
                limit=first_stage_k,
                filter=query_filter,
            ),
        ]

        if q_sparse is not None:
            prefetch_list.append(
                models.Prefetch(
                    query=q_sparse,
                    using=settings.vectors.sparse_lexical,
                    limit=first_stage_k + 20,
                    filter=query_filter,
                )
            )

        # Hybrid search with configurable fusion - use query_points_groups for deduplication
        search_result = qdrant.query_points_groups(
            collection_name=settings.qdrant.collection,
            prefetch=prefetch_list,
            query=models.FusionQuery(fusion=fusion_enum),
            group_by="path",  # One best chunk per source file
            group_size=1,  # Only the best chunk per file
            limit=first_stage_k * 2,  # Get more candidate groups
            with_payload=True,
            score_threshold=score_threshold if score_threshold > 0 else None,
        )

        # Process grouped results - extract best hit from each group
        results = []
        for group in search_result.groups:
            for hit in group.hits:
                results.append(
                    {
                        "id": hit.id,
                        "text": hit.payload.get("text", ""),
                        "corpus": hit.payload.get("corpus", ""),
                        "kind": hit.payload.get("kind", ""),
                        "repo": hit.payload.get("repo", ""),
                        "path": hit.payload.get("path", ""),
                        "commit": hit.payload.get("commit", ""),
                        "chunk_id": hit.payload.get("chunk_id", ""),
                        "chunk_index": hit.payload.get("chunk_index"),
                        "start_line": hit.payload.get("start_line"),
                        "end_line": hit.payload.get("end_line"),
                        "score": hit.score,
                        "reranked": False,
                    }
                )

        all_results.append(results)

        if verbose:
            doc_count = sum(1 for r in results if r.get("kind") == "doc")
            code_count = sum(1 for r in results if r.get("kind") == "code")
            print(
                f"\n[2/6] Hybrid Search: Query {i + 1}/{len(query_variations)} → {len(results)} results (docs={doc_count}, code={code_count})"
            )

    timings["search"] = time.time() - t0 - timings.get("embedding", 0)

    # Stage 2b: Fuse results from multiple queries (if multi-query enabled)
    if multi_query and len(all_results) > 1:
        candidates = reciprocal_rank_fusion(all_results)
        if verbose:
            print(f"\n[2b/6] RRF Fusion: {len(candidates)} unique candidates")
    else:
        candidates = all_results[0] if all_results else []

    # Stage 3: Balance candidate pool BEFORE reranking
    t0 = time.time()
    if len(candidates) > rerank_candidates:
        balanced_candidates = balance_candidate_pool(candidates, rerank_candidates)
        if verbose:
            doc_count = sum(1 for c in balanced_candidates if c.get("kind") == "doc")
            code_count = sum(1 for c in balanced_candidates if c.get("kind") == "code")
            print(
                f"\n[3/6] Candidate Balancing: {len(balanced_candidates)} candidates (docs={doc_count}, code={code_count})"
            )
    else:
        balanced_candidates = candidates
        if verbose:
            print(
                f"\n[3/6] Candidate Balancing: skipped ({len(candidates)} < {rerank_candidates})"
            )
    timings["balancing"] = time.time() - t0

    # Stage 4: VoyageAI reranking with large candidate pool
    t0 = time.time()
    if rerank and len(balanced_candidates) > 0:
        try:
            documents = []
            for c in balanced_candidates:
                doc_str = f"SOURCE: {c['corpus']} | PATH: {c['path']}\n\n{c['text']}"
                documents.append(doc_str)

            intent_map = {
                "build": "Rank for correct implementation patterns and code examples",
                "debug": "Rank for debugging and error resolution",
                "explain": "Rank for explaining concepts and documentation",
                "refactor": "Rank for best practices and refactoring",
            }
            rerank_query = f"{intent_map.get(mode, intent_map['build'])}. QUERY: {query}"

            reranking = voyage.rerank(
                query=rerank_query,
                documents=documents,
                model=settings.voyage.rerank_model,
                top_k=min(
                    len(documents), rerank_candidates
                ),  # Rerank all balanced candidates
            )

            reranked_candidates = []
            for result in reranking.results:
                original = balanced_candidates[result.index].copy()
                original["rerank_score"] = result.relevance_score
                original["reranked"] = True
                reranked_candidates.append(original)

            candidates = reranked_candidates

            if verbose:
                print(f"\n[4/6] Reranking: {len(candidates)} candidates reranked")

        except Exception as e:
            warnings.append(f"rerank_unavailable: {str(e)}")
            candidates = balanced_candidates  # Use pre-rerank ordering
            if verbose:
                print(f"\n[4/6] Reranking: failed ({str(e)}), using fusion ordering")

    timings["reranking"] = time.time() - t0

    # Stage 4b: Context expansion (enabled by default)
    # Load config first to check if enabled
    ctx_config = settings.retrieval_defaults.context_expansion
    expand_context_enabled = (
        expand_context if expand_context is not None else ctx_config.enabled
    )

    if expand_context_enabled and len(candidates) > 0:
        t0 = time.time()

        # Load other config values
        expand_top_k_val = (
            expand_top_k if expand_top_k is not None else ctx_config.expand_top_k
        )
        expand_window_val = (
            expand_window if expand_window is not None else ctx_config.window_size
        )

        expanded_candidates, expansion_warnings = expand_context_around_chunks(
            candidates=candidates,
            qdrant=qdrant,
            collection_name=settings.qdrant.collection,
            expand_top_k=expand_top_k_val,
            window_size=expand_window_val,
            score_decay_factor=ctx_config.score_decay_factor,
            max_expanded_chunks=ctx_config.max_expanded_chunks,
            verbose=verbose,
        )

        warnings.extend(expansion_warnings)
        original_count = len(candidates)
        candidates = expanded_candidates
        timings["context_expansion"] = time.time() - t0

        if verbose:
            expanded_count = len(candidates) - original_count
            print(f"\n[4b/6] Context Expansion: +{expanded_count} adjacent chunks")

    # Stage 5: Coverage gates for final selection
    t0 = time.time()
    final_results, gate_warnings = apply_coverage_gates(candidates, top_k)
    warnings.extend(gate_warnings)
    timings["coverage_gates"] = time.time() - t0

    if verbose:
        doc_count = sum(1 for r in final_results if r.get("kind") == "doc")
        code_count = sum(1 for r in final_results if r.get("kind") == "code")
        print(
            f"\n[5/6] Coverage Gates: {len(final_results)} final results (docs={doc_count}, code={code_count})"
        )

    timings["total"] = time.time() - start_time

    # Dynamic coverage tracking across all corpora
    coverage = {}
    for corpus_name in ALL_CORPORA:
        count = sum(1 for r in final_results if r.get("corpus") == corpus_name)
        if count > 0:
            coverage[corpus_name] = count

    return {
        "query": query,
        "mode": mode,
        "query_variations": query_variations if multi_query else None,
        "results": final_results,
        "count": len(final_results),
        "coverage": coverage,
        "pipeline": {
            "multi_query": multi_query,
            "hybrid_search": True,
            "balanced_pool": True,
            "reranked": rerank,
        },
        "timings": timings,
        "warnings": warnings,
    }


def main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Optimal RAG query with multi-stage retrieval")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--top-k", type=int, default=12, help="Number of results")
    parser.add_argument(
        "--mode", choices=["build", "debug", "explain", "refactor"], default="build"
    )
    parser.add_argument(
        "--multi-query", action="store_true", help="Enable multi-query expansion"
    )
    parser.add_argument("--no-rerank", action="store_true", help="Disable reranking")
    parser.add_argument(
        "--first-stage-k", type=int, default=80, help="Candidates per prefetch lane"
    )
    parser.add_argument(
        "--rerank-candidates", type=int, default=60, help="Candidates to reranker"
    )
    parser.add_argument(
        "--fusion",
        choices=["dbsf", "rrf"],
        default="dbsf",
        help="Fusion method: dbsf (Distribution-Based Score Fusion) or rrf (Reciprocal Rank Fusion)",
    )
    parser.add_argument(
        "--score-threshold",
        type=float,
        default=0.0,
        help="Filter results below this score (0 = disabled)",
    )
    parser.add_argument(
        "--corpus",
        action="append",
        choices=ALL_CORPORA,
        help="Filter by corpus (can specify multiple: --corpus adk_docs --corpus adk_python)",
    )
    parser.add_argument(
        "--sdk",
        choices=list(CORPUS_GROUPS.keys()),
        help="Filter by SDK group: adk, openai, or general",
    )
    parser.add_argument(
        "--expand-context",
        action="store_true",
        help="Enable context-aware expansion (fetch adjacent chunks)",
    )
    parser.add_argument(
        "--expand-top-k",
        type=int,
        default=None,
        help="Number of top results to expand (default: from config)",
    )
    parser.add_argument(
        "--expand-window",
        type=int,
        default=None,
        help="Window size for adjacent chunks (±N, default: from config)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Build corpus filter from --sdk or --corpus
    filters = {}
    if args.sdk:
        filters["corpus"] = CORPUS_GROUPS[args.sdk]
    elif args.corpus:
        if len(args.corpus) == 1:
            filters["corpus"] = args.corpus[0]
        else:
            filters["corpus"] = args.corpus

    # Handle expand_context: if flag not provided, pass None to use config default
    # store_true gives False when not provided, but we want None for config fallback
    expand_context_arg = args.expand_context if "--expand-context" in sys.argv else None

    results = search(
        query=args.query,
        top_k=args.top_k,
        mode=args.mode,
        multi_query=args.multi_query,
        rerank=not args.no_rerank,
        first_stage_k=args.first_stage_k,
        rerank_candidates=args.rerank_candidates,
        fusion_method=args.fusion,
        score_threshold=args.score_threshold,
        filters=filters if filters else None,
        expand_context=expand_context_arg,
        expand_top_k=args.expand_top_k,
        expand_window=args.expand_window,
        verbose=args.verbose,
    )

    print(f"\n{'=' * 80}")
    print("RAG RETRIEVAL RESULTS")
    print(f"{'=' * 80}")
    print(f"\nQuery: {results['query']}")
    print(f"Mode: {results['mode']}")
    print(
        f"Pipeline: Multi-query={results['pipeline']['multi_query']}, "
        f"Balanced={results['pipeline']['balanced_pool']}, "
        f"Reranked={results['pipeline']['reranked']}"
    )
    print(f"Results: {results['count']}")
    # Display coverage for all corpora that have results
    coverage_parts = [f"{k}={v}" for k, v in results["coverage"].items()]
    print(f"Coverage: {', '.join(coverage_parts) if coverage_parts else 'none'}")

    if results["warnings"]:
        print(f"Warnings: {results['warnings']}")

    print(f"\nTimings:")
    for stage, duration in results["timings"].items():
        print(f"  {stage}: {duration:.3f}s")

    print(f"\n{'-' * 80}\n")

    for i, result in enumerate(results["results"], 1):
        score = result.get(
            "rerank_score", result.get("rrf_score", result.get("score", 0))
        )
        print(f"[{i}] Score: {score:.4f} | {result['corpus']} | {result['kind']}")
        if result.get("rrf_score") and result.get("reranked"):
            print(f"    RRF Score: {result['rrf_score']:.4f}")
        print(f"    Path: {result['path']}")
        if result.get("start_line"):
            print(f"    Lines: {result['start_line']}-{result['end_line']}")
        print(f"    Text: {result['text'][:200]}...")
        print()


if __name__ == "__main__":
    main()
