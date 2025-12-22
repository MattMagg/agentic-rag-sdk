#!/usr/bin/env python3
"""
Convert Jupyter notebooks to Markdown for ingestion.

This script scans the agent-dev-docs/notebooks directory, detects notebook files
(with or without .ipynb extension), and converts them to markdown format suitable
for ingestion with voyage-context-3.

Usage:
    python -m src.grounding.scripts.00_convert_notebooks
    python -m src.grounding.scripts.00_convert_notebooks --dry-run

Output:
    Markdown files in corpora/agent-dev-docs/notebooks-converted/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Project root is 4 levels up from this file
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

console = Console()


def is_jupyter_notebook(file_path: Path) -> bool:
    """
    Check if a file is a Jupyter notebook by examining its content.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if the file is a valid Jupyter notebook
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(1000)  # Read first 1000 chars for detection
            
        # Quick check for notebook structure
        if not content.strip().startswith('{'):
            return False
            
        # Full parse to confirm
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        return 'nbformat' in data and 'cells' in data
        
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError):
        return False


def extract_cell_source(cell: dict) -> str:
    """
    Extract source content from a notebook cell.
    
    Args:
        cell: Notebook cell dictionary
        
    Returns:
        Source text as a string
    """
    source = cell.get('source', [])
    if isinstance(source, list):
        return ''.join(source)
    return source


def notebook_to_markdown(notebook_path: Path, title: str) -> str:
    """
    Convert a Jupyter notebook to markdown format.
    
    Args:
        notebook_path: Path to the notebook file
        title: Title to use for the document
        
    Returns:
        Markdown string
    """
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)
    
    cells = notebook.get('cells', [])
    
    # Build markdown content
    md_parts = []
    
    # Add header with provenance
    md_parts.append(f"# {title}\n")
    md_parts.append(f"*Converted from: {notebook_path.name}*\n")
    md_parts.append("---\n")
    
    for cell in cells:
        cell_type = cell.get('cell_type', '')
        source = extract_cell_source(cell)
        
        if not source.strip():
            continue
        
        if cell_type == 'markdown':
            md_parts.append(source.strip())
            md_parts.append("")  # Empty line between cells
            
        elif cell_type == 'code':
            # Wrap code in fenced code block
            md_parts.append("```python")
            md_parts.append(source.strip())
            md_parts.append("```")
            md_parts.append("")  # Empty line between cells
            
        elif cell_type == 'raw':
            # Include raw cells as-is
            md_parts.append(source.strip())
            md_parts.append("")
    
    return '\n'.join(md_parts)


def clean_filename_for_title(filename: str) -> str:
    """
    Convert a filename to a clean title.
    
    Args:
        filename: Original filename
        
    Returns:
        Clean title string
    """
    # Remove common extensions
    title = filename
    for ext in ['.ipynb', '.json']:
        if title.endswith(ext):
            title = title[:-len(ext)]
    
    # Replace underscores with spaces (but keep colons for chapter markers)
    title = title.replace('_', ' ')
    
    return title


def discover_notebooks(input_dir: Path) -> list[Path]:
    """
    Discover all Jupyter notebook files in a directory.
    
    Args:
        input_dir: Directory to scan
        
    Returns:
        List of paths to notebook files
    """
    notebooks = []
    
    if not input_dir.exists():
        return notebooks
    
    for file_path in sorted(input_dir.iterdir()):
        # Skip directories and hidden files
        if file_path.is_dir() or file_path.name.startswith('.'):
            continue
        
        if is_jupyter_notebook(file_path):
            notebooks.append(file_path)
    
    return notebooks


def main() -> int:
    """Run the notebook conversion pipeline."""
    parser = argparse.ArgumentParser(description="Convert Jupyter notebooks to Markdown")
    parser.add_argument("--dry-run", action="store_true", help="Don't write files, just show what would be done")
    parser.add_argument("--input-dir", type=str, default="corpora/agent-dev-docs/notebooks",
                       help="Input directory containing notebooks")
    parser.add_argument("--output-dir", type=str, default="corpora/agent-dev-docs/notebooks-converted",
                       help="Output directory for converted markdown files")
    args = parser.parse_args()
    
    console.print(Panel.fit(
        "[bold blue]Notebook to Markdown Converter[/bold blue]\n"
        "Convert Jupyter notebooks for RAG ingestion",
        border_style="blue"
    ))
    
    input_dir = PROJECT_ROOT / args.input_dir
    output_dir = PROJECT_ROOT / args.output_dir
    
    console.print(f"Input directory: [cyan]{input_dir}[/cyan]")
    console.print(f"Output directory: [cyan]{output_dir}[/cyan]")
    
    # Discover notebooks
    console.print("\n[yellow]→[/yellow] Discovering notebooks...")
    notebooks = discover_notebooks(input_dir)
    console.print(f"[green]✓[/green] Found {len(notebooks)} notebooks")
    
    if not notebooks:
        console.print("[yellow]No notebooks found. Exiting.[/yellow]")
        return 0
    
    # Create output directory
    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]✓[/green] Created output directory")
    
    if args.dry_run:
        console.print("\n[yellow]DRY RUN MODE - No files will be written[/yellow]")
    
    # Convert notebooks
    stats = {"converted": 0, "skipped": 0, "errors": 0}
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Converting notebooks...", total=len(notebooks))
        
        for notebook_path in notebooks:
            progress.update(task, advance=1, description=f"[cyan]{notebook_path.name[:40]}[/cyan]")
            
            try:
                # Generate title and output filename
                title = clean_filename_for_title(notebook_path.name)
                output_filename = notebook_path.stem + ".md"
                output_path = output_dir / output_filename
                
                # Convert to markdown
                markdown_content = notebook_to_markdown(notebook_path, title)
                
                if args.dry_run:
                    console.print(f"  [dim]Would write: {output_path.name} ({len(markdown_content)} chars)[/dim]")
                else:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)
                
                stats["converted"] += 1
                
            except Exception as e:
                console.print(f"  [red]Error converting {notebook_path.name}: {e}[/red]")
                stats["errors"] += 1
    
    # Summary
    console.print("\n" + "=" * 50)
    console.print(f"[bold]Conversion Summary[/bold]")
    console.print(f"  Converted: [green]{stats['converted']}[/green]")
    console.print(f"  Skipped: [yellow]{stats['skipped']}[/yellow]")
    console.print(f"  Errors: [red]{stats['errors']}[/red]")
    
    if not args.dry_run:
        console.print(f"\n[bold]Output files written to:[/bold] {output_dir}")
    
    return 0 if stats["errors"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
