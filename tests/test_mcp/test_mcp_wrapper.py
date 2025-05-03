#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Pytest tests for the MCP wrapper.
"""

import pytest
import requests
from unittest.mock import patch, MagicMock

# Import our custom wrapper
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from mcp_wrapper import MCPWrapper

# Test data
MOCK_TOOLS = [
    {"name": "search_records", "description": "Search for records in an Odoo model"},
    {"name": "advanced_search", "description": "Perform an advanced search using natural language queries"}
]

MOCK_RESOURCES = [
    {"uri": "odoo://models/all", "description": "List of all models"},
    {"uri": "odoo://model/res.partner/metadata", "description": "Metadata for res.partner model"}
]

MOCK_SEARCH_RESULT = "Mock search result"
MOCK_RESOURCE_CONTENT = "Mock resource content"

@pytest.fixture
def mcp_wrapper():
    """Create an MCPWrapper instance for testing."""
    return MCPWrapper(url="http://mock-server")

@patch('requests.get')
def test_list_tools(mock_get, mcp_wrapper):
    """Test listing tools."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_TOOLS
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    # Call the method
    result = mcp_wrapper.list_tools()

    # Assertions
    assert result == MOCK_TOOLS
    mock_get.assert_called_once_with("http://mock-server/api/tools")

@patch('requests.get')
def test_list_resources(mock_get, mcp_wrapper):
    """Test listing resources."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_RESOURCES
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    # Call the method
    result = mcp_wrapper.list_resources()

    # Assertions
    assert result == MOCK_RESOURCES
    mock_get.assert_called_once_with("http://mock-server/api/resources")

@patch('requests.post')
def test_call_tool(mock_post, mcp_wrapper):
    """Test calling a tool."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.json.return_value = {"result": MOCK_SEARCH_RESULT}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    # Call the method
    result = mcp_wrapper.call_tool("search_records", model_name="res.partner", query="test")

    # Assertions
    assert result == MOCK_SEARCH_RESULT
    mock_post.assert_called_once_with(
        "http://mock-server/api/tools/call",
        json={
            "name": "search_records",
            "parameters": {"model_name": "res.partner", "query": "test"}
        }
    )

@patch('requests.get')
def test_read_resource(mock_get, mcp_wrapper):
    """Test reading a resource."""
    # Setup mock
    mock_response = MagicMock()
    mock_response.json.return_value = {"content": MOCK_RESOURCE_CONTENT}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    # Call the method
    result = mcp_wrapper.read_resource("odoo://models/all")

    # Assertions
    assert result == MOCK_RESOURCE_CONTENT
    # Use the same URL encoding method as in the implementation
    import urllib.parse
    encoded_uri = urllib.parse.quote("odoo://models/all")
    mock_get.assert_called_once_with(f"http://mock-server/api/resources/{encoded_uri}")
