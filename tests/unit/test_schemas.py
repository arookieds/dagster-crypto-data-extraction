"""
Unit tests for database schemas.
"""

import pytest
from pydantic import ValidationError

from app.database.schemas import (
    PipelineParameterBase,
    PipelineParameterUpdate,
)


def test_pipeline_parameter_base_valid():
    """Test that a valid PipelineParameterBase model is validated."""
    param = PipelineParameterBase(
        pipeline_name="test_pipeline",
        parameter_key="test_key",
        parameter_value="test_value",
    )
    assert param.pipeline_name == "test_pipeline"


def test_pipeline_parameter_base_invalid_pipeline_name():
    """Test that a long pipeline_name is invalid."""
    with pytest.raises(ValidationError):
        PipelineParameterBase(
            pipeline_name="a" * 256,
            parameter_key="test_key",
            parameter_value="test_value",
        )


def test_pipeline_parameter_update_valid():
    """Test that a valid PipelineParameterUpdate model is validated."""
    param = PipelineParameterUpdate(
        parameter_value="new_value",
        description="new description",
    )
    assert param.parameter_value == "new_value"
