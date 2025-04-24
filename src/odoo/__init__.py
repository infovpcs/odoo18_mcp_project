"""Odoo 18 Integration module for the MCP project.

This module provides Odoo client implementation, data schemas, and dynamic model handling.
"""

from .client import OdooClient, OdooError, AuthenticationError, OperationError, ConnectionError
from .schemas import (
    OdooConfig,
    MCPRequest,
    MCPResponse,
    SearchParams,
    CreateParams,
    UpdateParams,
    DeleteParams,
)

# Import dynamic model handling
from .dynamic import (
    ModelDiscovery,
    FieldAnalyzer,
    CrudGenerator,
    NlpAnalyzer
)

__all__ = [
    # Client and errors
    "OdooClient",
    "OdooError",
    "AuthenticationError",
    "OperationError",
    "ConnectionError",
    
    # Schemas
    "OdooConfig",
    "MCPRequest",
    "MCPResponse",
    "SearchParams",
    "CreateParams",
    "UpdateParams",
    "DeleteParams",
    
    # Dynamic model handling
    "ModelDiscovery",
    "FieldAnalyzer",
    "CrudGenerator",
    "NlpAnalyzer",
]