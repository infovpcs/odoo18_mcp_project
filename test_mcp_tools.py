#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for MCP server tools
This script tests all the MCP server tools to verify they are working correctly
"""

import os
import sys
import json
import requests
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_tools_test")

# Load environment variables
load_dotenv()

# MCP server URL (default to localhost:8000 if not specified)
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")

def test_tool(tool_name, params):
    """Test a specific MCP tool with the given parameters"""
    url = f"{MCP_SERVER_URL}/tool/{tool_name}"
    
    logger.info(f"Testing tool: {tool_name}")
    logger.info(f"Parameters: {json.dumps(params, indent=2)}")
    
    try:
        response = requests.post(url, json=params)
        
        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Success! Response: {json.dumps(result, indent=2)}")
            return True, result
        else:
            logger.error(f"Error: Status code {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False, response.text
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        return False, str(e)

def main():
    """Main function to run all tests"""
    logger.info("Starting MCP tools tests")
    
    # Test 1: search_records
    logger.info("\n=== Test 1: search_records ===")
    success, result = test_tool("search_records", {
        "model_name": "res.partner",
        "query": "company"
    })
    
    # Test 2: get_record_template
    logger.info("\n=== Test 2: get_record_template ===")
    success, result = test_tool("get_record_template", {
        "model_name": "product.product"
    })
    
    # Test 3: create_record
    logger.info("\n=== Test 3: create_record ===")
    success, result = test_tool("create_record", {
        "model_name": "res.partner",
        "values": json.dumps({"name": "Test Partner", "email": "test@example.com"})
    })
    
    # Store the created record ID for later tests if successful
    created_record_id = None
    if success and isinstance(result, dict) and "result" in result:
        try:
            # Try to extract the record ID from the result
            response_text = result.get("result", "")
            if "successfully with ID:" in response_text:
                created_record_id = int(response_text.split("ID: ")[-1].strip())
                logger.info(f"Created record ID: {created_record_id}")
        except Exception as e:
            logger.error(f"Could not extract record ID: {str(e)}")
    
    # Test 4: update_record (use the created record ID if available, otherwise use 42)
    record_id = created_record_id if created_record_id else 42
    logger.info(f"\n=== Test 4: update_record (ID: {record_id}) ===")
    success, result = test_tool("update_record", {
        "model_name": "res.partner",
        "record_id": record_id,
        "values": json.dumps({"name": "Updated Partner"})
    })
    
    # Test 5: execute_method
    logger.info("\n=== Test 5: execute_method ===")
    success, result = test_tool("execute_method", {
        "model_name": "res.partner",
        "method": "name_search",
        "args": json.dumps(["Test"])
    })
    
    # Test 6: analyze_field_importance
    logger.info("\n=== Test 6: analyze_field_importance ===")
    success, result = test_tool("analyze_field_importance", {
        "model_name": "res.partner",
        "use_nlp": True
    })
    
    # Test 7: get_field_groups
    logger.info("\n=== Test 7: get_field_groups ===")
    success, result = test_tool("get_field_groups", {
        "model_name": "product.product"
    })
    
    # Test 8: delete_record (use the created record ID if available, otherwise use 42)
    # Only run this test if we have a created record to avoid deleting important data
    if created_record_id:
        logger.info(f"\n=== Test 8: delete_record (ID: {created_record_id}) ===")
        success, result = test_tool("delete_record", {
            "model_name": "res.partner",
            "record_id": created_record_id
        })
    
    logger.info("\n=== All tests completed ===")

if __name__ == "__main__":
    main()
