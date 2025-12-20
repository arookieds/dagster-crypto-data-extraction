"""
Unit tests for configuration module.

Tests settings validation, environment variable loading,
and multi-environment configuration.
"""

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_local_dev_mode(test_settings: Settings) -> None:
    """Test that settings default to local development mode (SQLite)."""
    assert test_settings.environment == "test"
    assert test_settings.use_postgres is False
    assert "sqlite:///" in test_settings.database_url
    assert test_settings.dlt_destination_type == "duckdb"


def test_settings_environment_checks(test_settings: Settings) -> None:
    """Test environment flag properties."""
    assert test_settings.is_test is True
    assert test_settings.is_production is False
    assert test_settings.is_development is False


def test_settings_default_values(test_settings: Settings) -> None:
    """Test that default values are applied correctly."""
    settings = test_settings
    assert settings.postgres_port == 5432
    assert settings.log_level == "DEBUG"
    assert settings.extraction_timeout == 300
    assert settings.max_retries == 3
    assert settings.environment == "test"


def test_settings_with_postgres_credentials() -> None:
    """Test that PostgreSQL is used when all credentials provided."""
    settings = Settings(
        postgres_host="localhost",
        postgres_user="user",
        postgres_password="password",
        postgres_db="db",
    )
    assert settings.use_postgres is True
    assert "postgresql://" in settings.database_url
    assert settings.dlt_destination_type == "postgres"


def test_settings_without_postgres_credentials() -> None:
    """Test that SQLite is used when PostgreSQL credentials not provided."""
    settings = Settings()
    assert settings.use_postgres is False
    assert "sqlite:///" in settings.database_url
    assert settings.dlt_destination_type == "duckdb"


def test_settings_password_validation() -> None:
    """Test that empty password raises validation error when provided."""
    with pytest.raises(ValidationError):
        Settings(
            postgres_host="localhost",
            postgres_user="user",
            postgres_password="",
            postgres_db="db",
        )


def test_settings_partial_postgres_credentials() -> None:
    """Test that partial PostgreSQL credentials result in SQLite."""
    settings = Settings(
        postgres_host="localhost",
        postgres_user="user",
        postgres_db="db",
    )
    assert settings.use_postgres is False


def test_settings_port_range_validation() -> None:
    """Test that invalid port raises validation error."""
    with pytest.raises(ValidationError):
        Settings(
            postgres_host="localhost",
            postgres_port=99999,
            postgres_user="user",
            postgres_password="password",
            postgres_db="db",
        )


def test_settings_environment_info() -> None:
    """Test environment info dictionary."""
    settings = Settings()
    info = settings.get_environment_info()

    assert "environment" in info
    assert "database" in info
    assert "dlt_destination" in info
    assert "data_storage" in info
    assert info["database"] == "SQLite"
    assert info["data_storage"] == "DuckDB"
