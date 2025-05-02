#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple HTTP client to test the MCP server.
"""

import requests
import sys

def test_connection(url):
    """Test connection to a URL."""
    try:
        response = requests.get(url)
        print(f"Status code: {response.status_code}")
        print(f"Headers: {response.headers}")
        print(f"Content: {response.text[:500]}...")  # Show first 500 chars
        return True
    except Exception as e:
        print(f"Error connecting to {url}: {str(e)}")
        return False

def main():
    """Main function."""
    print("Testing MCP server connections...")
    
    # Test MCP Inspector
    print("\n=== Testing MCP Inspector (port 6274) ===")
    test_connection("http://127.0.0.1:6274")
    
    # Test MCP Proxy
    print("\n=== Testing MCP Proxy (port 6277) ===")
    test_connection("http://127.0.0.1:6277")
    
    # Test some potential API endpoints
    print("\n=== Testing potential API endpoints ===")
    endpoints = [
        "http://127.0.0.1:6274/api",
        "http://127.0.0.1:6274/api/tools",
        "http://127.0.0.1:6274/api/resources",
        "http://127.0.0.1:6277/api",
        "http://127.0.0.1:6277/api/tools",
        "http://127.0.0.1:6277/api/resources"
    ]
    
    for endpoint in endpoints:
        print(f"\nTesting {endpoint}")
        test_connection(endpoint)
    
    print("\nTests completed!")

if __name__ == "__main__":
    main()