#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script using the MCP client library.
"""

import sys
import os
import json
from typing import Dict, Any, List, Optional

try:
    from mcp.client import MCPClient
except ImportError:
    print("Error: MCP client library not found. Please install it with 'pip install mcp'.")
    sys.exit(1)

def main():
    """Main function."""
    print("Testing MCP client library...")
    
    # Create MCP client
    try:
        # Connect to the MCP server
        client = MCPClient(url="http://127.0.0.1:6277")
        print("Connected to MCP server!")
        
        # List available tools
        print("\n=== Available Tools ===")
        tools = client.list_tools()
        for tool in tools:
            print(f"- {tool.name}: {tool.description}")
        
        # List available resources
        print("\n=== Available Resources ===")
        resources = client.list_resources()
        for resource in resources:
            print(f"- {resource.uri}")
        
        # Test search_records tool
        print("\n=== Testing search_records Tool ===")
        result = client.call_tool(
            "search_records",
            model_name="res.partner",
            query="company"
        )
        print(result)
        
        # Test advanced_search tool
        print("\n=== Testing advanced_search Tool ===")
        result = client.call_tool(
            "advanced_search",
            query="List all customers"
        )
        print(result)
        
        # Test reading models resource
        print("\n=== Testing Read Models Resource ===")
        result = client.read_resource("odoo://models/all")
        print(result)
        
        print("\nTests completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()