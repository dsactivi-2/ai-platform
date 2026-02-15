"""
Lyzr Skills Adapters

Model-specific adapters for converting skills to different LLM formats.
"""

from .base import BaseAdapter, load_skill, load_skills_from_directory
from .claude_adapter import ClaudeAdapter, create_claude_skill
from .openai_adapter import OpenAIAdapter, create_openai_skill
from .gemini_adapter import GeminiAdapter, create_gemini_skill

__all__ = [
    "BaseAdapter",
    "load_skill",
    "load_skills_from_directory",
    "ClaudeAdapter",
    "create_claude_skill",
    "OpenAIAdapter",
    "create_openai_skill",
    "GeminiAdapter",
    "create_gemini_skill",
]


def get_adapter(skill_data: dict, model_type: str) -> BaseAdapter:
    """
    Factory function to get the appropriate adapter for a model type.

    Args:
        skill_data: The skill JSON data
        model_type: One of 'claude', 'openai', 'gemini'

    Returns:
        Appropriate adapter instance
    """
    adapters = {
        "claude": ClaudeAdapter,
        "anthropic": ClaudeAdapter,
        "openai": OpenAIAdapter,
        "gpt": OpenAIAdapter,
        "gemini": GeminiAdapter,
        "google": GeminiAdapter,
    }

    adapter_class = adapters.get(model_type.lower())
    if not adapter_class:
        raise ValueError(f"Unknown model type: {model_type}. Supported: {list(adapters.keys())}")

    return adapter_class(skill_data)
