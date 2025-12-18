
"""
Asset factories for creating reusable Dagster assets.
"""
from collections.abc import Iterator

from dagster import AssetExecutionContext, MetadataValue, Output, asset

from app.config.assets import CryptoExtractionConfig
from app.database.parameter_manager import ParameterManager
from app.extractors.base import BaseExchanger


def create_crypto_asset(
    extractor_class: type[BaseExchanger],
    asset_name: str,
    group_name: str = "crypto_extraction",
    description: str | None = None,
):
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
        timeframe = param_manager.get_parameter(
            pipeline_name, "timeframe", config.timeframe
        )
        limit = param_manager.get_parameter(pipeline_name, "limit", config.limit)

        context.log.info(
            f"Using symbols: {symbols}, timeframe: {timeframe}, limit: {limit}"
        )

        extractor = extractor_class()

        try:
            pipeline = extractor.create_dlt_pipeline(pipeline_name)
            results = {}
            data_preview = []
            total_rows = 0

            if config.extract_tickers:
                context.log.info("Extracting ticker data")
                ticker_data = list(extractor.ticker_resource(symbols))
                num_rows = len(ticker_data)
                total_rows += num_rows
                data_preview.extend(ticker_data[:5])

                if num_rows > 0:
                    ticker_info = pipeline.run(
                        ticker_data,
                        table_name="tickers",
                        write_disposition="append",
                    )
                    results["tickers"] = {
                        "rows": num_rows,
                        "loaded_at": ticker_info.finished_at,
                    }

            if config.extract_ohlcv and symbols:
                context.log.info("Extracting OHLCV data")
                for symbol in symbols:
                    ohlcv_data = list(extractor.ohlcv_resource(symbol, timeframe, limit))
                    num_rows = len(ohlcv_data)
                    total_rows += num_rows
                    if not data_preview:
                        data_preview.extend(ohlcv_data[:5])

                    if num_rows > 0:
                        ohlcv_info = pipeline.run(
                            ohlcv_data,
                            table_name="ohlcv",
                            write_disposition="append",
                        )
                        results[f"ohlcv_{symbol}"] = {
                            "rows": num_rows,
                            "loaded_at": ohlcv_info.finished_at,
                        }

            context.log.info(
                f"Extraction for {asset_name} completed", extra=results
            )

            yield Output(
                value=results,
                metadata={
                    "num_records": total_rows,
                    "preview": MetadataValue.json(data_preview),
                },
            )

        except Exception as e:
            context.log.error(f"Extraction for {asset_name} failed: {str(e)}")
            raise
        finally:
            extractor.close()

    return crypto_asset

