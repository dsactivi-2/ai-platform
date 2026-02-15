"""Shared resolver utilities for agent commands."""

from lyzr_kit.commands._console import console
from lyzr_kit.commands.agent_list import list_agents
from lyzr_kit.storage import (
    StorageManager,
    get_builtin_agent_by_serial,
    get_local_agent_by_serial,
)


def resolve_builtin_agent_id(identifier: str, storage: StorageManager) -> str | None:
    """Resolve identifier to a built-in agent ID.

    For 'get' command - only looks up built-in agents.

    Args:
        identifier: Serial number or agent ID.
        storage: StorageManager instance.

    Returns:
        Resolved agent ID, or None if not found.
    """
    # Try as serial number first
    try:
        serial = int(identifier)
        agent = get_builtin_agent_by_serial(serial)
        if agent:
            return agent.id
        console.print(f"[red]Error: Built-in agent #{serial} not found.[/red]")
        console.print("[dim]Run 'lk agent ls' to see available built-in agents.[/dim]")
        console.print()
        list_agents()
        return None
    except ValueError:
        # Not a number, treat as agent ID
        return identifier


def resolve_local_agent_id(identifier: str, storage: StorageManager) -> str | None:
    """Resolve identifier to a local agent ID.

    For 'set' and 'chat' commands - only looks up local agents.

    Args:
        identifier: Serial number or agent ID.
        storage: StorageManager instance.

    Returns:
        Resolved agent ID, or None if not found.
    """
    # Try as serial number first
    try:
        serial = int(identifier)
        agent = get_local_agent_by_serial(serial)
        if agent:
            return agent.id
        console.print(f"[red]Error: Local agent #{serial} not found.[/red]")
        console.print("[dim]Run 'lk agent ls' to see your local agents.[/dim]")
        console.print()
        list_agents()
        return None
    except ValueError:
        # Not a number, treat as agent ID
        return identifier
