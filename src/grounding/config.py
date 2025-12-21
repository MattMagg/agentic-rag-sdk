"""
Configuration loader for the grounding system.

Loads environment variables from .env and parses config/settings.yaml
with environment variable substitution.

Usage:
    from src.grounding.config import get_settings
    settings = get_settings()
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


# Project root is 2 levels up from this file
PROJECT_ROOT = Path(__file__).parent.parent.parent


def _substitute_env_vars(value: Any) -> Any:
    """Recursively substitute ${VAR} patterns with environment variables."""
    if isinstance(value, str):
        # Pattern: ${VAR_NAME}
        pattern = re.compile(r"\$\{([^}]+)\}")
        
        def replacer(match: re.Match) -> str:
            var_name = match.group(1)
            env_value = os.getenv(var_name, "")
            return env_value
        
        return pattern.sub(replacer, value)
    elif isinstance(value, dict):
        return {k: _substitute_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [_substitute_env_vars(item) for item in value]
    return value


class QdrantConfig(BaseModel):
    """Qdrant connection configuration."""
    url: str = Field(description="Qdrant Cloud URL")
    api_key: str = Field(description="Qdrant API key")
    collection: str = Field(description="Collection name")


class VoyageConfig(BaseModel):
    """Voyage AI configuration."""
    api_key: str = Field(description="Voyage API key")
    docs_model: str = Field(default="voyage-context-3", description="Model for docs embeddings")
    code_model: str = Field(default="voyage-code-3", description="Model for code embeddings")
    output_dimension: int = Field(default=2048, description="Embedding dimension")
    output_dtype: str = Field(default="float", description="Embedding data type")
    rerank_model: str = Field(default="rerank-2.5", description="Reranker model")


class VectorConfig(BaseModel):
    """Vector space names."""
    dense_docs: str = Field(default="dense_docs")
    dense_code: str = Field(default="dense_code")
    sparse_lexical: str = Field(default="sparse_lexical")


class RetrievalConfig(BaseModel):
    """Retrieval defaults."""
    fusion: str = Field(default="rrf")
    prefetch_limit_dense: int = Field(default=60)
    prefetch_limit_sparse: int = Field(default=80)
    final_limit: int = Field(default=30)
    rerank_top_k: int = Field(default=12)


class CorpusConfig(BaseModel):
    """Configuration for a single corpus."""
    root: str = Field(description="Path to corpus root directory")
    corpus: str = Field(description="Corpus identifier (adk_docs or adk_python)")
    repo: str = Field(description="Repository name (e.g., google/adk-docs)")
    kind: str = Field(description="Content kind: doc or code")
    ref: str = Field(default="main", description="Git ref (branch/tag)")
    include_globs: list[str] = Field(default_factory=list, description="Include patterns")
    exclude_globs: list[str] = Field(default_factory=list, description="Exclude patterns")
    allowed_exts: list[str] = Field(default_factory=list, description="Allowed extensions")
    max_file_bytes: int = Field(default=500_000, description="Max file size")


class IngestionConfig(BaseModel):
    """Ingestion pipeline configuration."""
    batch_size: int = Field(default=50, description="Points per Qdrant upsert batch")
    corpora: dict[str, CorpusConfig] = Field(default_factory=dict, description="Corpus configs")


class Settings(BaseModel):
    """Root settings model."""
    qdrant: QdrantConfig
    voyage: VoyageConfig
    vectors: VectorConfig = Field(default_factory=VectorConfig)
    retrieval_defaults: RetrievalConfig = Field(default_factory=RetrievalConfig)
    ingestion: IngestionConfig = Field(default_factory=IngestionConfig)


def load_yaml_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load and parse settings.yaml with environment variable substitution."""
    if config_path is None:
        config_path = PROJECT_ROOT / "config" / "settings.yaml"
    
    with open(config_path) as f:
        raw_config = yaml.safe_load(f)
    
    return _substitute_env_vars(raw_config)


@lru_cache(maxsize=1)
def get_settings(env_file: Path | None = None, config_file: Path | None = None) -> Settings:
    """
    Load and return the application settings.
    
    This function is cached - subsequent calls return the same settings instance.
    
    Args:
        env_file: Optional path to .env file. Defaults to PROJECT_ROOT/.env
        config_file: Optional path to settings.yaml. Defaults to PROJECT_ROOT/config/settings.yaml
    
    Returns:
        Validated Settings instance
    """
    # Load .env
    if env_file is None:
        env_file = PROJECT_ROOT / ".env"
    load_dotenv(env_file)
    
    # Load and parse YAML config
    config_dict = load_yaml_config(config_file)
    
    # Convert string values that should be ints
    if "retrieval_defaults" in config_dict:
        rd = config_dict["retrieval_defaults"]
        for key in ["prefetch_limit_dense", "prefetch_limit_sparse", "final_limit", "rerank_top_k"]:
            if key in rd and isinstance(rd[key], str):
                rd[key] = int(rd[key])
    
    return Settings(**config_dict)


def get_settings_redacted() -> dict[str, Any]:
    """
    Return settings as a dictionary with sensitive values redacted.
    
    Useful for logging and debugging without exposing secrets.
    """
    settings = get_settings()
    config_dict = settings.model_dump()
    
    # Redact sensitive fields
    if "qdrant" in config_dict:
        config_dict["qdrant"]["api_key"] = "***REDACTED***"
    if "voyage" in config_dict:
        config_dict["voyage"]["api_key"] = "***REDACTED***"
    
    return config_dict
