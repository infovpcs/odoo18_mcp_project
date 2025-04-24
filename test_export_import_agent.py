#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the Export/Import agent flow.
"""

import os
import sys
import logging
import argparse
from dotenv import load_dotenv

from src.agents.export_import.main import run_export_flow, run_import_flow

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_export_import")

# Load environment variables
load_dotenv()

# Get Odoo connection details from environment variables
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "llmdb18")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")


def test_export_flow():
    """Test the export flow with res.partner model."""
    logger.info("Testing export flow with res.partner model")

    # Create exports directory if it doesn't exist
    os.makedirs("exports", exist_ok=True)

    # Run the export flow
    result = run_export_flow(
        model_name="res.partner",
        fields=["id", "name", "email", "phone", "street", "city", "country_id"],
        filter_domain=[("customer_rank", ">", 0)],  # Only customers
        limit=100,
        export_path="exports/partners_export.csv",
        odoo_url=ODOO_URL,
        odoo_db=ODOO_DB,
        odoo_username=ODOO_USERNAME,
        odoo_password=ODOO_PASSWORD
    )

    # Print the results
    logger.info(f"Export success: {result['success']}")
    logger.info(f"Total records: {result['total_records']}")
    logger.info(f"Exported records: {result['exported_records']}")
    logger.info(f"Export path: {result['export_path']}")

    if not result["success"]:
        logger.error(f"Export error: {result.get('error', 'Unknown error')}")

    return result


def test_import_flow():
    """Test the import flow with res.partner model."""
    logger.info("Testing import flow with res.partner model")

    # Check if export file exists
    export_path = "exports/partners_export.csv"
    if not os.path.exists(export_path):
        logger.error(f"Export file not found: {export_path}")
        logger.info("Run test_export_flow first to create the export file")
        return None

    # Define field mapping
    field_mapping = {
        "id": "id",
        "name": "name",
        "email": "email",
        "phone": "phone",
        "street": "street",
        "city": "city",
        "country_id": "country_id"
    }

    # Run the import flow
    result = run_import_flow(
        import_path=export_path,
        model_name="res.partner",
        field_mapping=field_mapping,
        create_if_not_exists=False,  # Only update existing records
        update_if_exists=True,
        odoo_url=ODOO_URL,
        odoo_db=ODOO_DB,
        odoo_username=ODOO_USERNAME,
        odoo_password=ODOO_PASSWORD
    )

    # Print the results
    logger.info(f"Import success: {result['success']}")
    logger.info(f"Total records: {result['total_records']}")
    logger.info(f"Created records: {result['imported_records']}")
    logger.info(f"Updated records: {result['updated_records']}")
    logger.info(f"Failed records: {result['failed_records']}")

    if not result["success"]:
        logger.error(f"Import error: {result.get('error', 'Unknown error')}")

    return result


def test_product_export_flow():
    """Test the export flow with product.product model."""
    logger.info("Testing export flow with product.product model")

    # Create exports directory if it doesn't exist
    os.makedirs("exports", exist_ok=True)

    # Run the export flow
    result = run_export_flow(
        model_name="product.product",
        fields=["id", "name", "default_code", "list_price", "standard_price", "type", "categ_id"],
        filter_domain=[],  # All products
        limit=100,
        export_path="exports/products_export.csv",
        odoo_url=ODOO_URL,
        odoo_db=ODOO_DB,
        odoo_username=ODOO_USERNAME,
        odoo_password=ODOO_PASSWORD
    )

    # Print the results
    logger.info(f"Export success: {result['success']}")
    logger.info(f"Total records: {result['total_records']}")
    logger.info(f"Exported records: {result['exported_records']}")
    logger.info(f"Export path: {result['export_path']}")

    if not result["success"]:
        logger.error(f"Export error: {result.get('error', 'Unknown error')}")

    return result


def main():
    """Main function."""
    # Create exports directory if it doesn't exist
    try:
        os.makedirs("exports", exist_ok=True)
        logger.info("Exports directory created or already exists")
    except Exception as e:
        logger.error(f"Error creating exports directory: {str(e)}")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Test the Export/Import agent flow")
    parser.add_argument("--test", choices=["export", "import", "product"], default="export",
                        help="Test to run (export, import, or product)")

    args = parser.parse_args()

    try:
        if args.test == "export":
            result = test_export_flow()
            if result and result.get("success"):
                logger.info("Export test completed successfully")
            else:
                logger.error("Export test failed")
        elif args.test == "import":
            result = test_import_flow()
            if result and result.get("success"):
                logger.info("Import test completed successfully")
            else:
                logger.error("Import test failed")
        elif args.test == "product":
            result = test_product_export_flow()
            if result and result.get("success"):
                logger.info("Product export test completed successfully")
            else:
                logger.error("Product export test failed")
        else:
            logger.error(f"Unknown test: {args.test}")
    except Exception as e:
        logger.error(f"Error running test: {str(e)}")


if __name__ == "__main__":
    main()