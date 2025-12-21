"""
Python code chunker using AST parsing.

Implements AST-based chunking per spec §6.2:
- Extract functions and classes with docstrings
- Capture symbol names (class.method or function)
- Track line numbers (start_line, end_line)
- Fallback to character-based for unparseable files

Related files:
- src/grounding/contracts/chunk.py - Chunk model
- docs/spec/corpus_embedding_targets.md - Chunking requirements
"""

from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass
class ChunkData:
    """Raw chunk data before becoming a full Chunk model."""
    text: str
    chunk_index: int
    start_line: int | None
    end_line: int | None
    title: str | None
    symbol: str | None = None


class PythonChunker:
    """
    AST-based Python code chunker.
    
    Extracts functions and classes as individual chunks,
    with fallback to size-based chunking for unparseable code.
    """
    
    def __init__(
        self,
        min_chunk_size: int = 200,
        target_chunk_size: int = 3000,
        max_chunk_size: int = 9000,
        include_imports: bool = True,
    ):
        """
        Initialize chunker with size parameters.
        
        Args:
            min_chunk_size: Minimum chars for a chunk
            target_chunk_size: Ideal chunk size
            max_chunk_size: Maximum before forced split
            include_imports: Whether to include module-level imports in first chunk
        """
        self.min_chunk_size = min_chunk_size
        self.target_chunk_size = target_chunk_size
        self.max_chunk_size = max_chunk_size
        self.include_imports = include_imports
    
    def chunk(self, content: str, filename: str = "") -> list[ChunkData]:
        """
        Chunk Python content into logical units.
        
        Args:
            content: Python source code
            filename: Optional filename for error messages
            
        Returns:
            List of ChunkData objects
        """
        if not content.strip():
            return []
        
        try:
            tree = ast.parse(content)
            return self._chunk_ast(content, tree)
        except SyntaxError:
            # Fallback to size-based chunking
            return self._chunk_by_size(content)
    
    def _chunk_ast(self, content: str, tree: ast.Module) -> list[ChunkData]:
        """Chunk using AST analysis."""
        lines = content.split("\n")
        chunks: list[ChunkData] = []
        
        # Extract module docstring and imports as first chunk if present
        module_preamble = self._extract_preamble(tree, lines)
        if module_preamble:
            chunks.append(ChunkData(
                text=module_preamble["text"],
                chunk_index=0,
                start_line=1,
                end_line=module_preamble["end_line"],
                title=module_preamble.get("docstring_summary"),
                symbol=None,
            ))
        
        # Extract classes and functions
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                chunks.extend(self._process_class(node, lines, len(chunks)))
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                chunk = self._extract_function(node, lines, len(chunks), None)
                if chunk:
                    chunks.append(chunk)
        
        # If no semantic chunks found, fall back to size-based
        if not chunks:
            return self._chunk_by_size(content)
        
        return chunks
    
    def _extract_preamble(self, tree: ast.Module, lines: list[str]) -> dict | None:
        """Extract module docstring and imports."""
        preamble_end = 0
        docstring_summary = None
        
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                # Module docstring
                if isinstance(node.value.value, str):
                    docstring_summary = node.value.value.split("\n")[0][:100]
                    preamble_end = max(preamble_end, node.end_lineno or node.lineno)
            elif isinstance(node, ast.Import | ast.ImportFrom):
                preamble_end = max(preamble_end, node.end_lineno or node.lineno)
            elif isinstance(node, ast.Assign):
                # Module-level constants (like __version__)
                preamble_end = max(preamble_end, node.end_lineno or node.lineno)
            else:
                break
        
        if preamble_end == 0:
            return None
        
        preamble_text = "\n".join(lines[:preamble_end])
        if len(preamble_text.strip()) < self.min_chunk_size:
            return None
        
        return {
            "text": preamble_text,
            "end_line": preamble_end,
            "docstring_summary": docstring_summary,
        }
    
    def _process_class(
        self, node: ast.ClassDef, lines: list[str], start_idx: int
    ) -> list[ChunkData]:
        """Process a class definition into chunks."""
        chunks: list[ChunkData] = []
        
        # Get the full class text
        class_start = node.lineno - 1
        class_end = node.end_lineno or node.lineno
        class_text = "\n".join(lines[class_start:class_end])
        
        # If class is small enough, keep as one chunk
        if len(class_text) <= self.max_chunk_size:
            docstring = ast.get_docstring(node)
            chunks.append(ChunkData(
                text=class_text,
                chunk_index=start_idx,
                start_line=node.lineno,
                end_line=class_end,
                title=docstring.split("\n")[0][:100] if docstring else node.name,
                symbol=node.name,
            ))
            return chunks
        
        # Split large class into methods
        # First chunk: class definition + docstring (up to first method)
        class_header_end = class_start
        for child in node.body:
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                class_header_end = child.lineno - 2  # Line before the method
                break
            class_header_end = (child.end_lineno or child.lineno)
        
        header_text = "\n".join(lines[class_start:class_header_end + 1])
        if header_text.strip():
            chunks.append(ChunkData(
                text=header_text,
                chunk_index=start_idx + len(chunks),
                start_line=node.lineno,
                end_line=class_header_end + 1,
                title=node.name,
                symbol=node.name,
            ))
        
        # Each method as separate chunk
        for child in node.body:
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef):
                chunk = self._extract_function(
                    child, lines, start_idx + len(chunks), node.name
                )
                if chunk:
                    chunks.append(chunk)
        
        return chunks
    
    def _extract_function(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        lines: list[str],
        chunk_idx: int,
        class_name: str | None,
    ) -> ChunkData | None:
        """Extract a function/method as a chunk."""
        func_start = node.lineno - 1
        func_end = node.end_lineno or node.lineno
        func_text = "\n".join(lines[func_start:func_end])
        
        if len(func_text.strip()) < self.min_chunk_size:
            return None
        
        # Build symbol name
        symbol = f"{class_name}.{node.name}" if class_name else node.name
        
        # Get docstring for title
        docstring = ast.get_docstring(node)
        title = docstring.split("\n")[0][:100] if docstring else node.name
        
        return ChunkData(
            text=func_text,
            chunk_index=chunk_idx,
            start_line=node.lineno,
            end_line=func_end,
            title=title,
            symbol=symbol,
        )
    
    def _chunk_by_size(self, content: str) -> list[ChunkData]:
        """Fallback size-based chunking for unparseable code."""
        chunks: list[ChunkData] = []
        lines = content.split("\n")
        
        current_lines: list[str] = []
        current_size = 0
        current_start = 1
        
        for i, line in enumerate(lines, 1):
            line_size = len(line) + 1  # +1 for newline
            
            if current_size + line_size > self.target_chunk_size and current_lines:
                chunks.append(ChunkData(
                    text="\n".join(current_lines),
                    chunk_index=len(chunks),
                    start_line=current_start,
                    end_line=i - 1,
                    title=None,
                    symbol=None,
                ))
                current_lines = [line]
                current_size = line_size
                current_start = i
            else:
                current_lines.append(line)
                current_size += line_size
        
        if current_lines:
            chunks.append(ChunkData(
                text="\n".join(current_lines),
                chunk_index=len(chunks),
                start_line=current_start,
                end_line=len(lines),
                title=None,
                symbol=None,
            ))
        
        return chunks


def chunk_python(content: str, filename: str = "", **kwargs) -> list[ChunkData]:
    """
    Convenience function to chunk Python content.
    
    Args:
        content: Python source code
        filename: Optional filename for error context
        **kwargs: Passed to PythonChunker constructor
        
    Returns:
        List of ChunkData objects
    """
    chunker = PythonChunker(**kwargs)
    return chunker.chunk(content, filename)
