#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Custom MCP client wrapper that doesn't rely on the MCPClient class.
This wrapper uses direct HTTP requests to communicate with the MCP server.
"""

import json
import urllib.parse
import requests
from typing import Dict, Any, List, Optional

class MCPWrapper:
    """A wrapper for MCP API calls that doesn't rely on the MCPClient class."""
    
    def __init__(self, url: str = "http://127.0.0.1:6277"):
        """Initialize the MCP wrapper with the server URL."""
        self.url = url
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools."""
        response = requests.get(f"{self.url}/api/tools")
        response.raise_for_status()
        return response.json()
    
    def list_resources(self) -> List[Dict[str, Any]]:
        """List all available resources."""
        response = requests.get(f"{self.url}/api/resources")
        response.raise_for_status()
        return response.json()
    
    def call_tool(self, tool_name: str, **parameters) -> Any:
        """Call a specific tool with parameters."""
        payload = {
            "name": tool_name,
            "parameters": parameters
        }
        response = requests.post(f"{self.url}/api/tools/call", json=payload)
        response.raise_for_status()
        return response.json().get("result")
    
    def read_resource(self, resource_uri: str) -> Any:
        """Read a specific resource."""
        encoded_uri = urllib.parse.quote(resource_uri)
        response = requests.get(f"{self.url}/api/resources/{encoded_uri}")
        response.raise_for_status()
        return response.json().get("content")
