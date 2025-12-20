#!/usr/bin/env python3
"""
Print effective configuration with secrets redacted.

Useful for debugging and verifying config is loaded correctly.

Usage:
    python -m src.grounding.scripts.01_print_effective_config
"""

from __future__ import annotations

import json
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax


console = Console()


def main() -> None:
    """Print the effective configuration."""
    from src.grounding.config import get_settings_redacted
    
    config = get_settings_redacted()
    
    console.print(Panel.fit(
        "[bold blue]Effective Configuration[/bold blue]\n"
        "Secrets are redacted for safety",
        border_style="blue"
    ))
    
    # Pretty print as YAML-like structure
    config_json = json.dumps(config, indent=2)
    syntax = Syntax(config_json, "json", theme="monokai", line_numbers=False)
    console.print(syntax)


if __name__ == "__main__":
    main()
