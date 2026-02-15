"""
Base adapter class for model-specific skill formatting.
"""

from abc import ABC, abstractmethod
from typing import Any
import json
from pathlib import Path


class BaseAdapter(ABC):
    """Base class for model-specific adapters."""

    def __init__(self, skill_data: dict[str, Any]):
        self.skill = skill_data
        self.id = skill_data.get("id", "")
        self.name = skill_data.get("name", "")
        self.prompt = skill_data.get("prompt", {})
        self.system_prompt = self.prompt.get("system", "")
        self.variables = self.prompt.get("variables", [])

    @abstractmethod
    def format_system_prompt(self) -> str:
        """Format the system prompt for the specific model."""
        pass

    @abstractmethod
    def create_message(self, user_input: str) -> list[dict[str, str]]:
        """Create a message array for the model API."""
        pass

    @abstractmethod
    def get_api_params(self) -> dict[str, Any]:
        """Get model-specific API parameters."""
        pass

    def substitute_variables(self, text: str, values: dict[str, str] | None = None) -> str:
        """Substitute variables in prompt text."""
        if values is None:
            values = {}

        result = text

        for var in self.variables:
            var_name = var["name"]
            default = var.get("default", "")
            value = values.get(var_name, default)

            # Replace ${Variable:Default} pattern
            result = result.replace(f"${{{var_name}:{default}}}", value)
            result = result.replace(f"${{{var_name}}}", value)
            # Replace {variable} pattern
            result = result.replace(f"{{{var_name}}}", value)

        return result

    def to_dict(self) -> dict[str, Any]:
        """Convert adapter output to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "system_prompt": self.format_system_prompt(),
            "variables": self.variables,
            "api_params": self.get_api_params(),
        }


def load_skill(skill_path: str | Path) -> dict[str, Any]:
    """Load a skill from a JSON file."""
    with open(skill_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_skills_from_directory(skills_dir: str | Path) -> list[dict[str, Any]]:
    """Load all skills from a directory."""
    skills_dir = Path(skills_dir)
    skills = []

    for json_file in skills_dir.rglob("*.json"):
        if json_file.name == "index.json":
            continue
        try:
            skills.append(load_skill(json_file))
        except Exception as e:
            print(f"Error loading {json_file}: {e}")

    return skills
