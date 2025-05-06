#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the Export/Import Agent.

This script tests the langgraph agent flow for exporting and importing Odoo records.
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import the agent
try:
    from src.agents.export_import.main import run_export_import_agent
    from src.agents.export_import.state import AgentState, FlowMode
except ImportError:
    print("Failed to import Export/Import Agent. Make sure the package is installed.")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_export_import_agent")

# Load environment variables
load_dotenv()

# Get Odoo connection details from environment variables
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "llmdb18")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

# Test data directory
TEST_DATA_DIR = os.path.join(project_root, "tests", "data")
os.makedirs(TEST_DATA_DIR, exist_ok=True)


def test_export_flow(model_name: str, domain: Optional[str] = None,
                    fields: Optional[List[str]] = None, limit: int = 10,
                    export_path: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
    """Test the export flow of the Export/Import Agent.

    Args:
        model_name: Name of the model to export
        domain: Domain filter in string format
        fields: List of fields to export
        limit: Maximum number of records to export
        export_path: Path to export the CSV file

    Returns:
        Tuple of (success, result)
    """
    logger.info(f"Testing export flow for model: {model_name}")

    # Default export path if not provided
    if not export_path:
        export_path = os.path.join(TEST_DATA_DIR, f"{model_name.replace('.', '_')}_export.csv")

    # Run the agent in export mode
    result = run_export_import_agent(
        mode=FlowMode.EXPORT,
        model_name=model_name,
        domain=domain,
        fields=fields,
        limit=limit,
        export_path=export_path,
        odoo_url=ODOO_URL,
        odoo_db=ODOO_DB,
        odoo_username=ODOO_USERNAME,
        odoo_password=ODOO_PASSWORD
    )

    # Check if the export was successful
    if result.get("error"):
        logger.error(f"Export failed: {result['error']}")
        return False, result

    # Check if the file was created
    if not os.path.exists(export_path):
        logger.error(f"Export file was not created: {export_path}")
        return False, result

    # Get file size
    file_size = os.path.getsize(export_path)
    logger.info(f"Export successful. File created at: {export_path} (Size: {file_size} bytes)")

    # Check if the file has content
    if file_size == 0:
        logger.error("Export file is empty")
        return False, result

    return True, result


def test_import_flow(model_name: str, input_path: str,
                    field_mapping: Optional[Dict[str, str]] = None,
                    create_if_not_exists: bool = True,
                    update_if_exists: bool = True) -> Tuple[bool, Dict[str, Any]]:
    """Test the import flow of the Export/Import Agent.

    Args:
        model_name: Name of the model to import into
        input_path: Path to the CSV file to import
        field_mapping: Mapping from CSV field names to Odoo field names
        create_if_not_exists: Whether to create new records if they don't exist
        update_if_exists: Whether to update existing records

    Returns:
        Tuple of (success, result)
    """
    logger.info(f"Testing import flow for model: {model_name}")

    # Check if the input file exists
    if not os.path.exists(input_path):
        logger.error(f"Input file does not exist: {input_path}")
        return False, {"error": f"Input file does not exist: {input_path}"}

    # Run the agent in import mode
    result = run_export_import_agent(
        mode=FlowMode.IMPORT,
        model_name=model_name,
        input_path=input_path,
        field_mapping=field_mapping,
        create_if_not_exists=create_if_not_exists,
        update_if_exists=update_if_exists,
        odoo_url=ODOO_URL,
        odoo_db=ODOO_DB,
        odoo_username=ODOO_USERNAME,
        odoo_password=ODOO_PASSWORD
    )

    # Check if the import was successful
    if result.get("error"):
        logger.error(f"Import failed: {result['error']}")
        return False, result

    logger.info(f"Import successful. Records processed: {result.get('records_processed', 0)}")
    return True, result


def test_export_import_cycle(model_name: str, domain: Optional[str] = None,
                           fields: Optional[List[str]] = None, limit: int = 10) -> bool:
    """Test a complete export-import cycle for a model.

    Args:
        model_name: Name of the model to test
        domain: Domain filter in string format
        fields: List of fields to export
        limit: Maximum number of records to export

    Returns:
        True if the test was successful, False otherwise
    """
    logger.info(f"Testing export-import cycle for model: {model_name}")

    # Export path
    export_path = os.path.join(TEST_DATA_DIR, f"{model_name.replace('.', '_')}_cycle.csv")

    # Step 1: Export
    export_success, export_result = test_export_flow(
        model_name=model_name,
        domain=domain,
        fields=fields,
        limit=limit,
        export_path=export_path
    )

    if not export_success:
        logger.error("Export step failed")
        return False

    # Step 2: Import
    import_success, import_result = test_import_flow(
        model_name=model_name,
        input_path=export_path
    )

    if not import_success:
        logger.error("Import step failed")
        return False

    logger.info("Export-import cycle completed successfully")
    return True


def test_related_models_export_import(parent_model: str, child_model: str,
                                    relation_field: str, limit: int = 5) -> bool:
    """Test export and import of related models.

    Args:
        parent_model: Name of the parent model
        child_model: Name of the child model
        relation_field: Field in the child model that relates to the parent
        limit: Maximum number of parent records to export

    Returns:
        True if the test was successful, False otherwise
    """
    logger.info(f"Testing related models export-import for {parent_model} and {child_model}")

    # Export path
    export_path = os.path.join(TEST_DATA_DIR, f"{parent_model.replace('.', '_')}_related.csv")

    # Run the agent in export mode with related models
    export_result = run_export_import_agent(
        mode=FlowMode.EXPORT,
        parent_model=parent_model,
        child_model=child_model,
        relation_field=relation_field,
        limit=limit,
        export_path=export_path,
        odoo_url=ODOO_URL,
        odoo_db=ODOO_DB,
        odoo_username=ODOO_USERNAME,
        odoo_password=ODOO_PASSWORD
    )

    # Check if the export was successful
    if export_result.get("error"):
        logger.error(f"Related models export failed: {export_result['error']}")
        return False

    # Check if the file was created
    if not os.path.exists(export_path):
        logger.error(f"Related models export file was not created: {export_path}")
        return False

    # Run the agent in import mode with related models
    import_result = run_export_import_agent(
        mode=FlowMode.IMPORT,
        parent_model=parent_model,
        child_model=child_model,
        relation_field=relation_field,
        input_path=export_path,
        odoo_url=ODOO_URL,
        odoo_db=ODOO_DB,
        odoo_username=ODOO_USERNAME,
        odoo_password=ODOO_PASSWORD
    )

    # Check if the import was successful
    if import_result.get("error"):
        logger.error(f"Related models import failed: {import_result['error']}")
        return False

    logger.info("Related models export-import completed successfully")
    return True


def main():
    """Main function to run the tests."""
    parser = argparse.ArgumentParser(description="Test the Export/Import Agent")
    parser.add_argument("--export", action="store_true", help="Test export flow")
    parser.add_argument("--import_data", action="store_true", help="Test import flow")
    parser.add_argument("--cycle", action="store_true", help="Test export-import cycle")
    parser.add_argument("--related", action="store_true", help="Test related models export-import")
    parser.add_argument("--model", default="res.partner", help="Model to test (default: res.partner)")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of records to export")
    args = parser.parse_args()

    # Run the requested tests
    if args.export:
        test_export_flow(args.model, limit=args.limit)

    if args.import_data:
        # First export to create a file to import
        export_path = os.path.join(TEST_DATA_DIR, f"{args.model.replace('.', '_')}_for_import.csv")
        test_export_flow(args.model, limit=args.limit, export_path=export_path)
        test_import_flow(args.model, export_path)

    if args.cycle:
        test_export_import_cycle(args.model, limit=args.limit)

    if args.related:
        # Test related models based on the selected model
        if args.model == "res.partner":
            test_related_models_export_import("res.partner", "res.partner.bank", "partner_id", limit=args.limit)
        elif args.model == "sale.order":
            test_related_models_export_import("sale.order", "sale.order.line", "order_id", limit=args.limit)
        elif args.model == "account.move":
            test_related_models_export_import("account.move", "account.move.line", "move_id", limit=args.limit)
        elif args.model == "project.project":
            test_related_models_export_import("project.project", "project.task", "project_id", limit=args.limit)
        else:
            logger.error(f"Related models test not implemented for model: {args.model}")

    # If no specific test is requested, run all tests with default model
    if not (args.export or args.import_data or args.cycle or args.related):
        logger.info("Running all tests with default model: res.partner")
        test_export_flow("res.partner", limit=args.limit)
        test_export_import_cycle("res.partner", limit=args.limit)
        test_related_models_export_import("res.partner", "res.partner.bank", "partner_id", limit=args.limit)


if __name__ == "__main__":
    main()
