FROM python:3.11-slim

LABEL maintainer="Your Name <your.email@example.com>"
LABEL description="Dagster Crypto Data Extraction Pipeline"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency installation
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml README.md ./

# Install Python dependencies
RUN uv pip install --system --no-cache -e .

# Copy application code
COPY app/ ./app/

# Create non-root user for security
RUN useradd -m -u 1000 dagster && \
    chown -R dagster:dagster /app

# Switch to non-root user
USER dagster

# Expose ports
# 3000: Dagster webserver
# 4000: Dagster gRPC server (code location)
EXPOSE 3000 4000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command: run code location gRPC server
CMD ["dagster", "api", "grpc", "-h", "0.0.0.0", "-p", "4000", "-f", "app/definitions.py"]
