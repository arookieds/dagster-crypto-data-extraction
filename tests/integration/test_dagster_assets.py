"""
Integration tests for Dagster assets.

Tests asset execution and integration between components.
"""

from unittest.mock import MagicMock, patch

import pytest
from dagster import build_asset_context

from app.assets import binance_crypto_data
from app.config.assets import CryptoExtractionConfig


class TestDagsterAssets:
    """Integration tests for Dagster assets."""

    @patch("app.factories.ParameterManager")
    @patch("app.assets.BinanceExtractor")
    @pytest.mark.integration
    def test_binance_asset_execution(
        self,
        mock_extractor_class: MagicMock,
        mock_param_manager: MagicMock,
    ) -> None:
        """Test that Binance asset can be executed."""
        # Setup mocks
        mock_param_mgr_instance = MagicMock()
        mock_param_manager.return_value = mock_param_mgr_instance
        mock_param_mgr_instance.get_parameter.side_effect = lambda p, k, d: d

        mock_extractor = MagicMock()
        mock_extractor_class.return_value = mock_extractor
        
        mock_extractor.ticker_resource.return_value = [{"symbol": "BTC/USDT", "price": 100}]

        mock_pipeline = MagicMock()
        mock_extractor.create_dlt_pipeline.return_value = mock_pipeline

        mock_run_info = MagicMock()
        mock_run_info.metrics = {"rows": 1}
        mock_run_info.finished_at = "2024-01-01T00:00:00"
        mock_pipeline.run.return_value = mock_run_info

        # Create config and context
        config = CryptoExtractionConfig(
            symbols=["BTC/USDT"],
            extract_tickers=True,
            extract_ohlcv=False,
        )
        context = build_asset_context()

        # Execute asset
        result_iterator = binance_crypto_data(context, config)
        results = list(result_iterator)
        result = results[0]

        # Verify results
        assert "tickers" in result.value
        assert result.value["tickers"]["rows"] == 1
        assert result.metadata["num_records"].value == 1
        assert len(result.metadata["preview"].value) == 1

    @patch("app.factories.ParameterManager")
    @patch("app.assets.BinanceExtractor")
    @pytest.mark.integration
    def test_binance_asset_execution_failure(
        self,
        mock_extractor_class: MagicMock,
        mock_param_manager: MagicMock,
    ) -> None:
        """Test that Binance asset execution handles exceptions."""
        # Setup mocks
        mock_param_manager.side_effect = Exception("Test Exception")

        # Create config and context
        config = CryptoExtractionConfig(
            symbols=["BTC/USDT"],
            extract_tickers=True,
            extract_ohlcv=False,
        )
        context = build_asset_context()

        # Execute asset and expect an exception
        with pytest.raises(Exception, match="Test Exception"):
            list(binance_crypto_data(context, config))
