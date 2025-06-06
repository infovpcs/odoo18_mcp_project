#!/bin/bash

# Path to Claude Desktop configuration
CONFIG_PATH="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

# Check if the configuration file exists
if [ ! -f "$CONFIG_PATH" ]; then
    echo "Claude Desktop configuration file not found at $CONFIG_PATH"
    exit 1
fi

# Load environment variables from .env file
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(grep -v '^#' .env | xargs)
else
    echo "Warning: .env file not found. Using default values."
    # Set default values
    export GEMINI_API_KEY="your-api-key-here"
    export GEMINI_MODEL="gemini-2.0-flash"
fi

# Create a temporary file with environment variables substituted
echo "Creating configuration with environment variables..."
cat <<EOF | envsubst > claude_config_temp.json
{
  "mcpServers": {
    "odoo18-mcp": {
      "command": "$(which python3)",
      "args": [
        "$(pwd)/mcp_server.py"
      ],
      "env": {
        "ODOO_URL": "${ODOO_URL}",
        "ODOO_DB": "${ODOO_DB}",
        "ODOO_USERNAME": "${ODOO_USERNAME}",
        "ODOO_PASSWORD": "${ODOO_PASSWORD}",
        "GEMINI_MODEL": "${GEMINI_MODEL}",
        "GEMINI_API_KEY": "${GEMINI_API_KEY}",
        "BRAVE_API_KEY": "${BRAVE_API_KEY}",
        "ODOO_DOCS_DIR": "$(pwd)/odoo_docs",
        "ODOO_INDEX_DIR": "$(pwd)/odoo_docs_index",
        "ODOO_DB_PATH": "$(pwd)/odoo_docs_index/embeddings.db"
      }
    }
  }
}
EOF

# Copy the new configuration
cp claude_config_temp.json "$CONFIG_PATH"


# Clean up temporary file
rm claude_config_temp.json

echo "Claude Desktop configuration updated successfully!"
echo "Please restart Claude Desktop for the changes to take effect."