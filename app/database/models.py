"""
SQLAlchemy ORM models for the application.

Uses SQLAlchemy 2.0 style with declarative base and proper type hints.
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class PipelineParameter(Base):
    """
    ORM model for pipeline parameters stored in the database.

    Stores configuration parameters for data pipelines using JSON
    for flexible value storage.
    """

    __tablename__ = "pipeline_parameters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pipeline_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    parameter_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    parameter_value: Mapped[dict[str, Any] | list[Any] | str | int | float | bool] = (
        mapped_column(JSON, nullable=False)
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    def __repr__(self) -> str:
        """String representation of the parameter."""
        return (
            f"PipelineParameter(id={self.id}, "
            f"pipeline_name='{self.pipeline_name}', "
            f"parameter_key='{self.parameter_key}')"
        )
