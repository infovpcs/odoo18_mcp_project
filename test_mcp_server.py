#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple test script for the MCP server.
"""

import requests
import json
import sys

# MCP server URL
MCP_URL = "http://127.0.0.1:6277"  # This is the proxy server port from your logs

def list_tools():
    """List all available tools in the MCP server."""
    try:
        response = requests.get(f"{MCP_URL}/list_tools")
        if response.status_code == 200:
            data = response.json()
            print("Available tools:")
            for tool_name, tool_info in data.get("tools", {}).items():
                print(f"- {tool_name}")
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error connecting to MCP server: {str(e)}")
        return False

def call_tool(tool_name, params):
    """Call a specific tool with parameters."""
    try:
        payload = {
            "tool": tool_name,
            "params": params
        }
        response = requests.post(f"{MCP_URL}/call_tool", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"Tool {tool_name} result:")
            print(json.dumps(data.get("result", {}), indent=2))
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error calling tool: {str(e)}")
        return False

def health_check():
    """Check if the MCP server is running."""
    try:
        response = requests.get(f"{MCP_URL}/health")
        if response.status_code == 200:
            print("MCP server is running!")
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error connecting to MCP server: {str(e)}")
        return False

def main():
    """Main function."""
    print("Testing MCP server...")
    
    # Check if server is running
    if not health_check():
        print("MCP server is not running. Please start it with 'mcp dev mcp_server.py'")
        sys.exit(1)
    
    # List available tools
    list_tools()
    
    # Test search_records tool
    print("\nTesting search_records tool...")
    call_tool("search_records", {
        "model_name": "res.partner",
        "query": "company"
    })
    
    # Test advanced_search tool
    print("\nTesting advanced_search tool...")
    call_tool("advanced_search", {
        "query": "List all customers"
    })
    
    # Test retrieve_odoo_documentation tool
    print("\nTesting retrieve_odoo_documentation tool...")
    call_tool("retrieve_odoo_documentation", {
        "query": "How to create a custom module in Odoo 18",
        "max_results": 2
    })
    
    print("\nTests completed!")

if __name__ == "__main__":
    main()