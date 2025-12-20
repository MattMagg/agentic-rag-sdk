"""
Grounding package for RAG pipeline.

Provides:
- Configuration loading via get_settings()
- Qdrant Cloud client via get_qdrant_client()
- Voyage AI client via get_voyage_client()
- Data contracts for chunks and documents
"""

from src.grounding.config import get_settings, get_settings_redacted

__all__ = [
    "get_settings",
    "get_settings_redacted",
]
