"""
Base extractor class for crypto exchanges.

Provides common interface and shared functionality for all exchange extractors
using the CCXT library and dlt for data loading.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

import ccxt
import dlt

from app.config import get_settings
from app.utils.logger import get_logger
from app.utils.retry import retry_with_backoff

logger = get_logger(__name__)


class BaseExchanger(ABC):
    """
    Abstract base class for cryptocurrency exchange data extractors.

    Provides common functionality for all exchange extractors including
    connection management, retry logic, and dlt integration.
    """

    def __init__(self, exchange_id: str, api_key: str | None = None, secret: str | None = None):
        """
        Initialize exchange extractor.

        Args:
            exchange_id: CCXT exchange identifier (e.g., 'binance', 'bybit')
            api_key: Optional API key for authenticated endpoints
            secret: Optional API secret for authenticated endpoints
        """
        self.exchange_id = exchange_id
        self.settings = get_settings()
        self.logger = logger.bind(exchange=exchange_id)

        # Check if exchange_id is supported by CCXT, and if not, throw an error.
        # It is a deliberate choice to have Dagster capture early an issue with
        # the configuration.
        if exchange_id not in ccxt.exchanges:
            raise ValueError(f"Exchange '{exchange_id}' is not supported by CCXT")

        # Initialize CCXT exchange
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange: ccxt.Exchange = exchange_class(
            {
                "apiKey": api_key,
                "secret": secret,
                "enableRateLimit": True,
                "timeout": self.settings.extraction_timeout * 1000,  # Convert to ms
            }
        )

        self.logger.info("Exchange extractor initialized")

    @abstractmethod
    def get_exchange_name(self) -> str:
        """
        Get human-readable exchange name.

        Returns:
            Exchange name for logging and identification
        """
        pass

    @retry_with_backoff(exceptions=(ccxt.NetworkError, ccxt.ExchangeError))
    def fetch_markets(self) -> list[dict[str, Any]]:
        """
        Fetch all available markets from the exchange.

        Returns:
            List of market information dictionaries

        Raises:
            ccxt.NetworkError: Network connectivity issues
            ccxt.ExchangeError: Exchange-specific errors
        """
        self.logger.info("Fetching markets")
        markets = self.exchange.fetch_markets()
        self.logger.info("Fetched markets", count=len(markets))
        return markets

    @retry_with_backoff(exceptions=(ccxt.NetworkError, ccxt.ExchangeError))
    def fetch_tickers(self, symbols: list[str] | None = None) -> dict[str, Any]:
        """
        Fetch ticker data for specified symbols.

        Args:
            symbols: List of trading symbols (e.g., ['BTC/USDT']). If None, fetch all.

        Returns:
            Dictionary mapping symbols to ticker data

        Raises:
            ccxt.NetworkError: Network connectivity issues
            ccxt.ExchangeError: Exchange-specific errors
        """
        self.logger.info("Fetching tickers", symbols=symbols)
        tickers = self.exchange.fetch_tickers(symbols)
        self.logger.info("Fetched tickers", count=len(tickers))
        return tickers

    @retry_with_backoff(exceptions=(ccxt.NetworkError, ccxt.ExchangeError))
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: int = 100,
        since: int | None = None,
    ) -> list[list[Any]]:
        """
        Fetch OHLCV (candlestick) data for a symbol.

        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            timeframe: Candle timeframe (e.g., '1m', '1h', '1d')
            limit: Number of candles to fetch
            since: Timestamp in ms to fetch data from

        Returns:
            List of OHLCV data [timestamp, open, high, low, close, volume]

        Raises:
            ccxt.NetworkError: Network connectivity issues
            ccxt.ExchangeError: Exchange-specific errors
        """
        self.logger.info(
            "Fetching OHLCV",
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
        )
        ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, since, limit)
        self.logger.info("Fetched OHLCV", symbol=symbol, count=len(ohlcv))
        return ohlcv

    @retry_with_backoff(exceptions=(ccxt.NetworkError, ccxt.ExchangeError))
    def fetch_order_book(self, symbol: str, limit: int | None = None) -> dict[str, Any]:
        """
        Fetch order book for a symbol.

        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            limit: Number of order book entries to fetch

        Returns:
            Order book data with bids and asks

        Raises:
            ccxt.NetworkError: Network connectivity issues
            ccxt.ExchangeError: Exchange-specific errors
        """
        self.logger.info("Fetching order book", symbol=symbol, limit=limit)
        order_book = self.exchange.fetch_order_book(symbol, limit)
        self.logger.info(
            "Fetched order book",
            symbol=symbol,
            bids=len(order_book.get("bids", [])),
            asks=len(order_book.get("asks", [])),
        )
        return order_book

    @retry_with_backoff(exceptions=(ccxt.NetworkError, ccxt.ExchangeError))
    def fetch_trades(self, symbol: str, limit: int = 100) -> list[dict[str, Any]]:
        """
        Fetch recent trades for a symbol.

        Args:
            symbol: Trading symbol (e.g., 'BTC/USDT')
            limit: Number of trades to fetch

        Returns:
            List of trade data dictionaries

        Raises:
            ccxt.NetworkError: Network connectivity issues
            ccxt.ExchangeError: Exchange-specific errors
        """
        self.logger.info("Fetching trades", symbol=symbol, limit=limit)
        trades = self.exchange.fetch_trades(symbol, limit=limit)
        self.logger.info("Fetched trades", symbol=symbol, count=len(trades))
        return trades

    def ticker_resource(self, symbols: list[str] | None = None) -> Iterator[dict[str, Any]]:
        """
        DLT resource for ticker data.

        Yields ticker data in a format suitable for dlt loading.

        Args:
            symbols: List of symbols to fetch tickers for

        Yields:
            Ticker data dictionaries
        """
        self.logger.info("Starting ticker resource extraction")
        tickers = self.fetch_tickers(symbols)

        for symbol, ticker in tickers.items():
            yield {
                "exchange": self.exchange_id,
                "symbol": symbol,
                "timestamp": ticker.get("timestamp"),
                "last": ticker.get("last"),
                "bid": ticker.get("bid"),
                "ask": ticker.get("ask"),
                "high": ticker.get("high"),
                "low": ticker.get("low"),
                "volume": ticker.get("volume"),
                "quote_volume": ticker.get("quoteVolume"),
            }

    def ohlcv_resource(
        self,
        symbol: str,
        timeframe: str = "1d",
        limit: int = 100,
    ) -> Iterator[dict[str, Any]]:
        """
        DLT resource for OHLCV data.

        Yields OHLCV data in a format suitable for dlt loading.

        Args:
            symbol: Trading symbol
            timeframe: Candle timeframe
            limit: Number of candles

        Yields:
            OHLCV data dictionaries
        """
        self.logger.info(
            "Starting OHLCV resource extraction",
            symbol=symbol,
            timeframe=timeframe,
        )
        ohlcv_data = self.fetch_ohlcv(symbol, timeframe, limit)

        for candle in ohlcv_data:
            yield {
                "exchange": self.exchange_id,
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": candle[0],
                "open": candle[1],
                "high": candle[2],
                "low": candle[3],
                "close": candle[4],
                "volume": candle[5],
            }

    def create_dlt_pipeline(self) -> dlt.Pipeline:
        """
        Create a dlt pipeline with a fixed name, configured via environment.

        This approach allows dlt to handle its own configuration via environment
        variables or config files, which is the best practice for production.

        Returns:
            Configured dlt pipeline

        Example:
            # DLT configuration is loaded from environment variables:
            # - CRYPTO_DATA_EXTRACTION__DESTINATION__FILESYSTEM__BUCKET_URL
            # - CRYPTO_DATA_EXTRACTION__DESTINATION__...
        """
        pipeline_name = self.settings.dlt_pipeline_name
        destination_type = self.settings.dlt_destination_type
        self.logger.info(
            "Creating dlt pipeline",
            pipeline_name=pipeline_name,
            destination=destination_type,
        )

        # Explicitly passing destination as a workaround for discovery issues.
        # dlt will still find credentials from the environment.
        pipeline = dlt.pipeline(
            pipeline_name=pipeline_name, destination=destination_type
        )

        return pipeline

    def close(self) -> None:
        """Close exchange connection and cleanup resources."""
        if hasattr(self.exchange, "close") and callable(self.exchange.close):
            self.exchange.close()
        self.logger.info("Exchange connection closed")
