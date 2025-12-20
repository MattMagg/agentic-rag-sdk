"""
Chunk data contract per spec §8.1.

Defines the canonical payload schema for chunks stored in Qdrant.
This model is used during ingestion and when reading chunks back.

Related files:
- src/grounding/contracts/ids.py - ID generation functions
- src/grounding/contracts/document.py - Parent document model
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SourceCorpus = Literal["adk_docs", "adk_python"]


class Chunk(BaseModel):
    """
    Canonical chunk payload for Qdrant storage.
    
    All fields from spec §8.1 are represented here.
    """
    
    # Core identifiers
    chunk_id: str = Field(
        description="Globally unique chunk ID (SHA-1 based)"
    )
    parent_doc_id: str = Field(
        description="ID of the parent document this chunk belongs to"
    )
    
    # Source tracking
    source_corpus: SourceCorpus = Field(
        description="Which corpus this chunk comes from"
    )
    repo: str = Field(
        description="Repository identifier, e.g. 'google/adk-docs'"
    )
    ref: str = Field(
        description="Git ref (branch/tag), e.g. 'main'"
    )
    commit: str = Field(
        description="Git commit SHA at time of ingestion"
    )
    path: str = Field(
        description="File path within the repository"
    )
    
    # Content metadata
    language: str | None = Field(
        default=None,
        description="Programming language if applicable (e.g., 'python', 'markdown')"
    )
    content_type: str = Field(
        description="MIME type, e.g. 'text/markdown', 'text/x-python'"
    )
    
    # Chunk position
    chunk_index: int = Field(
        ge=0,
        description="0-based index of this chunk within the document"
    )
    chunk_text: str = Field(
        description="The actual text content of this chunk"
    )
    chunk_char_start: int = Field(
        ge=0,
        description="Character offset where this chunk starts in the source file"
    )
    chunk_char_end: int = Field(
        ge=0,
        description="Character offset where this chunk ends in the source file"
    )
    
    # Optional metadata
    title_hint: str | None = Field(
        default=None,
        description="Extracted title from headings, filename, or docstring"
    )
    created_at: str = Field(
        description="ISO 8601 timestamp when this chunk was created"
    )
    hash: str = Field(
        description="SHA-256 hash of normalized chunk_text"
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Flexible additional metadata"
    )
    
    def to_qdrant_payload(self) -> dict:
        """
        Convert to Qdrant-compatible payload dict.
        
        Returns:
            Dictionary suitable for Qdrant point payload
        """
        return self.model_dump(exclude_none=True)
