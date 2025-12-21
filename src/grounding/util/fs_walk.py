"""
File system discovery utilities for corpus ingestion.

Implements include/exclude glob patterns per spec §8 corpus embedding targets.

Related files:
- docs/spec/corpus_embedding_targets.md - Pattern specifications
- src/grounding/scripts/03_ingest_corpus.py - Main consumer
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from dataclasses import dataclass


@dataclass
class DiscoveredFile:
    """A discovered file for ingestion."""
    path: Path
    relative_path: str
    size_bytes: int


def _glob_to_regex(pattern: str) -> re.Pattern:
    """
    Convert a glob pattern to a regex pattern.
    
    Handles:
    - ** for recursive directory matching
    - * for single directory/file matching
    - ? for single character matching
    
    Args:
        pattern: Glob pattern like 'docs/**/*.md' or '**/site/**'
        
    Returns:
        Compiled regex pattern
    """
    # Escape regex special chars except * and ?
    regex = ""
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == '*':
            if i + 1 < len(pattern) and pattern[i + 1] == '*':
                # ** matches any path (including /)
                if i + 2 < len(pattern) and pattern[i + 2] == '/':
                    regex += r"(?:.*/)?"  # Match any directories or nothing
                    i += 3
                else:
                    regex += r".*"  # Match anything
                    i += 2
            else:
                regex += r"[^/]*"  # Match anything except /
                i += 1
        elif c == '?':
            regex += r"[^/]"  # Match single char except /
            i += 1
        elif c in '.^$+{}[]|()\\':
            regex += '\\' + c  # Escape regex special chars
            i += 1
        else:
            regex += c
            i += 1
    
    return re.compile(f"^{regex}$")


def matches_any_pattern(path_str: str, patterns: list[str]) -> bool:
    """
    Check if path matches any of the glob patterns.
    
    Supports standard glob patterns including ** for recursive matching.
    
    Args:
        path_str: Path string to check (relative to root)
        patterns: List of glob patterns
        
    Returns:
        True if path matches any pattern
    """
    for pattern in patterns:
        regex = _glob_to_regex(pattern)
        if regex.match(path_str):
            return True
    return False


def discover_files(
    root: Path,
    include_globs: list[str],
    exclude_globs: list[str],
    allowed_exts: list[str],
    max_file_bytes: int = 500_000,
) -> list[DiscoveredFile]:
    """
    Discover files matching include patterns and not matching exclude patterns.
    
    Implements spec §2 file discovery logic for corpus ingestion.
    
    Args:
        root: Root directory to search
        include_globs: Patterns for files to include (must match at least one)
        exclude_globs: Patterns for files to exclude (if matches any, skip)
        allowed_exts: Allowed file extensions (with dot, e.g. [".py", ".md"])
        max_file_bytes: Maximum file size to include (default 500KB)
        
    Returns:
        List of DiscoveredFile objects for matching files
        
    Example:
        files = discover_files(
            root=Path("corpora/adk-docs"),
            include_globs=["docs/**/*.md", "examples/python/**/*.py"],
            exclude_globs=["**/site/**", "**/__pycache__/**"],
            allowed_exts=[".md", ".py"],
        )
    """
    root = Path(root).resolve()
    if not root.exists():
        raise ValueError(f"Root directory does not exist: {root}")
    
    discovered: list[DiscoveredFile] = []
    
    # Walk the directory tree
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        
        # Get relative path for pattern matching
        try:
            rel_path = file_path.relative_to(root)
        except ValueError:
            continue
        
        rel_path_str = str(rel_path)
        
        # Check extension
        ext = file_path.suffix.lower()
        if ext not in allowed_exts:
            continue
        
        # Check file size
        try:
            size = file_path.stat().st_size
            if size > max_file_bytes:
                continue
            if size == 0:
                continue  # Skip empty files
        except OSError:
            continue
        
        # Check exclude patterns first (if excluded, skip)
        if exclude_globs and matches_any_pattern(rel_path_str, exclude_globs):
            continue
        
        # Check include patterns (must match at least one)
        if include_globs and not matches_any_pattern(rel_path_str, include_globs):
            continue
        
        discovered.append(DiscoveredFile(
            path=file_path,
            relative_path=rel_path_str,
            size_bytes=size,
        ))
    
    # Sort by path for deterministic ordering
    discovered.sort(key=lambda f: f.relative_path)
    
    return discovered


def read_file_content(file: DiscoveredFile) -> str | None:
    """
    Read file content as UTF-8 text.
    
    Args:
        file: DiscoveredFile to read
        
    Returns:
        File content as string, or None if unreadable
    """
    try:
        return file.path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Try with latin-1 fallback
        try:
            return file.path.read_text(encoding="latin-1")
        except Exception:
            return None
    except Exception:
        return None
