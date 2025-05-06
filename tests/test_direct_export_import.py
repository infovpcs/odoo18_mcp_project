#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for direct export/import operations.

This script tests the direct export and import functions without using the agent flow.
"""

import os
import sys
import csv
import logging
import argparse
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import the export/import functions
try:
    from src.odoo.export_import.export_functions import export_records_to_csv, export_related_records_to_csv
    from src.odoo.export_import.import_functions import import_records_from_csv, import_related_records_from_csv
    from src.odoo.client import OdooClient
except ImportError:
    print("Failed to import export/import functions. Make sure the package is installed.")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_direct_export_import")

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


def get_odoo_client() -> OdooClient:
    """Get an Odoo client instance.

    Returns:
        OdooClient instance
    """
    return OdooClient(
        url=ODOO_URL,
        db=ODOO_DB,
        username=ODOO_USERNAME,
        password=ODOO_PASSWORD
    )


def test_export_records(model_name: str, domain: Optional[str] = None,
                       fields: Optional[List[str]] = None, limit: int = 10,
                       export_path: Optional[str] = None) -> Tuple[bool, str]:
    """Test exporting records to CSV.

    Args:
        model_name: Name of the model to export
        domain: Domain filter in string format
        fields: List of fields to export
        limit: Maximum number of records to export
        export_path: Path to export the CSV file

    Returns:
        Tuple of (success, export_path)
    """
    logger.info(f"Testing export_records_to_csv for model: {model_name}")

    # Default export path if not provided
    if not export_path:
        export_path = os.path.join(TEST_DATA_DIR, f"{model_name.replace('.', '_')}_direct_export.csv")

    # Get Odoo client
    client = get_odoo_client()

    try:
        # Convert domain string to list if provided
        domain_list = eval(domain) if domain else []

        # Export records
        result = export_records_to_csv(
            client=client,
            model_name=model_name,
            fields=fields,
            filter_domain=domain_list,
            limit=limit,
            export_path=export_path
        )

        # Check if the export was successful
        if not result.get("success", False):
            logger.error(f"Export failed: {result.get('error', 'Unknown error')}")
            return False, export_path

        # Check if the file was created
        if not os.path.exists(export_path):
            logger.error(f"Export file was not created: {export_path}")
            return False, export_path

        # Get file size and record count
        file_size = os.path.getsize(export_path)
        record_count = result.get("record_count", 0)

        logger.info(f"Export successful. File created at: {export_path}")
        logger.info(f"Records exported: {record_count}, File size: {file_size} bytes")

        # Check if the file has content
        if file_size == 0:
            logger.error("Export file is empty")
            return False, export_path

        # Read the CSV file to verify its structure
        with open(export_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            header = next(reader, None)
            first_row = next(reader, None)

            if not header:
                logger.error("CSV file has no header")
                return False, export_path

            logger.info(f"CSV header: {header}")
            if first_row:
                logger.info(f"First row sample: {first_row[:5]}...")

        return True, export_path

    except Exception as e:
        logger.error(f"Error in test_export_records: {str(e)}")
        return False, export_path


def test_import_records(model_name: str, input_path: str,
                      field_mapping: Optional[Dict[str, str]] = None,
                      create_if_not_exists: bool = True,
                      update_if_exists: bool = True) -> bool:
    """Test importing records from CSV.

    Args:
        model_name: Name of the model to import into
        input_path: Path to the CSV file to import
        field_mapping: Mapping from CSV field names to Odoo field names
        create_if_not_exists: Whether to create new records if they don't exist
        update_if_exists: Whether to update existing records

    Returns:
        True if the test was successful, False otherwise
    """
    logger.info(f"Testing import_records_from_csv for model: {model_name}")

    # Check if the input file exists
    if not os.path.exists(input_path):
        logger.error(f"Input file does not exist: {input_path}")
        return False

    # Get Odoo client
    client = get_odoo_client()

    try:
        # Import records
        result = import_records_from_csv(
            client=client,
            model_name=model_name,
            input_path=input_path,
            field_mapping=field_mapping,
            create_if_not_exists=create_if_not_exists,
            update_if_exists=update_if_exists
        )

        # Check if the import was successful
        if not result.get("success", False):
            logger.error(f"Import failed: {result.get('error', 'Unknown error')}")
            return False

        # Get record counts
        created_count = result.get("created_count", 0)
        updated_count = result.get("updated_count", 0)
        skipped_count = result.get("skipped_count", 0)

        logger.info(f"Import successful. Records created: {created_count}, updated: {updated_count}, skipped: {skipped_count}")
        return True

    except Exception as e:
        logger.error(f"Error in test_import_records: {str(e)}")
        return False


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
    logger.info(f"Testing direct export-import cycle for model: {model_name}")

    # Step 1: Export
    export_success, export_path = test_export_records(
        model_name=model_name,
        domain=domain,
        fields=fields,
        limit=limit
    )

    if not export_success:
        logger.error("Direct export step failed")
        return False

    # Step 2: Import
    import_success = test_import_records(
        model_name=model_name,
        input_path=export_path
    )

    if not import_success:
        logger.error("Direct import step failed")
        return False

    logger.info("Direct export-import cycle completed successfully")
    return True


def test_export_related_records(parent_model: str, child_model: str,
                              relation_field: str, limit: int = 5,
                              export_path: Optional[str] = None) -> Tuple[bool, str]:
    """Test exporting related records to CSV.

    Args:
        parent_model: Name of the parent model
        child_model: Name of the child model
        relation_field: Field in the child model that relates to the parent
        limit: Maximum number of parent records to export
        export_path: Path to export the CSV file

    Returns:
        Tuple of (success, export_path)
    """
    logger.info(f"Testing export_related_records_to_csv for {parent_model} and {child_model}")

    # Default export path if not provided
    if not export_path:
        export_path = os.path.join(TEST_DATA_DIR, f"{parent_model.replace('.', '_')}_related_direct.csv")

    # Get Odoo client
    client = get_odoo_client()

    try:
        # Export related records
        result = export_related_records_to_csv(
            client=client,
            parent_model=parent_model,
            child_model=child_model,
            relation_field=relation_field,
            limit=limit,
            export_path=export_path
        )

        # Check if the export was successful
        if not result.get("success", False):
            logger.error(f"Related export failed: {result.get('error', 'Unknown error')}")
            return False, export_path

        # Check if the file was created
        if not os.path.exists(export_path):
            logger.error(f"Related export file was not created: {export_path}")
            return False, export_path

        # Get file size and record counts
        file_size = os.path.getsize(export_path)
        parent_count = result.get("parent_count", 0)
        child_count = result.get("child_count", 0)

        logger.info(f"Related export successful. File created at: {export_path}")
        logger.info(f"Parent records: {parent_count}, Child records: {child_count}, File size: {file_size} bytes")

        return True, export_path

    except Exception as e:
        logger.error(f"Error in test_export_related_records: {str(e)}")
        return False, export_path


def test_import_related_records(parent_model: str, child_model: str,
                              relation_field: str, input_path: str) -> bool:
    """Test importing related records from CSV.

    Args:
        parent_model: Name of the parent model
        child_model: Name of the child model
        relation_field: Field in the child model that relates to the parent
        input_path: Path to the CSV file to import

    Returns:
        True if the test was successful, False otherwise
    """
    logger.info(f"Testing import_related_records_from_csv for {parent_model} and {child_model}")

    # Check if the input file exists
    if not os.path.exists(input_path):
        logger.error(f"Input file does not exist: {input_path}")
        return False

    # Get Odoo client
    client = get_odoo_client()

    try:
        # Import related records
        result = import_related_records_from_csv(
            client=client,
            parent_model=parent_model,
            child_model=child_model,
            relation_field=relation_field,
            input_path=input_path
        )

        # Check if the import was successful
        if not result.get("success", False):
            logger.error(f"Related import failed: {result.get('error', 'Unknown error')}")
            return False

        # Get record counts
        parent_created = result.get("parent_created", 0)
        parent_updated = result.get("parent_updated", 0)
        child_created = result.get("child_created", 0)
        child_updated = result.get("child_updated", 0)

        logger.info(f"Related import successful.")
        logger.info(f"Parent records: created={parent_created}, updated={parent_updated}")
        logger.info(f"Child records: created={child_created}, updated={child_updated}")

        return True

    except Exception as e:
        logger.error(f"Error in test_import_related_records: {str(e)}")
        return False


def main():
    """Main function to run the tests."""
    parser = argparse.ArgumentParser(description="Test direct export/import operations")
    parser.add_argument("--export", action="store_true", help="Test export_records_to_csv")
    parser.add_argument("--import_data", action="store_true", help="Test import_records_from_csv")
    parser.add_argument("--cycle", action="store_true", help="Test export-import cycle")
    parser.add_argument("--related-export", action="store_true", help="Test export_related_records_to_csv")
    parser.add_argument("--related-import", action="store_true", help="Test import_related_records_from_csv")
    parser.add_argument("--model", default="res.partner", help="Model to test (default: res.partner)")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of records to export")
    args = parser.parse_args()

    # Run the requested tests
    if args.export:
        test_export_records(args.model, limit=args.limit)

    if args.import_data:
        # First export to create a file to import
        export_success, export_path = test_export_records(args.model, limit=args.limit)
        if export_success:
            test_import_records(args.model, export_path)

    if args.cycle:
        test_export_import_cycle(args.model, limit=args.limit)

    if args.related_export or args.related_import:
        # Define related models based on the selected model
        related_models = {
            "res.partner": ("res.partner", "res.partner.bank", "partner_id"),
            "sale.order": ("sale.order", "sale.order.line", "order_id"),
            "account.move": ("account.move", "account.move.line", "move_id"),
            "project.project": ("project.project", "project.task", "project_id"),
        }

        if args.model not in related_models:
            logger.error(f"Related models test not implemented for model: {args.model}")
            return

        parent_model, child_model, relation_field = related_models[args.model]

        if args.related_export:
            test_export_related_records(parent_model, child_model, relation_field, limit=args.limit)

        if args.related_import:
            # First export to create a file to import
            export_success, export_path = test_export_related_records(
                parent_model, child_model, relation_field, limit=args.limit
            )
            if export_success:
                test_import_related_records(parent_model, child_model, relation_field, export_path)

    # If no specific test is requested, run all tests with default model
    if not (args.export or args.import_data or args.cycle or args.related_export or args.related_import):
        logger.info("Running all direct export/import tests with default model: res.partner")
        test_export_records("res.partner", limit=args.limit)
        test_export_import_cycle("res.partner", limit=args.limit)
        test_export_related_records("res.partner", "res.partner.bank", "partner_id", limit=args.limit)


if __name__ == "__main__":
    main()
