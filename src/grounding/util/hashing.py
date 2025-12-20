"""
Hashing utilities for deterministic ID generation.

Provides SHA-1 (for IDs) and SHA-256 (for content hashing) functions.

Related files:
- src/grounding/contracts/ids.py - Uses these functions for ID generation
"""

from __future__ import annotations

import hashlib


def sha1_hex(data: str) -> str:
    """
    Compute SHA-1 hash of a string and return as hex digest.
    
    Used for generating stable IDs (parent_doc_id, chunk_id).
    
    Args:
        data: String to hash
        
    Returns:
        40-character hexadecimal SHA-1 digest
    """
    return hashlib.sha1(data.encode("utf-8")).hexdigest()


def sha256_hex(data: str) -> str:
    """
    Compute SHA-256 hash of a string and return as hex digest.
    
    Used for content hashing to detect changes.
    
    Args:
        data: String to hash
        
    Returns:
        64-character hexadecimal SHA-256 digest
    """
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def normalize_text(text: str) -> str:
    """
    Normalize text before hashing for consistent comparison.
    
    Strips leading/trailing whitespace and normalizes line endings.
    
    Args:
        text: Raw text to normalize
        
    Returns:
        Normalized text suitable for hashing
    """
    return text.strip().replace("\r\n", "\n")
