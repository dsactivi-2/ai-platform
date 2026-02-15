"""
Claude (Anthropic) adapter for Lyzr Skills.

Formats skills for use with Claude API.
"""

from typing import Any
from .base import BaseAdapter


class ClaudeAdapter(BaseAdapter):
    """Adapter for Anthropic Claude models."""

    DEFAULT_MODEL = "claude-sonnet-4-20250514"
    MAX_TOKENS = 4096

    def format_system_prompt(self) -> str:
        """Format system prompt for Claude."""
        # Claude handles system prompts directly
        return self.system_prompt

    def create_message(
        self,
        user_input: str,
        variable_values: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """
        Create a message payload for Claude API.

        Args:
            user_input: The user's message
            variable_values: Values to substitute for prompt variables

        Returns:
            Dict ready for Anthropic API call
        """
        system = self.substitute_variables(self.system_prompt, variable_values)

        return {
            "model": self.DEFAULT_MODEL,
            "max_tokens": self.MAX_TOKENS,
            "system": system,
            "messages": [
                {"role": "user", "content": user_input}
            ]
        }

    def get_api_params(self) -> dict[str, Any]:
        """Get Claude-specific API parameters."""
        return {
            "model": self.DEFAULT_MODEL,
            "max_tokens": self.MAX_TOKENS,
            "temperature": 0.7,
            "top_p": 0.9,
        }

    def to_anthropic_format(self, variable_values: dict[str, str] | None = None) -> dict[str, Any]:
        """
        Export skill in Anthropic API format.

        Returns:
            Dict with system prompt and default parameters
        """
        system = self.substitute_variables(self.system_prompt, variable_values)

        return {
            "skill_id": self.id,
            "skill_name": self.name,
            "anthropic_config": {
                "model": self.DEFAULT_MODEL,
                "max_tokens": self.MAX_TOKENS,
                "system": system,
            },
            "variables": self.variables,
            "usage_example": {
                "python": f'''
from anthropic import Anthropic

client = Anthropic()

message = client.messages.create(
    model="{self.DEFAULT_MODEL}",
    max_tokens={self.MAX_TOKENS},
    system="""{system[:100]}...""",
    messages=[
        {{"role": "user", "content": "Your message here"}}
    ]
)
print(message.content[0].text)
'''
            }
        }


def create_claude_skill(skill_data: dict[str, Any]) -> ClaudeAdapter:
    """Factory function to create a Claude adapter from skill data."""
    return ClaudeAdapter(skill_data)
