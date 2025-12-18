# Usage Guide

## Quick Start

### 1. Running Your First Extraction

After completing the setup (see `GETTING_STARTED.md`), you can run your first data extraction:

```bash
# Start Dagster development server
uv run dagster dev -f app/definitions.py
```

Navigate to http://localhost:3000 and:

1. Click on "Assets" in the left sidebar
2. Select `binance_crypto_data`, `bybit_crypto_data`, or `gateio_crypto_data`
3. Click "Materialize" button in the top right
4. Monitor the execution in real-time

### 2. Configuring Extraction Parameters

Parameters can be configured via the database (SQLite for local, PostgreSQL for production) for centralized management:

```python
from app.database.parameter_manager import ParameterManager

pm = ParameterManager()

# Set symbols to extract
pm.set_parameter(
    pipeline_name="binance_extraction",
    parameter_key="symbols",
    parameter_value=["BTC/USDT", "ETH/USDT", "SOL/USDT"],
    description="Trading pairs to extract from Binance"
)
```

### 3. Running Scheduled Extractions

To enable automatic scheduled extractions:

Edit `app/definitions.py` and uncomment desired schedules:

```python
all_schedules = [
    daily_extraction_schedule,    # Runs daily at midnight UTC
    # hourly_extraction_schedule,  # Runs every hour
]
```

Restart Dagster to pick up schedule changes.

## Asset Operations

### Materializing Individual Assets

**Via UI:**
1. Navigate to Assets
2. Click on the asset name
3. Click "Materialize"

**Via CLI:**

```bash
# Materialize a single asset
uv run dagster asset materialize -f app/definitions.py -a binance_crypto_data

# Materialize all assets
uv run dagster asset materialize -f app/definitions.py --select "*"
```

### Running Jobs

Jobs group multiple assets together:

```bash
# Run all exchanges extraction
uv run dagster job execute -f app/definitions.py -j all_exchanges_extraction
```

## Working with Data

### Querying Extracted Data

After extraction, data is available in DuckDB (local) or PostgreSQL (production):

```sql
-- For local development with DuckDB
-- View ticker data in crypto_dev_binance schema
SELECT * FROM crypto_dev_binance.tickers
ORDER BY timestamp DESC
LIMIT 10;

-- For production with PostgreSQL
-- View ticker data in crypto_prod_binance schema
SELECT * FROM crypto_prod_binance.tickers
ORDER BY timestamp DESC
LIMIT 10;
```

## Advanced Usage

### Adding New Exchanges

To add support for a new exchange:

1.  **Create an extractor** for the new exchange in `app/extractors/` by inheriting from `BaseExchanger`.

    ```python
    # app/extractors/kraken.py
    from app.extractors.base import BaseExchanger

    class KrakenExtractor(BaseExchanger):
        def __init__(self, api_key=None, secret=None):
            super().__init__(exchange_id="kraken", api_key=api_key, secret=secret)

        def get_exchange_name(self) -> str:
            return "Kraken"
    ```

2.  **Create a new asset** in `app/assets.py` using the `create_crypto_asset` factory.

    ```python
    # app/assets.py
    from app.extractors import KrakenExtractor
    from app.factories import create_crypto_asset

    kraken_crypto_data = create_crypto_asset(
        extractor_class=KrakenExtractor,
        asset_name="kraken_crypto_data",
        description="Extract cryptocurrency data from Kraken exchange",
    )
    ```
3. **Import the new asset** in `app/definitions.py` and add it to the `all_assets` list.
4. **Write tests** for the new extractor in the `tests/` directory.

### Incremental Loading

For efficient extractions, you can use dlt's incremental loading feature. This requires modifying the extractor's resource methods.

```python
import dlt
from dlt.sources.helpers import incremental

@dlt.resource
def incremental_tickers(last_timestamp=dlt.sources.incremental("timestamp")):
    """Extract only new ticker data since last run."""
    # ... logic to fetch tickers and yield only new ones
```

