"""
Unit tests for Dagster resources.
"""

from dagster_duckdb import DuckDBResource

from app.resources import get_data_storage_resource, get_duckdb_resource


def test_get_duckdb_resource():
    """Test that get_duckdb_resource returns a DuckDBResource."""
    resource = get_duckdb_resource()
    assert isinstance(resource, DuckDBResource)


def test_get_data_storage_resource():
    """Test that get_data_storage_resource returns a DuckDBResource."""
    resource = get_data_storage_resource()
    assert isinstance(resource, DuckDBResource)
