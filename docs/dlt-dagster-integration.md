# dlt and Dagster Integration

This guide explains how `dlt` (data load tool) and Dagster work together in this project.

## Division of Responsibilities

In this project, the responsibilities are divided as follows:

*   **Dagster**: Handles the "what" and "when". It's responsible for orchestrating the data extraction process, managing dependencies, and providing observability.
*   **dlt**: Handles the "how". It's responsible for the details of extracting data from the source, inferring the schema, and loading it into the destination.

This separation of concerns makes the pipeline more modular, maintainable, and testable.

## How They Work Together

The integration between Dagster and `dlt` is done at the asset level. A Dagster asset is a function that produces a data asset. In our case, the data assets are the tables in our data warehouse (DuckDB or PostgreSQL).

Here's a simplified example of how they integrate in the `create_crypto_asset` factory:

```python
# In app/factories.py

@asset
def crypto_asset(context: AssetExecutionContext, config: CryptoExtractionConfig) -> Iterator[Output]:
    # Dagster provides context, config, scheduling, and logging
    context.log.info("Starting extraction")

    # Business logic: create an extractor
    extractor = extractor_class()

    # dlt provides: pipeline creation and data loading
    pipeline = extractor.create_dlt_pipeline(pipeline_name)

    # The extractor's resource methods are dlt resources
    ticker_data = list(extractor.ticker_resource(symbols))
    
    # dlt handles schema inference, loading, and transactions
    if ticker_data:
        ticker_info = pipeline.run(ticker_data, table_name="tickers")

    # The asset yields a Dagster Output with metadata
    yield Output(
        value={"rows": len(ticker_data)},
        metadata={
            "num_records": len(ticker_data),
            "preview": MetadataValue.json(ticker_data[:5]),
        },
    )
```

## Using dlt Standalone

You can also use the extractors and `dlt` pipelines independently, without Dagster. This is useful for debugging, ad-hoc extractions, or prototyping.

To run a standalone script, make sure to use `uv run` to use the project's virtual environment:

```bash
uv run python scripts/extract_standalone.py
```

## dlt CLI

`dlt` provides a CLI for managing pipelines. To use it, make sure you are in the project's virtual environment.

```bash
# Activate the virtual environment
source .venv/bin/activate

# View pipeline state
dlt pipeline binance_extraction info
```

For more information on `dlt`, please refer to the [official dlt documentation](https://dlthub.com/docs).

