"""
Configuration for Dagster assets.
"""

from dagster import Config


class CryptoExtractionConfig(Config):
    """
    Configuration for crypto data extraction assets.
    """

    symbols: list[str] | None = None
    timeframe: str = "1d"
    limit: int = 100
    extract_tickers: bool = True
    extract_ohlcv: bool = True
    extract_order_book: bool = False
    extract_trades: bool = False
