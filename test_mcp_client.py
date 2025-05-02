#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the MCP client.
"""

import sys
import json
import requests
from typing import Dict, Any, List, Optional

# MCP server URL
MCP_URL = "http://127.0.0.1:6274"  # This is the MCP Inspector URL from your logs

def test_list_tools():
    """Test listing all available tools."""
    try:
        response = requests.get(f"{MCP_URL}/api/tools")
        if response.status_code == 200:
            data = response.json()
            print("Available tools:")
            for tool in data:
                print(f"- {tool['name']}: {tool['description']}")
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error connecting to MCP server: {str(e)}")
        return False

def test_list_resources():
    """Test listing all available resources."""
    try:
        response = requests.get(f"{MCP_URL}/api/resources")
        if response.status_code == 200:
            data = response.json()
            print("Available resources:")
            for resource in data:
                print(f"- {resource['uri']}")
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error connecting to MCP server: {str(e)}")
        return False

def test_call_tool(tool_name: str, params: Dict[str, Any]):
    """Test calling a specific tool."""
    try:
        payload = {
            "name": tool_name,
            "parameters": params
        }
        response = requests.post(f"{MCP_URL}/api/tools/call", json=payload)
        if response.status_code == 200:
            data = response.json()
            print(f"Tool {tool_name} result:")
            print(data.get("result", "No result"))
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error calling tool: {str(e)}")
        return False

def test_read_resource(resource_uri: str):
    """Test reading a specific resource."""
    try:
        # URL encode the resource URI
        import urllib.parse
        encoded_uri = urllib.parse.quote(resource_uri)
        
        response = requests.get(f"{MCP_URL}/api/resources/{encoded_uri}")
        if response.status_code == 200:
            data = response.json()
            print(f"Resource {resource_uri} content:")
            print(data.get("content", "No content"))
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error reading resource: {str(e)}")
        return False

def main():
    """Main function."""
    print("Testing MCP client...")
    
    # Test listing tools
    print("\n=== Testing List Tools ===")
    test_list_tools()
    
    # Test listing resources
    print("\n=== Testing List Resources ===")
    test_list_resources()
    
    # Test calling search_records tool
    print("\n=== Testing search_records Tool ===")
    test_call_tool("search_records", {
        "model_name": "res.partner",
        "query": "company"
    })
    
    # Test calling advanced_search tool
    print("\n=== Testing advanced_search Tool ===")
    test_call_tool("advanced_search", {
        "query": "List all customers"
    })
    
    # Test reading models resource
    print("\n=== Testing Read Models Resource ===")
    test_read_resource("odoo://models/all")
    
    # Test reading model metadata resource
    print("\n=== Testing Read Model Metadata Resource ===")
    test_read_resource("odoo://model/res.partner/metadata")
    
    print("\nTests completed!")

if __name__ == "__main__":
    main()