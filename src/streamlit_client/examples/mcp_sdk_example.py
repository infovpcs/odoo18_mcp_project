#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example of using the MCP connector with the HTTP API.

This script demonstrates how to use the MCPConnector class with the HTTP connection
to interact with the MCP server using the HTTP API.
"""

import asyncio
import sys
import logging
from pathlib import Path

# Add the parent directory to the path so we can import the MCPConnector
sys.path.append(str(Path(__file__).parent.parent))

from utils.mcp_connector import MCPConnector, ConnectionType

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_sdk_example")

async def main():
    """Run the MCP SDK example."""
    # Create the MCP connector with HTTP connection
    connector = MCPConnector(
        connection_type=ConnectionType.HTTP,
        server_url="http://localhost:8001"
    )

    # Connect to the MCP server
    logger.info("Connecting to MCP server at http://localhost:8001")
    connected = await connector.connect()

    if not connected:
        logger.error("Failed to connect to MCP server")
        logger.error("Make sure the standalone MCP server is running with: python standalone_mcp_server.py")
        return

    try:
        # Call a tool
        logger.info("Calling search_records tool")
        result = await connector.async_call_tool(
            "search_records",
            {"model_name": "res.partner", "query": "company"}
        )

        # Print the result
        logger.info(f"Result: {result}")

        # Call another tool
        logger.info("Calling advanced_search tool")
        result = await connector.async_call_tool(
            "advanced_search",
            {"query": "List all customers", "limit": 5}
        )

        # Print the result
        logger.info(f"Result: {result}")

    finally:
        # Close the connection
        logger.info("Closing connection")
        await connector.close()

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
