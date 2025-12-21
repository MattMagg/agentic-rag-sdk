"""
FastEmbed client wrapper for SPLADE sparse vector generation.

Provides sparse text embeddings using SPLADE++ model for hybrid search.
The model is lazy-loaded on first use and cached for subsequent calls.

Related files:
- src/grounding/clients/voyage_client.py - Dense embeddings (Voyage)
- docs/spec/qdrant_schema_and_config.md - Sparse vector schema
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastembed import SparseTextEmbedding


# SPLADE++ model - good balance of quality and speed
DEFAULT_MODEL = "prithivida/Splade_PP_en_v1"


@dataclass
class SparseVector:
    """
    Sparse vector representation for Qdrant.
    
    Qdrant expects sparse vectors as (indices, values) pairs.
    """
    indices: list[int]
    values: list[float]
    
    def to_qdrant_format(self) -> dict:
        """
        Convert to Qdrant sparse vector format.
        
        Returns:
            Dict with 'indices' and 'values' keys for Qdrant API
        """
        return {
            "indices": self.indices,
            "values": self.values,
        }


class FastEmbedClient:
    """
    FastEmbed wrapper for SPLADE sparse embeddings.
    
    Uses lazy loading to defer model download until first use.
    The SPLADE++ model provides learned sparse representations
    that combine lexical and semantic matching.
    """
    
    def __init__(self, model_name: str = DEFAULT_MODEL):
        """
        Initialize client with model name.
        
        The model is NOT loaded until first embed call.
        
        Args:
            model_name: SPLADE model to use (default: prithivida/Splade_PP_en_v1)
        """
        self._model_name = model_name
        self._model: "SparseTextEmbedding | None" = None
    
    def _ensure_model(self) -> "SparseTextEmbedding":
        """Lazy load the model on first use."""
        if self._model is None:
            from fastembed import SparseTextEmbedding
            self._model = SparseTextEmbedding(model_name=self._model_name)
        return self._model
    
    def embed_sparse(self, texts: list[str]) -> list[SparseVector]:
        """
        Generate sparse embeddings for texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of SparseVector objects (one per input text)
        """
        if not texts:
            return []
        
        model = self._ensure_model()
        embeddings = list(model.embed(texts))
        
        return [
            SparseVector(
                indices=list(emb.indices),
                values=list(emb.values),
            )
            for emb in embeddings
        ]
    
    def embed_sparse_query(self, query: str) -> SparseVector:
        """
        Generate sparse embedding for a query.
        
        Some SPLADE models have separate query encoding.
        
        Args:
            query: Query string to embed
            
        Returns:
            SparseVector for the query
        """
        model = self._ensure_model()
        
        # Try query_embed if available, fall back to regular embed
        try:
            embeddings = list(model.query_embed([query]))
        except AttributeError:
            embeddings = list(model.embed([query]))
        
        emb = embeddings[0]
        return SparseVector(
            indices=list(emb.indices),
            values=list(emb.values),
        )


@lru_cache(maxsize=1)
def get_fastembed_client() -> FastEmbedClient:
    """
    Get a cached FastEmbed client instance.
    
    Returns:
        Singleton FastEmbedClient
    """
    return FastEmbedClient()
