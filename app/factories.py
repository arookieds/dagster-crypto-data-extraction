from collections.abc import Iterator
from datetime import datetime

from dagster import AssetExecutionContext, MetadataValue, Output, asset, AssetsDefinition

from app.config.assets import CryptoExtractionConfig
from app.database.parameter_manager import ParameterManager
from app.utils.s3_metadata import S3MetadataManager


def create_crypto_asset(
    extractor_class: type,
    asset_name: str,
    group_name: str = "crypto_extraction",
    description: str | None = None,
) -> AssetsDefinition:
    """
    Asset factory for creating cryptocurrency data extraction assets.

    Args:
        extractor_class: The extractor class to use (e.g., BinanceExtractor).
        asset_name: The name of the asset.
        group_name: The group name for the asset.
        description: The description for the asset.

    Returns:
        A Dagster asset.
    """

    @asset(
        name=asset_name,
        group_name=group_name,
        description=description or f"Extract cryptocurrency data from {extractor_class.__name__}",
    )
    def crypto_asset(
        context: AssetExecutionContext, config: CryptoExtractionConfig
    ) -> Iterator[Output]:
        """
        Generic crypto data extraction asset.
        """

        context.log.info(f"Starting data extraction for {asset_name}")

        param_manager = ParameterManager()
        pipeline_name = f"{asset_name}_extraction"

        symbols = param_manager.get_parameter(pipeline_name, "symbols", config.symbols)
        timeframe = param_manager.get_parameter(pipeline_name, "timeframe", config.timeframe)
        limit = param_manager.get_parameter(pipeline_name, "limit", config.limit)

        context.log.info(f"Using symbols: {symbols}, timeframe: {timeframe}, limit: {limit}")

        extractor = extractor_class()

        try:
            # Create separate pipelines for each data type with proper table names
            results = {}
            data_preview: list[dict] = []
            total_rows = 0
            uploaded_files: list[dict] = []

            if config.extract_tickers:
                context.log.info("Extracting ticker data")
                ticker_data = list(
                    extractor.ticker_resource(symbols, dagster_run_id=context.run_id)
                )
                num_rows = len(ticker_data)
                total_rows += num_rows
                if not data_preview:
                    data_preview.extend(ticker_data[:5])

                if num_rows > 0:
                    # Create pipeline with correct table name
                    ticker_pipeline = extractor.create_dlt_pipeline(context.run_id, "tickers")
                    ticker_info = ticker_pipeline.run(
                        ticker_data,
                        table_name="tickers",
                        write_disposition="append",
                    )
                    results["tickers"] = {
                        "rows": num_rows,
                        "loaded_at": ticker_info.finished_at,
                    }

                    # Track uploaded files for potential cleanup
                    if hasattr(ticker_info, "load_packages") and ticker_info.load_packages:
                        uploaded_files.extend(
                            [
                                {
                                    "table_name": "tickers",
                                }
                            ]
                        )

            if config.extract_ohlcv and symbols:
                context.log.info("Extracting OHLCV data")
                for symbol in symbols:
                    ohlcv_data = list(
                        extractor.ohlcv_resource(
                            symbol, timeframe, limit, dagster_run_id=context.run_id
                        )
                    )
                    num_rows = len(ohlcv_data)
                    total_rows += num_rows
                    if not data_preview:
                        data_preview.extend(ohlcv_data[:5])

                    if num_rows > 0:
                        # Create separate pipeline for OHLCV data with proper table name
                        ohlcv_pipeline = extractor.create_dlt_pipeline(context.run_id, "ohlcv")
                        ohlcv_info = ohlcv_pipeline.run(
                            ohlcv_data,
                            table_name="ohlcv",
                            write_disposition="append",
                        )
                        results[f"ohlcv_{symbol}"] = {
                            "rows": num_rows,
                            "loaded_at": ohlcv_info.finished_at,
                        }

                        # Track uploaded files for potential cleanup
                        if hasattr(ohlcv_info, "load_packages") and ohlcv_info.load_packages:
                            uploaded_files.extend(
                                [
                                    {
                                        "table_name": "ohlcv",
                                        "symbol": symbol,
                                    }
                                ]
                            )

            # Inject object-level metadata for successful uploads if configured
            if extractor.settings.use_s3 and uploaded_files:
                try:
                    metadata_manager = S3MetadataManager(
                        exchange_name=extractor.exchange_id, run_id=context.run_id
                    )

                    # Inject metadata for each uploaded file
                    for file_info in uploaded_files:
                        table_name = file_info["table_name"]

                        # Object key matches DLT's actual file creation pattern
                        object_key = f"{table_name}/{extractor.exchange_id}_{table_name}_{context.run_id}_{int(datetime.now().timestamp())}.jsonl"

                        if metadata_manager.inject_metadata_to_object(
                            bucket_name=extractor.settings.s3_bucket_name or "",
                            object_key=object_key,
                            data_type=table_name,
                        ):
                            context.log.info(
                                f"Successfully injected S3 metadata - run_id: {context.run_id} - table_name: {table_name} - object_key: {object_key}",
                            )
                        else:
                            context.log.warning(
                                f"Failed to inject S3 metadata - run_id: {context.run_id} - table_name: {table_name} - object_key: {object_key}",
                            )

                except Exception as metadata_error:
                    context.log.warning(
                        f"Failed to inject S3 metadata - run_id: {context.run_id} - error: {str(metadata_error)}",
                    )

            context.log.info(
                f"Extraction completed - asset_name: {asset_name} - run_id: {context.run_id} - total_records: {total_rows}",
            )

            yield Output(
                value=results,
                metadata={
                    "num_records": total_rows,
                    "preview": MetadataValue.json(data_preview),
                    "run_id": context.run_id,
                    "exchange": extractor.exchange_id.lower(),
                    "s3_files_uploaded": extractor.settings.use_s3,
                },
            )

        except Exception as e:
            context.log.error(
                f"Extraction failed - asset_name: {asset_name} - run_id: {context.run_id} - error: {str(e)}",
            )

            # Cleanup S3 files on failure if configured
            if extractor.settings.use_s3 and extractor.settings.s3_auto_cleanup:
                try:
                    metadata_manager = S3MetadataManager(
                        exchange_name=extractor.exchange_id, run_id=context.run_id
                    )
                    deleted_count = metadata_manager.cleanup_failed_run(
                        bucket_name=extractor.settings.s3_bucket_name or ""
                    )

                    context.log.info(
                        f"Cleaned up S3 files from failed run - run_id: {context.run_id} - deleted_count: {deleted_count}",
                    )

                except Exception as cleanup_error:
                    context.log.warning(
                        f"Failed to cleanup S3 files - run_id: {context.run_id} - error: {str(cleanup_error)}",
                    )

            yield Output(
                value={"error": str(e)},
                metadata={
                    "num_records": 0,
                    "run_id": context.run_id,
                    "exchange": extractor.exchange_id.lower(),
                    "error": str(e),
                    "s3_files_uploaded": extractor.settings.use_s3,
                },
            )

        finally:
            extractor.close()

    return crypto_asset
