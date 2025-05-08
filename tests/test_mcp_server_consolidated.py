#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolidated test script for the MCP server.

This script provides comprehensive testing for the MCP server:
1. Server startup and health check
2. Listing available tools
3. Testing basic tools (search_records)
4. Testing advanced tools (advanced_search)
5. Testing the Odoo code agent tool
6. Testing export/import tools
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

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test the MCP server")
    parser.add_argument("--health", action="store_true", help="Test health check")
    parser.add_argument("--tools", action="store_true", help="Test listing tools")
    parser.add_argument("--search", action="store_true", help="Test search_records tool")
    parser.add_argument("--advanced", action="store_true", help="Test advanced_search tool")
    parser.add_argument("--code-agent", action="store_true", help="Test run_odoo_code_agent_tool")
    parser.add_argument("--export", action="store_true", help="Test export_records_to_csv tool")
    parser.add_argument("--import", action="store_true", help="Test import_records_from_csv tool")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    args = parser.parse_args()
    
    logger.info("Starting MCP server test...")
    
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
    
    if args.all or args.health:
        tests.append(("Health Check", test_health_check))
    
    if args.all or args.tools:
        tests.append(("List Tools", test_list_tools))
    
    if args.all or args.search:
        tests.append(("Search Records", test_search_records))
    
    if args.all or args.advanced:
        tests.append(("Advanced Search", test_advanced_search))
    
    if args.all or args.code_agent:
        tests.append(("Run Odoo Code Agent", test_run_odoo_code_agent))
    
    if args.all or args.export:
        tests.append(("Export Records", test_export_records))
    
    if args.all or getattr(args, "import"):  # Using getattr because 'import' is a Python keyword
        tests.append(("Import Records", test_import_records))
    
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
