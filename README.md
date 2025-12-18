# Dagster Crypto Data Extraction

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)

A professional, production-ready data engineering pipeline for extracting cryptocurrency data from multiple exchanges using Dagster and dlt (data load tool).

## Features

- **Multi-Exchange Support**: Extract data from Binance, Bybit, and Gate.io (easily extensible)
- **Asset-Based Orchestration**: Modern Dagster assets for better observability and testing
- **Multiple Destinations**: Store data in PostgreSQL, DuckDB, or any S3-compatible object storage (like MinIO).
- **Flexible Data Loading**: dlt integration for schema inference and evolution
- **Parameter Management**: PostgreSQL-backed configuration for runtime parameters
- **Production-Ready**: Comprehensive logging, retry logic, connection pooling, and error handling
- **Type-Safe**: Full type hints with mypy and pyright validation
- **Well-Tested**: Unit and integration tests with pytest
- **Kubernetes-Ready**: Designed for deployment in Kubernetes clusters

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Dagster                               │
│  ┌────────────────────────────────────────────────────┐     │
│  │           Assets (Orchestration)                   │     │
│  │  • binance_crypto_data                             │     │
│  │  • bybit_crypto_data                               │     │
│  │  • gateio_crypto_data                              │     │
│  └──────────────┬─────────────────────────────────────┘     │
│                 ▼                                            │
│  ┌────────────────────────────────────────────────────┐     │
│  │         Extractors (Business Logic)                │     │
│  │  • CCXT-based exchange connectors                  │     │
│  │  • Retry logic with exponential backoff            │     │
│  │  • Rate limiting                                   │     │
│  └──────────────┬─────────────────────────────────────┘     │
│                 ▼                                            │
│  ┌────────────────────────────────────────────────────┐     │
│  │              dlt Pipeline                          │     │
│  │  • Schema inference and evolution                  │     │
│  │  • Data normalization                              │     │
│  │  • Incremental loading                             │     │
│  └──────────────┬─────────────────────────────────────┘     │
└─────────────────┼────────────────────────────────────────────┘
                  ▼
          ┌──────────────┐
          │  Data Storage│
          │(DuckDB, PG, S3)│
          └──────────────┘
```

## Quick Start

This project supports multiple destinations for your data. By default, it uses DuckDB for local development. You can switch to PostgreSQL or S3 by configuring the environment variables in your `.env` file.

### Prerequisites

- Python 3.11 or higher
- (Optional) PostgreSQL 13 or higher for PostgreSQL destination
- (Optional) MinIO or other S3-compatible storage for S3 destination

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd dagster-crypto-data-extraction
```

2. **Install dependencies**

Using uv (recommended):

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

3. **Configure environment**

```bash
cp .env.example .env
# Edit .env to configure your desired destination (DuckDB, PostgreSQL, or S3)
```

4. **Run Dagster**

```bash
uv run dagster dev -f app/definitions.py
```

Navigate to http://localhost:3000 and materialize assets!

## Project Structure

```
dagster-crypto-data-extraction/
├── app/                          # Main application code
│   ├── config/                   # Configuration management
│   │   ├── __init__.py
│   │   ├── assets.py            # Asset configuration
│   │   └── settings.py          # Pydantic settings
│   ├── database/                # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py        # Connection pooling
│   │   └── parameter_manager.py # Parameter storage
│   ├── extractors/              # Exchange data extractors
│   │   ├── __init__.py
│   │   ├── base.py              # Base extractor class
│   │   ├── binance.py           # Binance extractor
│   │   ├── bybit.py             # Bybit extractor
│   │   └── gateio.py            # Gate.io extractor
│   ├── utils/                   # Utility functions
│   │   ├── __init__.py
│   │   ├── logger.py            # Structured logging
│   │   └── retry.py             # Retry decorators
│   ├── __init__.py
│   ├── assets.py                # Dagster assets
│   ├── factories.py             # Asset factories
│   └── definitions.py           # Dagster definitions (entry point)
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── conftest.py              # Pytest fixtures
├── docs/                        # Documentation
│   ├── architecture.md          # Architecture documentation
│   ├── deployment.md            # Deployment guide
│   ├── dlt-dagster-integration.md  # DLT + Dagster guide
│   └── usage.md                 # Usage guide
├── .env.example                 # Example environment variables
├── pyproject.toml               # Project configuration
└── README.md                    # This file
```

## Usage

### Extracting Data

**Via Dagster UI:**

1. Open http://localhost:3000
2. Navigate to Assets
3. Click "Materialize" on desired asset
4. Monitor execution and view logs

### Configuring Parameters

Parameters can be stored in the database (SQLite for local, PostgreSQL for production) for centralized management:

```python
from app.database.parameter_manager import ParameterManager

pm = ParameterManager()

# Set parameters
pm.set_parameter("binance_extraction", "symbols", ["BTC/USDT", "ETH/USDT"])
pm.set_parameter("binance_extraction", "timeframe", "1d")
```

### Querying Extracted Data

The way you query your data depends on the destination you have configured.

**DuckDB:**
```python
import duckdb
conn = duckdb.connect('.dagster_data/crypto_data.duckdb')
df = conn.execute("SELECT * FROM crypto_dev_binance.tickers").fetchdf()
print(df)
```

**PostgreSQL:**
```sql
SELECT * FROM crypto_prod_binance.tickers;
```

**S3/MinIO:**
You can use any S3 client to access the data in your bucket. The data is stored in JSONL format.

## Configuration

### Environment Variables

```bash
# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO

# PostgreSQL (optional)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=crypto_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=crypto_data

# S3/MinIO (optional)
S3_BUCKET_NAME=my-crypto-data-bucket
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin

# Extraction Settings
EXTRACTION_TIMEOUT=300
MAX_RETRIES=3
RETRY_DELAY=5
```

