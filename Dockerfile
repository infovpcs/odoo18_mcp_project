FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY setup.py pyproject.toml ./
COPY README.md ./
COPY src ./src

# Install dependencies
RUN pip install --no-cache-dir .

# Copy the rest of the application
COPY main.py mcp_server.py standalone_mcp_server.py ./
COPY test_mcp_functions.py test_mcp_tools.py ./
COPY .env.example ./.env.example

# Create a directory for logs
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ODOO_URL=http://localhost:8069
ENV ODOO_DB=llmdb18
ENV ODOO_USERNAME=admin
ENV ODOO_PASSWORD=admin

# Expose the port the app runs on
EXPOSE 8000

# Create entrypoint script
RUN echo '#!/bin/sh\n\
if [ "$1" = "standalone" ]; then\n\
    exec python standalone_mcp_server.py\n\
elif [ "$1" = "test" ]; then\n\
    if [ "$2" = "functions" ]; then\n\
        exec python test_mcp_functions.py\n\
    elif [ "$2" = "tools" ]; then\n\
        exec python test_mcp_tools.py\n\
    elif [ "$2" = "all" ]; then\n\
        python test_mcp_functions.py && python test_mcp_tools.py\n\
    else\n\
        echo "Unknown test type: $2"\n\
        exit 1\n\
    fi\n\
else\n\
    exec python main.py "$@"\n\
fi' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Command to run the application
ENTRYPOINT ["/app/entrypoint.sh"]
CMD []