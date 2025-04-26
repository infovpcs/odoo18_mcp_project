#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tool-based implementation for Export/Import operations.
This replaces the langgraph-based implementation.
"""

import os
import sys
import logging
import xmlrpc.client
import pandas as pd
from typing import Dict, List, Any, Optional, Union, Tuple

# Import our field converter
from field_converter import FieldConverter
from direct_export_import import export_records, import_records

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("export_import_tools")


def run_export_flow(
    model_name: str,
    fields: Optional[List[str]] = None,
    filter_domain: Optional[List[Any]] = None,
    limit: int = 1000,
    export_path: Optional[str] = None,
    odoo_url: str = "http://localhost:8069",
    odoo_db: str = "llmdb18",
    odoo_username: str = "admin",
    odoo_password: str = "admin"
) -> Dict[str, Any]:
    """
    Run the export flow with the given parameters.

    Args:
        model_name: Name of the Odoo model to export
        fields: List of fields to export (if None, all fields are exported)
        filter_domain: Domain filter for the export
        limit: Maximum number of records to export
        export_path: Path to export the CSV file
        odoo_url: URL of the Odoo server
        odoo_db: Name of the Odoo database
        odoo_username: Odoo username
        odoo_password: Odoo password

    Returns:
        Dictionary with the export results
    """
    try:
        # Set default export path if not provided
        if not export_path:
            model_name_safe = model_name.replace('.', '_')
            export_path = f"exports/{model_name_safe}_export.csv"

        # Create exports directory if it doesn't exist
        os.makedirs(os.path.dirname(export_path), exist_ok=True)

        # Call the export_records function from direct_export_import.py
        # Set environment variables for Odoo connection
        os.environ["ODOO_URL"] = odoo_url
        os.environ["ODOO_DB"] = odoo_db
        os.environ["ODOO_USERNAME"] = odoo_username
        os.environ["ODOO_PASSWORD"] = odoo_password

        # Call the export_records function
        result = export_records(
            model_name=model_name,
            fields=fields,
            filter_domain=filter_domain,
            limit=limit,
            export_path=export_path
        )

        # Return the results
        return {
            "success": result["success"],
            "model_name": model_name,
            "selected_fields": fields,
            "filter_domain": filter_domain,
            "total_records": result.get("total_records", 0),
            "exported_records": result.get("exported_records", 0),
            "export_path": result.get("export_path", export_path),
            "error": result.get("error", None)
        }
    except Exception as e:
        logger.error(f"Error running export flow: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def run_import_flow(
    import_path: str,
    model_name: str,
    field_mapping: Optional[Dict[str, str]] = None,
    create_if_not_exists: bool = True,
    update_if_exists: bool = True,
    odoo_url: str = "http://localhost:8069",
    odoo_db: str = "llmdb18",
    odoo_username: str = "admin",
    odoo_password: str = "admin"
) -> Dict[str, Any]:
    """
    Run the import flow with the given parameters.

    Args:
        import_path: Path to the CSV file to import
        model_name: Name of the Odoo model to import into
        field_mapping: Mapping from CSV field names to Odoo field names
        create_if_not_exists: Whether to create new records if they don't exist
        update_if_exists: Whether to update existing records
        odoo_url: URL of the Odoo server
        odoo_db: Name of the Odoo database
        odoo_username: Odoo username
        odoo_password: Odoo password

    Returns:
        Dictionary with the import results
    """
    try:
        # Check if import file exists
        if not os.path.exists(import_path):
            return {
                "success": False,
                "error": f"Import file not found: {import_path}"
            }

        # Call the import_records function from direct_export_import.py
        # Set environment variables for Odoo connection
        os.environ["ODOO_URL"] = odoo_url
        os.environ["ODOO_DB"] = odoo_db
        os.environ["ODOO_USERNAME"] = odoo_username
        os.environ["ODOO_PASSWORD"] = odoo_password

        # Call the import_records function
        result = import_records(
            import_path=import_path,
            model_name=model_name,
            field_mapping=field_mapping,
            create_if_not_exists=create_if_not_exists,
            update_if_exists=update_if_exists
        )

        # Return the results
        return {
            "success": result["success"],
            "model_name": model_name,
            "import_path": import_path,
            "field_mapping": field_mapping,
            "total_records": result.get("total_records", 0),
            "imported_records": result.get("imported_records", 0),
            "updated_records": result.get("updated_records", 0),
            "failed_records": result.get("failed_records", 0),
            "error": result.get("error", None)
        }
    except Exception as e:
        logger.error(f"Error running import flow: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }