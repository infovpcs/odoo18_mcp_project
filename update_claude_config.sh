#!/bin/bash

# Path to Claude Desktop configuration
CONFIG_PATH="$HOME/Library/Application Support/Claude/config.json"

# Check if the configuration file exists
if [ ! -f "$CONFIG_PATH" ]; then
    echo "Claude Desktop configuration file not found at $CONFIG_PATH"
    exit 1
fi

# Copy the new configuration
cp claude_config.json "$CONFIG_PATH"

echo "Claude Desktop configuration updated successfully!"
echo "Please restart Claude Desktop for the changes to take effect."