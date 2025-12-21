"""
Markdown chunker for documentation files.

Implements heading-aware chunking per spec §6.1:
- Split on H2/H3 boundaries
- Target chunk size: 3000-5000 chars
- Preserve heading hierarchy in metadata

Related files:
- src/grounding/contracts/chunk.py - Chunk model
- docs/spec/corpus_embedding_targets.md - Chunking requirements
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class MarkdownSection:
    """A section of markdown content with its heading hierarchy."""
    heading: str | None
    heading_level: int
    content: str
    start_line: int
    end_line: int


@dataclass
class ChunkData:
    """Raw chunk data before becoming a full Chunk model."""
    text: str
    chunk_index: int
    start_line: int | None
    end_line: int | None
    title: str | None


class MarkdownChunker:
    """
    Heading-aware markdown chunker.
    
    Splits markdown on H2/H3 boundaries while respecting target chunk size.
    """
    
    def __init__(
        self,
        min_chunk_size: int = 500,
        target_chunk_size: int = 4000,
        max_chunk_size: int = 6000,
    ):
        """
        Initialize chunker with size parameters.
        
        Args:
            min_chunk_size: Minimum chars before splitting (avoid tiny chunks)
            target_chunk_size: Ideal chunk size to aim for
            max_chunk_size: Force split if exceeds this size
        """
        self.min_chunk_size = min_chunk_size
        self.target_chunk_size = target_chunk_size
        self.max_chunk_size = max_chunk_size
        
        # Regex for markdown headings
        self.heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    
    def chunk(self, content: str) -> list[ChunkData]:
        """
        Chunk markdown content into sections.
        
        Args:
            content: Full markdown content
            
        Returns:
            List of ChunkData objects
        """
        if not content.strip():
            return []
        
        lines = content.split("\n")
        sections = self._extract_sections(lines)
        
        if not sections:
            # No headings found - chunk by size
            return self._chunk_by_size(content)
        
        # Merge small sections, split large ones
        return self._process_sections(sections)
    
    def _extract_sections(self, lines: list[str]) -> list[MarkdownSection]:
        """Extract sections based on headings (H1-H3 splits)."""
        sections: list[MarkdownSection] = []
        current_lines: list[str] = []
        current_heading: str | None = None
        current_level: int = 0
        section_start: int = 1
        
        for i, line in enumerate(lines, 1):
            match = self.heading_pattern.match(line)
            if match:
                level = len(match.group(1))
                heading_text = match.group(2).strip()
                
                # H1, H2, H3 are split points
                if level <= 3:
                    # Save previous section if exists
                    if current_lines or current_heading:
                        sections.append(MarkdownSection(
                            heading=current_heading,
                            heading_level=current_level,
                            content="\n".join(current_lines),
                            start_line=section_start,
                            end_line=i - 1,
                        ))
                    
                    # Start new section
                    current_heading = heading_text
                    current_level = level
                    current_lines = [line]
                    section_start = i
                else:
                    current_lines.append(line)
            else:
                current_lines.append(line)
        
        # Don't forget last section
        if current_lines or current_heading:
            sections.append(MarkdownSection(
                heading=current_heading,
                heading_level=current_level,
                content="\n".join(current_lines),
                start_line=section_start,
                end_line=len(lines),
            ))
        
        return sections
    
    def _process_sections(self, sections: list[MarkdownSection]) -> list[ChunkData]:
        """Merge small sections and split large ones."""
        chunks: list[ChunkData] = []
        buffer: list[MarkdownSection] = []
        buffer_size = 0
        
        for section in sections:
            section_size = len(section.content)
            
            # If section alone exceeds max, split it
            if section_size > self.max_chunk_size:
                # First, flush buffer
                if buffer:
                    chunks.append(self._merge_sections(buffer, len(chunks)))
                    buffer = []
                    buffer_size = 0
                
                # Split large section
                chunks.extend(self._split_large_section(section, len(chunks)))
                continue
            
            # If adding this section exceeds target, flush buffer first
            if buffer_size + section_size > self.target_chunk_size and buffer:
                chunks.append(self._merge_sections(buffer, len(chunks)))
                buffer = []
                buffer_size = 0
            
            buffer.append(section)
            buffer_size += section_size
        
        # Flush remaining buffer
        if buffer:
            chunks.append(self._merge_sections(buffer, len(chunks)))
        
        return chunks
    
    def _merge_sections(self, sections: list[MarkdownSection], chunk_idx: int) -> ChunkData:
        """Merge multiple sections into one chunk."""
        text = "\n\n".join(s.content for s in sections)
        first_heading = next((s.heading for s in sections if s.heading), None)
        
        return ChunkData(
            text=text.strip(),
            chunk_index=chunk_idx,
            start_line=sections[0].start_line,
            end_line=sections[-1].end_line,
            title=first_heading,
        )
    
    def _split_large_section(
        self, section: MarkdownSection, start_idx: int
    ) -> list[ChunkData]:
        """Split a large section by paragraph or size."""
        chunks: list[ChunkData] = []
        paragraphs = section.content.split("\n\n")
        
        current_text = ""
        current_start = section.start_line
        
        for para in paragraphs:
            if len(current_text) + len(para) > self.target_chunk_size and current_text:
                chunks.append(ChunkData(
                    text=current_text.strip(),
                    chunk_index=start_idx + len(chunks),
                    start_line=current_start,
                    end_line=None,  # Approximate
                    title=section.heading if not chunks else None,
                ))
                current_text = para
            else:
                current_text = current_text + "\n\n" + para if current_text else para
        
        if current_text.strip():
            chunks.append(ChunkData(
                text=current_text.strip(),
                chunk_index=start_idx + len(chunks),
                start_line=current_start,
                end_line=section.end_line,
                title=section.heading if not chunks else None,
            ))
        
        return chunks
    
    def _chunk_by_size(self, content: str) -> list[ChunkData]:
        """Simple size-based chunking when no headings found."""
        chunks: list[ChunkData] = []
        paragraphs = content.split("\n\n")
        
        current_text = ""
        for para in paragraphs:
            if len(current_text) + len(para) > self.target_chunk_size and current_text:
                chunks.append(ChunkData(
                    text=current_text.strip(),
                    chunk_index=len(chunks),
                    start_line=None,
                    end_line=None,
                    title=None,
                ))
                current_text = para
            else:
                current_text = current_text + "\n\n" + para if current_text else para
        
        if current_text.strip():
            chunks.append(ChunkData(
                text=current_text.strip(),
                chunk_index=len(chunks),
                start_line=None,
                end_line=None,
                title=None,
            ))
        
        return chunks


def chunk_markdown(content: str, **kwargs) -> list[ChunkData]:
    """
    Convenience function to chunk markdown content.
    
    Args:
        content: Markdown text to chunk
        **kwargs: Passed to MarkdownChunker constructor
        
    Returns:
        List of ChunkData objects
    """
    chunker = MarkdownChunker(**kwargs)
    return chunker.chunk(content)
