"""
MCP Integration module for the Odoo 18 MCP Integration project.

This module provides MCP client implementation and request handlers.
"""

from .client import MCPClient
from .handlers import (
    handle_create_request,
    handle_read_request,
    handle_update_request,
    handle_delete_request,
    handle_execute_request,
)

__all__ = [
    "MCPClient",
    "handle_create_request",
    "handle_read_request",
    "handle_update_request",
    "handle_delete_request",
    "handle_execute_request",
]