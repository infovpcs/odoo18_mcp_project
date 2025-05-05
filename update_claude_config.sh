#!/bin/bash

# Path to Claude Desktop configuration
CONFIG_PATH="$HOME/Library/Application Support/Claude/config.json"

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
envsubst < claude_config.json > claude_config_temp.json

# Copy the new configuration
cp claude_config_temp.json "$CONFIG_PATH"

# Clean up temporary file
rm claude_config_temp.json

echo "Claude Desktop configuration updated successfully!"
echo "Please restart Claude Desktop for the changes to take effect."