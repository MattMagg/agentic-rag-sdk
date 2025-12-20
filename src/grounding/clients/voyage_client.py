"""
Voyage AI client wrapper per spec §7.2.

Provides three embedding/reranking operations:
1. embed_code() - For code using voyage-code-3
2. embed_docs_contextualized() - For docs using voyage-context-3 
3. rerank() - For reranking using rerank-2.5

Related files:
- src/grounding/config.py - Configuration loading
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

import voyageai

from src.grounding.config import get_settings


InputType = Literal["query", "document"]


@dataclass
class RerankResult:
    """Single reranked document result."""
    document: str
    relevance_score: float
    index: int


class VoyageClientWrapper:
    """
    Wrapper for Voyage AI API calls.
    
    Implements the three methods specified in §7.2:
    - embed_code: Code embeddings with voyage-code-3
    - embed_docs_contextualized: Contextualized doc embeddings with voyage-context-3
    - rerank: Reranking with rerank-2.5
    """
    
    def __init__(self) -> None:
        """Initialize client with API key from config."""
        settings = get_settings()
        self._client = voyageai.Client(api_key=settings.voyage.api_key)
        self._code_model = settings.voyage.code_model
        self._docs_model = settings.voyage.docs_model
        self._rerank_model = settings.voyage.rerank_model
        self._output_dimension = settings.voyage.output_dimension
        self._output_dtype = settings.voyage.output_dtype
    
    @property
    def client(self) -> voyageai.Client:
        """Access the underlying Voyage client."""
        return self._client
    
    def embed_code(
        self, 
        texts: list[str], 
        input_type: InputType = "document"
    ) -> list[list[float]]:
        """
        Embed code snippets using voyage-code-3.
        
        Args:
            texts: List of code strings to embed
            input_type: Either "query" or "document"
            
        Returns:
            List of embedding vectors (2048 dimensions each)
        """
        result = self._client.embed(
            texts,
            model=self._code_model,
            input_type=input_type,
            output_dimension=self._output_dimension,
            output_dtype=self._output_dtype,
        )
        return result.embeddings
    
    def embed_docs_contextualized(
        self,
        inputs: list[list[str]],
        input_type: InputType = "document"
    ) -> list[list[float]]:
        """
        Embed documents using voyage-context-3 contextualized embeddings.
        
        The contextualized endpoint takes a list of document chunks where
        each document is a list of strings (the chunks). It returns 
        embeddings that incorporate the full document context.
        
        Args:
            inputs: List of documents, each document is a list of chunk strings
            input_type: Either "query" or "document"
            
        Returns:
            Flattened list of embeddings (one per chunk across all documents)
        """
        result = self._client.contextualized_embed(
            inputs,
            model=self._docs_model,
            input_type=input_type,
            output_dimension=self._output_dimension,
            output_dtype=self._output_dtype,
        )
        # Contextualized embeddings return a ContextualizedEmbeddingsObject
        # with a .results attribute containing document results, each with .embeddings
        # Flatten all embeddings across all documents
        all_embeddings = []
        for doc_result in result.results:
            all_embeddings.extend(doc_result.embeddings)
        return all_embeddings
    
    def rerank(
        self,
        query: str,
        documents: list[str],
        top_k: int | None = None
    ) -> list[RerankResult]:
        """
        Rerank documents against a query using rerank-2.5.
        
        Args:
            query: The search query
            documents: List of documents to rerank
            top_k: Number of top results to return (default: all)
            
        Returns:
            List of RerankResult objects sorted by relevance
        """
        result = self._client.rerank(
            query=query,
            documents=documents,
            model=self._rerank_model,
            top_k=top_k,
        )
        
        return [
            RerankResult(
                document=r.document,
                relevance_score=r.relevance_score,
                index=r.index,
            )
            for r in result.results
        ]


@lru_cache(maxsize=1)
def get_voyage_client() -> VoyageClientWrapper:
    """
    Get a cached Voyage client instance.
    
    Returns:
        Singleton VoyageClientWrapper
    """
    return VoyageClientWrapper()
