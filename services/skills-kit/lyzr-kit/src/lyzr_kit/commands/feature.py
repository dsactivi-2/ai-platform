"""Feature CLI commands.

TODO: Feature commands will be fully implemented in Phase 5.
Currently, all commands return a placeholder message.
"""

import typer
from rich.console import Console

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("ls")
def list_features() -> None:
    """List all features (built-in + cloned)."""
    console.print("[yellow]Not implemented (Phase 5)[/yellow]")


@app.command("get")
def get_feature(feature_id: str) -> None:
    """Clone feature to features/<id>.yaml."""
    console.print("[yellow]Not implemented (Phase 5)[/yellow]")


@app.command("set")
def set_feature(feature_id: str) -> None:
    """Update feature from features/<id>.yaml."""
    console.print("[yellow]Not implemented (Phase 5)[/yellow]")
