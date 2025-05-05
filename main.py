#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main entry point for the Odoo 18 MCP Integration project.

This module provides the main entry point for the MCP server and related functionality.
It supports various operations including:
- Running the MCP server
- Testing Odoo connections
- Running standalone MCP server for testing
- Running export/import operations
- Testing the Odoo documentation RAG functionality
"""

import argparse
import os
import sys
import subprocess
import json
import subprocess
import sys

# CLI wrappers for dynamic_data_tool
def mdt_export(model_name: str, export_path: str, domain=None, fields=None, limit=None):
    """Export records from a model to a CSV file using dynamic_data_tool.py.

    Args:
        model_name: The technical name of the Odoo model
        export_path: Path to export CSV file
        domain: Optional domain filter as a Python list of tuples
        fields: Optional list of fields to export
        limit: Optional limit on number of records to export

    Returns:
        Dictionary with export results
    """
    cmd = [sys.executable, 'scripts/dynamic_data_tool.py', 'export', '--model', model_name, '--output', export_path]
    if domain:
        cmd.extend(['--domain', json.dumps(domain)])
    if fields:
        cmd.extend(['--fields', ','.join(fields)])
    subprocess.run(cmd, check=True)
    total = 0
    try:
        with open(export_path) as f: total = len(f.readlines()) -1
    except IOError:
        pass
    return {'success': True, 'total_records': total, 'export_path': export_path}

def mdt_import(import_path: str, model_name: str, defaults=None, force=False, skip_invalid=False):
    """Import records from a CSV file into a model using dynamic_data_tool.py.

    Args:
        import_path: Path to import CSV file
        model_name: The technical name of the Odoo model
        defaults: Optional default values for fields as a Python dict
        force: Whether to force import even if required fields are missing
        skip_invalid: Whether to skip invalid values for selection fields

    Returns:
        Dictionary with import results
    """
    cmd = [sys.executable, 'scripts/dynamic_data_tool.py', 'import', '--model', model_name, '--input', import_path]
    if defaults:
        cmd.extend(['--defaults', json.dumps(defaults)])
    if force:
        cmd.append('--force')
    if skip_invalid:
        cmd.append('--skip-invalid')
    subprocess.run(cmd, check=True)
    total = 0
    try:
        with open(import_path) as f: total = len(f.readlines()) -1
    except IOError:
        pass
    return {'success': True, 'imported_records': total, 'updated_records': 0}

from typing import Optional, List, Dict, Any, Union

from src.core import get_settings, get_logger
from src.mcp.client import MCPClient
from src.odoo.client import OdooClient
from src.odoo.schemas import OdooConfig

# Check if Odoo documentation RAG is available
try:
    from src.odoo_docs_rag import OdooDocsRetriever
    odoo_docs_retriever_available = True
except ImportError:
    odoo_docs_retriever_available = False

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
        choices=["functions", "tools", "all", "export_import", "advanced_search", "docs_rag"],
        help="Run tests: 'functions' for direct function tests, 'tools' for HTTP tool tests, "
             "'export_import' for export/import functionality, 'advanced_search' for advanced search, "
             "'docs_rag' for Odoo documentation RAG, 'all' for all tests",
    )
    parser.add_argument(
        "--export-model",
        type=str,
        help="Model to export (used with --test export_import)",
    )
    parser.add_argument(
        "--export-path",
        type=str,
        default="./tmp/export.csv",
        help="Path to export CSV file (used with --test export_import)",
    )
    parser.add_argument(
        "--import-path",
        type=str,
        help="Path to import CSV file (used with --test export_import)",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Query to use for advanced search or docs RAG (used with --test advanced_search or docs_rag)",
    )
    args = parser.parse_args()

    # Get settings
    settings = get_settings()

    if args.test_connection:
        test_odoo_connection()
        return

    if args.standalone:
        run_standalone_server(host=args.host, port=args.port)
        return

    if args.test:
        if args.test == "export_import":
            if not args.export_model:
                logger.error("Export model is required for export/import test")
                sys.exit(1)
            test_export_import(
                model_name=args.export_model,
                export_path=args.export_path,
                import_path=args.import_path
            )
        elif args.test == "advanced_search":
            if not args.query:
                logger.error("Query is required for advanced search test")
                sys.exit(1)
            test_advanced_search(query=args.query)
        elif args.test == "docs_rag":
            if not args.query:
                logger.error("Query is required for docs RAG test")
                sys.exit(1)
            test_docs_rag(query=args.query)
        else:
            run_tests(args.test)
        return

    # Create and run MCP server
    mcp_client = MCPClient()
    mcp_client.run(host=args.host, port=args.port)


def test_odoo_connection() -> None:
    """Test the Odoo connection and display information about the server.

    This function tests the connection to the Odoo server and displays information
    about the server, including the version, database, and available modules.
    """
    settings = get_settings()
    logger.info("Testing Odoo connection...")

    try:
        # Create Odoo client
        config = OdooConfig(**settings.dict_for_odoo_client())
        client = OdooClient(config)
        client.authenticate()

        # Test a simple operation to get version info
        version_info = client.execute('ir.module.module', 'get_module_info', 'base')

        # Get server info
        server_info = {
            "url": config.url,
            "database": config.database,
            "username": config.username,
            "version": version_info.get('version', 'Unknown'),
            "installed_modules": 0,
            "models_count": 0,
        }

        # Get count of installed modules
        try:
            installed_modules_count = client.search_count(
                'ir.module.module',
                [('state', '=', 'installed')]
            )
            server_info["installed_modules"] = installed_modules_count
        except Exception as e:
            logger.warning(f"Could not get installed modules count: {str(e)}")

        # Get count of models
        try:
            models_count = client.search_count(
                'ir.model',
                [('transient', '=', False)]
            )
            server_info["models_count"] = models_count
        except Exception as e:
            logger.warning(f"Could not get models count: {str(e)}")

        # Display server info
        print("\n" + "=" * 80)
        print("Odoo Server Information:")
        print("=" * 80)
        print(f"URL:              {server_info['url']}")
        print(f"Database:         {server_info['database']}")
        print(f"Username:         {server_info['username']}")
        print(f"Odoo Version:     {server_info['version']}")
        print(f"Installed Modules: {server_info['installed_modules']}")
        print(f"Available Models: {server_info['models_count']}")
        print("=" * 80 + "\n")

        logger.info("Connection test successful!")

    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        raise


def run_standalone_server(host: Optional[str] = None, port: Optional[int] = None) -> None:
    """Run the standalone MCP server for testing.

    This function starts the standalone MCP server, which provides a simplified HTTP API
    for testing MCP tools without requiring the full MCP client.

    Args:
        host: The host to bind to (default: 0.0.0.0)
        port: The port to bind to (default: 8001)
    """
    logger.info("Starting standalone MCP server...")

    # Set environment variables for the server
    if host:
        os.environ["HOST"] = host
    if port:
        os.environ["PORT"] = str(port)

    # Check if the mcp_server.py file exists
    if not os.path.exists("mcp_server.py"):
        logger.error("mcp_server.py not found. Make sure you're in the correct directory.")
        sys.exit(1)

    # Check if the standalone_mcp_server.py file exists
    if not os.path.exists("standalone_mcp_server.py"):
        logger.error("standalone_mcp_server.py not found. Make sure you're in the correct directory.")
        sys.exit(1)

    # Run the standalone server
    cmd = [sys.executable, "standalone_mcp_server.py"]

    try:
        # Print the command for debugging
        logger.info(f"Running command: {' '.join(cmd)}")

        # Run the server
        subprocess.run(cmd, check=True)

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to run standalone server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Standalone server stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error running standalone server: {str(e)}")
        sys.exit(1)


def run_tests(test_type: str) -> None:
    """Run the specified tests."""
    test_scripts: List[str] = []

    if test_type == "functions" or test_type == "all":
        test_scripts.append("test_mcp_functions.py")

    if test_type == "tools" or test_type == "all":
        test_scripts.append("test_mcp_tools.py")

    if test_type == "all":
        test_scripts.append("test_export_import_tools.py")
        test_scripts.append("test_advanced_search_tool.py")
        if odoo_docs_retriever_available:
            test_scripts.append("test_odoo_docs_rag.py")

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


def test_export_import(model_name: str, export_path: str, import_path: Optional[str] = None) -> None:
    """Test the export/import functionality.

    Args:
        model_name: The model to export/import
        export_path: Path to export CSV file
        import_path: Path to import CSV file (if None, will use export_path for import)
    """
    logger.info(f"Testing export/import for model {model_name}")

    try:
        # Import the direct export/import implementation
        from direct_export_import import export_records, import_records

        # Ensure the export directory exists
        export_dir = os.path.dirname(export_path)
        if export_dir and not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)

        # Export records
        logger.info(f"Exporting records from {model_name} to {export_path}")
        export_result = export_records(
            model_name=model_name,
            export_path=export_path,
            domain=[],  # Empty domain to export all records
            fields=None,  # Auto-detect fields
            limit=100  # Limit to 100 records for testing
        )

        if not export_result["success"]:
            logger.error(f"Export failed: {export_result.get('error', 'Unknown error')}")
            sys.exit(1)

        logger.info(f"Export successful: {export_result['total_records']} records exported to {export_result['export_path']}")

        # Import records if import_path is provided
        if import_path:
            if not os.path.exists(import_path):
                logger.error(f"Import file not found: {import_path}")
                sys.exit(1)

            logger.info(f"Importing records from {import_path} to {model_name}")
            import_result = import_records(
                import_path=import_path,
                model_name=model_name,
                field_mapping=None,  # Auto-detect field mapping
                create_if_not_exists=True,
                update_if_exists=True
            )

            if not import_result["success"]:
                logger.error(f"Import failed: {import_result.get('error', 'Unknown error')}")
                sys.exit(1)

            logger.info(f"Import successful: {import_result['imported_records']} records created, {import_result['updated_records']} records updated")

    except ImportError:
        logger.error("Failed to import export/import implementation")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error testing export/import: {str(e)}")
        sys.exit(1)


def test_advanced_search(query: str) -> None:
    """Test the advanced search functionality.

    Args:
        query: The query to search for
    """
    logger.info(f"Testing advanced search with query: {query}")

    try:
        # Import the advanced search implementation
        from advanced_search import AdvancedSearch

        # Initialize Odoo model discovery
        from mcp_server import OdooModelDiscovery

        # Get Odoo connection details from environment variables
        odoo_url = os.getenv("ODOO_URL", "http://localhost:8069")
        odoo_db = os.getenv("ODOO_DB", "llmdb18")
        odoo_username = os.getenv("ODOO_USERNAME", "admin")
        odoo_password = os.getenv("ODOO_PASSWORD", "admin")

        # Initialize model discovery
        model_discovery = OdooModelDiscovery(odoo_url, odoo_db, odoo_username, odoo_password)

        # Initialize advanced search
        advanced_search = AdvancedSearch(model_discovery)

        # Execute the query
        result = advanced_search.execute_query(query, limit=100)

        # Print the result
        print("\n" + "=" * 80)
        print("Advanced Search Results:")
        print("=" * 80)
        print(result)
        print("=" * 80 + "\n")

    except ImportError:
        logger.error("Failed to import advanced search implementation")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error testing advanced search: {str(e)}")
        sys.exit(1)


def test_docs_rag(query: str) -> None:
    """Test the Odoo documentation RAG functionality.

    Args:
        query: The query to search for in the documentation
    """
    if not odoo_docs_retriever_available:
        logger.error("Odoo documentation RAG is not available")
        logger.error("Install the required dependencies: sentence-transformers, faiss-cpu, beautifulsoup4, markdown, gitpython")
        sys.exit(1)

    logger.info(f"Testing Odoo documentation RAG with query: {query}")

    try:
        # Use a directory in the project for storing the documentation
        docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "odoo_docs")
        index_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "odoo_docs_index")

        # Create directories if they don't exist
        os.makedirs(docs_dir, exist_ok=True)
        os.makedirs(index_dir, exist_ok=True)

        # Initialize the retriever
        retriever = OdooDocsRetriever(
            docs_dir=docs_dir,
            index_dir=index_dir,
            force_rebuild=False  # Set to True to force rebuilding the index
        )

        # Query the documentation
        result = retriever.query(query, max_results=5)

        # Print the result
        print("\n" + "=" * 80)
        print("Odoo Documentation RAG Results:")
        print("=" * 80)
        print(result)
        print("=" * 80 + "\n")

    except Exception as e:
        logger.error(f"Error testing Odoo documentation RAG: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
