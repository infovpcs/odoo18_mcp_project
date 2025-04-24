#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple MCP Server for testing

This is a minimal MCP server for testing the MCP SDK integration.
"""

import sys
import traceback
import logging

# Set up basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("simple_mcp")

try:
    from mcp.server.fastmcp import FastMCP, Context

    # Create a simple MCP server
    mcp = FastMCP(
        "Simple Odoo MCP",
        description="A simple MCP server for testing",
    )

    # Add a simple resource
    @mcp.resource("https://example.com/hello")
    def hello() -> str:
        """Say hello."""
        return "# Hello from Simple Odoo MCP Server\n\nThis is a test resource."

    # Add a simple tool
    @mcp.tool()
    def echo(message: str, ctx: Context) -> str:
        """Echo a message.
        
        Args:
            message: The message to echo
            
        Returns:
            The same message
        """
        return f"You said: {message}"

    # Main entry point
    if __name__ == "__main__":
        try:
            logger.info("Starting simple MCP server...")
            mcp.run()
        except Exception as e:
            logger.error(f"Error running MCP server: {str(e)}")
            traceback.print_exc()

except Exception as e:
    logger.error(f"Error during initialization: {str(e)}")
    traceback.print_exc()