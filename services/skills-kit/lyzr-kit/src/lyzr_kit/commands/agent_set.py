"""Agent set command implementation."""

from pathlib import Path

import typer
from rich.status import Status

from lyzr_kit.commands._auth_helper import require_auth
from lyzr_kit.commands._console import console
from lyzr_kit.commands._resolver import resolve_local_agent_id
from lyzr_kit.storage import (
    StorageManager,
    detect_cycle,
    format_cycle_error,
    format_schema_errors,
    format_subagent_errors,
    validate_agent_yaml_file,
    validate_sub_agents,
)
from lyzr_kit.utils.auth import STUDIO_BASE_URL
from lyzr_kit.utils.platform import PlatformClient, PlatformError


def set_agent(identifier: str) -> None:
    """Update agent on platform from agents/<id>.yaml.

    Args:
        identifier: Agent ID or serial number.
    """
    auth = require_auth()
    storage = StorageManager()

    # Resolve identifier (could be serial number or agent ID)
    # For 'set' command, we only look up local agents
    agent_id = resolve_local_agent_id(identifier, storage)
    if agent_id is None:
        raise typer.Exit(1)

    # Check if exists in local (by filename)
    yaml_path = Path(storage.local_path) / "agents" / f"{agent_id}.yaml"
    if not yaml_path.exists():
        console.print(f"[red]Error: Agent '{agent_id}' not found in agents/[/red]")
        console.print("[dim]Run 'lk agent get' first to clone the agent[/dim]")
        raise typer.Exit(1)

    # Load and validate with detailed error messages
    agent, schema_error, yaml_error = validate_agent_yaml_file(yaml_path)

    if yaml_error:
        console.print(f"[red]Error: {yaml_error}[/red]")
        console.print(f"[dim]Fix the YAML file and re-run 'lk agent set {agent_id}'[/dim]")
        raise typer.Exit(1)

    if schema_error:
        console.print(format_schema_errors(schema_error, agent_id))
        raise typer.Exit(1)

    if not agent:
        console.print(f"[red]Error: Failed to load agent '{agent_id}'[/red]")
        raise typer.Exit(1)

    # Validate sub-agents exist locally
    if agent.sub_agents:
        missing_sub_agents = validate_sub_agents(agent.sub_agents, storage)
        if missing_sub_agents:
            console.print(format_subagent_errors(missing_sub_agents))
            raise typer.Exit(1)

        # Detect circular dependencies
        cycle = detect_cycle(agent.id, agent.sub_agents, storage)
        if cycle:
            console.print(format_cycle_error(cycle))
            raise typer.Exit(1)

    # Detect if ID in YAML differs from filename
    id_changed = agent.id != agent_id
    if id_changed:
        # Check if a file with the new ID already exists (different from current file)
        new_yaml_path = Path(storage.local_path) / "agents" / f"{agent.id}.yaml"
        if new_yaml_path.exists():
            console.print(f"[red]Error: ID '{agent.id}' already exists[/red]")
            console.print("[dim]Update the ID in the YAML file and re-run the command[/dim]")
            raise typer.Exit(1)

    # Check if agent has platform IDs
    if not agent.platform_agent_id or not agent.platform_env_id:
        console.print(f"[red]Error: Agent '{agent_id}' has no platform IDs[/red]")
        console.print("[dim]This agent may have been created before platform integration.[/dim]")
        console.print(f"[dim]Delete agents/{agent_id}.yaml and run 'lk agent get' again.[/dim]")
        raise typer.Exit(1)

    # Update agent on platform
    try:
        with Status("[bold cyan]Updating agent on platform...[/bold cyan]", console=console):
            platform = PlatformClient(auth)
            response = platform.update_agent(
                agent=agent,
                agent_id=agent.platform_agent_id,
                env_id=agent.platform_env_id,
            )
            agent.endpoint = response.endpoint

    except PlatformError as e:
        console.print(f"[red]Platform Error:[/red] {e}")
        raise typer.Exit(1) from None

    # Save updated agent
    path = storage.save_agent(agent)

    # If ID changed, update sub-agent references in other agents and delete old file
    if id_changed:
        updated_agents = storage.update_subagent_references(agent_id, agent.id)
        if updated_agents:
            console.print(
                f"\n[cyan]Updated sub-agent references in {len(updated_agents)} agent(s):[/cyan]"
            )
            for updated_id in updated_agents:
                console.print(f"  - {updated_id}")

        # Delete the old YAML file
        old_path = Path(storage.local_path) / "agents" / f"{agent_id}.yaml"
        if old_path.exists():
            old_path.unlink()

    console.print(f"\n[green]Agent '{agent.id}' updated successfully![/green]")
    console.print(f"[dim]Agent ID:[/dim] {response.agent_id}")
    console.print(f"[dim]Platform URL:[/dim] {response.platform_url}")
    if agent.marketplace_app_id:
        chat_url = f"{STUDIO_BASE_URL}/agent/{agent.marketplace_app_id}/"
        console.print(f"[dim]Chat URL:[/dim] {chat_url}")
    console.print(f"[dim]API Endpoint:[/dim] {agent.endpoint}")
    console.print(f"[dim]Local config:[/dim] {path}")
