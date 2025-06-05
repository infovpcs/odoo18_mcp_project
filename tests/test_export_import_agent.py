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
import pytest

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Import the agent
try:
    from export_import_tools import run_export_flow, run_import_flow
    from direct_export_import import export_related_records, import_related_records
    from src.agents.export_import.state import AgentState, FlowMode

    # Define the run_export_import_agent function to match the expected interface
    def run_export_import_agent(
        mode: FlowMode,
        model_name: Optional[str] = None,
        domain: Optional[str] = None,
        fields: Optional[List[str]] = None,
        limit: int = 1000,
        export_path: Optional[str] = None,
        input_path: Optional[str] = None,
        field_mapping: Optional[Dict[str, str]] = None,
        create_if_not_exists: bool = True,
        update_if_exists: bool = True,
        parent_model: Optional[str] = None,
        child_model: Optional[str] = None,
        relation_field: Optional[str] = None,
        odoo_url: str = "http://localhost:8069",
        odoo_db: str = "llmdb18",
        odoo_username: str = "admin",
        odoo_password: str = "admin"
    ) -> Dict[str, Any]:
        """Run the Export/Import Agent.

        Args:
            mode: Mode of operation (export or import)
            model_name: Name of the model to export/import
            domain: Domain filter in string format
            fields: List of fields to export
            limit: Maximum number of records to export
            export_path: Path to export the CSV file
            input_path: Path to the CSV file to import
            field_mapping: Mapping from CSV field names to Odoo field names
            create_if_not_exists: Whether to create new records if they don't exist
            update_if_exists: Whether to update existing records
            parent_model: Name of the parent model for related models export/import
            child_model: Name of the child model for related models export/import
            relation_field: Field in the child model that relates to the parent
            odoo_url: URL of the Odoo server
            odoo_db: Name of the Odoo database
            odoo_username: Odoo username
            odoo_password: Odoo password

        Returns:
            Dictionary with the result of the operation
        """
        # Set environment variables for Odoo connection
        os.environ["ODOO_URL"] = odoo_url
        os.environ["ODOO_DB"] = odoo_db
        os.environ["ODOO_USERNAME"] = odoo_username
        os.environ["ODOO_PASSWORD"] = odoo_password

        if mode == FlowMode.EXPORT:
            if parent_model and child_model and relation_field:
                # Handle related models export using direct_export_import.py
                return export_related_records(
                    parent_model=parent_model,
                    child_model=child_model,
                    relation_field=relation_field,
                    parent_fields=fields,
                    filter_domain=domain,
                    limit=limit,
                    export_path=export_path
                )
            else:
                # Handle single model export
                return run_export_flow(
                    model_name=model_name,
                    fields=fields,
                    filter_domain=domain,
                    limit=limit,
                    export_path=export_path,
                    odoo_url=odoo_url,
                    odoo_db=odoo_db,
                    odoo_username=odoo_username,
                    odoo_password=odoo_password
                )
        else:  # Import mode
            if parent_model and child_model and relation_field:
                # Handle related models import using direct_export_import.py
                return import_related_records(
                    parent_model=parent_model,
                    child_model=child_model,
                    relation_field=relation_field,
                    input_path=input_path,
                    create_if_not_exists=create_if_not_exists,
                    update_if_exists=update_if_exists
                )
            else:
                # Handle single model import
                return run_import_flow(
                    import_path=input_path,  # Changed from input_path to import_path to match the function signature
                    model_name=model_name,
                    field_mapping=field_mapping,
                    create_if_not_exists=create_if_not_exists,
                    update_if_exists=update_if_exists,
                    odoo_url=odoo_url,
                    odoo_db=odoo_db,
                    odoo_username=odoo_username,
                    odoo_password=odoo_password
                )
except ImportError:
    print("Failed to import Export/Import Agent. Make sure the package is installed.")
    pass # Allow pytest to continue collection

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


@pytest.mark.parametrize("model_name", ["res.partner"])
def test_export_flow(model_name: str, domain: Optional[str] = None,
                    fields: Optional[List[str]] = None, limit: int = 10,
                    export_path: Optional[str] = None):
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
    assert result.get("error") is None, f"Export failed: {result.get('error')}"

    # Check if the file was created
    assert os.path.exists(export_path), f"Export file was not created: {export_path}"

    # Get file size
    file_size = os.path.getsize(export_path)
    logger.info(f"Export successful. File created at: {export_path} (Size: {file_size} bytes)")

    # Check if the file has content
    assert file_size > 0, "Export file is empty"

    return True, result


def _run_import_flow(model_name: str, input_path: str,
                    field_mapping: Optional[Dict[str, str]] = None,
                    create_if_not_exists: bool = True,
                    update_if_exists: bool = True) -> Tuple[bool, Dict[str, Any]]:
    """Helper function to run the import flow."""
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


@pytest.mark.parametrize("model_name", ["res.partner"])
def test_export_import_cycle(model_name: str, domain: Optional[str] = None,
                           fields: Optional[List[str]] = None, limit: int = 10):
    """Test a complete export-import cycle for a model."""
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

    assert export_success, "Export step failed"

    # Step 2: Import
    import_success, import_result = _run_import_flow(
        model_name=model_name,
        input_path=export_path
    )

    assert import_success, "Import step failed"

    logger.info("Export-import cycle completed successfully")


@pytest.mark.parametrize("parent_model, child_model, relation_field", [("res.partner", "res.partner.bank", "partner_id")])
def test_related_models_export_import(parent_model: str, child_model: str,
                                    relation_field: str, limit: int = 5):
    """Test export and import of related models."""
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
    assert export_result.get("error") is None, f"Related models export failed: {export_result.get('error')}"

    # Check if the file was created
    assert os.path.exists(export_path), f"Related models export file was not created: {export_path}"

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
    assert import_result.get("error") is None, f"Related models import failed: {import_result.get('error')}"

    logger.info("Related models export-import completed successfully")


def test_import_flow_standalone(model_name: str = "res.partner"):
    """Standalone test for the import flow - requires a pre-existing export file."""
    logger.info(f"Running standalone import test for model: {model_name}")
    # This test requires a pre-exported file, which might not exist if export tests failed.
    # For now, we'll skip this test if the cycle test is run, or add a dependency.
    # A better approach would be to use a temporary directory and generate the file within the test.
    export_path = os.path.join(TEST_DATA_DIR, f"{model_name.replace('.', '_')}_export.csv")
    if not os.path.exists(export_path):
        logger.warning(f"Skipping standalone import test: Export file not found at {export_path}")
        pytest.skip(f"Export file not found at {export_path}")

    success, result = _run_import_flow(model_name, export_path)
    assert success, f"Standalone import test failed: {result.get('error')}"


# Modify the main function to avoid running tests directly
# This file is now intended to be run by pytest
def main_for_pytest():
    """Placeholder main function to avoid direct execution of tests."""
    pass

if __name__ == "__main__":
    # This block will not be executed by pytest
    print("This script is intended to be run using pytest.")
    sys.exit(1)
