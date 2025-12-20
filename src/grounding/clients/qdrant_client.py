"""
Qdrant Cloud client wrapper per spec §7.1.

Thin wrapper around qdrant-client that reads config and provides
the minimal interface needed for this grounding system.

Related files:
- src/grounding/config.py - Configuration loading
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from qdrant_client import QdrantClient as _QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

if TYPE_CHECKING:
    from qdrant_client.http.models import CollectionInfo

from src.grounding.config import get_settings


class QdrantClientWrapper:
    """
    Wrapper for Qdrant Cloud connection.
    
    Provides a minimal interface for healthcheck and collection operations.
    The underlying QdrantClient is initialized with credentials from config.
    """
    
    def __init__(self) -> None:
        """Initialize client with config from settings.yaml."""
        settings = get_settings()
        self._client = _QdrantClient(
            url=settings.qdrant.url,
            api_key=settings.qdrant.api_key,
        )
        self._collection_name = settings.qdrant.collection
    
    @property
    def client(self) -> _QdrantClient:
        """Access the underlying QdrantClient instance."""
        return self._client
    
    @property
    def collection_name(self) -> str:
        """Get the configured collection name."""
        return self._collection_name
    
    def healthcheck(self) -> bool:
        """
        Verify connection to Qdrant Cloud.
        
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            # get_collections() will fail if not connected
            self._client.get_collections()
            return True
        except Exception:
            return False
    
    def list_collections(self) -> list[str]:
        """
        List all collection names.
        
        Returns:
            List of collection name strings
        """
        response = self._client.get_collections()
        return [c.name for c in response.collections]
    
    def collection_exists(self, name: str) -> bool:
        """
        Check if a collection exists.
        
        Args:
            name: Collection name to check
            
        Returns:
            True if collection exists
        """
        return self._client.collection_exists(name)
    
    def get_collection_info(self, name: str) -> "CollectionInfo | None":
        """
        Get detailed info about a collection.
        
        Args:
            name: Collection name
            
        Returns:
            CollectionInfo if exists, None otherwise
        """
        try:
            return self._client.get_collection(name)
        except UnexpectedResponse:
            return None


@lru_cache(maxsize=1)
def get_qdrant_client() -> QdrantClientWrapper:
    """
    Get a cached Qdrant client instance.
    
    Returns:
        Singleton QdrantClientWrapper
    """
    return QdrantClientWrapper()
