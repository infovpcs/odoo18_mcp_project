#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Direct test script for MCP server functions
This script tests the OdooModelDiscovery class functions directly
"""

import os
import sys
import json
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_functions_test")

# Load environment variables
load_dotenv()

# Import the OdooModelDiscovery class from mcp_server.py
try:
    from mcp_server import OdooModelDiscovery
except ImportError:
    logger.error("Could not import OdooModelDiscovery from mcp_server.py")
    sys.exit(1)

# Get Odoo connection details from environment variables
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "llmdb18")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

def test_function(function_name, function, *args, **kwargs):
    """Test a specific function with the given arguments"""
    logger.info(f"Testing function: {function_name}")
    logger.info(f"Arguments: {args}")
    logger.info(f"Keyword arguments: {kwargs}")
    
    try:
        result = function(*args, **kwargs)
        logger.info(f"Success! Result: {result}")
        return True, result
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        return False, str(e)

def main():
    """Main function to run all tests"""
    logger.info("Starting MCP functions tests")
    
    # Initialize the OdooModelDiscovery class
    try:
        model_discovery = OdooModelDiscovery(ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
        logger.info("OdooModelDiscovery initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize OdooModelDiscovery: {str(e)}")
        sys.exit(1)
    
    # Test 1: get_all_models
    logger.info("\n=== Test 1: get_all_models ===")
    success, models = test_function("get_all_models", model_discovery.get_all_models)
    
    # Test 2: get_model_fields
    logger.info("\n=== Test 2: get_model_fields ===")
    success, fields = test_function("get_model_fields", model_discovery.get_model_fields, "res.partner")
    
    # Test 3: get_model_records
    logger.info("\n=== Test 3: get_model_records ===")
    success, records_data = test_function("get_model_records", model_discovery.get_model_records, "res.partner", 5, 0, [('name', 'ilike', 'company')])
    
    # Test 4: get_model_schema
    logger.info("\n=== Test 4: get_model_schema ===")
    success, schema = test_function("get_model_schema", model_discovery.get_model_schema, "product.product")
    
    # Test 5: create_record
    logger.info("\n=== Test 5: create_record ===")
    success, record_id = test_function("create_record", model_discovery.create_record, "res.partner", {"name": "Test Partner MCP", "email": "test_mcp@example.com"})
    
    # Store the created record ID for later tests if successful
    created_record_id = None
    if success and record_id:
        created_record_id = record_id
        logger.info(f"Created record ID: {created_record_id}")
    
    # Test 6: update_record (use the created record ID if available, otherwise use a default ID)
    record_id = created_record_id if created_record_id else 1
    logger.info(f"\n=== Test 6: update_record (ID: {record_id}) ===")
    success, update_result = test_function("update_record", model_discovery.update_record, "res.partner", record_id, {"name": "Updated Partner MCP"})
    
    # Test 7: execute_method
    logger.info("\n=== Test 7: execute_method ===")
    success, method_result = test_function("execute_method", model_discovery.execute_method, "res.partner", "name_search", [["Test"]])
    
    # Test 8: delete_record (use the created record ID if available)
    # Only run this test if we have a created record to avoid deleting important data
    if created_record_id:
        logger.info(f"\n=== Test 8: delete_record (ID: {created_record_id}) ===")
        success, delete_result = test_function("delete_record", model_discovery.delete_record, "res.partner", created_record_id)
    
    logger.info("\n=== All tests completed ===")

if __name__ == "__main__":
    main()
