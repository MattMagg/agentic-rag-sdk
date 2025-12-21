#!/usr/bin/env python3
"""
SPEC-03 Ingestion Pipeline: Discover → Chunk → Embed → Upsert.

This script ingests all configured corpora into Qdrant with:
- Dense embeddings via Voyage (voyage-context-3 for docs, voyage-code-3 for code)
- Sparse embeddings via FastEmbed SPLADE
- Full payload schema per spec §4.1
- Idempotent ingestion via text_hash comparison

Usage:
    python -m src.grounding.scripts.03_ingest_corpus
    python -m src.grounding.scripts.03_ingest_corpus --corpus adk_docs
    python -m src.grounding.scripts.03_ingest_corpus --dry-run

Related files:
- docs/spec/corpus_embedding_targets.md - File patterns
- docs/spec/qdrant_schema_and_config.md - Schema spec
- src/grounding/chunkers/ - Chunking modules
- src/grounding/clients/ - Embedding clients
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table

from qdrant_client.models import PointStruct, SparseVector as QdrantSparseVector

if TYPE_CHECKING:
    from src.grounding.config import CorpusConfig

from src.grounding.config import get_settings, PROJECT_ROOT
from src.grounding.clients.qdrant_client import get_qdrant_client
from src.grounding.clients.voyage_client import get_voyage_client
from src.grounding.clients.fastembed_client import get_fastembed_client, SparseVector
from src.grounding.contracts.chunk import Chunk
from src.grounding.contracts.ids import make_parent_doc_id, make_chunk_id
from src.grounding.util.hashing import sha256_hex, normalize_text
from src.grounding.util.time import now_iso
from src.grounding.util.fs_walk import discover_files, read_file_content
from src.grounding.chunkers.markdown import chunk_markdown, ChunkData as MdChunkData
from src.grounding.chunkers.python_code import chunk_python, ChunkData as PyChunkData

console = Console()


def chunk_id_to_uuid(chunk_id: str) -> str:
    """
    Convert chunk_id hex string to UUID format for Qdrant.
    
    Qdrant requires point IDs to be either unsigned integers or UUIDs.
    We use UUID5 with a namespace derived from the chunk_id.
    
    Args:
        chunk_id: 40-char hex string from make_chunk_id()
        
    Returns:
        UUID string in standard format
    """
    # Use UUID5 with a DNS namespace and the chunk_id as name
    # This ensures deterministic conversion
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))


def get_git_commit(repo_path: Path) -> str:
    """Get current git commit SHA for a repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()[:12]  # Short SHA
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def get_language_from_ext(ext: str) -> str:
    """Map file extension to language identifier."""
    mapping = {
        ".py": "py",
        ".md": "md",
        ".mdx": "md",
        ".rst": "rst",
        ".txt": "txt",
        ".toml": "toml",
    }
    return mapping.get(ext.lower(), "unknown")


def process_corpus(
    corpus_name: str,
    corpus_config: "CorpusConfig",
    dry_run: bool = False,
) -> dict:
    """
    Process a single corpus: discover, chunk, embed, upsert.
    
    Args:
        corpus_name: Name of the corpus (e.g., adk_docs)
        corpus_config: Corpus configuration from settings
        dry_run: If True, don't actually upsert to Qdrant
        
    Returns:
        Stats dict with counts
    """
    settings = get_settings()
    qdrant = get_qdrant_client()
    voyage = get_voyage_client()
    fastembed = get_fastembed_client()
    
    # Resolve corpus root
    corpus_root = PROJECT_ROOT / corpus_config.root
    if not corpus_root.exists():
        console.print(f"[red]Corpus root not found: {corpus_root}[/red]")
        return {"files": 0, "chunks": 0, "upserted": 0, "skipped": 0}
    
    # Get git commit
    commit = get_git_commit(corpus_root)
    console.print(f"  Git commit: [cyan]{commit}[/cyan]")
    
    stats = {"files": 0, "chunks": 0, "upserted": 0, "skipped": 0}
    
    # Step 1: Discover files
    console.print("  [yellow]→[/yellow] Discovering files...")
    files = discover_files(
        root=corpus_root,
        include_globs=corpus_config.include_globs,
        exclude_globs=corpus_config.exclude_globs,
        allowed_exts=corpus_config.allowed_exts,
        max_file_bytes=corpus_config.max_file_bytes,
    )
    stats["files"] = len(files)
    console.print(f"  [green]✓[/green] Found {len(files)} files")
    
    if not files:
        return stats
    
    # Get existing hashes for this corpus for idempotency
    existing_hashes: set[str] = set()
    if not dry_run:
        try:
            # Scroll through existing points for this corpus
            offset = None
            while True:
                points, offset = qdrant.client.scroll(
                    collection_name=qdrant.collection_name,
                    scroll_filter={
                        "must": [{"key": "corpus", "match": {"value": corpus_config.corpus}}]
                    },
                    limit=1000,
                    offset=offset,
                    with_payload=["text_hash"],
                )
                for p in points:
                    if p.payload and "text_hash" in p.payload:
                        existing_hashes.add(p.payload["text_hash"])
                if offset is None:
                    break
            console.print(f"  [dim]Found {len(existing_hashes)} existing chunk hashes[/dim]")
        except Exception as e:
            console.print(f"  [yellow]Warning: Could not fetch existing hashes: {e}[/yellow]")
    
    # Batch processing
    batch_size = settings.ingestion.batch_size
    points_batch: list[PointStruct] = []
    ingested_at = now_iso()
    
    # Determine if this is doc or code corpus
    is_code = corpus_config.kind == "code"
    dense_vector_name = settings.vectors.dense_code if is_code else settings.vectors.dense_docs
    sparse_vector_name = settings.vectors.sparse_lexical
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Processing files...", total=len(files))
        
        for file in files:
            progress.update(task, advance=1, description=f"[cyan]{file.relative_path[:40]}[/cyan]")
            
            # Read content
            content = read_file_content(file)
            if not content:
                continue
            
            # Determine language
            ext = file.path.suffix
            lang = get_language_from_ext(ext)
            
            # Chunk based on content type
            if lang == "py":
                raw_chunks = chunk_python(content, file.relative_path)
            else:
                raw_chunks = chunk_markdown(content)
            
            if not raw_chunks:
                continue
            
            # Create parent doc ID
            parent_doc_id = make_parent_doc_id(
                corpus=corpus_config.corpus,
                commit=commit,
                path=file.relative_path,
            )
            
            for raw_chunk in raw_chunks:
                # Normalize and hash text
                text = raw_chunk.text.strip()
                if not text:
                    continue
                
                text_hash = sha256_hex(normalize_text(text))
                
                # Skip if unchanged (idempotency)
                if text_hash in existing_hashes:
                    stats["skipped"] += 1
                    continue
                
                stats["chunks"] += 1
                
                # Build chunk ID
                chunk_id = make_chunk_id(
                    parent_doc_id=parent_doc_id,
                    chunk_index=raw_chunk.chunk_index,
                    chunk_hash=text_hash,
                )
                
                # Create Chunk object
                chunk = Chunk(
                    chunk_id=chunk_id,
                    corpus=corpus_config.corpus,  # type: ignore
                    repo=corpus_config.repo,
                    commit=commit,
                    ref=corpus_config.ref,
                    path=file.relative_path,
                    symbol=getattr(raw_chunk, "symbol", None),
                    chunk_index=raw_chunk.chunk_index,
                    start_line=raw_chunk.start_line,
                    end_line=raw_chunk.end_line,
                    text=text,
                    text_hash=text_hash,
                    kind="code" if is_code else "doc",  # type: ignore
                    lang=lang,
                    ingested_at=ingested_at,
                    title=raw_chunk.title,
                )
                
                # Queue for embedding (batch later)
                points_batch.append((chunk, text))
                
                # Process batch when full
                if len(points_batch) >= batch_size:
                    upserted = _process_batch(
                        qdrant, voyage, fastembed, 
                        points_batch, dense_vector_name, sparse_vector_name,
                        is_code, dry_run
                    )
                    stats["upserted"] += upserted
                    points_batch = []
        
        # Process remaining batch
        if points_batch:
            upserted = _process_batch(
                qdrant, voyage, fastembed,
                points_batch, dense_vector_name, sparse_vector_name,
                is_code, dry_run
            )
            stats["upserted"] += upserted
    
    return stats


def _process_batch(
    qdrant,
    voyage,
    fastembed,
    batch: list[tuple[Chunk, str]],
    dense_vector_name: str,
    sparse_vector_name: str,
    is_code: bool,
    dry_run: bool,
) -> int:
    """Process a batch of chunks: embed and upsert."""
    if not batch:
        return 0
    
    chunks = [c for c, _ in batch]
    texts = [t for _, t in batch]
    
    # Generate dense embeddings
    if is_code:
        dense_embeddings = voyage.embed_code(texts, input_type="document")
    else:
        # For contextualized, we pass each text as a single-chunk doc
        # This is simpler than true contextualization across a document
        dense_embeddings = []
        for text in texts:
            emb = voyage.embed_docs_contextualized([[text]], input_type="document")
            dense_embeddings.extend(emb)
    
    # Generate sparse embeddings
    sparse_vectors = fastembed.embed_sparse(texts)
    
    # Build Qdrant points
    points = []
    for i, (chunk, dense_emb, sparse_vec) in enumerate(zip(chunks, dense_embeddings, sparse_vectors)):
        point = PointStruct(
            id=chunk_id_to_uuid(chunk.chunk_id),
            vector={
                dense_vector_name: dense_emb,
                sparse_vector_name: QdrantSparseVector(
                    indices=sparse_vec.indices,
                    values=sparse_vec.values,
                ),
            },
            payload=chunk.to_qdrant_payload(),
        )
        points.append(point)
    
    if dry_run:
        return len(points)
    
    # Upsert to Qdrant
    qdrant.client.upsert(
        collection_name=qdrant.collection_name,
        points=points,
    )
    
    return len(points)


def main() -> int:
    """Run the ingestion pipeline."""
    parser = argparse.ArgumentParser(description="SPEC-03 Corpus Ingestion Pipeline")
    parser.add_argument("--corpus", type=str, help="Specific corpus to ingest (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually upsert to Qdrant")
    args = parser.parse_args()
    
    console.print(Panel.fit(
        "[bold blue]SPEC-03 Ingestion Pipeline[/bold blue]\n"
        "Discover → Chunk → Embed → Upsert",
        border_style="blue"
    ))
    
    settings = get_settings()
    
    # Validate collection exists
    qdrant = get_qdrant_client()
    if not qdrant.client.collection_exists(qdrant.collection_name):
        console.print(f"[red]Collection '{qdrant.collection_name}' does not exist![/red]")
        console.print("[dim]Run 02_ensure_collection_schema.py first.[/dim]")
        return 1
    
    if args.dry_run:
        console.print("[yellow]DRY RUN MODE - No changes will be made[/yellow]\n")
    
    # Determine which corpora to process
    corpora_to_process = settings.ingestion.corpora
    if args.corpus:
        if args.corpus not in corpora_to_process:
            console.print(f"[red]Unknown corpus: {args.corpus}[/red]")
            console.print(f"[dim]Available: {list(corpora_to_process.keys())}[/dim]")
            return 1
        corpora_to_process = {args.corpus: corpora_to_process[args.corpus]}
    
    # Process each corpus
    total_stats = {"files": 0, "chunks": 0, "upserted": 0, "skipped": 0}
    
    try:
        for corpus_name, corpus_config in corpora_to_process.items():
            console.print(f"\n[bold]Processing corpus:[/bold] {corpus_name}")
            console.print(f"  Root: [cyan]{corpus_config.root}[/cyan]")
            console.print(f"  Kind: [cyan]{corpus_config.kind}[/cyan]")
            
            stats = process_corpus(corpus_name, corpus_config, dry_run=args.dry_run)
            
            for key in total_stats:
                total_stats[key] += stats[key]
            
            console.print(f"  [green]✓[/green] Files: {stats['files']}, Chunks: {stats['chunks']}, "
                         f"Upserted: {stats['upserted']}, Skipped: {stats['skipped']}")
        
        # Summary
        console.print("\n" + "=" * 50)
        
        summary_table = Table(title="Ingestion Summary")
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", style="green")
        summary_table.add_row("Total Files", str(total_stats["files"]))
        summary_table.add_row("Total Chunks", str(total_stats["chunks"]))
        summary_table.add_row("Upserted", str(total_stats["upserted"]))
        summary_table.add_row("Skipped (unchanged)", str(total_stats["skipped"]))
        console.print(summary_table)
        
        # Verify point count
        if not args.dry_run:
            info = qdrant.client.get_collection(qdrant.collection_name)
            console.print(f"\n[bold]Collection points:[/bold] {info.points_count}")
        
        return 0
        
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
