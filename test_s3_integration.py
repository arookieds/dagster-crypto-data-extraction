#!/usr/bin/env python3
"""
Simple test script to verify S3 metadata implementation works.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import get_settings
from app.utils.s3_metadata import S3MetadataManager


def test_settings():
    """Test that S3 configuration is loaded correctly."""
    settings = get_settings()
    print("✅ Settings loaded successfully")
    print(f"S3 enabled: {settings.use_s3}")

    if hasattr(settings, "get_dlt_destination_config"):
        config = settings.get_dlt_destination_config()
        print("✅ DLT destination config method exists")
        print(f"Bucket URL: {config.get('bucket_url', 'N/A')}")
        print(f"Layout: {config.get('layout', 'N/A')}")
    else:
        print("❌ DLT destination config method missing")


def test_s3_metadata_manager():
    """Test S3 metadata manager initialization."""
    print("\n🧪 Testing S3 Metadata Manager...")

    try:
        # Test with mock settings
        os.environ["S3_BUCKET_NAME"] = "test-bucket"
        os.environ["S3_ACCESS_KEY_ID"] = "test-key"
        os.environ["S3_SECRET_ACCESS_KEY"] = "test-secret"

        manager = S3MetadataManager("binance", "test-run-123")
        print("✅ S3MetadataManager initialized successfully")
        print(f"Exchange: {manager.exchange_name}")
        print(f"Run ID: {manager.run_id}")

        # Test metadata generation
        metadata = manager._generate_metadata_headers("ticker_data")
        print("✅ Metadata headers generated:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")

    except Exception as e:
        print(f"❌ S3MetadataManager test failed: {e}")


def test_base_enhanced():
    """Test that enhanced base extractor can be imported."""
    print("\n🏗 Testing Enhanced Base Extractor...")

    try:
        from app.extractors.base_enhanced import BaseExchangerEnhanced

        print("✅ Enhanced base extractor imported successfully")

        # Test class instantiation
        extractor = BaseExchangerEnhanced("binance")
        print("✅ Enhanced extractor instantiated")
        print(f"Exchange ID: {extractor.exchange_id}")
        print(f"Settings: {extractor.settings.environment}")

    except ImportError as e:
        print(f"❌ Enhanced base extractor import failed: {e}")
    except Exception as e:
        print(f"❌ Enhanced base extractor test failed: {e}")


def test_factories():
    """Test that factories can import enhanced components."""
    print("\n🏭 Testing Enhanced Factories...")

    try:
        from app.factories import create_crypto_asset

        print("✅ Factories imported successfully")

        # Test asset factory function
        asset_func = create_crypto_asset(
            extractor_class=BaseExchangerEnhanced,
            asset_name="test_binance",
        )
        print("✅ Asset factory function created")

    except ImportError as e:
        print(f"❌ Factories import failed: {e}")
    except Exception as e:
        print(f"❌ Factories test failed: {e}")


if __name__ == "__main__":
    print("🚀 Testing S3 Metadata Integration")
    print("=" * 50)

    test_settings()
    test_s3_metadata_manager()
    test_base_enhanced()
    test_factories()

    print("\n" + "=" * 50)
    print("✅ S3 Metadata Integration Test Complete!")
    print("📋 Next Steps:")
    print("  1. Set up S3/MinIO with credentials")
    print("  2. Add USE_S3=true to .env")
    print("  3. Run Dagster pipeline to test hybrid storage")
