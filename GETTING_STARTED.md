# Getting Started Guide

This guide will get you running in **3 minutes** with **ZERO external dependencies** for local development. It also covers how to set up a production-grade environment.

## Local Development (3-Minute Setup)

### Step 1: Install Dependencies (1 minute)

```bash
# Install uv (if you don't have it)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### Step 2: Run Dagster (30 seconds)

```bash
uv run dagster dev -f app/definitions.py
```

That's it! Open http://localhost:3000

### Step 3: Extract Your First Data (1 minute)

In the Dagster UI:
1. Click **"Assets"** in the left sidebar
2. Click on **"binance_crypto_data"**
3. Click **"Materialize"** button
4. Watch it run!

**No PostgreSQL to install. No Docker to run. No configuration to set up.**

### What Just Happened?

The application automatically created:
- `.dagster_data/parameters.db` - SQLite database for your pipeline settings
- `.dagster_data/crypto_data.duckdb` - DuckDB database with your crypto data

### Viewing Your Data

You can query your data using Python with DuckDB:

```python
import duckdb

conn = duckdb.connect('.dagster_data/crypto_data.duckdb')

# View available tables
conn.execute("SHOW TABLES").fetchdf()

# Query ticker data
tickers = conn.execute("""
    SELECT * FROM crypto_dev_binance.tickers
    ORDER BY timestamp DESC
    LIMIT 5
""").fetchdf()

print(tickers)
```

## Production Setup (10-Minute Setup)

For a production environment, it is recommended to use PostgreSQL for data storage and parameter management.

### Step 1: Start PostgreSQL Database

Using Docker (easiest):

```bash
docker run -d \
  --name crypto-postgres \
  -e POSTGRES_USER=crypto_user \
  -e POSTGRES_PASSWORD=crypto_pass123 \
  -e POSTGRES_DB=crypto_data \
  -p 5432:5432 \
  postgres:15-alpine
```

### Step 2: Configure Environment

Create your environment file:

```bash
cp .env.example .env
```

Edit `.env` with your PostgreSQL settings:

```bash
ENVIRONMENT=production
LOG_LEVEL=INFO

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=crypto_user
POSTGRES_PASSWORD=crypto_pass123
POSTGRES_DB=crypto_data
```

When you start the application with these environment variables set, it will automatically connect to PostgreSQL.

### Step 3: Verify Data in PostgreSQL

Connect to PostgreSQL and query the data:

```bash
docker exec -it crypto-postgres psql -U crypto_user -d crypto_data
```

Run SQL queries:

```sql
-- List all schemas (should see crypto_prod_binance)
\dn

-- View ticker data
SELECT * FROM crypto_prod_binance.tickers ORDER BY timestamp DESC LIMIT 5;

-- View OHLCV data (if extracted)
SELECT * FROM crypto_prod_binance.ohlcv ORDER BY timestamp DESC LIMIT 5;

-- Exit psql
\q
```

## S3/MinIO Setup

You can also store the extracted data in any S3-compatible object storage, like MinIO.

### Step 1: Start MinIO

Using Docker:

```bash
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio \
  -e "MINIO_ROOT_USER=minioadmin" \
  -e "MINIO_ROOT_PASSWORD=minioadmin" \
  minio/minio server /data --console-address ":9001"
```

### Step 2: Configure Environment

Edit your `.env` file to include the S3 settings:

```bash
S3_BUCKET_NAME=my-crypto-data-bucket
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
```

Create the bucket in MinIO, and then run the Dagster pipeline. The data will be saved to the specified S3 bucket.

## Next Steps

### 1. Configure What to Extract

You can configure the extraction parameters (symbols, timeframe, etc.) by setting them in the database.

```bash
python << 'EOF'
from app.database.parameter_manager import ParameterManager

pm = ParameterManager()

# Configure what symbols to extract
pm.set_parameter(
    "binance_extraction",
    "symbols",
    ["BTC/USDT", "ETH/USDT", "SOL/USDT"],
    "Trading pairs to extract"
)

# Set timeframe
pm.set_parameter("binance_extraction", "timeframe", "1h")

# Set how much data to fetch
pm.set_parameter("binance_extraction", "limit", 100)

print("Parameters configured!")
EOF
```

Now re-run the extraction in the Dagster UI to get your configured symbols!

### 2. Schedule Automatic Extractions

Edit `app/definitions.py` and uncomment schedules:

```python
all_schedules = [
    daily_extraction_schedule,    # Runs at midnight UTC
    # hourly_extraction_schedule,  # Uncomment for hourly runs
]
```

Restart Dagster to activate the schedules.

### 3. Explore the Code

Key files to explore:
- `app/definitions.py` - Dagster entry point
- `app/assets.py` - Asset definitions
- `app/factories.py` - Asset factory for creating assets
- `app/extractors/base.py` - Base extractor logic
- `app/database/parameter_manager.py` - Parameter management

### 4. Read the Documentation

For more detailed information, check out the `docs/` folder.