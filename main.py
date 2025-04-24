#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main entry point for the Odoo 18 MCP Integration project.

This module provides the main entry point for the MCP server.
"""

import argparse
import os
from typing import Optional

from src.core import get_settings, get_logger
from src.mcp.client import MCPClient
from src.odoo.client import OdooClient
from src.odoo.schemas import OdooConfig


logger = get_logger(__name__)


def main() -> None:
    """Run the MCP server."""
    parser = argparse.ArgumentParser(description="Odoo 18 MCP Integration Server")
    parser.add_argument(
        "--host",
        type=str,
        help="Host to bind to",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port to bind to",
    )
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test Odoo connection and exit",
    )
    args = parser.parse_args()

    settings = get_settings()
    
    if args.test_connection:
        test_odoo_connection()
        return

    # Create and run MCP server
    mcp_client = MCPClient()
    mcp_client.run(host=args.host, port=args.port)


def test_odoo_connection() -> None:
    """Test the Odoo connection."""
    settings = get_settings()
    logger.info("Testing Odoo connection...")
    
    try:
        config = OdooConfig(**settings.dict_for_odoo_client())
        client = OdooClient(config)
        client.authenticate()
        
        # Test a simple operation
        version_info = client.execute('ir.module.module', 'get_module_info', 'base')
        logger.info(f"Connected to Odoo server at {config.url}")
        logger.info(f"Odoo version: {version_info.get('version', 'Unknown')}")
        logger.info("Connection test successful!")
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()
