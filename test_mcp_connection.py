#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test MCP Server Connection

This script tests the connection to the MCP server and verifies that the tools are working correctly.
"""

import argparse
import json
import logging
import os
import sys
import requests
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_mcp_connection")

# Default MCP server URL
DEFAULT_MCP_SERVER_URL = "http://localhost:8001"

def health_check(server_url: str) -> bool:
    """Check if the MCP server is running.
    
    Args:
        server_url: URL of the MCP server
        
    Returns:
        True if the server is running, False otherwise
    """
    try:
        response = requests.get(f"{server_url}/health")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error checking MCP server health: {str(e)}")
        return False

def list_tools(server_url: str) -> Dict[str, Any]:
    """List available tools on the MCP server.
    
    Args:
        server_url: URL of the MCP server
        
    Returns:
        List of available tools
    """
    try:
        response = requests.get(f"{server_url}/list_tools")
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error listing tools: {response.text}")
            return {}
    except Exception as e:
        logger.error(f"Error listing tools: {str(e)}")
        return {}

def call_tool(server_url: str, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Call a tool on the MCP server.
    
    Args:
        server_url: URL of the MCP server
        tool_name: Name of the tool to call
        params: Parameters for the tool
        
    Returns:
        Response from the tool
    """
    try:
        payload = {
            "tool": tool_name,
            "params": params
        }
        
        logger.info(f"Calling tool {tool_name} with params: {json.dumps(params, indent=2)}")
        
        response = requests.post(
            f"{server_url}/call_tool",
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            error_msg = f"Error calling tool {tool_name}: {response.text}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Error calling tool {tool_name}: {str(e)}"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}

def test_search_records(server_url: str) -> None:
    """Test the search_records tool.
    
    Args:
        server_url: URL of the MCP server
    """
    logger.info("Testing search_records tool...")
    result = call_tool(server_url, "search_records", {
        "model_name": "res.partner",
        "query": "company"
    })
    
    if result.get("success", False):
        logger.info("search_records test passed!")
        logger.info(f"Result: {result.get('data', '')}")
    else:
        logger.error(f"search_records test failed: {result.get('error', 'Unknown error')}")

def test_advanced_search(server_url: str) -> None:
    """Test the advanced_search tool.
    
    Args:
        server_url: URL of the MCP server
    """
    logger.info("Testing advanced_search tool...")
    result = call_tool(server_url, "advanced_search", {
        "query": "List all customers"
    })
    
    if result.get("success", False):
        logger.info("advanced_search test passed!")
        logger.info(f"Result: {result.get('data', '')}")
    else:
        logger.error(f"advanced_search test failed: {result.get('error', 'Unknown error')}")

def test_retrieve_odoo_documentation(server_url: str) -> None:
    """Test the retrieve_odoo_documentation tool.
    
    Args:
        server_url: URL of the MCP server
    """
    logger.info("Testing retrieve_odoo_documentation tool...")
    result = call_tool(server_url, "retrieve_odoo_documentation", {
        "query": "How to create a custom module in Odoo 18",
        "max_results": 2
    })
    
    if result.get("success", False):
        logger.info("retrieve_odoo_documentation test passed!")
        logger.info(f"Result: {result.get('data', '')}")
    else:
        logger.error(f"retrieve_odoo_documentation test failed: {result.get('error', 'Unknown error')}")

def test_run_odoo_code_agent(server_url: str) -> None:
    """Test the run_odoo_code_agent_tool tool.
    
    Args:
        server_url: URL of the MCP server
    """
    logger.info("Testing run_odoo_code_agent_tool tool...")
    result = call_tool(server_url, "run_odoo_code_agent_tool", {
        "query": "Create a simple Odoo 18 module for customer feedback"
    })
    
    if result.get("success", False):
        logger.info("run_odoo_code_agent_tool test passed!")
        logger.info(f"Result summary: {result.get('data', '')[:200]}...")
    else:
        logger.error(f"run_odoo_code_agent_tool test failed: {result.get('error', 'Unknown error')}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test MCP server connection")
    parser.add_argument("--url", default=DEFAULT_MCP_SERVER_URL, help="MCP server URL")
    parser.add_argument("--test", choices=["health", "tools", "search", "advanced", "docs", "agent", "all"], default="health", help="Test to run")
    args = parser.parse_args()
    
    server_url = args.url
    
    # Check if server is running
    if not health_check(server_url):
        logger.error(f"MCP server is not running at {server_url}")
        sys.exit(1)
    
    logger.info(f"MCP server is running at {server_url}")
    
    # Run the specified test
    if args.test == "health":
        logger.info("Health check passed!")
    elif args.test == "tools":
        tools = list_tools(server_url)
        logger.info(f"Available tools: {json.dumps(tools, indent=2)}")
    elif args.test == "search":
        test_search_records(server_url)
    elif args.test == "advanced":
        test_advanced_search(server_url)
    elif args.test == "docs":
        test_retrieve_odoo_documentation(server_url)
    elif args.test == "agent":
        test_run_odoo_code_agent(server_url)
    elif args.test == "all":
        test_search_records(server_url)
        test_advanced_search(server_url)
        test_retrieve_odoo_documentation(server_url)
        test_run_odoo_code_agent(server_url)

if __name__ == "__main__":
    main()
