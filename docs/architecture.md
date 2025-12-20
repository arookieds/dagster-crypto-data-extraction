# Architecture Documentation

## System Overview

This project implements a production-grade data pipeline for extracting cryptocurrency data from multiple exchanges. The architecture follows modern data engineering best practices with clear separation of concerns, testability, and scalability. It features a multi-environment setup that allows for zero-dependency local development and a robust production deployment.

## High-Level Architecture

The architecture is designed to be flexible and automatically adapt to the environment it's running in.

### Local Development Environment

```
┌─────────────────────────────────────────────────────────────┐
│                        Local Machine                          │
│                                                             │
│  ┌────────────────────────────────────────────────────┐     │
│  │                    Dagster UI                        │     │
│  └────────────────────────────────────────────────────┘     │
│                                                             │
│  ┌────────────────────────────────────────────────────┐     │
│  │           Assets (Orchestration)                   │     │
│  └──────────────┬─────────────────────────────────────┘     │
│                 ▼                                            │
│  ┌────────────────────────────────────────────────────┐     │
│  │         Extractors (Business Logic)                │     │
│  └──────────────┬─────────────────────────────────────┘     │
│                 ▼                                            │
│  ┌────────────────────────────────────────────────────┐     │
│  │         dlt Pipeline (to DuckDB)                   │     │
│  └────────────────────────────────────────────────────┘     │
│                                                             │
└─────────────────┬──────────────────────────┬─────────────────┘
                  │                          │
                  ▼                          ▼
        ┌──────────────────┐        ┌──────────────────┐
        │      SQLite      │        │      DuckDB      │
        │   (Parameters)   │        │   (Extracted     │
        │                  │        │      Data)       │
        └──────────────────┘        └──────────────────┘
```

### Production Environment

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Dagster Deployment                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└──────────────────┬───────────────────────────┬───────────────────┘
                   │                           │
                   ▼                           ▼
         ┌──────────────────┐        ┌──────────────────┐
         │    PostgreSQL    │        │  External APIs   │
         │   (Parameters,   │        │  - Binance       │
         │    Dagster DB)   │        │  - Bybit         │
         └──────────────────┘        │  - Gate.io       │
                   │                 └──────────────────┘
                   ▼
         ┌──────────────────┐
         │    PostgreSQL    │
         │  (Data Warehouse)│
         └──────────────────┘
```

## Component Architecture

### 1. Configuration Layer (`app/config/`)

**Purpose**: Centralized and environment-aware configuration management.

**Components**:
- `settings.py`: Pydantic-based settings that load from environment variables. It automatically detects the environment based on the presence of `POSTGRES_` variables.
- `assets.py`: Defines the `CryptoExtractionConfig` class used for configuring the assets at runtime.

### 2. Database Layer (`app/database/`)

**Purpose**: Database connectivity and parameter management using SQLAlchemy ORM.

**Components**:
- `connection.py`: Manages database connections for both SQLite (local) and PostgreSQL (production).
- `models.py`: Defines the `PipelineParameter` table schema using SQLAlchemy's declarative mapping.
- `parameter_manager.py`: Provides a high-level API to get and set pipeline parameters in the database.

**Design Decisions**:
- SQLAlchemy ORM is used for database interactions to provide an abstraction layer and ensure type safety.
- The `ParameterManager` decouples the application logic from the underlying database.

### 3. Extractor Layer (`app/extractors/`)

**Purpose**: Data extraction logic for each crypto exchange.

**Components**:
- `base.py`: An abstract base class, `BaseExchanger`, that defines the common interface for all extractors.
- `binance.py`, `bybit.py`, `gateio.py`: Concrete implementations of `BaseExchanger` for each exchange.

**Design Decisions**:
- The use of a base class promotes code reuse and a consistent interface.
- CCXT library is used to interact with the different exchange APIs.
- `dlt` is used to create data loading pipelines that are aware of the environment.

### 4. Asset Factory (`app/factories.py`)

**Purpose**: To dynamically create Dagster assets for each exchange, reducing code duplication.

**Components**:
- `create_crypto_asset`: A factory function that takes an extractor class and returns a fully configured Dagster asset.

**Design Decisions**:
- The factory pattern makes it easy to add new exchanges without writing boilerplate code.

## Data Flow

The data flow is designed to be resilient and adaptable to the environment.

```
1. Dagster Schedule/Manual Trigger
         ↓
2. Asset Execution
         ↓
3. Load Runtime Config (from Dagster UI)
         ↓
4. Load Parameters from Database (SQLite or PostgreSQL)
         ↓
5. Initialize Extractor
         ↓
6. Create dlt Pipeline (to DuckDB or PostgreSQL)
         ↓
7. Extract Data from Exchange API (with retries)
         ↓
8. dlt Loads Data into Destination
         ↓
9. Yield `Output` with Metadata (row count, preview) to Dagster
```

## Scalability and Security

The architecture is designed with scalability and security in mind. Please refer to the main `README.md` for more details on these aspects.

