"""
Pipeline parameter management using SQLAlchemy ORM.

Stores and retrieves pipeline configuration parameters from the database
using SQLAlchemy 2.0 style ORM for flexible, centralized parameter management.
"""

from typing import Any

from sqlalchemy import select

from app.database.connection import DatabaseConnection, get_db_connection
from app.database.models import PipelineParameter
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ParameterManager:
    """
    Manages pipeline parameters using SQLAlchemy ORM.

    Provides methods to get, set, and manage pipeline configuration
    parameters with JSON support for complex data types.
    """

    def __init__(self, db_connection: DatabaseConnection | None = None, auto_create_tables: bool = True) -> None:
        """
        Initialize parameter manager.

        Args:
            db_connection: Optional DatabaseConnection instance.
            auto_create_tables: If True, automatically create tables on init
        """
        self.db = db_connection or get_db_connection()

        if auto_create_tables:
            self._ensure_table_exists()

    def _ensure_table_exists(self) -> None:
        """
        Create parameters table if it doesn't exist.

        Uses SQLAlchemy metadata to create the table with proper schema.
        """
        try:
            self.db.create_tables()
            logger.info("Pipeline parameters table ready")
        except Exception as e:
            logger.error("Failed to create parameters table", error=str(e))
            raise

    def get_parameter(
        self,
        pipeline_name: str,
        parameter_key: str,
        default: Any = None,
    ) -> Any:
        """
        Get a parameter value from the database.

        Args:
            pipeline_name: Name of the pipeline
            parameter_key: Parameter key to retrieve
            default: Default value if parameter not found

        Returns:
            Parameter value (supports any JSON-serializable type) or default

        Example:
            params = ParameterManager()
            symbols = params.get_parameter("binance_extraction", "symbols", ["BTC/USDT"])
        """
        try:
            with self.db.get_session() as session:
                stmt = select(PipelineParameter).where(
                    PipelineParameter.pipeline_name == pipeline_name,
                    PipelineParameter.parameter_key == parameter_key,
                )
                result = session.execute(stmt).scalar_one_or_none()

                if result is None:
                    logger.debug(
                        "Parameter not found, using default",
                        pipeline=pipeline_name,
                        key=parameter_key,
                        default=default,
                    )
                    return default

                value = result.parameter_value
                logger.debug(
                    "Retrieved parameter",
                    pipeline=pipeline_name,
                    key=parameter_key,
                    value=value,
                )
                return value

        except Exception as e:
            logger.error(
                "Failed to retrieve parameter",
                pipeline=pipeline_name,
                key=parameter_key,
                error=str(e),
            )
            return default

    def set_parameter(
        self,
        pipeline_name: str,
        parameter_key: str,
        parameter_value: Any,
        description: str | None = None,
    ) -> None:
        """
        Set a parameter value in the database.

        If the parameter exists, it will be updated. Otherwise, a new
        parameter will be created.

        Args:
            pipeline_name: Name of the pipeline
            parameter_key: Parameter key to set
            parameter_value: Parameter value (must be JSON-serializable)
            description: Optional description of the parameter

        Example:
            params = ParameterManager()
            params.set_parameter(
                "binance_extraction",
                "symbols",
                ["BTC/USDT", "ETH/USDT"],
                "Trading symbols to extract from Binance"
            )
        """
        try:
            with self.db.get_session() as session:
                # Check if parameter exists
                stmt = select(PipelineParameter).where(
                    PipelineParameter.pipeline_name == pipeline_name,
                    PipelineParameter.parameter_key == parameter_key,
                )
                existing_param = session.execute(stmt).scalar_one_or_none()

                if existing_param is None:
                    # Create new parameter
                    new_param = PipelineParameter(
                        pipeline_name=pipeline_name,
                        parameter_key=parameter_key,
                        parameter_value=parameter_value,
                        description=description,
                    )
                    session.add(new_param)
                    logger.info(
                        "Created new parameter",
                        pipeline=pipeline_name,
                        key=parameter_key,
                    )
                else:
                    # Update existing parameter
                    existing_param.parameter_value = parameter_value
                    if description is not None:
                        existing_param.description = description
                    logger.info(
                        "Updated parameter",
                        pipeline=pipeline_name,
                        key=parameter_key,
                    )

        except Exception as e:
            logger.error(
                "Failed to set parameter",
                pipeline=pipeline_name,
                key=parameter_key,
                error=str(e),
            )
            raise

    def get_all_parameters(self, pipeline_name: str) -> dict[str, Any]:
        """
        Get all parameters for a pipeline.

        Args:
            pipeline_name: Name of the pipeline

        Returns:
            Dictionary mapping parameter keys to values

        Example:
            params = ParameterManager()
            all_params = params.get_all_parameters("binance_extraction")
        """
        try:
            with self.db.get_session() as session:
                stmt = select(PipelineParameter).where(
                    PipelineParameter.pipeline_name == pipeline_name
                )
                results = session.execute(stmt).scalars().all()

                parameters = {param.parameter_key: param.parameter_value for param in results}

                logger.info(
                    "Retrieved all parameters",
                    pipeline=pipeline_name,
                    count=len(parameters),
                )

                return parameters

        except Exception as e:
            logger.error(
                "Failed to retrieve all parameters",
                pipeline=pipeline_name,
                error=str(e),
            )
            return {}

    def delete_parameter(self, pipeline_name: str, parameter_key: str) -> bool:
        """
        Delete a parameter from the database.

        Args:
            pipeline_name: Name of the pipeline
            parameter_key: Parameter key to delete

        Returns:
            True if parameter was deleted, False if not found

        Example:
            params = ParameterManager()
            params.delete_parameter("binance_extraction", "old_param")
        """
        try:
            with self.db.get_session() as session:
                stmt = select(PipelineParameter).where(
                    PipelineParameter.pipeline_name == pipeline_name,
                    PipelineParameter.parameter_key == parameter_key,
                )
                param = session.execute(stmt).scalar_one_or_none()

                if param is not None:
                    session.delete(param)
                    logger.info(
                        "Deleted parameter",
                        pipeline=pipeline_name,
                        key=parameter_key,
                    )
                    return True
                else:
                    logger.debug(
                        "Parameter not found for deletion",
                        pipeline=pipeline_name,
                        key=parameter_key,
                    )
                    return False

        except Exception as e:
            logger.error(
                "Failed to delete parameter",
                pipeline=pipeline_name,
                key=parameter_key,
                error=str(e),
            )
            return False

    def list_pipelines(self) -> list[str]:
        """
        List all pipeline names that have parameters.

        Returns:
            List of unique pipeline names

        Example:
            params = ParameterManager()
            pipelines = params.list_pipelines()
            # ['binance_extraction', 'bybit_extraction', 'gateio_extraction']
        """
        try:
            with self.db.get_session() as session:
                stmt = select(PipelineParameter.pipeline_name).distinct()
                results = session.execute(stmt).scalars().all()

                pipelines = list(results)
                logger.info("Listed pipelines", count=len(pipelines))
                return pipelines

        except Exception as e:
            logger.error("Failed to list pipelines", error=str(e))
            return []
