"""
Chunk data contract aligned with Qdrant payload schema per spec §4.1.

Defines the canonical payload schema for chunks stored in Qdrant.
This model is used during ingestion and when reading chunks back.

Related files:
- src/grounding/contracts/ids.py - ID generation functions
- src/grounding/contracts/document.py - Parent document model
- docs/spec/qdrant_schema_and_config.md - Schema specification
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


SourceCorpus = Literal["adk_docs", "adk_python"]
ContentKind = Literal["code", "doc"]


class Chunk(BaseModel):
    """
    Canonical chunk payload for Qdrant storage.
    
    All fields match spec §4.1 - Payload Schema requirements.
    Field names are aligned with Qdrant payload indexes.
    """
    
    # Identity & provenance (spec §4.1)
    chunk_id: str = Field(
        description="Stable unique ID (SHA-1 based) - also used as Qdrant point ID"
    )
    corpus: SourceCorpus = Field(
        description="Which corpus: adk_docs | adk_python"
    )
    repo: str = Field(
        description="Repository identifier, e.g. 'google/adk-docs'"
    )
    commit: str = Field(
        description="Git commit SHA at time of ingestion"
    )
    ref: str = Field(
        default="main",
        description="Git branch/tag (optional but recommended)"
    )
    
    # Location (spec §4.1)
    path: str = Field(
        description="Repo-relative file path"
    )
    symbol: str | None = Field(
        default=None,
        description="Optional symbol name for code (class.method or function)"
    )
    
    # Chunk boundaries (spec §4.1)
    chunk_index: int = Field(
        ge=0,
        description="0-based index of this chunk within the file"
    )
    start_line: int | None = Field(
        default=None,
        description="Start line number (1-indexed), nullable for docs"
    )
    end_line: int | None = Field(
        default=None,
        description="End line number (1-indexed), nullable for docs"
    )
    
    # Content (spec §4.1)
    text: str = Field(
        description="The chunk text used for embedding + rerank candidates"
    )
    text_hash: str = Field(
        description="SHA-256 hash of normalized text (for dedupe/change detection)"
    )
    
    # Type flags (spec §4.1)
    kind: ContentKind = Field(
        description="Content type: code | doc"
    )
    lang: str = Field(
        description="Language: py | md | rst | toml | etc."
    )
    
    # Timestamps (spec §4.1)
    ingested_at: str = Field(
        description="ISO8601 timestamp of ingestion"
    )
    
    # Optional metadata (not indexed but stored)
    title: str | None = Field(
        default=None,
        description="Extracted title from headings/docstring"
    )
    
    def to_qdrant_payload(self) -> dict:
        """
        Convert to Qdrant-compatible payload dict.
        
        Excludes None values for cleaner storage.
        
        Returns:
            Dictionary suitable for Qdrant point payload
        """
        return self.model_dump(exclude_none=True)
    
    @classmethod
    def get_indexed_fields(cls) -> dict[str, str]:
        """
        Return fields that should be indexed in Qdrant.
        
        Returns:
            Dict mapping field_name -> index_type (keyword/integer/datetime)
        """
        return {
            # Keyword indexes
            "corpus": "keyword",
            "repo": "keyword",
            "commit": "keyword",
            "ref": "keyword",
            "path": "keyword",
            "kind": "keyword",
            "lang": "keyword",
            "symbol": "keyword",
            "text_hash": "keyword",
            # Integer indexes
            "chunk_index": "integer",
            "start_line": "integer",
            "end_line": "integer",
            # Datetime indexes
            "ingested_at": "datetime",
        }
