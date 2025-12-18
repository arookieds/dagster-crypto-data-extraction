"""
Binance exchange data extractor.

Specialized extractor for Binance exchange with support for
spot, futures, and margin trading data.
"""

from collections.abc import Iterator
from typing import Any

from app.extractors.base import BaseExchanger


class BinanceExtractor(BaseExchanger):
    """
    Binance exchange data extractor.

    Extends BaseExchanger with Binance-specific functionality
    and optimizations.
    """

    def __init__(self, api_key: str | None = None, secret: str | None = None):
        """
        Initialize Binance extractor.

        Args:
            api_key: Optional Binance API key
            secret: Optional Binance API secret
        """
        super().__init__(exchange_id="binance", api_key=api_key, secret=secret)

    def get_exchange_name(self) -> str:
        """Get exchange name."""
        return "Binance"

    def fetch_funding_rates(self, symbols: list[str] | None = None) -> list[dict[str, Any]]:
        """
        Fetch funding rates for perpetual futures.

        Args:
            symbols: List of symbols to fetch funding rates for

        Returns:
            List of funding rate data

        Note:
            This requires futures market data availability.
        """
        self.logger.info("Fetching funding rates", symbols=symbols)

        try:
            # Binance-specific endpoint for funding rates
            if hasattr(self.exchange, "fapiPublicGetPremiumIndex"):
                funding_rates = self.exchange.fapiPublicGetPremiumIndex()
                self.logger.info("Fetched funding rates", count=len(funding_rates))
                return funding_rates
            else:
                self.logger.warning("Funding rates not supported by exchange client")
                return []
        except Exception as e:
            self.logger.error("Failed to fetch funding rates", error=str(e))
            return []

    def fetch_24h_stats(self, symbols: list[str] | None = None) -> dict[str, Any]:
        """
        Fetch 24-hour statistics for symbols.

        Args:
            symbols: List of symbols to fetch stats for

        Returns:
            Dictionary mapping symbols to 24h statistics
        """
        self.logger.info("Fetching 24h statistics", symbols=symbols)
        return self.fetch_tickers(symbols)

    def funding_rate_resource(self, symbols: list[str] | None = None) -> Iterator[dict[str, Any]]:
        """
        DLT resource for funding rate data.

        Args:
            symbols: Symbols to fetch funding rates for

        Yields:
            Funding rate data dictionaries
        """
        self.logger.info("Starting funding rate resource extraction")
        funding_rates = self.fetch_funding_rates(symbols)

        for rate in funding_rates:
            yield {
                "exchange": self.exchange_id,
                "symbol": rate.get("symbol"),
                "funding_rate": rate.get("lastFundingRate"),
                "funding_time": rate.get("nextFundingTime"),
                "mark_price": rate.get("markPrice"),
                "index_price": rate.get("indexPrice"),
            }
