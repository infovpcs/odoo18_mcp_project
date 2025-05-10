# Build stage
FROM python:3.10-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY setup.py pyproject.toml ./
COPY README.md ./
COPY src ./src

# Install dependencies
RUN pip install --no-cache-dir build wheel
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -e .

# Final stage
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js and NPM for mermaid-cli
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    && npm install -g npm@latest \
    && npm install -g @mermaid-js/mermaid-cli \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder stage
COPY --from=builder /app/wheels /app/wheels

# Install the application
RUN pip install --no-cache-dir /app/wheels/*.whl

# Copy the rest of the application
COPY main.py mcp_server.py standalone_mcp_server.py ./
COPY .env.example ./.env.example
COPY entrypoint.sh /app/entrypoint.sh
COPY src ./src
COPY tests ./tests

# Create directories for logs, data, and generated modules
RUN mkdir -p /app/logs /app/data /app/exports /app/tmp /app/generated_modules

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ODOO_URL=http://localhost:8069
ENV ODOO_DB=llmdb18
ENV ODOO_USERNAME=admin
ENV ODOO_PASSWORD=admin
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Create a non-root user to run the application
RUN groupadd -r mcp && useradd -r -g mcp mcp
RUN chown -R mcp:mcp /app /app/logs /app/data /app/exports /app/tmp /app/generated_modules
USER mcp

# Expose the port the app runs on
EXPOSE 8000

# Set entrypoint script permissions
USER root
RUN chmod +x /app/entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
ENTRYPOINT ["/app/entrypoint.sh"]
CMD []