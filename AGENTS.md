# Development Guidelines for Agentic Coding

## Commands

### Testing
- Run all tests: `make test` or `pytest`
- Run unit tests only: `make test-unit` or `pytest tests/unit/ -v`
- Run single test: `pytest tests/unit/test_file.py::test_function -v`
- Run integration tests: `make test-integration` or `pytest tests/integration/ -m integration -v`

### Code Quality
- Lint: `make lint` or `ruff check app/ tests/`
- Format: `make format` or `black app/ tests/ && isort app/ tests/`
- Type check: `make type-check` or `mypy app/ && pyright app/`
- Full check: `make all` (format, lint, type-check, test)

## Code Style Guidelines

### Import Organization
- Use isort with black profile (line length: 100)
- Standard library imports first, then third-party, then local imports
- Group imports: `from collections.abc import ...` for new-style imports

### Type Hints
- Use strict type hints everywhere (mypy configured with `disallow_untyped_defs`)
- Use `str | None` syntax for Union types (Python 3.11+)
- Use `collections.abc` for generic types (Iterator, Generator, etc.)

### Error Handling
- Use structured logging with structlog (see `app/utils/logger.py`)
- Handle CCXT exceptions with retry decorators (see `app/utils/retry.py`)
- Raise ValueError for configuration issues early

### Naming Conventions
- Classes: PascalCase (e.g., `BaseExchanger`)
- Functions/variables: snake_case
- Constants: UPPER_SNAKE_CASE
- Private methods: prefix with underscore

### Testing Patterns
- Use fixtures from `conftest.py` for database and exchange mocking
- Mark tests with `@pytest.mark.unit` or `@pytest.mark.integration`
- Use descriptive test names following `test_` prefix
- Mock external dependencies (CCXT exchanges, databases)

### Dagster Specific
- Define assets in `app/assets.py`
- Use resource factories for exchange connections
- Implement proper asset dependencies
- Follow DLT integration patterns from `app/extractors/base.py`