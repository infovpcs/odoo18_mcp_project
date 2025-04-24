#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test MCP Client

This script tests the MCP server by making requests to it.
"""

import requests
import json
import sys

# MCP server URL
MCP_URL = "http://localhost:8080"

def make_request(endpoint, data=None):
    """Make a request to the MCP server.
    
    Args:
        endpoint: API endpoint
        data: Request data
        
    Returns:
        Response from the MCP server
    """
    url = f"{MCP_URL}{endpoint}"
    
    try:
        if data:
            response = requests.post(url, json=data)
        else:
            response = requests.get(url)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {str(e)}")
        raise

def test_list_resources():
    """Test listing resources."""
    print("\n=== Testing List Resources ===")
    
    try:
        response = make_request("/resources")
        
        print(f"Found {len(response)} resources:")
        for resource in response:
            print(f"  - {resource['uri']}")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_read_resource(uri):
    """Test reading a resource.
    
    Args:
        uri: Resource URI
    """
    print(f"\n=== Testing Read Resource: {uri} ===")
    
    try:
        response = make_request(f"/resources/read", {"uri": uri})
        
        print("Resource content:")
        print(response.get("content", "No content"))
    except Exception as e:
        print(f"Error: {str(e)}")

def test_list_tools():
    """Test listing tools."""
    print("\n=== Testing List Tools ===")
    
    try:
        response = make_request("/tools")
        
        print(f"Found {len(response)} tools:")
        for tool in response:
            print(f"  - {tool['name']}: {tool['description']}")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_call_tool(name, params):
    """Test calling a tool.
    
    Args:
        name: Tool name
        params: Tool parameters
    """
    print(f"\n=== Testing Call Tool: {name} ===")
    
    try:
        response = make_request("/tools/call", {
            "name": name,
            "params": params
        })
        
        print("Tool response:")
        print(response.get("content", "No content"))
    except Exception as e:
        print(f"Error: {str(e)}")

def test_list_prompts():
    """Test listing prompts."""
    print("\n=== Testing List Prompts ===")
    
    try:
        response = make_request("/prompts")
        
        print(f"Found {len(response)} prompts:")
        for prompt in response:
            print(f"  - {prompt['name']}: {prompt['description']}")
    except Exception as e:
        print(f"Error: {str(e)}")

def test_get_prompt(name, params):
    """Test getting a prompt.
    
    Args:
        name: Prompt name
        params: Prompt parameters
    """
    print(f"\n=== Testing Get Prompt: {name} ===")
    
    try:
        response = make_request("/prompts/get", {
            "name": name,
            "params": params
        })
        
        print("Prompt content:")
        print(response.get("content", "No content"))
    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    """Main function."""
    print("=== MCP Client Test ===")
    
    # Test listing resources
    test_list_resources()
    
    # Test reading resources
    test_read_resource("https://example.com/hello")
    
    # Test listing tools
    test_list_tools()
    
    # Test calling tools
    test_call_tool("echo", {
        "message": "Hello, MCP!"
    })
    
    # Test listing prompts
    test_list_prompts()
    
    print("\n=== Test completed successfully ===")

if __name__ == "__main__":
    main()