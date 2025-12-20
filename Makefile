.PHONY: help install install-dev test lint format type-check clean docker-build docker-run dagster-dev

help:
	@echo "Available commands:"
	@echo "  make install        - Install production dependencies"
	@echo "  make install-dev    - Install development dependencies"
	@echo "  make test          - Run tests with coverage"
	@echo "  make lint          - Run linters (ruff)"
	@echo "  make format        - Format code (black, isort)"
	@echo "  make type-check    - Run type checkers (mypy, pyright)"
	@echo "  make clean         - Clean build artifacts and cache"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run Docker container"
	@echo "  make dagster-dev   - Run Dagster development server"

install:
	uv pip install -e .

install-dev:
	uv pip install -e ".[dev]"

test:
	pytest --cov=app --cov-report=html --cov-report=term

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -m integration -v

lint:
	ruff check app/ tests/

format:
	black app/ tests/
	isort app/ tests/
	ruff check --fix app/ tests/

type-check:
	mypy app/
	pyright app/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.duckdb" -delete
	find . -type f -name "*.log" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf build/ dist/ htmlcov/ .coverage coverage.xml

docker-build:
	docker build -t crypto-extraction:latest .

docker-run:
	docker run -it --rm \
		--env-file .env \
		-p 4000:4000 \
		crypto-extraction:latest

dagster-dev:
	dagster dev -f app/definitions.py

all: format lint type-check test
