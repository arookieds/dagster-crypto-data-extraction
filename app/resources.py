"""
Dagster resources for multi-environment support.

Provides environment-aware resources for data storage:
- DuckDB resource for local development
- Note: PostgreSQL is handled directly by dlt, not as a Dagster resource
"""

from dagster_duckdb import DuckDBResource

from app.config import get_settings


def get_duckdb_resource() -> DuckDBResource:
    """
    Get DuckDB resource for local development.

    Returns:
        DuckDBResource: Configured DuckDB resource
    """
    settings = get_settings()
    return DuckDBResource(
        database=str(settings.duckdb_path),
    )


def get_data_storage_resource() -> DuckDBResource:
    """
    Get appropriate data storage resource based on environment.

    For local development, returns DuckDB resource.
    For production, dlt handles PostgreSQL directly (no resource needed).

    Returns:
        DuckDBResource for development, or DuckDBResource as placeholder for production
    """
    # Always return DuckDB resource for Dagster
    # PostgreSQL is handled by dlt directly via connection strings
    return get_duckdb_resource()
