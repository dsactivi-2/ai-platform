"""Agent rm (delete) command implementation."""

import typer

from lyzr_kit.commands._console import console
from lyzr_kit.commands._resolver import resolve_local_agent_id
from lyzr_kit.schemas.agent import Agent
from lyzr_kit.storage import StorageManager


def _collect_sub_agents_recursive(
    agent: Agent,
    storage: StorageManager,
    collected: set[str] | None = None,
) -> list[str]:
    """Recursively collect all sub-agent IDs that exist locally.

    Args:
        agent: The agent whose sub-agents to collect.
        storage: StorageManager instance.
        collected: Set of already collected IDs to avoid duplicates.

    Returns:
        List of sub-agent IDs in deletion order (deepest first).
    """
    if collected is None:
        collected = set()

    result: list[str] = []

    for sub_id in agent.sub_agents:
        if sub_id in collected:
            continue

        sub_agent = storage.get_agent(sub_id)
        if sub_agent and storage.agent_exists_local(sub_id):
            collected.add(sub_id)
            # Recursively collect this sub-agent's sub-agents first
            result.extend(_collect_sub_agents_recursive(sub_agent, storage, collected))
            result.append(sub_id)

    return result


def rm_agent(identifier: str, force: bool = False, tree: bool = False) -> None:
    """Delete a local agent.

    Args:
        identifier: Agent ID or serial number.
        force: If True, remove from parent agents' sub_agents arrays first.
        tree: If True, also delete all sub-agents recursively.
    """
    storage = StorageManager()

    # Resolve identifier (could be serial number or agent ID)
    agent_id = resolve_local_agent_id(identifier, storage)
    if agent_id is None:
        raise typer.Exit(1)

    # Load the agent to check sub-agents
    agent = storage.get_agent(agent_id)
    if not agent:
        console.print(f"[red]Error: Agent '{agent_id}' not found[/red]")
        raise typer.Exit(1)

    # Check if agent has sub-agents
    if agent.sub_agents and not tree:
        # Get locally existing sub-agents
        local_subs = [s for s in agent.sub_agents if storage.agent_exists_local(s)]
        if local_subs:
            console.print(f"\nAgent '[bold]{agent_id}[/bold]' has {len(local_subs)} sub-agent(s):")
            for sub_id in local_subs:
                console.print(f"  • {sub_id}")
            console.print()
            console.print("[dim]Delete sub-agents too? Use --tree flag.[/dim]")
            console.print()

    # Check if agent is used as a sub-agent by any other agent
    using_agents = storage.find_agents_using_subagent(agent_id)
    if using_agents:
        if force:
            # Remove from parent agents' sub_agents arrays
            console.print(f"[yellow]Removing '{agent_id}' from parent agents...[/yellow]")
            for parent in using_agents:
                parent.sub_agents = [s for s in parent.sub_agents if s != agent_id]
                storage.save_agent(parent)
                console.print(f"  [dim]Updated:[/dim] {parent.id}")
        else:
            console.print(f"[red]Error: Cannot delete '{agent_id}'[/red]")
            console.print("")
            console.print("[yellow]This agent is used as a sub-agent by:[/yellow]")
            for parent in using_agents:
                console.print(f"  • {parent.id}")
            console.print("")
            console.print("[dim]Use --force to remove from parent agents and delete.[/dim]")
            raise typer.Exit(1)

    # Collect agents to delete
    agents_to_delete: list[str] = []

    if tree and agent.sub_agents:
        # Collect all sub-agents recursively (deepest first)
        agents_to_delete = _collect_sub_agents_recursive(agent, storage)

    # Add the main agent last
    agents_to_delete.append(agent_id)

    # Delete agents
    deleted_count = 0
    for aid in agents_to_delete:
        # Before deleting sub-agents, remove from parent's sub_agents array
        if aid != agent_id:
            parent_agents = storage.find_agents_using_subagent(aid)
            for parent in parent_agents:
                # Only update if parent is in our deletion list (will be deleted anyway)
                # or if the parent is being deleted now
                if parent.id in agents_to_delete:
                    continue
                parent.sub_agents = [s for s in parent.sub_agents if s != aid]
                storage.save_agent(parent)

        deleted = storage.delete_agent(aid)
        if deleted:
            if aid == agent_id:
                # Main agent - will show success at end
                deleted_count += 1
            else:
                console.print(f"  [green]✓[/green] {aid}")
                deleted_count += 1

    if deleted_count > 1:
        console.print(f"\n[green]{deleted_count} agent(s) deleted successfully[/green]")
    elif deleted_count == 1:
        console.print(f"[green]Agent '{agent_id}' deleted successfully[/green]")
    else:
        console.print(f"[red]Error: Agent '{agent_id}' not found[/red]")
        raise typer.Exit(1)
