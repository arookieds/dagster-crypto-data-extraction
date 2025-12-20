#!/usr/bin/env python3
"""
Test script to verify all imports work correctly.

Run this after installing dependencies:
    uv pip install -e ".[dev]"
    python test_imports.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all key imports work."""

    print("Testing imports...")
    print("=" * 60)

    errors = []

    # Test 1: Config
    try:
        from app.config import get_settings
        settings = get_settings()
        env_info = settings.get_environment_info()
        print("✓ app.config - OK")
        print(f"  Environment: {env_info['environment']}")
        print(f"  Database: {env_info['database']}")
        print(f"  Storage: {env_info['data_storage']}")
    except Exception as e:
        print(f"✗ app.config - FAILED: {e}")
        errors.append(("app.config", e))

    # Test 2: Database Models
    try:
        from app.database.models import Base, PipelineParameter
        print("✓ app.database.models - OK")
    except Exception as e:
        print(f"✗ app.database.models - FAILED: {e}")
        errors.append(("app.database.models", e))

    # Test 3: Database Connection
    try:
        from app.database.connection import get_db_connection
        db = get_db_connection()
        print("✓ app.database.connection - OK")
        print(f"  Using: {settings.database_url.split('://')[0]}")
    except Exception as e:
        print(f"✗ app.database.connection - FAILED: {e}")
        errors.append(("app.database.connection", e))

    # Test 4: Resources
    try:
        from app.resources import get_data_storage_resource
        resource = get_data_storage_resource()
        print("✓ app.resources - OK")
        print(f"  Resource type: {type(resource).__name__}")
    except Exception as e:
        print(f"✗ app.resources - FAILED: {e}")
        errors.append(("app.resources", e))

    # Test 5: Extractors
    try:
        from app.extractors import BinanceExtractor, BybitExtractor, GateioExtractor
        print("✓ app.extractors - OK")
    except Exception as e:
        print(f"✗ app.extractors - FAILED: {e}")
        errors.append(("app.extractors", e))

    # Test 6: Assets
    try:
        from app import assets
        print("✓ app.assets - OK")
    except Exception as e:
        print(f"✗ app.assets - FAILED: {e}")
        errors.append(("app.assets", e))

    # Test 7: Definitions (most important)
    try:
        from app.definitions import defs
        print("✓ app.definitions - OK")
        print(f"  Assets: {len(defs.assets)}")
        print(f"  Jobs: {len(defs.jobs)}")
    except Exception as e:
        print(f"✗ app.definitions - FAILED: {e}")
        errors.append(("app.definitions", e))
        import traceback
        traceback.print_exc()

    print("=" * 60)

    if errors:
        print(f"\n❌ {len(errors)} import(s) failed:\n")
        for module, error in errors:
            print(f"  {module}: {error}")
        return False
    else:
        print("\n✅ All imports successful!")
        print("\nYou can now run:")
        print("  dagster dev -f app/definitions.py")
        return True


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
