#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dynamic Model Handlers Module

This module provides handlers for dynamic model operations in the MCP server.
"""

import logging
from typing import Dict, Any, List, Optional

from ..odoo.client import OdooClient
from ..odoo.schemas import MCPRequest, MCPResponse
from ..odoo.dynamic import ModelDiscovery, FieldAnalyzer, CrudGenerator, NlpAnalyzer

logger = logging.getLogger(__name__)

def handle_discover_models_request(odoo_client: OdooClient, request: MCPRequest) -> MCPResponse:
    """Handle a discover models request.
    
    Args:
        odoo_client: Odoo client
        request: MCP request
        
    Returns:
        MCPResponse: MCP response
    """
    try:
        # Extract parameters
        filter_keyword = request.params.get("filter")
        
        # Create model discovery instance
        model_discovery = ModelDiscovery(odoo_client)
        
        # Get available models
        models = model_discovery.get_available_models(filter_keyword)
        
        return MCPResponse(
            success=True,
            data=models,
        )
    except Exception as e:
        logger.error(f"Error handling discover models request: {str(e)}")
        return MCPResponse(
            success=False,
            error=f"Discover models operation failed: {str(e)}",
        )

def handle_model_metadata_request(odoo_client: OdooClient, request: MCPRequest) -> MCPResponse:
    """Handle a model metadata request.
    
    Args:
        odoo_client: Odoo client
        request: MCP request
        
    Returns:
        MCPResponse: MCP response
    """
    try:
        # Extract parameters
        model_name = request.model
        
        # Create instances
        model_discovery = ModelDiscovery(odoo_client)
        field_analyzer = FieldAnalyzer(model_discovery)
        crud_generator = CrudGenerator(odoo_client, model_discovery, field_analyzer)
        
        # Get model metadata
        metadata = crud_generator.get_model_metadata(model_name)
        
        return MCPResponse(
            success=True,
            data=metadata,
        )
    except Exception as e:
        logger.error(f"Error handling model metadata request: {str(e)}")
        return MCPResponse(
            success=False,
            error=f"Model metadata operation failed: {str(e)}",
        )

def handle_field_importance_request(odoo_client: OdooClient, request: MCPRequest) -> MCPResponse:
    """Handle a field importance request.
    
    Args:
        odoo_client: Odoo client
        request: MCP request
        
    Returns:
        MCPResponse: MCP response
    """
    try:
        # Extract parameters
        model_name = request.model
        use_nlp = request.params.get("use_nlp", False)
        
        # Create instances
        model_discovery = ModelDiscovery(odoo_client)
        field_analyzer = FieldAnalyzer(model_discovery)
        
        if use_nlp:
            # Use NLP analyzer for more sophisticated analysis
            nlp_analyzer = NlpAnalyzer(model_discovery)
            importance = nlp_analyzer.analyze_field_importance(model_name)
        else:
            # Use basic field analyzer
            importance = field_analyzer.get_field_importance(model_name)
        
        return MCPResponse(
            success=True,
            data=importance,
        )
    except Exception as e:
        logger.error(f"Error handling field importance request: {str(e)}")
        return MCPResponse(
            success=False,
            error=f"Field importance operation failed: {str(e)}",
        )

def handle_record_template_request(odoo_client: OdooClient, request: MCPRequest) -> MCPResponse:
    """Handle a record template request.
    
    Args:
        odoo_client: Odoo client
        request: MCP request
        
    Returns:
        MCPResponse: MCP response
    """
    try:
        # Extract parameters
        model_name = request.model
        
        # Create instances
        model_discovery = ModelDiscovery(odoo_client)
        field_analyzer = FieldAnalyzer(model_discovery)
        crud_generator = CrudGenerator(odoo_client, model_discovery, field_analyzer)
        
        # Get record template
        template = crud_generator.get_record_template(model_name)
        
        return MCPResponse(
            success=True,
            data=template,
        )
    except Exception as e:
        logger.error(f"Error handling record template request: {str(e)}")
        return MCPResponse(
            success=False,
            error=f"Record template operation failed: {str(e)}",
        )

def handle_dynamic_create_request(odoo_client: OdooClient, request: MCPRequest) -> MCPResponse:
    """Handle a dynamic create request.
    
    Args:
        odoo_client: Odoo client
        request: MCP request
        
    Returns:
        MCPResponse: MCP response
    """
    try:
        # Extract parameters
        model_name = request.model
        values = request.params.get("values", {})
        
        # Create instances
        model_discovery = ModelDiscovery(odoo_client)
        field_analyzer = FieldAnalyzer(model_discovery)
        crud_generator = CrudGenerator(odoo_client, model_discovery, field_analyzer)
        
        # Create record
        result = crud_generator.create_record(model_name, values)
        
        # Check if result is an error
        if isinstance(result, dict) and 'success' in result and not result['success']:
            return MCPResponse(
                success=False,
                error=result.get('error', 'Unknown error'),
            )
        
        return MCPResponse(
            success=True,
            data=result,
        )
    except Exception as e:
        logger.error(f"Error handling dynamic create request: {str(e)}")
        return MCPResponse(
            success=False,
            error=f"Dynamic create operation failed: {str(e)}",
        )

def handle_dynamic_read_request(odoo_client: OdooClient, request: MCPRequest) -> MCPResponse:
    """Handle a dynamic read request.
    
    Args:
        odoo_client: Odoo client
        request: MCP request
        
    Returns:
        MCPResponse: MCP response
    """
    try:
        # Extract parameters
        model_name = request.model
        domain = request.params.get("domain")
        fields = request.params.get("fields")
        limit = request.params.get("limit")
        offset = request.params.get("offset")
        order = request.params.get("order")
        
        # Create instances
        model_discovery = ModelDiscovery(odoo_client)
        field_analyzer = FieldAnalyzer(model_discovery)
        crud_generator = CrudGenerator(odoo_client, model_discovery, field_analyzer)
        
        # Read records
        result = crud_generator.read_records(
            model_name, 
            domain=domain, 
            fields=fields, 
            limit=limit, 
            offset=offset, 
            order=order
        )
        
        # Check if result is an error
        if isinstance(result, dict) and 'success' in result and not result['success']:
            return MCPResponse(
                success=False,
                error=result.get('error', 'Unknown error'),
            )
        
        return MCPResponse(
            success=True,
            data=result,
        )
    except Exception as e:
        logger.error(f"Error handling dynamic read request: {str(e)}")
        return MCPResponse(
            success=False,
            error=f"Dynamic read operation failed: {str(e)}",
        )

def handle_dynamic_update_request(odoo_client: OdooClient, request: MCPRequest) -> MCPResponse:
    """Handle a dynamic update request.
    
    Args:
        odoo_client: Odoo client
        request: MCP request
        
    Returns:
        MCPResponse: MCP response
    """
    try:
        # Extract parameters
        model_name = request.model
        record_id = request.params.get("id")
        values = request.params.get("values", {})
        
        if not record_id:
            return MCPResponse(
                success=False,
                error="Record ID is required for update operation",
            )
        
        # Create instances
        model_discovery = ModelDiscovery(odoo_client)
        field_analyzer = FieldAnalyzer(model_discovery)
        crud_generator = CrudGenerator(odoo_client, model_discovery, field_analyzer)
        
        # Update record
        result = crud_generator.update_record(model_name, record_id, values)
        
        # Check if result is an error
        if isinstance(result, dict) and 'success' in result and not result['success']:
            return MCPResponse(
                success=False,
                error=result.get('error', 'Unknown error'),
            )
        
        return MCPResponse(
            success=True,
            data=result,
        )
    except Exception as e:
        logger.error(f"Error handling dynamic update request: {str(e)}")
        return MCPResponse(
            success=False,
            error=f"Dynamic update operation failed: {str(e)}",
        )

def handle_dynamic_delete_request(odoo_client: OdooClient, request: MCPRequest) -> MCPResponse:
    """Handle a dynamic delete request.
    
    Args:
        odoo_client: Odoo client
        request: MCP request
        
    Returns:
        MCPResponse: MCP response
    """
    try:
        # Extract parameters
        model_name = request.model
        record_id = request.params.get("id")
        
        if not record_id:
            return MCPResponse(
                success=False,
                error="Record ID is required for delete operation",
            )
        
        # Create instances
        model_discovery = ModelDiscovery(odoo_client)
        field_analyzer = FieldAnalyzer(model_discovery)
        crud_generator = CrudGenerator(odoo_client, model_discovery, field_analyzer)
        
        # Delete record
        result = crud_generator.delete_record(model_name, record_id)
        
        # Check if result is an error
        if isinstance(result, dict) and 'success' in result and not result['success']:
            return MCPResponse(
                success=False,
                error=result.get('error', 'Unknown error'),
            )
        
        return MCPResponse(
            success=True,
            data=result,
        )
    except Exception as e:
        logger.error(f"Error handling dynamic delete request: {str(e)}")
        return MCPResponse(
            success=False,
            error=f"Dynamic delete operation failed: {str(e)}",
        )

def handle_field_groups_request(odoo_client: OdooClient, request: MCPRequest) -> MCPResponse:
    """Handle a field groups request.
    
    Args:
        odoo_client: Odoo client
        request: MCP request
        
    Returns:
        MCPResponse: MCP response
    """
    try:
        # Extract parameters
        model_name = request.model
        
        # Create instances
        model_discovery = ModelDiscovery(odoo_client)
        nlp_analyzer = NlpAnalyzer(model_discovery)
        
        # Get field groups
        groups = nlp_analyzer.suggest_field_groups(model_name)
        
        return MCPResponse(
            success=True,
            data=groups,
        )
    except Exception as e:
        logger.error(f"Error handling field groups request: {str(e)}")
        return MCPResponse(
            success=False,
            error=f"Field groups operation failed: {str(e)}",
        )

def handle_search_fields_request(odoo_client: OdooClient, request: MCPRequest) -> MCPResponse:
    """Handle a search fields request.
    
    Args:
        odoo_client: Odoo client
        request: MCP request
        
    Returns:
        MCPResponse: MCP response
    """
    try:
        # Extract parameters
        model_name = request.model
        
        # Create instances
        model_discovery = ModelDiscovery(odoo_client)
        nlp_analyzer = NlpAnalyzer(model_discovery)
        
        # Get search fields
        search_fields = nlp_analyzer.suggest_search_fields(model_name)
        
        return MCPResponse(
            success=True,
            data=search_fields,
        )
    except Exception as e:
        logger.error(f"Error handling search fields request: {str(e)}")
        return MCPResponse(
            success=False,
            error=f"Search fields operation failed: {str(e)}",
        )