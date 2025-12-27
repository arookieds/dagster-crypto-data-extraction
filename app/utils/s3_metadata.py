"""
S3 metadata management for enhanced crypto data extraction.

This module provides S3 object-level metadata injection capabilities
for proper data organization and traceability.
"""

from datetime import datetime

import boto3

from app.config import get_settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class S3MetadataManager:
    """
    Enhanced S3 metadata manager for object-level metadata injection.

    Provides proper S3 object metadata injection with x-amz-meta-* headers
    for traceability and searchability at the object level.
    """

    def __init__(self, exchange_name: str, run_id: str):
        """
        Initialize S3 metadata manager.

        Args:
            exchange_name: Name of the exchange (e.g., 'binance')
            run_id: Dagster run ID for traceability
        """
        self.settings = get_settings()
        self.exchange_name = exchange_name.lower()
        self.run_id = run_id
        self.logger = logger.bind(exchange=exchange_name, run_id=run_id)

    def _get_s3_client(self) -> any:
        """Get configured S3 client."""
        s3_config = {
            "aws_access_key_id": self.settings.s3_access_key_id,
            "aws_secret_access_key": self.settings.s3_secret_access_key,
            "endpoint_url": self.settings.s3_endpoint_url,
        }

        # Remove None values
        s3_config = {k: v for k, v in s3_config.items() if v is not None}

        return boto3.client("s3", **s3_config)

    def _generate_metadata_headers(self, data_type: str) -> dict[str, str]:
        """
        Generate S3 metadata headers for object.

        Args:
            data_type: Type of data (e.g., 'tickers', 'ohlcv')

        Returns:
            Dictionary of metadata headers for S3 object
        """
        return {
            f"{self.settings.s3_metadata_prefix}-run-id": self.run_id,
            f"{self.settings.s3_metadata_prefix}-exchange": self.exchange_name,
            f"{self.settings.s3_metadata_prefix}-data-type": data_type,
            f"{self.settings.s3_metadata_prefix}-extraction-time": datetime.now().isoformat(),
        }

    def inject_metadata_to_object(
        self,
        bucket_name: str,
        object_key: str,
        data_type: str,
    ) -> bool:
        """
        Inject metadata at S3 object level.

        This uses put_object with metadata directly for better efficiency.

        Args:
            bucket_name: S3 bucket name
            object_key: S3 object key
            data_type: Type of data (e.g., 'tickers', 'ohlcv')

        Returns:
            True if metadata injection was successful, False otherwise
        """
        try:
            # Get the object content first
            s3_client = self._get_s3_client()

            # Get the current object
            response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
            current_content = response["Body"].read()

            # Generate metadata headers
            metadata = self._generate_metadata_headers(data_type)

            # Put the object back with metadata
            s3_client.put_object(
                Bucket=bucket_name,
                Key=object_key,
                Body=current_content,
                Metadata={f"x-amz-meta-{k}": v for k, v in metadata.items()},
            )

            self.logger.info(
                "Successfully injected object-level metadata",
                object_key=object_key,
                data_type=data_type,
                metadata_count=len(metadata),
            )

            return True

        except Exception as e:
            self.logger.error(
                "Failed to inject object-level metadata",
                object_key=object_key,
                data_type=data_type,
                error=str(e),
            )
            return False

    def cleanup_failed_run(self, bucket_name: str) -> int:
        """
        Clean up all files from a failed run.

        This prevents orphaned files from incomplete runs.

        Args:
            bucket_name: S3 bucket name to clean

        Returns:
            Number of files deleted
        """
        try:
            s3_client = self._get_s3_client()
            deleted_count = 0

            # List all objects with run ID prefix
            paginator = s3_client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=bucket_name, Prefix=self.run_id):
                for obj in page.get("Contents", []):
                    if obj["Key"].startswith(f"{self.run_id}_"):
                        s3_client.delete_object(Bucket=bucket_name, Key=obj["Key"])
                        deleted_count += 1

            self.logger.info(
                "Cleaned up failed run",
                run_id=self.run_id,
                deleted_count=deleted_count,
            )

            return deleted_count

        except Exception as e:
            self.logger.error(
                "Failed to cleanup failed run",
                run_id=self.run_id,
                error=str(e),
            )
            return 0
