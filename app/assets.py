"""
Dagster assets for crypto data extraction.
"""

from app.extractors import BinanceExtractor, BybitExtractor, GateioExtractor
from app.factories import create_crypto_asset

binance_crypto_data = create_crypto_asset(
    extractor_class=BinanceExtractor,
    asset_name="binance_crypto_data",
    description="Extract cryptocurrency data from Binance exchange",
)

bybit_crypto_data = create_crypto_asset(
    extractor_class=BybitExtractor,
    asset_name="bybit_crypto_data",
    description="Extract cryptocurrency data from Bybit exchange",
)

gateio_crypto_data = create_crypto_asset(
    extractor_class=GateioExtractor,
    asset_name="gateio_crypto_data",
    description="Extract cryptocurrency data from Gate.io exchange",
)
