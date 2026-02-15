"""Auth command for lyzr-kit."""

from pathlib import Path

import typer
from rich.console import Console

from lyzr_kit.storage import init_project_structure

console = Console()

# Environment variable names
ENV_VAR_API_KEY = "LYZR_API_KEY"
ENV_VAR_USER_ID = "LYZR_USER_ID"
ENV_VAR_ORG_ID = "LYZR_ORG_ID"
ENV_VAR_MEMBERSTACK_TOKEN = "LYZR_MEMBERSTACK_TOKEN"


def _update_env_value(env_path: Path, key: str, value: str) -> None:
    """Update or add a key-value pair in .env file."""
    if env_path.exists():
        existing_content = env_path.read_text()
        lines = existing_content.splitlines()
    else:
        lines = []

    updated = False
    new_lines = []

    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"{key}={value}")

    env_path.write_text("\n".join(new_lines) + "\n")


def auth() -> None:
    """Set up API credentials (.env file)."""
    try:
        env_path = Path.cwd() / ".env"
    except (FileNotFoundError, OSError) as e:
        console.print("[red]Error: Current directory not found[/red]")
        console.print("[dim]Please run this command from a valid directory.[/dim]")
        raise typer.Exit(1) from e

    console.print("\n[bold]Lyzr Authentication Setup[/bold]")
    console.print("[dim]Get your credentials from https://studio.lyzr.ai[/dim]\n")

    # Prompt for API key (required)
    api_key = typer.prompt("Enter your Lyzr API key", hide_input=True)
    if not api_key or not api_key.strip():
        console.print("[red]Error: API key cannot be empty[/red]")
        raise typer.Exit(1)
    api_key = api_key.strip()
    _update_env_value(env_path, ENV_VAR_API_KEY, api_key)
    console.print("[green]✓ API key saved[/green]")

    # Prompt for User ID (optional)
    user_id = typer.prompt("Enter your User ID", default="", show_default=False)
    if user_id.strip():
        _update_env_value(env_path, ENV_VAR_USER_ID, user_id.strip())
        console.print("[green]✓ User ID saved[/green]")
    else:
        console.print("[dim]Skipped User ID[/dim]")

    # Prompt for Org ID (optional)
    org_id = typer.prompt("Enter your Org ID", default="", show_default=False)
    if org_id.strip():
        _update_env_value(env_path, ENV_VAR_ORG_ID, org_id.strip())
        console.print("[green]✓ Org ID saved[/green]")
    else:
        console.print("[dim]Skipped Org ID[/dim]")

    # Prompt for Memberstack token (optional)
    memberstack_token = typer.prompt("Enter your Memberstack token", default="", show_default=False)
    if memberstack_token.strip():
        _update_env_value(env_path, ENV_VAR_MEMBERSTACK_TOKEN, memberstack_token.strip())
        console.print("[green]✓ Memberstack token saved[/green]")
    else:
        console.print("[dim]Skipped Memberstack token[/dim]")

    # Initialize project structure
    init_project_structure()

    console.print("\n[green]✓ Authentication configured successfully![/green]")
    console.print(f"[dim]Credentials saved to: {env_path}[/dim]")
    console.print("[dim]Project initialized with README.md, .gitignore, and agents/[/dim]")
    console.print("[dim]You can now use lk commands to manage agents.[/dim]")
