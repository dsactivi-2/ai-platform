"""Serial number management for agents."""

from pathlib import Path

from lyzr_kit.schemas.agent import Agent


def get_builtin_agent_by_serial(serial: int) -> Agent | None:
    """Get a built-in agent by serial number.

    Args:
        serial: Serial number (positive integer).

    Returns:
        Agent if found, None otherwise.
    """
    # Import here to avoid circular dependency
    from lyzr_kit.storage.manager import StorageManager

    storage = StorageManager()
    agents = storage.list_agents()

    for agent, source in agents:
        if source == "built-in" and agent.serial == serial:
            return agent

    return None


def get_local_agent_by_serial(serial: int) -> Agent | None:
    """Get a local agent by serial number.

    Args:
        serial: Serial number (positive integer).

    Returns:
        Agent if found, None otherwise.
    """
    # Import here to avoid circular dependency
    from lyzr_kit.storage.manager import StorageManager

    storage = StorageManager()
    agents = storage.list_agents()

    for agent, source in agents:
        if source == "local" and agent.serial == serial:
            return agent

    return None


def get_next_local_serial() -> int:
    """Get the next available serial number for local agents.

    Local agents use positive serial numbers starting from 1.
    Returns the maximum local serial + 1 (or 1 if no local agents exist).
    """
    # Import here to avoid circular dependency
    from lyzr_kit.storage.manager import StorageManager

    storage = StorageManager()
    local_dir = Path.cwd() / "agents"

    if not local_dir.exists():
        return 1

    max_serial = 0
    for yaml_file in storage._list_yaml_files(local_dir):
        agent = storage._load_agent(yaml_file)
        if agent and agent.serial is not None and agent.serial > max_serial:
            max_serial = agent.serial

    return max_serial + 1
