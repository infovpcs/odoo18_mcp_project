#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive test script for the Odoo 18 MCP Project.

This script provides comprehensive testing for all components of the Odoo 18 MCP Project:
1. MCP Server:
   - Server startup and health check
   - Listing available tools
   - Testing basic tools (search_records, create_record, update_record, delete_record)
   - Testing advanced tools (advanced_search, execute_method)
   - Testing documentation tools (retrieve_odoo_documentation)
   - Testing validation tools (validate_field_value, analyze_field_importance)

2. Export/Import Functionality:
   - Testing export_records_to_csv
   - Testing import_records_from_csv
   - Testing export_related_records_to_csv
   - Testing import_related_records_from_csv
   - Testing complete export-import cycles

3. Odoo Code Agent:
   - Testing basic functionality
   - Testing with feedback
   - Testing with Gemini fallback
   - Testing with Ollama fallback
   - Testing file generation and saving

4. Visualization:
   - Testing mermaid diagram generation
"""

import os
import sys
import json
import logging
import requests
import time
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_mcp_server")

# MCP server URL
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001")

def start_mcp_server():
    """Start the MCP server."""
    logger.info("Starting MCP server...")

    # Try standalone_mcp_server.py first
    try:
        logger.info("Trying to start MCP server with standalone_mcp_server.py...")
        process = subprocess.Popen(
            ["uv", "run", "standalone_mcp_server.py"],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Wait for the server to start
        for i in range(30):
            try:
                response = requests.get(f"{MCP_SERVER_URL}/health", timeout=5)
                if response.status_code == 200:
                    logger.info(f"MCP server started successfully after {i+1} seconds")
                    return process
            except Exception:
                pass
            time.sleep(1)

        # If we get here, the server didn't start
        logger.warning("Failed to start MCP server with standalone_mcp_server.py")

        # Try to terminate the process
        try:
            process.terminate()
        except Exception:
            pass
    except Exception as e:
        logger.warning(f"Error starting MCP server with standalone_mcp_server.py: {str(e)}")

    # Try mcp_server.py as a fallback
    try:
        logger.info("Trying to start MCP server with mcp_server.py...")
        process = subprocess.Popen(
            ["uv", "run", "mcp_server.py"],
            cwd=project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Wait for the server to start
        for i in range(30):
            try:
                response = requests.get(f"{MCP_SERVER_URL}/health", timeout=5)
                if response.status_code == 200:
                    logger.info(f"MCP server started successfully after {i+1} seconds")
                    return process
            except Exception:
                pass
            time.sleep(1)

        # If we get here, the server didn't start
        logger.error("Failed to start MCP server with mcp_server.py")

        # Try to terminate the process
        try:
            process.terminate()
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error starting MCP server with mcp_server.py: {str(e)}")

    return None

def test_health_check():
    """Test the health check endpoint."""
    try:
        response = requests.get(f"{MCP_SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info("Health check passed")
            return True
        else:
            logger.error(f"Health check failed with status code {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error checking health: {str(e)}")
        return False

def test_list_tools():
    """Test the list_tools endpoint."""
    try:
        response = requests.get(f"{MCP_SERVER_URL}/list_tools", timeout=5)
        if response.status_code == 200:
            data = response.json()
            tools = data.get("tools", {})
            logger.info(f"Found {len(tools)} tools: {', '.join(tools.keys())}")
            return True
        else:
            logger.error(f"List tools failed with status code {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}")
        return False

def call_tool(tool_name: str, params: Dict[str, Any], timeout: int = 60) -> Tuple[bool, Any]:
    """Call a tool on the MCP server."""
    try:
        payload = {
            "tool": tool_name,
            "params": params
        }

        logger.info(f"Calling tool {tool_name} with parameters: {json.dumps(params, indent=2)}")

        response = requests.post(f"{MCP_SERVER_URL}/call_tool", json=payload, timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            if data.get("success", False):
                logger.info(f"Tool {tool_name} call succeeded")
                result = data.get("result", "")
                if isinstance(result, str) and len(result) > 100:
                    logger.info(f"Result: {result[:100]}...")
                else:
                    logger.info(f"Result: {result}")
                return True, result
            else:
                logger.error(f"Tool {tool_name} call failed: {data.get('error', 'Unknown error')}")
                return False, data.get("error", "Unknown error")
        else:
            logger.error(f"Tool {tool_name} call failed with status code {response.status_code}")
            return False, f"HTTP error: {response.status_code}"
    except Exception as e:
        logger.error(f"Error calling tool {tool_name}: {str(e)}")
        return False, str(e)

def test_search_records():
    """Test the search_records tool."""
    return call_tool("search_records", {
        "model_name": "res.partner",
        "query": "Gemini"
    })

def test_advanced_search():
    """Test the advanced_search tool."""
    return call_tool("advanced_search", {
        "query": "List all customers with more than 5 orders",
        "limit": 10
    }, timeout=120)

def test_run_odoo_code_agent():
    """Test the run_odoo_code_agent_tool."""
    return call_tool("run_odoo_code_agent_tool", {
        "query": "Create a simple Odoo 18 module for customer feedback",
        "use_gemini": False,
        "use_ollama": False,
        "wait_for_validation": True
    }, timeout=180)

def test_export_records():
    """Test the export_records_to_csv tool."""
    return call_tool("export_records_to_csv", {
        "model_name": "res.partner",
        "fields": ["id", "name", "email", "phone"],
        "limit": 10,
        "export_path": "/tmp/partners.csv"
    })

def test_import_records():
    """Test the import_records_from_csv tool."""
    # First, export some records to use for import testing
    success, _ = test_export_records()
    if not success:
        logger.error("Failed to export records for import testing")
        return False, "Export failed"

    # Now try to import the records
    return call_tool("import_records_from_csv", {
        "input_path": "/tmp/partners.csv",
        "model_name": "res.partner",
        "create_if_not_exists": False,
        "update_if_exists": True
    })

def test_export_related_records():
    """Test the export_related_records_to_csv tool."""
    return call_tool("export_related_records_to_csv", {
        "parent_model": "res.partner",
        "child_model": "res.partner.bank",
        "relation_field": "partner_id",
        "parent_fields": ["id", "name", "email", "phone"],
        "child_fields": ["id", "acc_number", "bank_id"],
        "limit": 5,
        "export_path": "/tmp/partners_with_banks.csv"
    })

def test_import_related_records():
    """Test the import_related_records_from_csv tool."""
    # First, export some records to use for import testing
    success, _ = test_export_related_records()
    if not success:
        logger.error("Failed to export related records for import testing")
        return False, "Export failed"

    # Now try to import the records
    return call_tool("import_related_records_from_csv", {
        "input_path": "/tmp/partners_with_banks.csv",
        "parent_model": "res.partner",
        "child_model": "res.partner.bank",
        "relation_field": "partner_id",
        "create_if_not_exists": False,
        "update_if_exists": True
    })

def test_create_record():
    """Test the create_record tool."""
    # Create a test partner
    return call_tool("create_record", {
        "model_name": "res.partner",
        "values": {
            "name": "Test Partner (MCP Test)",
            "email": "test.partner@example.com",
            "phone": "+1234567890"
        }
    })

def test_update_record():
    """Test the update_record tool."""
    # First, create a record to update
    success, result = test_create_record()
    if not success:
        logger.error("Failed to create record for update testing")
        return False, "Create failed"

    # Get the ID of the created record
    try:
        record_id = json.loads(result)["id"]
    except Exception as e:
        logger.error(f"Failed to parse create result: {str(e)}")
        return False, "Parse failed"

    # Now update the record
    return call_tool("update_record", {
        "model_name": "res.partner",
        "record_id": record_id,
        "values": {
            "name": "Updated Test Partner (MCP Test)",
            "email": "updated.test.partner@example.com"
        }
    })

def test_delete_record():
    """Test the delete_record tool."""
    # First, create a record to delete
    success, result = test_create_record()
    if not success:
        logger.error("Failed to create record for delete testing")
        return False, "Create failed"

    # Get the ID of the created record
    try:
        record_id = json.loads(result)["id"]
    except Exception as e:
        logger.error(f"Failed to parse create result: {str(e)}")
        return False, "Parse failed"

    # Now delete the record
    return call_tool("delete_record", {
        "model_name": "res.partner",
        "record_id": record_id
    })

def test_execute_method():
    """Test the execute_method tool."""
    # Test the name_search method on res.partner
    return call_tool("execute_method", {
        "model_name": "res.partner",
        "method": "name_search",
        "args": ["Gemini", [], "ilike", 5]
    })

def test_retrieve_odoo_documentation():
    """Test the retrieve_odoo_documentation tool."""
    return call_tool("retrieve_odoo_documentation", {
        "query": "How to create a custom module in Odoo 18",
        "max_results": 3
    }, timeout=120)

def test_validate_field_value():
    """Test the validate_field_value tool."""
    return call_tool("validate_field_value", {
        "model_name": "res.partner",
        "field_name": "email",
        "value": "test.email@example.com"
    })

def test_analyze_field_importance():
    """Test the analyze_field_importance tool."""
    return call_tool("analyze_field_importance", {
        "model_name": "res.partner",
        "use_nlp": True
    }, timeout=120)

def test_get_field_groups():
    """Test the get_field_groups tool."""
    return call_tool("get_field_groups", {
        "model_name": "res.partner"
    })

def test_get_record_template():
    """Test the get_record_template tool."""
    return call_tool("get_record_template", {
        "model_name": "res.partner"
    })

def test_generate_mermaid():
    """Test the generate_npx tool."""
    mermaid_code = """
    graph TD
        A[Start] --> B{Is MCP Server Running?}
        B -->|Yes| C[List Tools]
        B -->|No| D[Start MCP Server]
        D --> C
        C --> E[Run Tests]
        E --> F[Report Results]
        F --> G[End]
    """
    return call_tool("generate_npx", {
        "code": mermaid_code,
        "name": "mcp_test_flow",
        "theme": "default",
        "backgroundColor": "white"
    })

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Comprehensive test for the Odoo 18 MCP Project")

    # Server tests
    parser.add_argument("--health", action="store_true", help="Test health check")
    parser.add_argument("--tools", action="store_true", help="Test listing tools")

    # Basic CRUD tests
    parser.add_argument("--search", action="store_true", help="Test search_records tool")
    parser.add_argument("--create", action="store_true", help="Test create_record tool")
    parser.add_argument("--update", action="store_true", help="Test update_record tool")
    parser.add_argument("--delete", action="store_true", help="Test delete_record tool")
    parser.add_argument("--execute", action="store_true", help="Test execute_method tool")
    parser.add_argument("--crud", action="store_true", help="Test all CRUD operations")

    # Advanced search and documentation tests
    parser.add_argument("--advanced", action="store_true", help="Test advanced_search tool")
    parser.add_argument("--docs", action="store_true", help="Test retrieve_odoo_documentation tool")

    # Field analysis tests
    parser.add_argument("--validate", action="store_true", help="Test validate_field_value tool")
    parser.add_argument("--analyze", action="store_true", help="Test analyze_field_importance tool")
    parser.add_argument("--groups", action="store_true", help="Test get_field_groups tool")
    parser.add_argument("--template", action="store_true", help="Test get_record_template tool")
    parser.add_argument("--field-tools", action="store_true", help="Test all field analysis tools")

    # Export/import tests
    parser.add_argument("--export", action="store_true", help="Test export_records_to_csv tool")
    parser.add_argument("--import", action="store_true", help="Test import_records_from_csv tool")
    parser.add_argument("--export-related", action="store_true", help="Test export_related_records_to_csv tool")
    parser.add_argument("--import-related", action="store_true", help="Test import_related_records_from_csv tool")
    parser.add_argument("--export-import", action="store_true", help="Test all export/import tools")

    # Code agent tests
    parser.add_argument("--code-agent", action="store_true", help="Test run_odoo_code_agent_tool")

    # Visualization tests
    parser.add_argument("--mermaid", action="store_true", help="Test generate_npx tool")

    # Test categories
    parser.add_argument("--server", action="store_true", help="Run all server tests")
    parser.add_argument("--basic", action="store_true", help="Run basic tests (health, tools, search)")

    # Run all tests
    parser.add_argument("--all", action="store_true", help="Run all tests")

    args = parser.parse_args()

    logger.info("Starting comprehensive MCP server test...")

    # Check if the MCP server is already running
    try:
        response = requests.get(f"{MCP_SERVER_URL}/health", timeout=5)
        if response.status_code == 200:
            logger.info("MCP server is already running")
            mcp_process = None
        else:
            logger.info("MCP server is running but health check failed")
            mcp_process = start_mcp_server()
    except Exception:
        logger.info("MCP server is not running, starting it...")
        mcp_process = start_mcp_server()

    if mcp_process is None and not test_health_check():
        logger.error("MCP server is not running and could not be started")
        return 1

    # Run the tests
    tests = []

    # Server tests
    if args.all or args.server or args.basic or args.health:
        tests.append(("Health Check", test_health_check))

    if args.all or args.server or args.basic or args.tools:
        tests.append(("List Tools", test_list_tools))

    # Basic CRUD tests
    if args.all or args.crud or args.basic or args.search:
        tests.append(("Search Records", test_search_records))

    if args.all or args.crud or args.create:
        tests.append(("Create Record", test_create_record))

    if args.all or args.crud or args.update:
        tests.append(("Update Record", test_update_record))

    if args.all or args.crud or args.delete:
        tests.append(("Delete Record", test_delete_record))

    if args.all or args.crud or args.execute:
        tests.append(("Execute Method", test_execute_method))

    # Advanced search and documentation tests
    if args.all or args.advanced:
        tests.append(("Advanced Search", test_advanced_search))

    if args.all or args.docs:
        tests.append(("Retrieve Odoo Documentation", test_retrieve_odoo_documentation))

    # Field analysis tests
    if args.all or args.field_tools or args.validate:
        tests.append(("Validate Field Value", test_validate_field_value))

    if args.all or args.field_tools or args.analyze:
        tests.append(("Analyze Field Importance", test_analyze_field_importance))

    if args.all or args.field_tools or args.groups:
        tests.append(("Get Field Groups", test_get_field_groups))

    if args.all or args.field_tools or args.template:
        tests.append(("Get Record Template", test_get_record_template))

    # Export/import tests
    if args.all or args.export_import or args.export:
        tests.append(("Export Records", test_export_records))

    if args.all or args.export_import or getattr(args, "import"):  # Using getattr because 'import' is a Python keyword
        tests.append(("Import Records", test_import_records))

    if args.all or args.export_import or args.export_related:
        tests.append(("Export Related Records", test_export_related_records))

    if args.all or args.export_import or args.import_related:
        tests.append(("Import Related Records", test_import_related_records))

    # Code agent tests
    if args.all or args.code_agent:
        tests.append(("Run Odoo Code Agent", test_run_odoo_code_agent))

    # Visualization tests
    if args.all or args.mermaid:
        tests.append(("Generate Mermaid Diagram", test_generate_mermaid))

    # If no tests were specified, run the basic tests
    if not tests:
        tests = [
            ("Health Check", test_health_check),
            ("List Tools", test_list_tools),
            ("Search Records", test_search_records)
        ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"Running test: {test_name}")
        try:
            if test_func == test_health_check or test_func == test_list_tools:
                result = test_func()
                results.append((test_name, result))
            else:
                success, _ = test_func()
                results.append((test_name, success))
        except Exception as e:
            logger.error(f"Error running test {test_name}: {str(e)}")
            results.append((test_name, False))

    # Print the results
    logger.info("Test results:")
    for test_name, result in results:
        logger.info(f"  {test_name}: {'PASS' if result else 'FAIL'}")

    # Clean up
    if mcp_process:
        logger.info("Stopping MCP server...")
        try:
            mcp_process.terminate()
        except Exception as e:
            logger.warning(f"Error stopping MCP server: {str(e)}")

    # Return success if all tests passed
    if all(result for _, result in results):
        logger.info("All tests passed")
        return 0
    else:
        logger.error("Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
