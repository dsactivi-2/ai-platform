"""Agent tree command implementation - show dependency graph."""

import typer
from rich.tree import Tree

from lyzr_kit.commands._console import console
from lyzr_kit.commands._resolver import resolve_local_agent_id
from lyzr_kit.schemas.agent import Agent
from lyzr_kit.storage import StorageManager


def _build_agent_tree(
    agent: Agent,
    storage: StorageManager,
    visited: set[str] | None = None,
) -> Tree:
    """Build a Rich Tree for an agent and its sub-agents.

    Args:
        agent: The agent to build tree for.
        storage: StorageManager instance.
        visited: Set of visited agent IDs to detect cycles.

    Returns:
        Rich Tree object.
    """
    if visited is None:
        visited = set()

    # Create tree node
    tree = Tree(f"[bold cyan]{agent.id}[/bold cyan]")

    if agent.id in visited:
        tree.add("[dim](circular reference)[/dim]")
        return tree

    visited.add(agent.id)

    # Add sub-agents
    for sub_id in agent.sub_agents:
        sub_agent = storage.get_agent(sub_id)
        if sub_agent:
            subtree = _build_agent_tree(sub_agent, storage, visited.copy())
            tree.add(subtree)
        else:
            tree.add(f"[red]{sub_id}[/red] [dim](missing)[/dim]")

    return tree


def tree_agent(identifier: str | None = None) -> None:
    """Show dependency tree for agent(s).

    Args:
        identifier: Optional agent ID or serial number. If None, shows all local agents.
    """
    storage = StorageManager()

    if identifier:
        # Show tree for specific agent
        agent_id = resolve_local_agent_id(identifier, storage)
        if agent_id is None:
            raise typer.Exit(1)

        agent = storage.get_agent(agent_id)
        if not agent:
            console.print(f"[red]Error: Agent '{agent_id}' not found[/red]")
            raise typer.Exit(1)

        tree = _build_agent_tree(agent, storage)
        console.print()
        console.print(tree)
        console.print()
    else:
        # Show trees for all local agents that are "roots" (not sub-agents of others)
        local_agents = storage.list_local_agents()

        if not local_agents:
            console.print("[dim]No local agents found.[/dim]")
            console.print("[dim]Run 'lk agent get' to create one.[/dim]")
            return

        # Find all agent IDs that are sub-agents of other agents
        all_sub_agent_ids: set[str] = set()
        for agent in local_agents:
            all_sub_agent_ids.update(agent.sub_agents)

        # Root agents are those not used as sub-agents
        root_agents = [a for a in local_agents if a.id not in all_sub_agent_ids]

        # If no root agents, show all (might have orphaned sub-agents)
        if not root_agents:
            root_agents = local_agents

        console.print()
        for agent in root_agents:
            tree = _build_agent_tree(agent, storage)
            console.print(tree)
            console.print()
