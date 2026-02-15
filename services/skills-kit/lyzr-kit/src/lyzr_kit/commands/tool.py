"""Tool CLI commands.

TODO: Tool commands will be fully implemented in Phase 4.
Currently, all commands return a placeholder message.
"""

import typer
from rich.console import Console

app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("ls")
def list_tools() -> None:
    """List all tools (built-in + cloned)."""
    console.print("[yellow]Not implemented (Phase 4)[/yellow]")


@app.command("get")
def get_tool(tool_id: str) -> None:
    """Clone tool to tools/<id>.yaml."""
    console.print("[yellow]Not implemented (Phase 4)[/yellow]")


@app.command("set")
def set_tool(tool_id: str) -> None:
    """Update tool from tools/<id>.yaml."""
    console.print("[yellow]Not implemented (Phase 4)[/yellow]")
