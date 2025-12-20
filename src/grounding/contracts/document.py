"""
Document data contract.

Defines the model for source documents before chunking.
Used to track document-level metadata during ingestion.

Related files:
- src/grounding/contracts/chunk.py - Chunks derived from documents
- src/grounding/contracts/ids.py - ID generation
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SourceCorpus = Literal["adk_docs", "adk_python"]


class Document(BaseModel):
    """
    Source document metadata before chunking.
    
    Represents a single file from the corpus that will be chunked
    and embedded.
    """
    
    # Identity
    doc_id: str = Field(
        description="Stable document ID (SHA-1 of corpus:commit:path)"
    )
    
    # Source tracking
    corpus: SourceCorpus = Field(
        description="Which corpus this document belongs to"
    )
    repo: str = Field(
        description="Repository identifier, e.g. 'google/adk-docs'"
    )
    ref: str = Field(
        description="Git ref (branch/tag)"
    )
    commit: str = Field(
        description="Git commit SHA"
    )
    path: str = Field(
        description="File path within repository"
    )
    
    # File metadata
    content_type: str = Field(
        description="MIME type of the file"
    )
    size_bytes: int = Field(
        ge=0,
        description="File size in bytes"
    )
    last_modified: str | None = Field(
        default=None,
        description="Last modified timestamp if available"
    )
    
    # Content
    content: str = Field(
        description="Raw file content"
    )
