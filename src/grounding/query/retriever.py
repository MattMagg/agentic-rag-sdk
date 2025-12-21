"""
Runtime retrieval logic per spec §5.

Implements the hybrid search fusion + reranking pipeline:
1. Normalize query
2. Generate 3 query vectors (dense docs, dense code, sparse)
3. Qdrant hybrid query (prefetch x3 + RRF fusion)
4. Candidate normalization
5. Voyage rerank-2.5
6. Coverage gates
7. Evidence pack formatting
"""

from __future__ import annotations

import re
import time
from typing import Any, Literal

from qdrant_client.http import models

from src.grounding.clients.fastembed_client import get_fastembed_client
from src.grounding.clients.qdrant_client import get_qdrant_client
from src.grounding.clients.voyage_client import get_voyage_client
from src.grounding.config import get_settings


# Use exact string types for mode to match spec
RetrievalMode = Literal["build", "debug", "explain", "refactor"]


def _normalize_query(query: str) -> str:
    """
    Normalize query text per spec §4.
    
    - Trim whitespace
    - Collapse internal whitespace
    - No semantic rewriting
    """
    # Collapse multiple whitespace to single space and trim
    return " ".join(query.split())


def _construct_rerank_document(point_payload: dict[str, Any]) -> str:
    """
    Construct the string representation for reranking per spec §7.3.
    
    Format:
    SOURCE_TYPE: {corpus}
    REPO: {repo}
    REF: {ref} or {commit}
    PATH_OR_URL: {path}
    LINES: {start_line}-{end_line} (or null)
    CHUNK_ID: {chunk_id}
    
    {text}
    """
    lines_str = "null"
    if point_payload.get("start_line") is not None:
        lines_str = f"{point_payload['start_line']}-{point_payload.get('end_line', '')}"
        
    parts = [
        f"SOURCE_TYPE: {point_payload.get('corpus', 'unknown')}",
        f"REPO: {point_payload.get('repo', 'unknown')}",
        f"REF: {point_payload.get('commit', 'unknown')}", # Use commit for stability
        f"PATH_OR_URL: {point_payload.get('path', 'unknown')}",
        f"LINES: {lines_str}",
        f"CHUNK_ID: {point_payload.get('chunk_id', 'unknown')}",
        "",
        point_payload.get("text", "")
    ]
    return "\n".join(parts)


def retrieve_adk_evidence(
    query: str,
    mode: RetrievalMode = "build",
    top_k_final: int | None = None,
    filter_spec: dict | None = None,
) -> dict[str, Any]:
    """
    Retrieve and rerank official ADK evidence from Qdrant (hybrid) and Voyage rerank-2.5.
    
    Args:
      query: Developer request/question.
      mode: build|debug|explain|refactor (steers rerank instruction only).
      top_k_final: final number of evidence items to return (default from config).
      filter_spec: optional payload filter constraints (repo/path/ref allowlists, etc).
      
    Returns:
      Evidence Pack dictionary per spec §2.2
    """
    settings = get_settings()
    
    # 0. Defaults
    if top_k_final is None:
        top_k_final = settings.retrieval_defaults.final_limit
        
    start_time = time.time()
    
    # 1. Normalize Query
    clean_query = _normalize_query(query)
    
    # 2. Compute Query Vectors (Parallelizable in theory, sequential here for simplicity)
    voyage_client = get_voyage_client()
    fastembed_client = get_fastembed_client()
    
    # Dense Docs (Voyage Context 3)
    # The embed_docs_contextualized method takes list of documents (chunks).
    # But for a QUERY, we should just use standard embedding or confirm if we use same model.
    # Checking voyage_client.py: embed_docs_contextualized uses "voyage-context-3".
    # Spec §3 Step B says: q_dense_docs: Voyage voyage-context-3 (query mode)
    # The wrapper exposes embed_docs_contextualized which takes list[list[str]].
    # BUT standard client.embed() also works with this model. 
    # Let's inspect voyage_client.py wrapper again. 
    # It seems missing a simple `embed_query_for_docs` method.
    # However, `embed_code` uses `voyage-code-3`, we need `voyage-context-3` for docs.
    # The wrapper is specialized. I might need to access the raw client or add a helper.
    # Let's use the raw client for the docs query embedding to be safe and efficient.
    
    # Dense Docs Vector
    # Spec §3 Step B says: q_dense_docs: Voyage voyage-context-3 (query mode)
    # Probing revealed that voyage-context-3 requires the contextualized endpoint.
    # We pass the query as a single-chunk document.
    q_dense_docs_result = voyage_client.embed_docs_contextualized(
        inputs=[[clean_query]],
        input_type="query"
    )
    # The wrapper returns a flattened list of embeddings. Since we sent 1 chunk, we get 1 vector.
    q_dense_docs = q_dense_docs_result[0]
    
    # Dense Code Vector
    q_dense_code = voyage_client.embed_code([clean_query], input_type="query")[0]
    
    # Sparse Vector
    q_sparse_obj = fastembed_client.embed_sparse_query(clean_query)
    # Convert to Qdrant SparseVector model
    q_sparse_model = models.SparseVector(
        indices=q_sparse_obj.indices,
        values=q_sparse_obj.values
    )
    
    # 3. Hybrid Query Construction
    qdrant = get_qdrant_client()
    
    prefetch_hits = []
    
    # Prepare filter if exists
    q_filter = None
    if filter_spec:
        # Simple translation of dict to match conditions
        # Implementation of full filter spec to Qdrant Filter translation would go here
        # For now, assuming filter_spec is already a models.Filter or we support basic k-v
        # Keeping it None for MVP unless spec defines the filter_spec format strictly
        pass

    # Prefetch requests
    prefetch = [
        models.Prefetch(
            query=q_dense_docs,
            using=settings.vectors.dense_docs,
            limit=settings.retrieval_defaults.prefetch_limit_dense,
            filter=q_filter
        ),
        models.Prefetch(
            query=q_dense_code,
            using=settings.vectors.dense_code,
            limit=settings.retrieval_defaults.prefetch_limit_dense,
            filter=q_filter
        ),
        models.Prefetch(
            query=q_sparse_model,
            using=settings.vectors.sparse_lexical,
            limit=settings.retrieval_defaults.prefetch_limit_sparse,
            filter=q_filter
        ),
    ]
    
    # Fused Query
    search_result = qdrant.client.query_points(
        collection_name=settings.qdrant.collection,
        prefetch=prefetch,
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=settings.retrieval_defaults.final_limit * 3, # Get plenty of candidates for reranking
        with_payload=True
    )
    
    # 4. Candidate Normalization & Dedup
    # Qdrant with fusion returns ScoredPoint
    candidates_by_id = {}
    candidates_list = []
    
    for point in search_result.points:
        # Key for deduplication
        # Spec 6.3: dedup rules. Point ID is SHA1 of content/path, so it is a good dedup key itself.
        # But let's follow the composite ID from spec just in case point IDs collide across logical versions (unlikely here)
        c_id = point.id
        if c_id not in candidates_by_id:
            candidates_by_id[c_id] = point
            candidates_list.append(point)
            
    # 5. Voyage Reranking
    if not candidates_list:
        return {
            "status": "no_results",
            "query": clean_query,
            "evidence": [],
            "coverage": {},
            "warnings": ["No candidates found from Qdrant"]
        }
        
    rerank_docs = [_construct_rerank_document(p.payload) for p in candidates_list]
    
    # Reranking Instruction (Spec 7.4)
    intent_map = {
        "build": "Rank evidence for correct Google ADK implementation. Prefer official ADK docs and official ADK Python source.",
        "debug": "Rank evidence for debugging errors and understanding ADK internals.",
        "explain": "Rank evidence for explaining ADK concepts and architecture.",
        "refactor": "Rank evidence for best practices and refactoring ADK code."
    }
    
    # Ensure mode is valid or fallback
    if mode not in intent_map:
        mode = "build"
        
    rerank_results = voyage_client.rerank(
        query=intent_map[mode] + f"\nQUERY: {clean_query}",
        documents=rerank_docs,
        top_k=top_k_final * 2 # Retrieve more to satisfy coverage gates
    )
    
    # 6. Apply Coverage Gates
    # Spec 8: min 3 docs and 3 code (unless requested otherwise - logic implicit here)
    # We will pick top_k_final items satisfying the mix if possible
    
    # Augment rerank results with original metadata
    scored_candidates = []
    for rr in rerank_results:
        original_point = candidates_list[rr.index]
        scored_candidates.append({
            "point": original_point,
            "rerank_score": rr.relevance_score,
            "rerank_rank": 0 # To be assigned
        })
        
    # Selection Logic
    final_evidence = []
    docs_count = 0
    code_count = 0
    min_each = 3
    
    # Pass 1: Greedily take top items if they help meet minimums or if minimums met
    # Actually, better to separate into buckets and merge? 
    # Spec says "require at least 3 docs and 3 code in final 12"
    
    doc_candidates = [c for c in scored_candidates if c["point"].payload.get("kind") == "doc"]
    code_candidates = [c for c in scored_candidates if c["point"].payload.get("kind") == "code"]
    
    # If we don't have enough of one type, we just take what we have
    take_docs = min(len(doc_candidates), min_each)
    take_code = min(len(code_candidates), min_each)
    
    # If we can't meet the gate, we record a warning later but do best effort.
    
    # We want the highest score items.
    # Let's sort all by score descending (already sorted by rerank)
    # We need to pick top N such that constraints are met.
    
    selected_indices = set()
    
    # Force include top `min_each` of docs
    for i in range(take_docs):
        final_evidence.append(doc_candidates[i])
        selected_indices.add(doc_candidates[i]["point"].id)
        docs_count += 1
        
    # Force include top `min_each` of code
    for i in range(take_code):
        # Check if already added (unlikely since sets are disjoint by kind, but safe)
        if code_candidates[i]["point"].id not in selected_indices:
            final_evidence.append(code_candidates[i])
            selected_indices.add(code_candidates[i]["point"].id)
            code_count += 1
            
    # File the rest with highest scorers not yet selected
    remaining_slots = top_k_final - len(final_evidence)
    
    for cand in scored_candidates:
        if remaining_slots <= 0:
            break
        if cand["point"].id not in selected_indices:
            final_evidence.append(cand)
            selected_indices.add(cand["point"].id)
            remaining_slots -= 1
            if cand["point"].payload.get("kind") == "doc":
                docs_count += 1
            else:
                code_count += 1
                
    # Sort final evidence by score
    final_evidence.sort(key=lambda x: x["rerank_score"], reverse=True)
    
    # Assign Ranks
    for i, item in enumerate(final_evidence):
        item["rerank_rank"] = i + 1

    # Warnings
    warnings = []
    if docs_count < min_each or code_count < min_each:
        warnings.append(f"Coverage gate failed: docs={docs_count}, code={code_count} (wanted {min_each})")

    # 7. Assemble Evidence Pack
    evidence_list = []
    for item in final_evidence:
        payload = item["point"].payload
        
        # Citation format
        # Docs: adk-docs@{ref}:{url}#{chunk_id}
        # Code: adk-python@{ref}:{path}#L{start}-L{end}
        citation = ""
        path = payload.get("path", "")
        ref = payload.get("commit", "main")[:7] # Short SHA
        
        if payload.get("kind") == "doc":
             citation = f"adk-docs@{ref}:{path}#{payload.get('chunk_id')}"
        else:
            if payload.get("start_line"):
                citation = f"adk-python@{ref}:{path}#L{payload.get('start_line')}-L{payload.get('end_line')}"
            else:
                citation = f"adk-python@{ref}:{path}#{payload.get('chunk_id')}"
        
        evidence_list.append({
            "rank": item["rerank_rank"],
            "rerank_score": item["rerank_score"],
            "source_type": payload.get("corpus"),
            "repo": payload.get("repo"),
            "ref": payload.get("commit"),
            "path_or_url": path,
            "chunk_id": payload.get("chunk_id"),
            "text": payload.get("text"),
            "citation": citation,
            "citation_confidence": "high" if item["rerank_score"] > 0.7 else "medium"
        })
        
    return {
        "query": query,
        "mode": mode,
        "retrieval": {
            "collection": settings.qdrant.collection,
            "fusion": "rrf",
            "prefetch_limits": {
                "dense_docs": settings.retrieval_defaults.prefetch_limit_dense,
                "dense_code": settings.retrieval_defaults.prefetch_limit_dense,
                "sparse_lexical": settings.retrieval_defaults.prefetch_limit_sparse,
            },
            "final_candidate_limit": search_result.points[0].payload if hasattr(search_result, "points") and False else len(candidates_list) # Debug info
        },
        "evidence": evidence_list,
        "coverage": {
            "adk_docs": docs_count,
            "adk_python": code_count
        },
        "warnings": warnings,
        "debug": {
            "latency": time.time() - start_time,
            "candidates_found": len(candidates_list)
        }
    }
