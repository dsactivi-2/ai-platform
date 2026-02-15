"""Tool schema definitions.

TODO: Full implementation planned for Phase 4.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Tool parameter definition."""

    name: str = Field(..., min_length=1, max_length=50, description="Parameter name")
    type: Literal["string", "number", "boolean", "array", "object"] = Field(
        ..., description="Parameter type"
    )
    required: bool = Field(default=True, description="Is parameter required")
    default: Any = Field(default=None, description="Default value")
    description: str = Field(..., description="Parameter description")


class ToolReturn(BaseModel):
    """Tool return field definition."""

    name: str = Field(..., description="Return field name")
    type: Literal["string", "number", "boolean", "array", "object"] = Field(
        ..., description="Return type"
    )
    description: str = Field(..., description="Return field description")


class Tool(BaseModel):
    """Tool entity definition."""

    id: str = Field(..., min_length=1, max_length=50, description="Unique identifier (snake_case)")
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: str = Field(..., min_length=1, max_length=1000, description="Tool description")

    owner: str | None = Field(default=None, description="Owner user/org ID")
    share: Literal["private", "org", "public"] = Field(
        default="private", description="Sharing level"
    )
    tags: list[str] = Field(default_factory=list, description="Searchable tags")

    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")

    is_active: bool = Field(default=False, description="Set to true by 'lk tool get'")
    endpoint: str | None = Field(default=None, description="Inference URL (populated by 'get')")

    parameters: list[ToolParameter] = Field(default_factory=list, description="Tool parameters")
    returns: list[ToolReturn] = Field(default_factory=list, description="Tool return fields")
