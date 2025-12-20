"""
Dagster definitions for the crypto data extraction pipeline.

This is the main entry point for Dagster. It defines all assets,
resources, schedules, and sensors with multi-environment support.

Environment Detection:
- Local Dev: Uses DuckDB for data storage (zero external dependencies)
- Production: Uses PostgreSQL for data storage (configured via env vars)
"""

from dagster import (
    AssetSelection,
    Definitions,
    ScheduleDefinition,
    define_asset_job,
    load_assets_from_modules,
)

from app import assets
from app.config import get_settings
from app.resources import get_data_storage_resource
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Get settings and log environment info
settings = get_settings()
env_info = settings.get_environment_info()
logger.info("Initializing Dagster definitions", **env_info)

# Load all assets from the assets module
all_assets = load_assets_from_modules([assets])

# Define jobs for different extraction scenarios

# Job to extract from all exchanges
all_exchanges_job = define_asset_job(
    name="all_exchanges_extraction",
    description="Extract data from all supported exchanges (Binance, Bybit, Gate.io)",
    selection=AssetSelection.all(),
)

# Job for individual exchanges
binance_job = define_asset_job(
    name="binance_extraction",
    description="Extract data from Binance exchange only",
    selection=AssetSelection.assets(assets.binance_crypto_data),
)

bybit_job = define_asset_job(
    name="bybit_extraction",
    description="Extract data from Bybit exchange only",
    selection=AssetSelection.assets(assets.bybit_crypto_data),
)

gateio_job = define_asset_job(
    name="gateio_extraction",
    description="Extract data from Gate.io exchange only",
    selection=AssetSelection.assets(assets.gateio_crypto_data),
)

# Define schedules

# Daily extraction at 00:00 UTC
daily_extraction_schedule = ScheduleDefinition(
    name="daily_extraction",
    job=all_exchanges_job,
    cron_schedule="0 0 * * *",  # Daily at midnight UTC
    description="Run daily extraction from all exchanges at midnight UTC",
)

# Hourly extraction
hourly_extraction_schedule = ScheduleDefinition(
    name="hourly_extraction",
    job=all_exchanges_job,
    cron_schedule="0 * * * *",  # Every hour
    description="Run hourly extraction from all exchanges",
)

# Individual exchange schedules (if needed for different timing)
binance_hourly_schedule = ScheduleDefinition(
    name="binance_hourly",
    job=binance_job,
    cron_schedule="5 * * * *",  # Every hour at 5 minutes past
    description="Run hourly Binance extraction",
)

# Combine all schedules (can enable/disable as needed)
all_schedules = [
    # Uncomment the schedule you want to use
    # daily_extraction_schedule,
    # hourly_extraction_schedule,
    # binance_hourly_schedule,
]

# Define resources with environment-aware configuration
# Automatically uses DuckDB for local dev, PostgreSQL for production
resources = {
    "database": get_data_storage_resource(),
}

# Log resource configuration
if settings.use_postgres:
    logger.info("Using PostgreSQL for data storage")
else:
    logger.info("Using DuckDB for local development", db_path=str(settings.duckdb_path))

# Create Dagster Definitions
# This is what Dagster loads when it starts
defs = Definitions(
    assets=all_assets,
    jobs=[
        all_exchanges_job,
        binance_job,
        bybit_job,
        gateio_job,
    ],
    schedules=all_schedules,
    resources=resources,
)

logger.info(
    "Dagster definitions loaded successfully",
    environment=settings.environment,
    database=env_info["database"],
    storage=env_info["data_storage"],
)
