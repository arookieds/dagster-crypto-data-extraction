"""
Unit tests for database modules with ORM support.

Tests database connection management, parameter operations, and ORM models.
"""


from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.connection import DatabaseConnection
from app.database.models import PipelineParameter
from app.database.parameter_manager import ParameterManager


class TestDatabaseConnection:
    """Tests for DatabaseConnection class with ORM support."""

    def test_connection_initialization(self) -> None:
        """Test database connection can be initialized."""
        db = DatabaseConnection()
        assert db._engine is None
        assert db._session_factory is None

    def test_connection_uses_sqlite_by_default(self, test_settings) -> None:
        """Test that SQLite is used when no PostgreSQL credentials."""
        db = DatabaseConnection()
        engine = db._get_engine()
        assert "sqlite" in str(engine.url)

    def test_create_tables(self, test_db_connection: DatabaseConnection) -> None:
        """Test that tables can be created."""
        test_db_connection.create_tables()
        # No exception means success

    def test_session_context_manager(self, test_db_connection: DatabaseConnection) -> None:
        """Test session context manager."""
        with test_db_connection.get_session() as session:
            assert isinstance(session, Session)
            # Session should be functional
            result = session.execute(text("SELECT 1"))
            assert result is not None

    def test_close_cleans_up_resources(self) -> None:
        """Test that close method cleans up all resources."""
        db = DatabaseConnection()
        db.close()
        assert db._engine is None
        assert db._session_factory is None


class TestParameterManager:
    """Tests for ParameterManager class with ORM."""

    def test_parameter_manager_initialization(self, test_db_connection: DatabaseConnection) -> None:
        """Test parameter manager can be initialized."""
        pm = ParameterManager(db_connection=test_db_connection, auto_create_tables=False)
        assert pm.db is not None

    def test_set_and_get_parameter(self, test_db_connection: DatabaseConnection) -> None:
        """Test setting and getting a parameter."""
        pm = ParameterManager(db_connection=test_db_connection, auto_create_tables=False)

        # Set parameter
        pm.set_parameter("test_pipeline", "test_key", "test_value", "Test description")

        # Get parameter
        value = pm.get_parameter("test_pipeline", "test_key")
        assert value == "test_value"

    def test_get_parameter_returns_default_when_not_found(
        self, test_db_connection: DatabaseConnection
    ) -> None:
        """Test that default value is returned when parameter not found."""
        pm = ParameterManager(db_connection=test_db_connection, auto_create_tables=False)
        result = pm.get_parameter("nonexistent", "test_key", "default_value")
        assert result == "default_value"

    def test_set_parameter_with_complex_value(
        self, test_db_connection: DatabaseConnection
    ) -> None:
        """Test storing complex JSON values."""
        pm = ParameterManager(db_connection=test_db_connection, auto_create_tables=False)

        complex_value = {
            "symbols": ["BTC/USDT", "ETH/USDT"],
            "config": {"limit": 100, "enabled": True},
        }

        pm.set_parameter("test_pipeline", "complex_key", complex_value)
        result = pm.get_parameter("test_pipeline", "complex_key")

        assert result == complex_value
        assert isinstance(result, dict)

    def test_update_existing_parameter(self, test_db_connection: DatabaseConnection) -> None:
        """Test updating an existing parameter."""
        pm = ParameterManager(db_connection=test_db_connection, auto_create_tables=False)

        # Create parameter
        pm.set_parameter("test_pipeline", "test_key", "initial_value")

        # Update parameter
        pm.set_parameter("test_pipeline", "test_key", "updated_value")

        # Verify update
        value = pm.get_parameter("test_pipeline", "test_key")
        assert value == "updated_value"

    def test_get_all_parameters(self, test_db_connection: DatabaseConnection) -> None:
        """Test getting all parameters for a pipeline."""
        pm = ParameterManager(db_connection=test_db_connection, auto_create_tables=False)

        # Set multiple parameters
        pm.set_parameter("test_pipeline", "key1", "value1")
        pm.set_parameter("test_pipeline", "key2", "value2")
        pm.set_parameter("other_pipeline", "key3", "value3")

        # Get all parameters for test_pipeline
        params = pm.get_all_parameters("test_pipeline")

        assert len(params) == 2
        assert params["key1"] == "value1"
        assert params["key2"] == "value2"
        assert "key3" not in params

    def test_delete_parameter(self, test_db_connection: DatabaseConnection) -> None:
        """Test deleting a parameter."""
        pm = ParameterManager(db_connection=test_db_connection, auto_create_tables=False)

        # Create parameter
        pm.set_parameter("test_pipeline", "test_key", "test_value")

        # Delete parameter
        result = pm.delete_parameter("test_pipeline", "test_key")
        assert result is True

        # Verify deletion
        value = pm.get_parameter("test_pipeline", "test_key", "default")
        assert value == "default"

    def test_delete_nonexistent_parameter(
        self, test_db_connection: DatabaseConnection
    ) -> None:
        """Test deleting a parameter that doesn't exist."""
        pm = ParameterManager(db_connection=test_db_connection, auto_create_tables=False)
        result = pm.delete_parameter("nonexistent", "test_key")
        assert result is False

    def test_list_pipelines(self, test_db_connection: DatabaseConnection) -> None:
        """Test listing all pipelines."""
        pm = ParameterManager(db_connection=test_db_connection, auto_create_tables=False)

        # Create parameters for different pipelines
        pm.set_parameter("pipeline1", "key1", "value1")
        pm.set_parameter("pipeline2", "key2", "value2")
        pm.set_parameter("pipeline1", "key3", "value3")

        # List pipelines
        pipelines = pm.list_pipelines()

        assert len(pipelines) == 2
        assert "pipeline1" in pipelines
        assert "pipeline2" in pipelines


class TestPipelineParameterModel:
    """Tests for PipelineParameter ORM model."""

    def test_create_parameter_model(self, test_db_session: Session) -> None:
        """Test creating a parameter using ORM model."""
        param = PipelineParameter(
            pipeline_name="test_pipeline",
            parameter_key="test_key",
            parameter_value={"key": "value"},
            description="Test parameter",
        )

        test_db_session.add(param)
        test_db_session.commit()

        assert param.id is not None
        assert param.created_at is not None
        assert param.updated_at is not None

    def test_parameter_repr(self) -> None:
        """Test parameter string representation."""
        param = PipelineParameter(
            pipeline_name="test",
            parameter_key="key",
            parameter_value="value",
        )
        param.id = 1

        repr_str = repr(param)
        assert "PipelineParameter" in repr_str
        assert "test" in repr_str
        assert "key" in repr_str
