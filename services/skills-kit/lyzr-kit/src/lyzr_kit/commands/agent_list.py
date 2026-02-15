"""Agent list command implementation."""

from pathlib import Path

import typer
from rich.table import Table

from lyzr_kit.commands._console import console
from lyzr_kit.schemas import Agent
from lyzr_kit.storage import StorageManager, format_validation_errors, validate_agents_folder


def _count_sub_agents_recursive(
    agent: Agent, agent_map: dict[str, Agent], visited: set[str] | None = None
) -> int:
    """Count total sub-agents in the dependency tree (recursive).

    Args:
        agent: The agent to count sub-agents for.
        agent_map: Map of agent ID to Agent object for lookups.
        visited: Set of already visited agent IDs (for cycle detection).

    Returns:
        Total count of unique sub-agents in the tree.
    """
    if visited is None:
        visited = set()

    if agent.id in visited:
        return 0  # Cycle detected, don't count again

    visited.add(agent.id)
    count = 0

    for sub_id in agent.sub_agents:
        if sub_id in visited:
            continue  # Skip already-counted agents (handles cycles)
        count += 1  # Count this sub-agent
        if sub_id in agent_map:
            # Recursively count nested sub-agents
            count += _count_sub_agents_recursive(agent_map[sub_id], agent_map, visited)

    return count


def list_agents() -> None:
    """List all agents (built-in + local)."""
    storage = StorageManager()

    # Validate agents folder structure first
    validation_result = validate_agents_folder(Path(storage.local_path))
    if not validation_result.is_valid:
        console.print(format_validation_errors(validation_result))
        raise typer.Exit(1)

    agents = storage.list_agents()

    # Build agent map for recursive sub-agent counting
    agent_map: dict[str, Agent] = {a.id: a for a, _ in agents}

    # Separate built-in and local agents
    builtin_agents = [(a, s) for a, s in agents if s == "built-in"]
    local_agents = [(a, s) for a, s in agents if s == "local"]

    # Studio URL base for deployed agents
    studio_base_url = "https://studio.lyzr.ai/agent-create/"

    # Built-in agents table
    console.print()
    builtin_table = Table(title="Built-in Agents", title_style="bold cyan")
    builtin_table.add_column("#", style="dim", justify="right")
    builtin_table.add_column("ID", style="cyan")
    builtin_table.add_column("NAME", style="white")
    builtin_table.add_column("CATEGORY", style="magenta")
    builtin_table.add_column("SUB-AGENT", style="yellow", justify="right")
    builtin_table.add_column("STUDIO", style="dim")

    if builtin_agents:
        for agent, _ in builtin_agents:
            serial_str = str(agent.serial) if agent.serial is not None else "?"
            total_subs = _count_sub_agents_recursive(agent, agent_map)
            subs_count = str(total_subs) if total_subs > 0 else "-"
            builtin_table.add_row(
                serial_str,
                agent.id,
                agent.name,
                agent.category,
                subs_count,
                "-",
            )
    else:
        builtin_table.add_row("-", "[dim]No built-in agents[/dim]", "", "", "", "")

    console.print(builtin_table)

    # Local agents table
    console.print()
    local_table = Table(title="Your Agents", title_style="bold green")
    local_table.add_column("#", style="dim", justify="right")
    local_table.add_column("ID", style="cyan")
    local_table.add_column("NAME", style="white")
    local_table.add_column("CATEGORY", style="magenta")
    local_table.add_column("SUB-AGENT", style="yellow", justify="right")
    local_table.add_column("STUDIO", style="dim")

    if local_agents:
        for agent, _ in local_agents:
            serial_str = str(agent.serial) if agent.serial is not None else "?"
            total_subs = _count_sub_agents_recursive(agent, agent_map)
            subs_count = str(total_subs) if total_subs > 0 else "-"
            # Build Studio URL from platform_agent_id
            if agent.platform_agent_id:
                studio_url = f"{studio_base_url}{agent.platform_agent_id}"
            else:
                studio_url = "-"
            local_table.add_row(
                serial_str,
                agent.id,
                agent.name,
                agent.category,
                subs_count,
                studio_url,
            )
    else:
        local_table.add_row("-", "[dim]No local agents yet[/dim]", "", "", "", "")
        console.print(local_table)
        console.print("[dim]Run 'lk agent get <#> [new-id]' to clone a built-in agent[/dim]")
        return

    console.print(local_table)
