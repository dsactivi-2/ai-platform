"""
Gemini (Google) adapter for Lyzr Skills.

Formats skills for use with Google Gemini API.
"""

from typing import Any
from .base import BaseAdapter


class GeminiAdapter(BaseAdapter):
    """Adapter for Google Gemini models."""

    DEFAULT_MODEL = "gemini-2.0-flash"
    MAX_OUTPUT_TOKENS = 4096

    def format_system_prompt(self) -> str:
        """Format system prompt for Gemini."""
        return self.system_prompt

    def create_message(
        self,
        user_input: str,
        variable_values: dict[str, str] | None = None
    ) -> dict[str, Any]:
        """
        Create a message payload for Gemini API.

        Args:
            user_input: The user's message
            variable_values: Values to substitute for prompt variables

        Returns:
            Dict ready for Gemini API call
        """
        system = self.substitute_variables(self.system_prompt, variable_values)

        return {
            "model": self.DEFAULT_MODEL,
            "system_instruction": system,
            "contents": [
                {"role": "user", "parts": [{"text": user_input}]}
            ],
            "generation_config": {
                "max_output_tokens": self.MAX_OUTPUT_TOKENS,
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }

    def get_api_params(self) -> dict[str, Any]:
        """Get Gemini-specific API parameters."""
        return {
            "model": self.DEFAULT_MODEL,
            "generation_config": {
                "max_output_tokens": self.MAX_OUTPUT_TOKENS,
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
            }
        }

    def to_gemini_format(self, variable_values: dict[str, str] | None = None) -> dict[str, Any]:
        """
        Export skill in Google Gemini API format.

        Returns:
            Dict with system instruction and generation config
        """
        system = self.substitute_variables(self.system_prompt, variable_values)

        return {
            "skill_id": self.id,
            "skill_name": self.name,
            "gemini_config": {
                "model": self.DEFAULT_MODEL,
                "system_instruction": system,
                "generation_config": {
                    "max_output_tokens": self.MAX_OUTPUT_TOKENS,
                    "temperature": 0.7,
                    "top_p": 0.9,
                }
            },
            "variables": self.variables,
            "usage_example": {
                "python": f'''
import google.generativeai as genai

genai.configure(api_key="YOUR_API_KEY")

model = genai.GenerativeModel(
    model_name="{self.DEFAULT_MODEL}",
    system_instruction="""{system[:100]}..."""
)

response = model.generate_content("Your message here")
print(response.text)
'''
            }
        }

    def to_vertex_format(self, variable_values: dict[str, str] | None = None) -> dict[str, Any]:
        """
        Export skill in Vertex AI format (for enterprise use).

        Returns:
            Dict for Vertex AI Generative AI
        """
        system = self.substitute_variables(self.system_prompt, variable_values)

        return {
            "skill_id": self.id,
            "skill_name": self.name,
            "vertex_config": {
                "model": self.DEFAULT_MODEL,
                "system_instruction": [system],
                "generation_config": {
                    "max_output_tokens": self.MAX_OUTPUT_TOKENS,
                    "temperature": 0.7,
                    "top_p": 0.9,
                }
            },
            "variables": self.variables,
        }


def create_gemini_skill(skill_data: dict[str, Any]) -> GeminiAdapter:
    """Factory function to create a Gemini adapter from skill data."""
    return GeminiAdapter(skill_data)
