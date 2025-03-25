#!/usr/bin/env python
"""CLI entry point for pytui."""

import sys
import click
from rich.console import Console

from .executor import ScriptExecutor
from .ui.app import PyTUIApp

console = Console()

@click.group()
def cli():
    """Python Terminal UI for visualizing script execution."""
    pass

@cli.command()
@click.argument('script_path', type=click.Path(exists=True))
@click.argument('script_args', nargs=-1)
def run(script_path, script_args):
    """Run a Python script through the TUI."""
    try:
        executor = ScriptExecutor(script_path, list(script_args))
        app = PyTUIApp()
        app.set_executor(executor)
        app.run()
    except Exception as e:
        console.print(f"Error: {e}", style="bold red")
        sys.exit(1)

if __name__ == "__main__":
    cli()
