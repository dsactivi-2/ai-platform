"""Agent schema definitions."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """LLM model configuration."""

    provider: str = Field(..., description="LLM provider ID")
    name: str = Field(..., description="Model name")
    credential_id: str = Field(..., description="Credential ID")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Nucleus sampling")
    max_tokens: int = Field(default=4096, gt=0, description="Max response tokens")


class AgentConfig(BaseModel):
    """Agent behavior configuration."""

    role: str = Field(default="assistant", description="Agent's role identity")
    goal: str = Field(default="", description="Agent's primary goal")
    instructions: str = Field(default="", description="System instructions/prompt")


class Agent(BaseModel):
    """Agent entity definition."""

    # Serial number for quick reference (DO NOT MODIFY for cloned agents)
    serial: int | None = Field(default=None, description="Serial number for quick reference")

    # Meta
    id: str = Field(..., min_length=3, max_length=50, description="Unique identifier (kebab-case)")
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: str = Field(default="", max_length=1000, description="Agent description")
    category: Literal["chat", "qa"] = Field(..., description="Agent category")

    owner: str | None = Field(default=None, description="Owner user/org ID")
    share: Literal["private", "org", "public"] = Field(
        default="private", description="Sharing level"
    )
    tags: list[str] = Field(default_factory=list, description="Searchable tags")

    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")

    is_active: bool = Field(default=False, description="Set to true by 'lk agent get'")
    endpoint: str | None = Field(default=None, description="Inference URL (populated by 'get')")

    # Platform IDs (set after agent creation on platform)
    platform_agent_id: str | None = Field(default=None, description="Agent ID on Lyzr platform")
    platform_env_id: str | None = Field(default=None, description="Environment ID on Lyzr platform")
    marketplace_app_id: str | None = Field(
        default=None, description="Marketplace App ID for Studio chat"
    )

    # Model
    model: ModelConfig = Field(..., description="LLM model configuration")

    # Config
    config: AgentConfig = Field(
        default_factory=AgentConfig, description="Agent behavior configuration"
    )

    # References
    vars: list[str] = Field(default_factory=list, description="Variable names to load from .env")
    tools: list[str] = Field(default_factory=list, description="Tool IDs")
    sub_agents: list[str] = Field(default_factory=list, description="Sub-agent IDs for delegation")
    features: list[str] = Field(default_factory=list, description="Feature IDs")
