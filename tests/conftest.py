"""
Pytest configuration and fixtures for the test suite.

Provides common fixtures and test configuration for all tests
with support for the new ORM architecture.
"""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings, get_settings
from app.database.connection import DatabaseConnection
from app.database.models import Base


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """
    Provide test settings configured for SQLite (no PostgreSQL required).

    Returns:
        Settings configured for testing with SQLite
    """
    # Clear any existing environment variables that would trigger PostgreSQL
    for key in ["POSTGRES_HOST", "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB"]:
        os.environ.pop(key, None)

    os.environ["ENVIRONMENT"] = "test"
    os.environ["LOG_LEVEL"] = "DEBUG"

    # Clear cache and get fresh settings
    get_settings.cache_clear()
    settings = get_settings()

    # Verify we're using SQLite for tests
    assert not settings.use_postgres, "Tests should use SQLite, not PostgreSQL"

    return settings


@pytest.fixture
def temp_test_db() -> Generator[Path, None, None]:
    """
    Provide a temporary database file for testing.

    Yields:
        Path to temporary database file
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()


@pytest.fixture(scope="function")
def reset_db_connection():
    """Reset the global database connection singleton."""
    import app.database.connection
    app.database.connection._db_connection = None
    yield
    app.database.connection._db_connection = None


@pytest.fixture(scope="function")
def test_db_connection(monkeypatch, reset_db_connection) -> Generator[DatabaseConnection, None, None]:
    """
    Provide a real DatabaseConnection for integration tests.
    Uses a temporary SQLite database file for each test function.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create a new Settings object with the temporary data directory
        test_settings = Settings(data_dir=temp_path, ENVIRONMENT="test", LOG_LEVEL="DEBUG")
        
        # Clear cache and patch the get_settings function
        get_settings.cache_clear()
        monkeypatch.setattr("app.config.get_settings", lambda: test_settings)
        
        db = DatabaseConnection()
        db.create_tables()

        yield db

        db.drop_tables()
        db.close()


@pytest.fixture
def test_db_session(test_db_connection: DatabaseConnection) -> Generator[Session, None, None]:
    """
    Provide a database session for testing.

    Yields:
        SQLAlchemy session
    """
    with test_db_connection.get_session() as session:
        yield session


@pytest.fixture
def mock_db_connection() -> Generator[MagicMock, None, None]:
    """
    Provide a mock database connection.

    Yields:
        Mock database connection for testing
    """
    mock_conn = MagicMock(spec=DatabaseConnection)
    mock_session = MagicMock(spec=Session)

    mock_conn.get_session.return_value.__enter__.return_value = mock_session

    yield mock_conn


@pytest.fixture
def in_memory_db() -> Generator[sessionmaker[Session], None, None]:
    """
    Provide an in-memory SQLite database for testing.

    Creates tables and provides a session factory for tests.

    Yields:
        SQLAlchemy session factory
    """
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionFactory = sessionmaker(bind=engine, expire_on_commit=False)

    yield SessionFactory

    engine.dispose()


@pytest.fixture
def mock_exchange() -> MagicMock:
    """
    Provide a mock CCXT exchange instance.

    Returns:
        Mock exchange for testing extractors
    """
    mock = MagicMock()

    # Configure common methods
    mock.fetch_markets.return_value = [
        {"symbol": "BTC/USDT", "base": "BTC", "quote": "USDT"},
        {"symbol": "ETH/USDT", "base": "ETH", "quote": "USDT"},
    ]

    mock.fetch_tickers.return_value = {
        "BTC/USDT": {
            "symbol": "BTC/USDT",
            "last": 50000.0,
            "bid": 49999.0,
            "ask": 50001.0,
            "high": 51000.0,
            "low": 49000.0,
            "volume": 1000.0,
            "timestamp": 1640000000000,
        },
    }

    mock.fetch_ohlcv.return_value = [
        [1640000000000, 50000, 51000, 49000, 50500, 1000],
        [1640003600000, 50500, 51500, 50000, 51000, 1100],
    ]

    mock.fetch_order_book.return_value = {
        "bids": [[50000, 1.0], [49999, 2.0]],
        "asks": [[50001, 1.5], [50002, 2.5]],
    }

    mock.fetch_trades.return_value = [
        {
            "id": "123",
            "timestamp": 1640000000000,
            "symbol": "BTC/USDT",
            "side": "buy",
            "price": 50000,
            "amount": 1.0,
        },
    ]

    return mock
