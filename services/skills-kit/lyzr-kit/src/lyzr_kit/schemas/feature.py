"""Feature schema definitions.

TODO: Full implementation planned for Phase 5.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class Feature(BaseModel):
    """Feature entity definition."""

    id: str = Field(..., min_length=1, max_length=50, description="Unique identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    description: str = Field(..., min_length=1, max_length=1000, description="Feature description")
    category: Literal["context", "guard", "policy"] = Field(..., description="Feature category")

    owner: str | None = Field(default=None, description="Owner user/org ID")
    share: Literal["private", "org", "public"] = Field(
        default="private", description="Sharing level"
    )
    tags: list[str] = Field(default_factory=list, description="Searchable tags")

    created_at: datetime | None = Field(default=None, description="Creation timestamp")
    updated_at: datetime | None = Field(default=None, description="Last update timestamp")

    is_active: bool = Field(default=False, description="Set to true by 'lk feature get'")
    endpoint: str | None = Field(default=None, description="Inference URL (populated by 'get')")

    config: dict[str, Any] = Field(
        default_factory=dict, description="Feature-specific configuration"
    )
