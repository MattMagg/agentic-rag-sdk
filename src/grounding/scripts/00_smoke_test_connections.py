#!/usr/bin/env python3
"""
Smoke test for API connections per spec §9.1.

This script verifies all connections work before proceeding to Spec 2.
Run this after setting up credentials in .env.

Usage:
    python -m src.grounding.scripts.00_smoke_test_connections
"""

from __future__ import annotations

import sys
from rich.console import Console
from rich.panel import Panel


console = Console()


def check_config() -> bool:
    """Check 1: Load and validate config."""
    console.print("\n[bold]1. Loading configuration...[/bold]")
    try:
        from src.grounding.config import get_settings
        
        settings = get_settings()
        
        # Verify required fields are populated
        assert settings.qdrant.url, "QDRANT_URL is empty"
        assert settings.qdrant.api_key, "QDRANT_API_KEY is empty"
        assert settings.voyage.api_key, "VOYAGE_API_KEY is empty"
        
        console.print("   [green]✓[/green] Config loaded successfully")
        console.print(f"   [dim]Collection: {settings.qdrant.collection}[/dim]")
        console.print(f"   [dim]Voyage docs model: {settings.voyage.docs_model}[/dim]")
        console.print(f"   [dim]Voyage code model: {settings.voyage.code_model}[/dim]")
        return True
    except Exception as e:
        console.print(f"   [red]✗[/red] Failed: {e}")
        return False


def check_qdrant() -> bool:
    """Check 2: Connect to Qdrant Cloud."""
    console.print("\n[bold]2. Connecting to Qdrant Cloud...[/bold]")
    try:
        from src.grounding.clients.qdrant_client import get_qdrant_client
        
        client = get_qdrant_client()
        
        if not client.healthcheck():
            raise Exception("Healthcheck failed")
        
        collections = client.list_collections()
        console.print("   [green]✓[/green] Connected to Qdrant Cloud")
        console.print(f"   [dim]Existing collections: {len(collections)}[/dim]")
        
        for coll in collections[:5]:
            console.print(f"   [dim]  - {coll}[/dim]")
        if len(collections) > 5:
            console.print(f"   [dim]  ... and {len(collections) - 5} more[/dim]")
            
        return True
    except Exception as e:
        console.print(f"   [red]✗[/red] Failed: {e}")
        return False


def check_voyage_code_embed() -> bool:
    """Check 3: Embed with voyage-code-3."""
    console.print("\n[bold]3. Testing voyage-code-3 embedding...[/bold]")
    try:
        from src.grounding.clients.voyage_client import get_voyage_client
        from src.grounding.config import get_settings
        
        client = get_voyage_client()
        settings = get_settings()
        
        test_texts = [
            "def hello_world():\n    print('Hello, world!')",
        ]
        
        embeddings = client.embed_code(test_texts, input_type="document")
        
        assert len(embeddings) == 1, f"Expected 1 embedding, got {len(embeddings)}"
        assert len(embeddings[0]) == settings.voyage.output_dimension, \
            f"Expected {settings.voyage.output_dimension} dims, got {len(embeddings[0])}"
        
        console.print("   [green]✓[/green] Code embedding succeeded")
        console.print(f"   [dim]Model: {settings.voyage.code_model}[/dim]")
        console.print(f"   [dim]Dimensions: {len(embeddings[0])}[/dim]")
        return True
    except Exception as e:
        console.print(f"   [red]✗[/red] Failed: {e}")
        return False


def check_voyage_contextualized_embed() -> bool:
    """Check 4: Embed with voyage-context-3 contextualized endpoint."""
    console.print("\n[bold]4. Testing voyage-context-3 contextualized embedding...[/bold]")
    try:
        from src.grounding.clients.voyage_client import get_voyage_client
        from src.grounding.config import get_settings
        
        client = get_voyage_client()
        settings = get_settings()
        
        # Contextualized input: list of documents, each document is list of chunks
        test_inputs = [
            ["# Getting Started\n\nThis guide helps you set up the ADK."],
        ]
        
        embeddings = client.embed_docs_contextualized(test_inputs, input_type="document")
        
        assert len(embeddings) == 1, f"Expected 1 embedding, got {len(embeddings)}"
        assert len(embeddings[0]) == settings.voyage.output_dimension, \
            f"Expected {settings.voyage.output_dimension} dims, got {len(embeddings[0])}"
        
        console.print("   [green]✓[/green] Contextualized embedding succeeded")
        console.print(f"   [dim]Model: {settings.voyage.docs_model}[/dim]")
        console.print(f"   [dim]Dimensions: {len(embeddings[0])}[/dim]")
        return True
    except Exception as e:
        console.print(f"   [red]✗[/red] Failed: {e}")
        return False


def check_voyage_rerank() -> bool:
    """Check 5: Rerank with rerank-2.5."""
    console.print("\n[bold]5. Testing rerank-2.5...[/bold]")
    try:
        from src.grounding.clients.voyage_client import get_voyage_client
        from src.grounding.config import get_settings
        
        client = get_voyage_client()
        settings = get_settings()
        
        query = "How do I create an ADK agent?"
        documents = [
            "The ADK provides tools for building AI agents.",
            "Climate change affects global temperatures.",
            "To create an agent, use the Agent class with a model and instruction.",
        ]
        
        results = client.rerank(query, documents, top_k=3)
        
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        
        # The third document should rank highest (most relevant)
        console.print("   [green]✓[/green] Reranking succeeded")
        console.print(f"   [dim]Model: {settings.voyage.rerank_model}[/dim]")
        console.print(f"   [dim]Top result index: {results[0].index} (score: {results[0].relevance_score:.3f})[/dim]")
        return True
    except Exception as e:
        console.print(f"   [red]✗[/red] Failed: {e}")
        return False


def main() -> int:
    """Run all smoke tests."""
    console.print(Panel.fit(
        "[bold blue]SPEC-01 Smoke Test[/bold blue]\n"
        "Verifying API connections before proceeding to Spec 2",
        border_style="blue"
    ))
    
    results = [
        ("Config", check_config()),
        ("Qdrant", check_qdrant()),
        ("Voyage Code Embed", check_voyage_code_embed()),
        ("Voyage Contextualized Embed", check_voyage_contextualized_embed()),
        ("Voyage Rerank", check_voyage_rerank()),
    ]
    
    # Summary
    console.print("\n" + "=" * 50)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    
    if passed == total:
        console.print(Panel.fit(
            f"[bold green]All {total} checks passed![/bold green]\n"
            "Ready to proceed to Spec 2.",
            border_style="green"
        ))
        return 0
    else:
        console.print(Panel.fit(
            f"[bold red]{total - passed} of {total} checks failed[/bold red]\n"
            "Fix the issues above before proceeding.",
            border_style="red"
        ))
        for name, ok in results:
            status = "[green]✓[/green]" if ok else "[red]✗[/red]"
            console.print(f"  {status} {name}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
