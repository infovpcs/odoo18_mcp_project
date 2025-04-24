#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main entry point for the Odoo 18 MCP Integration project.

This module provides the main entry point for the MCP server and related functionality.
"""

import argparse
import os
import sys
import subprocess
from typing import Optional, List

from src.core import get_settings, get_logger
from src.mcp.client import MCPClient
from src.odoo.client import OdooClient
from src.odoo.schemas import OdooConfig


logger = get_logger(__name__)


def main() -> None:
    """Run the MCP server or related functionality."""
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
    parser.add_argument(
        "--standalone",
        action="store_true",
        help="Run the standalone MCP server for testing",
    )
    parser.add_argument(
        "--test",
        choices=["functions", "tools", "all"],
        help="Run tests: 'functions' for direct function tests, 'tools' for HTTP tool tests, 'all' for both",
    )
    args = parser.parse_args()

    settings = get_settings()

    if args.test_connection:
        test_odoo_connection()
        return

    if args.standalone:
        run_standalone_server(host=args.host, port=args.port)
        return

    if args.test:
        run_tests(args.test)
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


def run_standalone_server(host: Optional[str] = None, port: Optional[int] = None) -> None:
    """Run the standalone MCP server for testing."""
    logger.info("Starting standalone MCP server...")

    cmd = [sys.executable, "standalone_mcp_server.py"]
    if host:
        os.environ["HOST"] = host
    if port:
        os.environ["PORT"] = str(port)

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run standalone server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Standalone server stopped by user")


def run_tests(test_type: str) -> None:
    """Run the specified tests."""
    test_scripts: List[str] = []

    if test_type == "functions" or test_type == "all":
        test_scripts.append("test_mcp_functions.py")

    if test_type == "tools" or test_type == "all":
        test_scripts.append("test_mcp_tools.py")

    logger.info(f"Running tests: {', '.join(test_scripts)}")

    for script in test_scripts:
        logger.info(f"Running {script}...")
        try:
            subprocess.run([sys.executable, script], check=True)
            logger.info(f"{script} completed successfully")
        except subprocess.CalledProcessError as e:
            logger.error(f"Test {script} failed: {e}")
            sys.exit(1)

    logger.info("All tests completed successfully")


if __name__ == "__main__":
    main()
