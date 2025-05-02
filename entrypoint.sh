#!/bin/sh

# Create required directories with proper permissions
mkdir -p /app/logs /app/data /app/exports /app/tmp
chown -R mcp:mcp /app/logs /app/data /app/exports /app/tmp

# Switch to non-root user
exec su -s /bin/sh mcp -c "if [ \"\$1\" = \"standalone\" ]; then exec python standalone_mcp_server.py; elif [ \"\$1\" = \"test\" ]; then if [ \"\$2\" = \"functions\" ]; then exec python test_mcp_functions.py; elif [ \"\$2\" = \"tools\" ]; then exec python test_mcp_tools.py; elif [ \"\$2\" = \"all\" ]; then python test_mcp_functions.py && python test_mcp_tools.py; else echo \"Unknown test type: \$2\"; exit 1; fi; else exec python main.py \$@; fi"