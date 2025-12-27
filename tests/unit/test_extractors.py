"""
Unit tests for crypto exchange extractors.

Tests extractor initialization, data fetching, and dlt integration.
"""

from unittest.mock import MagicMock, patch

import ccxt
import dlt
import pytest

from app.extractors import BinanceExtractor, BybitExtractor, GateioExtractor
from app.extractors.base_enhanced import BaseExchangerEnhanced


class TestBaseExchanger:
    """Tests for BaseExchanger base class."""

    @patch("app.extractors.base_enhanced.ccxt")
    def test_base_exchanger_initialization(self, mock_ccxt: MagicMock) -> None:
        """Test base exchanger can be initialized."""
        mock_exchange_class = MagicMock()
        mock_ccxt.binance = mock_exchange_class

        class TestExtractor(BaseExchangerEnhanced):
            def get_exchange_name(self) -> str:
                return "Test"

        extractor = TestExtractor("binance")
        assert extractor.exchange_id == "binance"
        mock_exchange_class.assert_called_once()

    @patch("app.extractors.base_enhanced.ccxt")
    def test_fetch_markets(self, mock_ccxt: MagicMock, mock_exchange: MagicMock) -> None:
        """Test fetching markets."""
        mock_exchange_class = MagicMock(return_value=mock_exchange)
        mock_ccxt.binance = mock_exchange_class

        class TestExtractor(BaseExchangerEnhanced):
            def get_exchange_name(self) -> str:
                return "Test"

        extractor = TestExtractor("binance")
        markets = extractor.fetch_markets()

        assert len(markets) == 2
        mock_exchange.fetch_markets.assert_called_once()

    @patch("app.extractors.base_enhanced.ccxt")
    def test_fetch_tickers(self, mock_ccxt: MagicMock, mock_exchange: MagicMock) -> None:
        """Test fetching tickers."""
        mock_exchange_class = MagicMock(return_value=mock_exchange)
        mock_ccxt.binance = mock_exchange_class

        class TestExtractor(BaseExchangerEnhanced):
            def get_exchange_name(self) -> str:
                return "Test"

        extractor = TestExtractor("binance")
        tickers = extractor.fetch_tickers(["BTC/USDT"])

        assert "BTC/USDT" in tickers
        assert tickers["BTC/USDT"]["last"] == 50000.0
        mock_exchange.fetch_tickers.assert_called_once()

    @patch("app.extractors.base_enhanced.ccxt")
    def test_ticker_resource(self, mock_ccxt: MagicMock, mock_exchange: MagicMock) -> None:
        """Test ticker resource generator."""
        mock_exchange_class = MagicMock(return_value=mock_exchange)
        mock_ccxt.binance = mock_exchange_class

        class TestExtractor(BaseExchangerEnhanced):
            def get_exchange_name(self) -> str:
                return "Test"

        extractor = TestExtractor("binance")
        tickers = list(extractor.ticker_resource(["BTC/USDT"]))

        assert len(tickers) == 1
        assert tickers[0]["exchange"] == "binance"
        assert tickers[0]["symbol"] == "BTC/USDT"
        assert tickers[0]["last"] == 50000.0

    @patch("app.extractors.base_enhanced.ccxt")
    def test_ohlcv_resource(self, mock_ccxt: MagicMock, mock_exchange: MagicMock) -> None:
        """Test OHLCV resource generator."""
        mock_exchange_class = MagicMock(return_value=mock_exchange)
        mock_ccxt.binance = mock_exchange_class

        class TestExtractor(BaseExchangerEnhanced):
            def get_exchange_name(self) -> str:
                return "Test"

        extractor = TestExtractor("binance")
        ohlcv = list(extractor.ohlcv_resource("BTC/USDT", "1d", 2))

        assert len(ohlcv) == 2
        assert ohlcv[0]["exchange"] == "binance"
        assert ohlcv[0]["symbol"] == "BTC/USDT"
        assert ohlcv[0]["open"] == 50000

    @patch("app.extractors.base.dlt.pipeline")
    def test_create_dlt_pipeline_exception(self, mock_pipeline: MagicMock) -> None:
        """Test that create_dlt_pipeline handles exceptions."""
        mock_pipeline.side_effect = Exception("Test Exception")

        class TestExtractor(BaseExchangerEnhanced):
            def get_exchange_name(self) -> str:
                return "Test"

        extractor = TestExtractor("binance")
        with pytest.raises(Exception, match="Test Exception"):
            extractor.create_dlt_pipeline("test_pipeline")


class TestBinanceExtractor:
    """Tests for BinanceExtractor."""

    @patch("app.extractors.base_enhanced.ccxt")
    def test_binance_extractor_initialization(self, mock_ccxt: MagicMock) -> None:
        """Test Binance extractor initialization."""
        mock_exchange_class = MagicMock()
        mock_ccxt.binance = mock_exchange_class

        extractor = BinanceExtractor()
        assert extractor.exchange_id == "binance"
        assert extractor.get_exchange_name() == "Binance"

    @patch("app.extractors.base_enhanced.ccxt")
    def test_binance_fetch_funding_rates(
        self, mock_ccxt: MagicMock, mock_exchange: MagicMock
    ) -> None:
        """Test fetching Binance funding rates."""
        mock_exchange.fapiPublicGetPremiumIndex = MagicMock(return_value=[{"symbol": "BTCUSDT"}])
        mock_exchange_class = MagicMock(return_value=mock_exchange)
        mock_ccxt.binance = mock_exchange_class

        extractor = BinanceExtractor()
        rates = extractor.fetch_funding_rates()

        assert len(rates) == 1

    @patch("app.extractors.base_enhanced.ccxt")
    def test_binance_fetch_funding_rates_failure(
        self, mock_ccxt: MagicMock, mock_exchange: MagicMock
    ) -> None:
        """Test fetching Binance funding rates failure."""
        mock_exchange.fapiPublicGetPremiumIndex = MagicMock(
            side_effect=ccxt.ExchangeError("Test Exception")
        )
        mock_exchange_class = MagicMock(return_value=mock_exchange)
        mock_ccxt.binance = mock_exchange_class

        extractor = BinanceExtractor()
        rates = extractor.fetch_funding_rates()

        assert len(rates) == 0


class TestBybitExtractor:
    """Tests for BybitExtractor."""

    @patch("app.extractors.base_enhanced.ccxt")
    def test_bybit_extractor_initialization(self, mock_ccxt: MagicMock) -> None:
        """Test Bybit extractor initialization."""
        mock_exchange_class = MagicMock()
        mock_ccxt.bybit = mock_exchange_class

        extractor = BybitExtractor()
        assert extractor.exchange_id == "bybit"
        assert extractor.get_exchange_name() == "Bybit"

    @patch("app.extractors.base_enhanced.ccxt")
    def test_bybit_fetch_insurance_fund(
        self, mock_ccxt: MagicMock, mock_exchange: MagicMock
    ) -> None:
        """Test fetching Bybit insurance fund."""
        mock_exchange.publicGetV2PublicRiskLimitInsuranceHistory = MagicMock(
            return_value={"result": [{"currency": "BTC"}]}
        )
        mock_exchange_class = MagicMock(return_value=mock_exchange)
        mock_ccxt.bybit = mock_exchange_class

        extractor = BybitExtractor()
        fund = extractor.fetch_insurance_fund()

        assert len(fund) == 1

    @patch("app.extractors.base_enhanced.ccxt")
    def test_bybit_fetch_insurance_fund_failure(
        self, mock_ccxt: MagicMock, mock_exchange: MagicMock
    ) -> None:
        """Test fetching Bybit insurance fund failure."""
        mock_exchange.publicGetV2PublicRiskLimitInsuranceHistory = MagicMock(
            side_effect=ccxt.ExchangeError("Test Exception")
        )
        mock_exchange_class = MagicMock(return_value=mock_exchange)
        mock_ccxt.bybit = mock_exchange_class

        extractor = BybitExtractor()
        fund = extractor.fetch_insurance_fund()

        assert len(fund) == 0


class TestGateioExtractor:
    """Tests for GateioExtractor."""

    @patch("app.extractors.base_enhanced.ccxt")
    def test_gateio_extractor_initialization(self, mock_ccxt: MagicMock) -> None:
        """Test Gate.io extractor initialization."""
        mock_exchange_class = MagicMock()
        mock_ccxt.gateio = mock_exchange_class

        extractor = GateioExtractor()
        assert extractor.exchange_id == "gateio"
        assert extractor.get_exchange_name() == "Gate.io"

    @patch("app.extractors.base_enhanced.ccxt")
    def test_gateio_fetch_currency_chains(
        self, mock_ccxt: MagicMock, mock_exchange: MagicMock
    ) -> None:
        """Test fetching Gate.io currency chains."""
        mock_exchange.publicSpotGetCurrenciesCurrency = MagicMock(return_value=[{"chain": "ETH"}])
        mock_exchange_class = MagicMock(return_value=mock_exchange)
        mock_ccxt.gateio = mock_exchange_class

        extractor = GateioExtractor()
        chains = extractor.fetch_currency_chains("USDT")

        assert len(chains) == 1

    @patch("app.extractors.base_enhanced.ccxt")
    def test_gateio_fetch_currency_chains_failure(
        self, mock_ccxt: MagicMock, mock_exchange: MagicMock
    ) -> None:
        """Test fetching Gate.io currency chains failure."""
        mock_exchange.publicSpotGetCurrenciesCurrency = MagicMock(
            side_effect=ccxt.ExchangeError("Test Exception")
        )
        mock_exchange_class = MagicMock(return_value=mock_exchange)
        mock_ccxt.gateio = mock_exchange_class

        extractor = GateioExtractor()
        chains = extractor.fetch_currency_chains("USDT")

        assert len(chains) == 0
