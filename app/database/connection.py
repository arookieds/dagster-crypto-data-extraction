"""
Database connection management with multi-environment support.

Supports both SQLite (development) and PostgreSQL (production) using
SQLAlchemy 2.0 style with proper ORM integration.
"""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database.models import Base
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _enable_sqlite_foreign_keys(dbapi_conn: any, _connection_record: any) -> None:
    """
    Enable foreign key constraints for SQLite.

    SQLAlchemy event handler to enable FK support in SQLite.
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class DatabaseConnection:
    """
    Manages database connections with multi-environment support.

    Automatically uses SQLite for development and PostgreSQL for production
    based on configuration. Provides SQLAlchemy ORM sessions.
    """

    def __init__(self) -> None:
        """Initialize database connection manager."""
        self.settings = get_settings()
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None

        # Log environment info
        env_info = self.settings.get_environment_info()
        logger.info("Initializing database connection", **env_info)

    def _get_engine(self) -> Engine:
        """
        Get or create SQLAlchemy engine.

        Returns:
            Engine: SQLAlchemy database engine configured for the environment
        """
        if self._engine is None:
            database_url = self.settings.database_url

            logger.info(
                "Creating SQLAlchemy engine",
                database_type="PostgreSQL" if self.settings.use_postgres else "SQLite",
            )

            # Create engine with appropriate configuration
            if self.settings.use_postgres:
                # PostgreSQL configuration
                self._engine = create_engine(
                    database_url,
                    pool_pre_ping=True,
                    pool_size=5,
                    max_overflow=10,
                    echo=self.settings.is_development,
                )
            else:
                # SQLite configuration
                self._engine = create_engine(
                    database_url,
                    echo=self.settings.is_development,
                    # SQLite-specific: enable write-ahead logging for better concurrency
                    connect_args={"check_same_thread": False},
                )
                # Enable foreign keys for SQLite
                event.listen(self._engine, "connect", _enable_sqlite_foreign_keys)

        return self._engine

    def _get_session_factory(self) -> sessionmaker[Session]:
        """
        Get or create SQLAlchemy session factory.

        Returns:
            sessionmaker: SQLAlchemy session factory
        """
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self._get_engine(),
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,  # Keep objects accessible after commit
            )
        return self._session_factory

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Get a SQLAlchemy session with automatic cleanup.

        Context manager that handles session lifecycle, commit/rollback,
        and proper resource cleanup.

        Yields:
            Session: SQLAlchemy ORM session

        Example:
            with db.get_session() as session:
                param = session.query(PipelineParameter).first()
                session.add(new_param)
                session.commit()
        """
        session_factory = self._get_session_factory()
        session = session_factory()

        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("Database session operation failed", error=str(e))
            raise
        finally:
            session.close()

    def create_tables(self) -> None:
        """
        Create all database tables defined in the ORM models.

        Uses SQLAlchemy metadata to create tables. Safe to call multiple
        times as it only creates missing tables.
        """
        engine = self._get_engine()
        logger.info("Creating database tables")
        Base.metadata.create_all(engine)
        logger.info("Database tables ready")

    def drop_tables(self) -> None:
        """
        Drop all database tables.

        WARNING: This will delete all data! Only use in development/testing.
        """
        if self.settings.is_production:
            raise RuntimeError("Cannot drop tables in production environment")

        engine = self._get_engine()
        logger.warning("Dropping all database tables")
        Base.metadata.drop_all(engine)
        logger.info("All tables dropped")

    def close(self) -> None:
        """
        Close all database connections and cleanup resources.

        Should be called when shutting down the application.
        """
        if self._engine is not None:
            logger.info("Disposing SQLAlchemy engine")
            self._engine.dispose()
            self._engine = None

        self._session_factory = None

    def test_connection(self) -> bool:
        """
        Test database connectivity.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with self.get_session() as session:
                # Execute a simple query to test connectivity
                session.execute("SELECT 1")
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error("Database connection test failed", error=str(e))
            return False

    def get_engine(self) -> Engine:
        """
        Get the SQLAlchemy engine.

        Public method to access engine for advanced use cases.

        Returns:
            Engine: SQLAlchemy engine
        """
        return self._get_engine()


# Global database connection instance
_db_connection: DatabaseConnection | None = None


def get_db_connection() -> DatabaseConnection:
    """
    Get global database connection instance.

    Returns:
        DatabaseConnection: Singleton database connection manager
    """
    global _db_connection
    if _db_connection is None:
        _db_connection = DatabaseConnection()
    return _db_connection


def initialize_database() -> None:
    """
    Initialize database by creating all tables.

    Convenience function for application startup.
    """
    db = get_db_connection()
    db.create_tables()
