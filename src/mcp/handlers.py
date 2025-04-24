#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Request Handlers for Odoo 18 Integration

This module provides request handlers for the MCP integration with Odoo 18.
"""

from typing import Any, Dict, List, Optional, Union

from ..core import get_logger
from ..odoo.client import OdooClient
from ..odoo.schemas import (
    MCPRequest,
    MCPResponse,
    SearchParams,
    CreateParams,
    UpdateParams,
    DeleteParams,
)

# Import dynamic handlers
from .dynamic_handlers import (
    handle_discover_models_request,
    handle_model_metadata_request,
    handle_field_importance_request,
    handle_record_template_request,
    handle_dynamic_create_request,
    handle_dynamic_read_request,
    handle_dynamic_update_request,
    handle_dynamic_delete_request,
    handle_field_groups_request,
    handle_search_fields_request
)

logger = get_logger(__name__)


def handle_create_request(odoo_client: OdooClient, request: MCPRequest) -> MCPResponse:
    """Handle a create request.

    Args:
        odoo_client: Odoo client
        request: MCP request

    Returns:
        MCPResponse: MCP response
    """
    try:
        # Validate and convert params
        create_params = CreateParams(**request.params)
        
        # Execute create operation
        record_id = odoo_client.create(request.model, create_params)
        
        return MCPResponse(
            success=True,
            data={"id": record_id},
        )
    except Exception as e:
        logger.error(f"Error handling create request: {str(e)}")
        return MCPResponse(
            success=False,
            error=f"Create operation failed: {str(e)}",
        )


def handle_read_request(odoo_client: OdooClient, request: MCPRequest) -> MCPResponse:
    """Handle a read request.

    Args:
        odoo_client: Odoo client
        request: MCP request

    Returns:
        MCPResponse: MCP response
    """
    try:
        # Extract fields if provided
        fields = request.params.get("fields")
        
        # Create a clean copy of params without None values
        clean_params = {}
        for key, value in request.params.items():
            if value is not None and key not in ['fields']:  # Exclude fields as it's handled separately
                clean_params[key] = value
        
        # Validate and convert params
        search_params = SearchParams(**clean_params)
        
        # Execute search_read operation
        records = odoo_client.search_read(request.model, search_params, fields)
        
        return MCPResponse(
            success=True,
            data={"records": records, "count": len(records)},
        )
    except Exception as e:
        logger.error(f"Error handling read request: {str(e)}")
        return MCPResponse(
            success=False,
            error=f"Read operation failed: {str(e)}",
        )


def handle_update_request(odoo_client: OdooClient, request: MCPRequest) -> MCPResponse:
    """Handle an update request.

    Args:
        odoo_client: Odoo client
        request: MCP request

    Returns:
        MCPResponse: MCP response
    """
    try:
        # Validate and convert params
        update_params = UpdateParams(**request.params)
        
        # Execute update operation
        success = odoo_client.update(request.model, update_params)
        
        return MCPResponse(
            success=success,
            data={"id": update_params.id},
        )
    except Exception as e:
        logger.error(f"Error handling update request: {str(e)}")
        return MCPResponse(
            success=False,
            error=f"Update operation failed: {str(e)}",
        )


def handle_delete_request(odoo_client: OdooClient, request: MCPRequest) -> MCPResponse:
    """Handle a delete request.

    Args:
        odoo_client: Odoo client
        request: MCP request

    Returns:
        MCPResponse: MCP response
    """
    try:
        # Validate and convert params
        delete_params = DeleteParams(**request.params)
        
        # Execute delete operation
        success = odoo_client.delete(request.model, delete_params)
        
        return MCPResponse(
            success=success,
            data={"ids": delete_params.ids},
        )
    except Exception as e:
        logger.error(f"Error handling delete request: {str(e)}")
        return MCPResponse(
            success=False,
            error=f"Delete operation failed: {str(e)}",
        )


def handle_execute_request(odoo_client: OdooClient, request: MCPRequest) -> MCPResponse:
    """Handle an execute request for custom methods.

    Args:
        odoo_client: Odoo client
        request: MCP request

    Returns:
        MCPResponse: MCP response
    """
    try:
        # Extract method and arguments
        method = request.params.get("method")
        args = request.params.get("args", [])
        kwargs = request.params.get("kwargs", {})
        
        if not method:
            raise ValueError("Method name is required for execute operation")
        
        # Execute the method
        # Convert args to a list if it's not already to ensure proper serialization
        args_list = list(args) if not isinstance(args, list) else args
        result = odoo_client.execute(request.model, method, args_list, kwargs)
        
        return MCPResponse(
            success=True,
            data=result,
        )
    except Exception as e:
        logger.error(f"Error handling execute request: {str(e)}")
        return MCPResponse(
            success=False,
            error=f"Execute operation failed: {str(e)}",
        )


def handle_request(odoo_client: OdooClient, request: MCPRequest) -> MCPResponse:
    """Handle an MCP request.

    Args:
        odoo_client: Odoo client
        request: MCP request

    Returns:
        MCPResponse: MCP response
    """
    # Standard CRUD operations
    if request.operation == "create":
        return handle_create_request(odoo_client, request)
    elif request.operation == "read":
        return handle_read_request(odoo_client, request)
    elif request.operation == "update":
        return handle_update_request(odoo_client, request)
    elif request.operation == "delete":
        return handle_delete_request(odoo_client, request)
    elif request.operation == "execute":
        return handle_execute_request(odoo_client, request)
    
    # Dynamic model operations
    elif request.operation == "discover_models":
        return handle_discover_models_request(odoo_client, request)
    elif request.operation == "model_metadata":
        return handle_model_metadata_request(odoo_client, request)
    elif request.operation == "field_importance":
        return handle_field_importance_request(odoo_client, request)
    elif request.operation == "record_template":
        return handle_record_template_request(odoo_client, request)
    elif request.operation == "dynamic_create":
        return handle_dynamic_create_request(odoo_client, request)
    elif request.operation == "dynamic_read":
        return handle_dynamic_read_request(odoo_client, request)
    elif request.operation == "dynamic_update":
        return handle_dynamic_update_request(odoo_client, request)
    elif request.operation == "dynamic_delete":
        return handle_dynamic_delete_request(odoo_client, request)
    elif request.operation == "field_groups":
        return handle_field_groups_request(odoo_client, request)
    elif request.operation == "search_fields":
        return handle_search_fields_request(odoo_client, request)
    
    # Unknown operation
    else:
        logger.error(f"Unknown operation: {request.operation}")
        return MCPResponse(
            success=False,
            error=f"Unknown operation: {request.operation}",
        )