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
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder stage
COPY --from=builder /app/wheels /app/wheels

# Install the application
RUN pip install --no-cache-dir /app/wheels/*.whl

# Copy the rest of the application
COPY main.py mcp_server.py standalone_mcp_server.py ./
COPY test_mcp_functions.py test_mcp_tools.py ./
COPY .env.example ./.env.example

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data /app/exports /app/tmp

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
RUN chown -R mcp:mcp /app
USER mcp

# Expose the port the app runs on
EXPOSE 8000

# Create entrypoint script
USER root
RUN echo '#!/bin/sh\n\
# Create required directories with proper permissions\n\
mkdir -p /app/logs /app/data /app/exports /app/tmp\n\
chown -R mcp:mcp /app/logs /app/data /app/exports /app/tmp\n\
\n\
# Switch to non-root user\n\
exec su -s /bin/sh mcp -c "\\\n\
if [ \\"\\$1\\" = \\"standalone\\" ]; then\\\n\
    exec python standalone_mcp_server.py\\\n\
elif [ \\"\\$1\\" = \\"test\\" ]; then\\\n\
    if [ \\"\\$2\\" = \\"functions\\" ]; then\\\n\
        exec python test_mcp_functions.py\\\n\
    elif [ \\"\\$2\\" = \\"tools\\" ]; then\\\n\
        exec python test_mcp_tools.py\\\n\
    elif [ \\"\\$2\\" = \\"all\\" ]; then\\\n\
        python test_mcp_functions.py && python test_mcp_tools.py\\\n\
    else\\\n\
        echo \\"Unknown test type: \\$2\\"\\\n\
        exit 1\\\n\
    fi\\\n\
else\\\n\
    exec python main.py \\$@\\\n\
fi"\n' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
ENTRYPOINT ["/app/entrypoint.sh"]
CMD []