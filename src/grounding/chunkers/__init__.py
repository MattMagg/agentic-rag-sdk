"""
Chunkers package for content segmentation.

Provides specialized chunkers for different content types:
- MarkdownChunker: Heading-based splitting for documentation
- PythonChunker: AST-based splitting for Python code

Related files:
- src/grounding/scripts/03_ingest_corpus.py - Main consumer
- src/grounding/contracts/chunk.py - Chunk model
"""

from src.grounding.chunkers.markdown import MarkdownChunker, chunk_markdown
from src.grounding.chunkers.python_code import PythonChunker, chunk_python

__all__ = [
    "MarkdownChunker",
    "PythonChunker",
    "chunk_markdown",
    "chunk_python",
]
