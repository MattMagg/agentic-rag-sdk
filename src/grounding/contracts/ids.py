"""
ID generation utilities per spec §8.2.

Generates stable, deterministic IDs for documents and chunks.
IDs change when content changes, enabling safe upserts and deletes.

Related files:
- src/grounding/util/hashing.py - SHA-1 function used here
- src/grounding/contracts/chunk.py - Uses these IDs
"""

from __future__ import annotations

from src.grounding.util.hashing import sha1_hex


def make_parent_doc_id(corpus: str, commit: str, path: str) -> str:
    """
    Generate a stable parent document ID.
    
    Formula: sha1(corpus + ":" + commit + ":" + path)
    
    Args:
        corpus: Corpus name, e.g. "adk_docs" or "adk_python"
        commit: Git commit SHA
        path: File path within the repository
        
    Returns:
        40-character hex string ID
    """
    data = f"{corpus}:{commit}:{path}"
    return sha1_hex(data)


def make_chunk_id(parent_doc_id: str, chunk_index: int, chunk_hash: str) -> str:
    """
    Generate a stable chunk ID.
    
    Formula: sha1(parent_doc_id + ":" + chunk_index + ":" + chunk_hash)
    
    The chunk_hash should be the SHA-256 of the normalized chunk text.
    This ensures IDs change when content changes.
    
    Args:
        parent_doc_id: ID from make_parent_doc_id()
        chunk_index: 0-based index of chunk within document
        chunk_hash: SHA-256 hex digest of chunk content
        
    Returns:
        40-character hex string ID
    """
    data = f"{parent_doc_id}:{chunk_index}:{chunk_hash}"
    return sha1_hex(data)
