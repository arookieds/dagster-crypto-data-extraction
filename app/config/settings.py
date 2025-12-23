"""
Application settings and configuration management.

Uses pydantic-settings for type-safe configuration with multi-environment support:
- Development: SQLite + DuckDB
- Production: PostgreSQL for everything
"""

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Automatically detects environment and configures appropriate database
    backends (SQLite/DuckDB for dev, PostgreSQL for prod).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Environment
    environment: Literal["development", "production", "test"] = Field(
        default="development",
        description="Application environment",
    )

    # PostgreSQL Configuration (optional - for production)
    postgres_host: str | None = Field(
        default=None,
        description="PostgreSQL host address (if not set, uses SQLite)",
    )
    postgres_port: int = Field(
        default=5432,
        description="PostgreSQL port",
        ge=1,
        le=65535,
    )
    postgres_user: str | None = Field(
        default=None,
        description="PostgreSQL username",
    )
    postgres_password: str | None = Field(
        default=None,
        description="PostgreSQL password",
    )
    postgres_db: str | None = Field(
        default=None,
        description="PostgreSQL database name",
    )

    # S3/MinIO Configuration (optional)
    s3_bucket_name: str | None = Field(
        default=None,
        description="S3 bucket name for raw data storage",
    )
    s3_endpoint_url: str | None = Field(
        default=None,
        description="S3 endpoint URL (for MinIO)",
    )
    s3_access_key_id: str | None = Field(
        default=None,
        description="S3 access key ID",
    )
    s3_secret_access_key: str | None = Field(
        default=None,
        description="S3 secret access key",
    )

    # Local Development Paths
    data_dir: Path = Field(
        default=Path(".dagster_data"),
        description="Directory for local data storage (SQLite, DuckDB)",
    )

    # Application Settings
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )

    # Data Extraction Settings
    extraction_timeout: int = Field(
        default=300,
        description="Timeout for data extraction in seconds",
        ge=1,
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retries for failed operations",
        ge=0,
    )
    retry_delay: int = Field(
        default=5,
        description="Delay between retries in seconds",
        ge=1,
    )

    # DLT Settings
    dlt_pipeline_name: str = Field(
        default="crypto_data_extraction",
        description="DLT pipeline name",
    )

    @field_validator("postgres_password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        """Ensure password is not empty if provided."""
        if v is not None and v.strip() == "":
            raise ValueError("PostgreSQL password cannot be empty")
        return v

    @property
    def use_postgres(self) -> bool:
        """
        Determine if PostgreSQL should be used.

        Returns True if all PostgreSQL credentials are provided, False otherwise.
        """
        return all(
            [
                self.postgres_host,
                self.postgres_user,
                self.postgres_password,
                self.postgres_db,
            ]
        )

    @property
    def use_s3(self) -> bool:
        """
        Determine if S3 should be used for data storage.

        Returns True if an S3 bucket name is provided.
        """
        return self.s3_bucket_name is not None

    @property
    def database_url(self) -> str:
        """
        Construct database URL for parameter storage.

        Returns PostgreSQL URL if credentials provided, otherwise SQLite URL.
        """
        if self.use_postgres:
            return (
                f"postgresql://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        else:
            # Use SQLite for local development
            self.data_dir.mkdir(parents=True, exist_ok=True)
            db_path = self.data_dir / "parameters.db"
            return f"sqlite:///{db_path}"







    @property
    def duckdb_path(self) -> Path:
        """Get DuckDB database file path for local development."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.data_dir / "crypto_data.duckdb"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    @property
    def is_test(self) -> bool:
        """Check if running in test environment."""
        return self.environment == "test"

    @property
    def dlt_destination_type(self) -> Literal["postgres", "duckdb", "filesystem"]:
        """
        Determine dlt destination based on environment.
        """
        if self.use_s3:
            return "filesystem"
        if self.use_postgres:
            return "postgres"
        return "duckdb"

    def get_environment_info(self) -> dict[str, str]:
        """
        Get environment configuration summary for logging.
        """
        data_storage = "S3" if self.use_s3 else "PostgreSQL" if self.use_postgres else "DuckDB"
        return {
            "environment": self.environment,
            "database": "PostgreSQL" if self.use_postgres else "SQLite",
            "data_storage": data_storage,
            "log_level": self.log_level,
        }


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns cached settings to avoid re-reading environment variables
    on every call. Clear cache by calling get_settings.cache_clear().

    Returns:
        Settings: Application settings instance
    """
    return Settings()
