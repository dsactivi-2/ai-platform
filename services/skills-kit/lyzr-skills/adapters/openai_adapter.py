"""
OpenAI adapter for Lyzr Skills.

Formats skills for use with OpenAI API (GPT-4, GPT-4o, etc.).
"""

from typing import Any
from .base import BaseAdapter


class OpenAIAdapter(BaseAdapter):
    """Adapter for OpenAI models."""

    DEFAULT_MODEL = "gpt-4o"
    MAX_TOKENS = 4096

    def format_system_prompt(self) -> str:
        """Format system prompt for OpenAI."""
        return self.system_prompt

    def create_message(
        self,
        user_input: str,
        variable_values: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """
        Create a message payload for OpenAI API.

        Args:
            user_input: The user's message
            variable_values: Values to substitute for prompt variables

        Returns:
            Dict ready for OpenAI API call
        """
        system = self.substitute_variables(self.system_prompt, variable_values)

        return {
            "model": self.DEFAULT_MODEL,
            "max_tokens": self.MAX_TOKENS,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_input}
            ]
        }

    def get_api_params(self) -> dict[str, Any]:
        """Get OpenAI-specific API parameters."""
        return {
            "model": self.DEFAULT_MODEL,
            "max_tokens": self.MAX_TOKENS,
            "temperature": 0.7,
            "top_p": 0.9,
            "frequency_penalty": 0,
            "presence_penalty": 0,
        }

    def to_openai_format(self, variable_values: dict[str, str] | None = None) -> dict[str, Any]:
        """
        Export skill in OpenAI API format.

        Returns:
            Dict with messages and default parameters
        """
        system = self.substitute_variables(self.system_prompt, variable_values)

        return {
            "skill_id": self.id,
            "skill_name": self.name,
            "openai_config": {
                "model": self.DEFAULT_MODEL,
                "max_tokens": self.MAX_TOKENS,
                "messages": [
                    {"role": "system", "content": system}
                ]
            },
            "variables": self.variables,
            "usage_example": {
                "python": f'''
from openai import OpenAI

client = OpenAI()

response = client.chat.completions.create(
    model="{self.DEFAULT_MODEL}",
    max_tokens={self.MAX_TOKENS},
    messages=[
        {{"role": "system", "content": """{system[:100]}..."""}},
        {{"role": "user", "content": "Your message here"}}
    ]
)
print(response.choices[0].message.content)
'''
            }
        }

    def to_assistant_format(self, variable_values: dict[str, str] | None = None) -> dict[str, Any]:
        """
        Export skill in OpenAI Assistants API format.

        Returns:
            Dict for creating an OpenAI Assistant
        """
        system = self.substitute_variables(self.system_prompt, variable_values)

        return {
            "skill_id": self.id,
            "skill_name": self.name,
            "assistant_config": {
                "name": self.name,
                "instructions": system,
                "model": self.DEFAULT_MODEL,
            },
            "variables": self.variables,
        }


def create_openai_skill(skill_data: dict[str, Any]) -> OpenAIAdapter:
    """Factory function to create an OpenAI adapter from skill data."""
    return OpenAIAdapter(skill_data)
