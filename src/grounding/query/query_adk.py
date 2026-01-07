#!/usr/bin/env python3
"""
Optimal ADK Grounding Query Script

Multi-Stage Retrieval Pipeline:
1. Multi-Query Expansion (optional, off by default for speed)
   - Generates balanced code/docs query variations
   - 14-20% improvement in retrieval quality

2. Hybrid Search (Dense Docs + Dense Code + Sparse)
   - Dense: semantic understanding via Voyage AI
   - Sparse: keyword/lexical matching via SPLADE
   - RRF fusion built into Qdrant

3. Coverage-Aware Candidate Pool
   - Ensures balanced code/docs mix BEFORE reranking
   - Prevents reranker from seeing only one type

4. VoyageAI Reranking (Cross-encoder)
   - Final refinement with rerank-2.5
   - Large candidate pool (60+) for best results

Usage:
    from src.grounding.query.query_adk import search_adk

    results = search_adk(
        query="how to use tool context",
        top_k=12
    )

Command line:
    python -m src.grounding.query.query_adk "how to use tool context" --top-k 12
    python -m src.grounding.query.query_adk "LoopAgent" --multi-query --verbose
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
    print("ERROR: qdrant-client not installed. Run: pip install qdrant-client", file=sys.stderr)
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

# SDK groupings for convenient filtering
SDK_GROUPS = {
    "adk": ["adk_docs", "adk_python"],
    "openai": ["openai_agents_docs", "openai_agents_python"],
    "general": ["agent_dev_docs"],
}

# All known corpora (for validation)
ALL_CORPORA = [
    "adk_docs", "adk_python", "agent_dev_docs",
    "openai_agents_docs", "openai_agents_python"
]


def generate_query_variations(original_query: str, num_variations: int = 3) -> List[str]:
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


def embed_query_dense_docs(query: str, voyage_client: voyageai.Client, settings) -> List[float]:
    """
    Embed query with voyage-context-3 for document matching.
    
    NOTE: voyage-context-3 requires the contextualized_embed endpoint.
    """
    result = voyage_client.contextualized_embed(
        inputs=[[query]],
        model=settings.voyage.docs_model,
        input_type="query",
        output_dimension=settings.voyage.output_dimension,
        output_dtype=settings.voyage.output_dtype
    )
    return result.results[0].embeddings[0]


def embed_query_dense_code(query: str, voyage_client: voyageai.Client, settings) -> List[float]:
    """Embed query with voyage-code-3 for code matching."""
    result = voyage_client.embed(
        texts=[query],
        model=settings.voyage.code_model,
        input_type="query",
        output_dimension=settings.voyage.output_dimension,
        output_dtype=settings.voyage.output_dtype
    )
    return result.embeddings[0]


def embed_query_sparse(query: str, sparse_model: SparseTextEmbedding) -> models.SparseVector:
    """Embed query with SPLADE (sparse vector)."""
    embeddings = list(sparse_model.query_embed([query]))
    emb = embeddings[0]
    return models.SparseVector(
        indices=list(emb.indices),
        values=list(emb.values)
    )


def reciprocal_rank_fusion(
    results_lists: List[List[Dict]],
    k: int = 60
) -> List[Dict]:
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
    candidates: List[Dict],
    target_size: int,
    min_per_type: int = 10
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
        all_remaining = [c for c in candidates if c["id"] not in {b["id"] for b in balanced}]
        balanced.extend(all_remaining[:remaining])
    
    return balanced


def apply_coverage_gates(
    candidates: List[Dict],
    top_k: int,
    min_docs: int = 3,
    min_code: int = 3
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
    selected.sort(key=lambda x: x.get("rerank_score", x.get("rrf_score", 0)), reverse=True)
    
    # Check coverage
    final_docs = sum(1 for c in selected if c.get("kind") == "doc")
    final_code = sum(1 for c in selected if c.get("kind") == "code")
    
    if final_docs < min_docs or final_code < min_code:
        warnings.append(f"Coverage gate: docs={final_docs}, code={final_code} (wanted {min_docs}/{min_code})")
    
    return selected, warnings


def search_adk(
    query: str,
    top_k: int = 12,
    mode: RetrievalMode = "build",
    multi_query: bool = False,  # Off by default for speed
    num_query_variations: int = 3,
    rerank: bool = True,
    first_stage_k: int = 80,  # Increased from 60
    rerank_candidates: int = 60,  # New: how many to send to reranker
    filters: Optional[Dict[str, Any]] = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Optimal RAG query for ADK grounding with multi-stage retrieval pipeline.

    Pipeline:
    1. Multi-query expansion (optional, off by default)
    2. Hybrid search (dense docs + dense code + sparse with RRF)
    3. Coverage-aware candidate balancing
    4. VoyageAI reranking with large candidate pool
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
        filters: Payload filters (e.g., {"corpus": "adk_docs"})
        verbose: Print debug info

    Returns:
        Evidence pack with results, coverage, timings, and warnings
    """
    start_time = time.time()
    timings = {}
    warnings = []

    settings = get_settings()

    # Initialize clients
    qdrant = QdrantClient(url=settings.qdrant.url, api_key=settings.qdrant.api_key, timeout=120)
    voyage = voyageai.Client(api_key=settings.voyage.api_key)
    sparse_model = SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1")

    # Stage 1: Multi-query expansion (optional)
    t0 = time.time()
    if multi_query:
        query_variations = generate_query_variations(query, num_query_variations)
        if verbose:
            print(f"\n[1/5] Query Expansion: {len(query_variations)} variations")
            for i, q in enumerate(query_variations):
                print(f"      {i+1}. {q}")
    else:
        query_variations = [query]
        if verbose:
            print(f"\n[1/5] Query Expansion: disabled (single query)")
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
                                lt=value.get("lt")
                            )
                        )
                    )
            elif isinstance(value, list):
                # Multi-value filter (e.g., corpus in ["adk_docs", "adk_python"])
                conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchAny(any=value)
                    )
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
        q_sparse = embed_query_sparse(query_var, sparse_model)
        
        if i == 0:
            timings["embedding"] = time.time() - t_embed

        # Hybrid search with RRF fusion - larger candidate pool
        search_result = qdrant.query_points(
            collection_name=settings.qdrant.collection,
            prefetch=[
                models.Prefetch(
                    query=q_dense_docs,
                    using=settings.vectors.dense_docs,
                    limit=first_stage_k,
                    filter=query_filter
                ),
                models.Prefetch(
                    query=q_dense_code,
                    using=settings.vectors.dense_code,
                    limit=first_stage_k,
                    filter=query_filter
                ),
                models.Prefetch(
                    query=q_sparse,
                    using=settings.vectors.sparse_lexical,
                    limit=first_stage_k + 20,
                    filter=query_filter
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=first_stage_k * 2,  # Get more candidates
            with_payload=True
        )

        results = []
        for point in search_result.points:
            results.append({
                "id": point.id,
                "text": point.payload.get("text", ""),
                "corpus": point.payload.get("corpus", ""),
                "kind": point.payload.get("kind", ""),
                "repo": point.payload.get("repo", ""),
                "path": point.payload.get("path", ""),
                "commit": point.payload.get("commit", ""),
                "chunk_id": point.payload.get("chunk_id", ""),
                "start_line": point.payload.get("start_line"),
                "end_line": point.payload.get("end_line"),
                "score": point.score if hasattr(point, 'score') else 0,
                "reranked": False
            })

        all_results.append(results)

        if verbose:
            doc_count = sum(1 for r in results if r.get("kind") == "doc")
            code_count = sum(1 for r in results if r.get("kind") == "code")
            print(f"\n[2/5] Hybrid Search: Query {i+1}/{len(query_variations)} → {len(results)} results (docs={doc_count}, code={code_count})")

    timings["search"] = time.time() - t0 - timings.get("embedding", 0)

    # Stage 2b: Fuse results from multiple queries (if multi-query enabled)
    if multi_query and len(all_results) > 1:
        candidates = reciprocal_rank_fusion(all_results)
        if verbose:
            print(f"\n[2b/5] RRF Fusion: {len(candidates)} unique candidates")
    else:
        candidates = all_results[0] if all_results else []

    # Stage 3: Balance candidate pool BEFORE reranking
    t0 = time.time()
    if len(candidates) > rerank_candidates:
        balanced_candidates = balance_candidate_pool(candidates, rerank_candidates)
        if verbose:
            doc_count = sum(1 for c in balanced_candidates if c.get("kind") == "doc")
            code_count = sum(1 for c in balanced_candidates if c.get("kind") == "code")
            print(f"\n[3/5] Candidate Balancing: {len(balanced_candidates)} candidates (docs={doc_count}, code={code_count})")
    else:
        balanced_candidates = candidates
        if verbose:
            print(f"\n[3/5] Candidate Balancing: skipped ({len(candidates)} < {rerank_candidates})")
    timings["balancing"] = time.time() - t0

    # Stage 4: VoyageAI reranking with large candidate pool
    t0 = time.time()
    if rerank and len(balanced_candidates) > 0:
        documents = []
        for c in balanced_candidates:
            doc_str = f"SOURCE: {c['corpus']} | PATH: {c['path']}\n\n{c['text']}"
            documents.append(doc_str)

        intent_map = {
            "build": "Rank for correct Google ADK implementation patterns",
            "debug": "Rank for debugging and error resolution",
            "explain": "Rank for explaining ADK concepts",
            "refactor": "Rank for best practices and refactoring"
        }
        rerank_query = f"{intent_map.get(mode, intent_map['build'])}. QUERY: {query}"

        reranking = voyage.rerank(
            query=rerank_query,
            documents=documents,
            model=settings.voyage.rerank_model,
            top_k=min(len(documents), rerank_candidates)  # Rerank all balanced candidates
        )

        reranked_candidates = []
        for result in reranking.results:
            original = balanced_candidates[result.index].copy()
            original["rerank_score"] = result.relevance_score
            original["reranked"] = True
            reranked_candidates.append(original)

        candidates = reranked_candidates

        if verbose:
            print(f"\n[4/5] Reranking: {len(candidates)} candidates reranked")

    timings["reranking"] = time.time() - t0

    # Stage 5: Coverage gates for final selection
    t0 = time.time()
    final_results, gate_warnings = apply_coverage_gates(candidates, top_k)
    warnings.extend(gate_warnings)
    timings["coverage_gates"] = time.time() - t0

    if verbose:
        doc_count = sum(1 for r in final_results if r.get("kind") == "doc")
        code_count = sum(1 for r in final_results if r.get("kind") == "code")
        print(f"\n[5/5] Coverage Gates: {len(final_results)} final results (docs={doc_count}, code={code_count})")

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
            "reranked": rerank
        },
        "timings": timings,
        "warnings": warnings
    }


def main():
    """Command-line interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Optimal ADK RAG query")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--top-k", type=int, default=12, help="Number of results")
    parser.add_argument("--mode", choices=["build", "debug", "explain", "refactor"], default="build")
    parser.add_argument("--multi-query", action="store_true", help="Enable multi-query expansion")
    parser.add_argument("--no-rerank", action="store_true", help="Disable reranking")
    parser.add_argument("--first-stage-k", type=int, default=80, help="Candidates per prefetch lane")
    parser.add_argument("--rerank-candidates", type=int, default=60, help="Candidates to reranker")
    parser.add_argument("--corpus", action="append", choices=ALL_CORPORA,
                        help="Filter by corpus (can specify multiple: --corpus adk_docs --corpus adk_python)")
    parser.add_argument("--sdk", choices=list(SDK_GROUPS.keys()),
                        help="Filter by SDK group: adk, openai, or general")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Build corpus filter from --sdk or --corpus
    filters = {}
    if args.sdk:
        filters["corpus"] = SDK_GROUPS[args.sdk]
    elif args.corpus:
        if len(args.corpus) == 1:
            filters["corpus"] = args.corpus[0]
        else:
            filters["corpus"] = args.corpus

    results = search_adk(
        query=args.query,
        top_k=args.top_k,
        mode=args.mode,
        multi_query=args.multi_query,
        rerank=not args.no_rerank,
        first_stage_k=args.first_stage_k,
        rerank_candidates=args.rerank_candidates,
        filters=filters if filters else None,
        verbose=args.verbose
    )

    print(f"\n{'='*80}")
    print("ADK GROUNDING RETRIEVAL RESULTS")
    print(f"{'='*80}")
    print(f"\nQuery: {results['query']}")
    print(f"Mode: {results['mode']}")
    print(f"Pipeline: Multi-query={results['pipeline']['multi_query']}, "
          f"Balanced={results['pipeline']['balanced_pool']}, "
          f"Reranked={results['pipeline']['reranked']}")
    print(f"Results: {results['count']}")
    # Display coverage for all corpora that have results
    coverage_parts = [f"{k}={v}" for k, v in results['coverage'].items()]
    print(f"Coverage: {', '.join(coverage_parts) if coverage_parts else 'none'}")
    
    if results['warnings']:
        print(f"Warnings: {results['warnings']}")

    print(f"\nTimings:")
    for stage, duration in results['timings'].items():
        print(f"  {stage}: {duration:.3f}s")

    print(f"\n{'-'*80}\n")

    for i, result in enumerate(results['results'], 1):
        score = result.get('rerank_score', result.get('rrf_score', result.get('score', 0)))
        print(f"[{i}] Score: {score:.4f} | {result['corpus']} | {result['kind']}")
        if result.get('rrf_score') and result.get('reranked'):
            print(f"    RRF Score: {result['rrf_score']:.4f}")
        print(f"    Path: {result['path']}")
        if result.get('start_line'):
            print(f"    Lines: {result['start_line']}-{result['end_line']}")
        print(f"    Text: {result['text'][:200]}...")
        print()


if __name__ == "__main__":
    main()
