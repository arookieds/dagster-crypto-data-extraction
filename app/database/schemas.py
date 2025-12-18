"""
Pydantic v2 schemas for validation and serialization.

These models validate data going into and coming out of the database.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PipelineParameterBase(BaseModel):
    """Base schema for pipeline parameters."""

    pipeline_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name of the pipeline",
    )
    parameter_key: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Parameter key",
    )
    parameter_value: dict[str, Any] | list[Any] | str | int | float | bool = Field(
        ...,
        description="Parameter value (JSON-serializable)",
    )
    description: str | None = Field(
        default=None,
        description="Optional description of the parameter",
    )


class PipelineParameterUpdate(BaseModel):
    """Schema for updating a pipeline parameter."""

    parameter_value: dict[str, Any] | list[Any] | str | int | float | bool = Field(
        ...,
        description="New parameter value",
    )
    description: str | None = Field(
        default=None,
        description="Updated description",
    )


class PipelineParameterResponse(PipelineParameterBase):
    """Schema for pipeline parameter responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Parameter ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class ParameterValueResponse(BaseModel):
    """Schema for returning just a parameter value."""

    value: dict[str, Any] | list[Any] | str | int | float | bool = Field(
        ...,
        description="Parameter value",
    )
