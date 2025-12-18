"""
Bybit exchange data extractor.

Specialized extractor for Bybit exchange with support for
spot, derivatives, and options trading data.
"""

from typing import Any

from app.extractors.base import BaseExchanger


class BybitExtractor(BaseExchanger):
    """
    Bybit exchange data extractor.

    Extends BaseExchanger with Bybit-specific functionality
    and optimizations.
    """

    def __init__(self, api_key: str | None = None, secret: str | None = None):
        """
        Initialize Bybit extractor.

        Args:
            api_key: Optional Bybit API key
            secret: Optional Bybit API secret
        """
        super().__init__(exchange_id="bybit", api_key=api_key, secret=secret)

    def get_exchange_name(self) -> str:
        """Get exchange name."""
        return "Bybit"

    def fetch_insurance_fund(self, currency: str = "USDT") -> list[dict[str, Any]]:
        """
        Fetch insurance fund balance history.

        Args:
            currency: Currency to fetch insurance fund for

        Returns:
            List of insurance fund balance records

        Note:
            This is a Bybit-specific feature.
        """
        self.logger.info("Fetching insurance fund", currency=currency)

        try:
            # Bybit-specific endpoint
            if hasattr(self.exchange, "publicGetV2PublicRiskLimitInsuranceHistory"):
                insurance = self.exchange.publicGetV2PublicRiskLimitInsuranceHistory(
                    {"coin": currency}
                )
                self.logger.info("Fetched insurance fund data")
                return insurance.get("result", [])
            else:
                self.logger.warning("Insurance fund not supported by exchange client")
                return []
        except Exception as e:
            self.logger.error("Failed to fetch insurance fund", error=str(e))
            return []

    def fetch_long_short_ratio(self, symbol: str, period: str = "1h") -> dict[str, Any]:
        """
        Fetch long/short ratio for a symbol.

        Args:
            symbol: Trading symbol
            period: Time period (e.g., '1h', '4h', '1d')

        Returns:
            Long/short ratio data

        Note:
            This provides market sentiment indicators.
        """
        self.logger.info("Fetching long/short ratio", symbol=symbol, period=period)

        try:
            # Note: This would require specific Bybit API implementation
            # Placeholder for demonstration
            self.logger.warning("Long/short ratio requires specific API implementation")
            return {}
        except Exception as e:
            self.logger.error("Failed to fetch long/short ratio", error=str(e))
            return {}
