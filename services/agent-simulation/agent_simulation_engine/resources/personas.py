"""
Personas resource for the Agent Simulation Engine SDK.
"""

from typing import List, TYPE_CHECKING

from ..models import (
    Persona,
    PersonasResponse,
    DeleteResponse,
)

if TYPE_CHECKING:
    from ..client import ASIMEngine


class Personas:
    """
    Manage personas (user archetypes) for agent testing.

    Usage:
        # Add personas manually
        personas = client.personas.create(
            environment_id,
            personas=[
                {"name": "Beginner", "description": "New user unfamiliar with the product"},
                {"name": "Expert", "description": "Technical user with deep knowledge"},
            ]
        )

        # Generate personas using AI
        personas = client.personas.generate(environment_id)

        # List all personas
        personas = client.personas.list(environment_id)

        # Delete a persona
        client.personas.delete(environment_id, persona_id)
    """

    def __init__(self, engine: "ASIMEngine"):
        self._engine = engine

    def create(
        self,
        environment_id: str,
        personas: List[dict],
    ) -> PersonasResponse:
        """
        Add multiple personas to an environment.

        Args:
            environment_id: The environment ID
            personas: List of persona dicts with 'name' and 'description'

        Returns:
            PersonasResponse with list of created personas and count
        """
        response = self._engine.post(
            f"/{environment_id}/personas",
            json={"personas": personas}
        )
        return PersonasResponse(
            personas=[Persona(**p) for p in response.get("personas", [])],
            count=response.get("count", 0)
        )

    def list(self, environment_id: str) -> PersonasResponse:
        """
        Get all personas for an environment.

        Args:
            environment_id: The environment ID

        Returns:
            PersonasResponse with list of personas and count
        """
        response = self._engine.get(f"/{environment_id}/personas")
        return PersonasResponse(
            personas=[Persona(**p) for p in response.get("personas", [])],
            count=response.get("count", 0)
        )

    def generate(self, environment_id: str) -> PersonasResponse:
        """
        Generate personas using the AI persona generator agent.

        Args:
            environment_id: The environment ID

        Returns:
            PersonasResponse with list of generated personas
        """
        response = self._engine.post(f"/{environment_id}/personas/generate")
        return PersonasResponse(
            personas=[Persona(**p) for p in response.get("personas", [])],
            count=len(response.get("personas", []))
        )

    def delete(self, environment_id: str, persona_id: str) -> DeleteResponse:
        """
        Delete a persona from an environment.

        Args:
            environment_id: The environment ID
            persona_id: The persona ID to delete

        Returns:
            DeleteResponse with success message
        """
        response = self._engine.delete(f"/{environment_id}/personas/{persona_id}")
        return DeleteResponse(**response)
