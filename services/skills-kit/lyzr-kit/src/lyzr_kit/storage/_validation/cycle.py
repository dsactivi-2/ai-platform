"""Cycle detection for sub-agent relationships."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lyzr_kit.storage.manager import StorageManager


class CycleDetector:
    """Detects circular dependencies in sub-agent graph using DFS."""

    def __init__(self, storage: StorageManager):
        """Initialize the cycle detector.

        Args:
            storage: StorageManager instance to load agents.
        """
        self.storage = storage

    def detect(
        self,
        agent_id: str,
        sub_agents: list[str],
        visiting: set[str] | None = None,
        path: list[str] | None = None,
    ) -> list[str] | None:
        """Detect if sub_agents would create a cycle with agent_id.

        Uses DFS to traverse sub-agent relationships and detect cycles.

        Args:
            agent_id: The agent being validated.
            sub_agents: The sub-agent IDs to check.
            visiting: Set of agent IDs currently in the DFS path (internal).
            path: Current traversal path for error reporting (internal).

        Returns:
            The cycle path if found (e.g., ["A", "B", "C", "A"]), None if acyclic.
        """
        if visiting is None:
            visiting = {agent_id}
        if path is None:
            path = [agent_id]

        for sub_id in sub_agents:
            # Cycle detected - we're revisiting an ancestor
            if sub_id in visiting:
                return path + [sub_id]

            # Load sub-agent to check its sub-agents
            sub_agent = self.storage.get_agent(sub_id)
            if sub_agent and sub_agent.sub_agents:
                # Add to visiting set for this branch
                visiting.add(sub_id)
                cycle = self.detect(
                    sub_id,
                    sub_agent.sub_agents,
                    visiting,
                    path + [sub_id],
                )
                if cycle:
                    return cycle
                # Remove from visiting when backtracking
                visiting.discard(sub_id)

        return None


def detect_cycle(
    agent_id: str,
    sub_agents: list[str],
    storage: StorageManager,
    visiting: set[str] | None = None,
    path: list[str] | None = None,
) -> list[str] | None:
    """Detect if sub_agents would create a cycle with agent_id.

    This is a convenience function that creates a CycleDetector and calls detect().

    Args:
        agent_id: The agent being validated.
        sub_agents: The sub-agent IDs to check.
        storage: StorageManager instance to load agents.
        visiting: Set of agent IDs currently in the DFS path (internal).
        path: Current traversal path for error reporting (internal).

    Returns:
        The cycle path if found (e.g., ["A", "B", "C", "A"]), None if acyclic.
    """
    detector = CycleDetector(storage)
    return detector.detect(agent_id, sub_agents, visiting, path)


def validate_sub_agents(sub_agents: list[str], storage: StorageManager) -> list[str]:
    """Validate that all sub-agent IDs exist in local agents.

    Args:
        sub_agents: List of sub-agent IDs to validate.
        storage: StorageManager instance to check agent existence.

    Returns:
        List of missing agent IDs (empty if all valid).
    """
    if not sub_agents:
        return []

    missing: list[str] = []
    for agent_id in sub_agents:
        if not storage.agent_exists_local(agent_id):
            missing.append(agent_id)

    return missing
