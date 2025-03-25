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

@cli.command()
@click.argument('script_path', type=click.Path(exists=True))
@click.argument('script_args', nargs=-1)
def run(script_path, script_args):
    """Run a Python script through the TUI."""
    try:
        app = PyTUIApp()
        executor = ScriptExecutor(script_path, list(script_args))
        app.set_executor(executor)
        app.run()
    except click.ClickException as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    cli()
