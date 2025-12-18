"""
Gate.io exchange data extractor.

Specialized extractor for Gate.io exchange with support for
spot, margin, and futures trading data.
"""

from typing import Any

from app.extractors.base import BaseExchanger


class GateioExtractor(BaseExchanger):
    """
    Gate.io exchange data extractor.

    Extends BaseExchanger with Gate.io-specific functionality
    and optimizations.
    """

    def __init__(self, api_key: str | None = None, secret: str | None = None):
        """
        Initialize Gate.io extractor.

        Args:
            api_key: Optional Gate.io API key
            secret: Optional Gate.io API secret
        """
        super().__init__(exchange_id="gateio", api_key=api_key, secret=secret)

    def get_exchange_name(self) -> str:
        """Get exchange name."""
        return "Gate.io"

    def fetch_currency_chains(self, currency: str) -> list[dict[str, Any]]:
        """
        Fetch supported blockchain networks for a currency.

        Args:
            currency: Currency code (e.g., 'USDT')

        Returns:
            List of supported chains for the currency

        Note:
            Gate.io supports multiple chains for the same currency.
        """
        self.logger.info("Fetching currency chains", currency=currency)

        try:
            # Gate.io-specific endpoint
            if hasattr(self.exchange, "publicSpotGetCurrenciesCurrency"):
                chains = self.exchange.publicSpotGetCurrenciesCurrency({"currency": currency})
                self.logger.info("Fetched currency chains", currency=currency)
                return chains if isinstance(chains, list) else [chains]
            else:
                self.logger.warning("Currency chains not supported by exchange client")
                return []
        except Exception as e:
            self.logger.error("Failed to fetch currency chains", error=str(e))
            return []

    def fetch_lending_rates(self, currency: str | None = None) -> list[dict[str, Any]]:
        """
        Fetch lending market rates.

        Args:
            currency: Optional specific currency to fetch rates for

        Returns:
            List of lending rate data

        Note:
            Gate.io has a lending market for earning interest on holdings.
        """
        self.logger.info("Fetching lending rates", currency=currency)

        try:
            # Note: This would require specific Gate.io API implementation
            # Placeholder for demonstration
            self.logger.warning("Lending rates require specific API implementation")
            return []
        except Exception as e:
            self.logger.error("Failed to fetch lending rates", error=str(e))
            return []
