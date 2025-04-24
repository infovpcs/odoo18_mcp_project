#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Server for Odoo 18 Integration

This module provides an MCP server implementation using the standard MCP Python SDK
that integrates with our existing Odoo 18 MCP project.
"""

import os
import json
from typing import Dict, Any, List, Optional, Union, Tuple
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from mcp.server.fastmcp import FastMCP, Context, Image

# Import our existing Odoo client
from src.odoo.client import OdooClient
from src.odoo.schemas import OdooConfig
from src.core.config import get_settings
from src.odoo.dynamic import (
    ModelDiscovery,
    FieldAnalyzer,
    CrudGenerator,
    NlpAnalyzer
)

# Create a lifespan context class for our application
class OdooContext:
    """Context for Odoo MCP server."""
    
    def __init__(self, odoo_client: OdooClient):
        self.odoo_client = odoo_client
        self.model_discovery = ModelDiscovery(odoo_client)
        self.field_analyzer = FieldAnalyzer(self.model_discovery)
        self.nlp_analyzer = NlpAnalyzer(self.model_discovery)
        self.crud_generator = CrudGenerator(
            odoo_client, self.model_discovery, self.field_analyzer
        )

@asynccontextmanager
async def odoo_lifespan(server: FastMCP) -> AsyncIterator[OdooContext]:
    """Manage Odoo client lifecycle."""
    # Initialize Odoo client
    settings = get_settings()
    config = OdooConfig(**settings.dict_for_odoo_client())
    odoo_client = OdooClient(config)
    
    # Authenticate with Odoo
    try:
        odoo_client.authenticate()
        server.info(f"Connected to Odoo server at {config.url}")
        
        # Create and yield the context
        yield OdooContext(odoo_client)
    finally:
        # No explicit cleanup needed for Odoo client
        server.info("Disconnected from Odoo server")

# Create the MCP server
mcp = FastMCP(
    "Odoo 18 MCP",
    description="Dynamic Odoo 18 integration with MCP",
    lifespan=odoo_lifespan,
    dependencies=["fastapi", "pydantic", "requests", "xmlrpc"]
)

# Resource for discovering available models
@mcp.resource("models://all")
def get_all_models(ctx: Context) -> str:
    """Get a list of all available Odoo models."""
    odoo_ctx = ctx.request_context.lifespan_context
    models = odoo_ctx.model_discovery.get_available_models()
    
    # Format the models as a readable string
    result = "# Available Odoo Models\n\n"
    for model in models:
        model_name = model.get('model')
        display_name = model.get('name')
        result += f"- **{display_name}** (`{model_name}`)\n"
    
    return result

# Dynamic resource for model metadata
@mcp.resource("model://{model_name}/metadata")
def get_model_metadata(model_name: str, ctx: Context) -> str:
    """Get metadata for a specific Odoo model."""
    odoo_ctx = ctx.request_context.lifespan_context
    metadata = odoo_ctx.crud_generator.get_model_metadata(model_name)
    
    # Format the metadata as a readable string
    result = f"# Metadata for {model_name}\n\n"
    
    # Model info
    model_info = metadata.get("model", {})
    if model_info:
        result += f"## Model Information\n\n"
        result += f"- **Name**: {model_info.get('name')}\n"
        result += f"- **Technical Name**: {model_info.get('model')}\n"
        if model_info.get('info'):
            result += f"- **Info**: {model_info.get('info')}\n"
    
    # Fields
    fields = metadata.get("fields", {})
    if fields:
        result += f"\n## Fields ({len(fields)})\n\n"
        for field_name, field_info in list(fields.items())[:20]:  # Limit to 20 fields to avoid too much text
            field_type = field_info.get('type', 'unknown')
            field_string = field_info.get('string', field_name)
            required = field_info.get('required', False)
            readonly = field_info.get('readonly', False)
            
            result += f"- **{field_string}** (`{field_name}`): {field_type}"
            if required:
                result += " (Required)"
            if readonly:
                result += " (Readonly)"
            result += "\n"
        
        if len(fields) > 20:
            result += f"\n*...and {len(fields) - 20} more fields*\n"
    
    # Required fields
    required_fields = metadata.get("required_fields", [])
    if required_fields:
        result += f"\n## Required Fields\n\n"
        result += ", ".join([f"`{field}`" for field in required_fields])
        result += "\n"
    
    # Recommended fields
    create_fields = metadata.get("create_fields", [])
    if create_fields:
        result += f"\n## Recommended Create Fields\n\n"
        result += ", ".join([f"`{field}`" for field in create_fields])
        result += "\n"
    
    return result

# Dynamic resource for model records
@mcp.resource("model://{model_name}/records")
def get_model_records(model_name: str, ctx: Context) -> str:
    """Get records for a specific Odoo model."""
    odoo_ctx = ctx.request_context.lifespan_context
    
    # Get records with a reasonable limit
    records = odoo_ctx.crud_generator.read_records(
        model_name,
        limit=10,
        fields=odoo_ctx.field_analyzer.get_read_fields(model_name)
    )
    
    if isinstance(records, dict) and not records.get('success', True):
        return f"Error retrieving records: {records.get('error', 'Unknown error')}"
    
    # Format the records as a readable string
    result = f"# Records for {model_name}\n\n"
    
    if not records:
        return result + "No records found."
    
    # Get field information for better display
    fields_info = odoo_ctx.model_discovery.get_model_fields(model_name)
    
    # Create a table header
    fields_to_show = list(records[0].keys())[:5]  # Limit to 5 fields to avoid too wide tables
    result += "| ID | " + " | ".join([fields_info.get(field, {}).get('string', field) for field in fields_to_show if field != 'id']) + " |\n"
    result += "|----| " + " | ".join(["----" for _ in fields_to_show if _ != 'id']) + " |\n"
    
    # Add records to the table
    for record in records[:10]:  # Limit to 10 records
        record_id = record.get('id', 'N/A')
        row = f"| {record_id} | "
        row += " | ".join([str(record.get(field, '')) for field in fields_to_show if field != 'id'])
        row += " |\n"
        result += row
    
    if len(records) > 10:
        result += f"\n*...and {len(records) - 10} more records*\n"
    
    return result

# Tool for searching records
@mcp.tool()
def search_records(model_name: str, query: str, ctx: Context) -> str:
    """Search for records in an Odoo model.
    
    Args:
        model_name: The technical name of the Odoo model to search
        query: The search query (will be converted to a domain)
    
    Returns:
        A formatted string with the search results
    """
    odoo_ctx = ctx.request_context.lifespan_context
    
    # Convert the query to a domain
    # This is a simple implementation - in a real app, you might want to use NLP
    # to convert natural language to Odoo domains
    domain = []
    if query:
        # Get search fields from NLP analyzer
        search_fields = odoo_ctx.nlp_analyzer.suggest_search_fields(model_name)
        if search_fields:
            # Create a domain that searches for the query in any of the search fields
            domain = ['|' for _ in range(len(search_fields) - 1)] + [(field, 'ilike', query) for field in search_fields]
    
    # Get records
    records = odoo_ctx.crud_generator.read_records(
        model_name,
        domain=domain,
        limit=10,
        fields=odoo_ctx.field_analyzer.get_read_fields(model_name)
    )
    
    if isinstance(records, dict) and not records.get('success', True):
        return f"Error searching records: {records.get('error', 'Unknown error')}"
    
    # Format the records as a readable string
    result = f"# Search Results for '{query}' in {model_name}\n\n"
    
    if not records:
        return result + "No records found matching the query."
    
    # Get field information for better display
    fields_info = odoo_ctx.model_discovery.get_model_fields(model_name)
    
    # Create a table header
    fields_to_show = list(records[0].keys())[:5]  # Limit to 5 fields to avoid too wide tables
    result += "| ID | " + " | ".join([fields_info.get(field, {}).get('string', field) for field in fields_to_show if field != 'id']) + " |\n"
    result += "|----| " + " | ".join(["----" for _ in fields_to_show if _ != 'id']) + " |\n"
    
    # Add records to the table
    for record in records:
        record_id = record.get('id', 'N/A')
        row = f"| {record_id} | "
        row += " | ".join([str(record.get(field, '')) for field in fields_to_show if field != 'id'])
        row += " |\n"
        result += row
    
    return result

# Tool for creating records
@mcp.tool()
def create_record(model_name: str, values: str, ctx: Context) -> str:
    """Create a new record in an Odoo model.
    
    Args:
        model_name: The technical name of the Odoo model
        values: JSON string with field values for the new record
    
    Returns:
        A confirmation message with the new record ID
    """
    odoo_ctx = ctx.request_context.lifespan_context
    
    try:
        # Parse the values JSON
        values_dict = json.loads(values)
    except json.JSONDecodeError:
        return "Error: Invalid JSON format for values. Please provide a valid JSON object."
    
    # Create the record
    result = odoo_ctx.crud_generator.create_record(model_name, values_dict)
    
    if isinstance(result, dict) and not result.get('success', True):
        return f"Error creating record: {result.get('error', 'Unknown error')}"
    
    # Return a success message
    return f"Record created successfully with ID: {result}"

# Tool for updating records
@mcp.tool()
def update_record(model_name: str, record_id: int, values: str, ctx: Context) -> str:
    """Update an existing record in an Odoo model.
    
    Args:
        model_name: The technical name of the Odoo model
        record_id: The ID of the record to update
        values: JSON string with field values to update
    
    Returns:
        A confirmation message
    """
    odoo_ctx = ctx.request_context.lifespan_context
    
    try:
        # Parse the values JSON
        values_dict = json.loads(values)
    except json.JSONDecodeError:
        return "Error: Invalid JSON format for values. Please provide a valid JSON object."
    
    # Update the record
    result = odoo_ctx.crud_generator.update_record(model_name, record_id, values_dict)
    
    if isinstance(result, dict) and not result.get('success', True):
        return f"Error updating record: {result.get('error', 'Unknown error')}"
    
    # Return a success message
    return f"Record {record_id} updated successfully"

# Tool for deleting records
@mcp.tool()
def delete_record(model_name: str, record_id: int, ctx: Context) -> str:
    """Delete a record from an Odoo model.
    
    Args:
        model_name: The technical name of the Odoo model
        record_id: The ID of the record to delete
    
    Returns:
        A confirmation message
    """
    odoo_ctx = ctx.request_context.lifespan_context
    
    # Delete the record
    result = odoo_ctx.crud_generator.delete_record(model_name, record_id)
    
    if isinstance(result, dict) and not result.get('success', True):
        return f"Error deleting record: {result.get('error', 'Unknown error')}"
    
    # Return a success message
    return f"Record {record_id} deleted successfully"

# Tool for executing custom Odoo methods
@mcp.tool()
def execute_method(model_name: str, method: str, args: str, ctx: Context) -> str:
    """Execute a custom method on an Odoo model.
    
    Args:
        model_name: The technical name of the Odoo model
        method: The method name to execute
        args: JSON string with arguments for the method
    
    Returns:
        The result of the method execution
    """
    odoo_ctx = ctx.request_context.lifespan_context
    
    try:
        # Parse the args JSON
        args_list = json.loads(args)
        if not isinstance(args_list, list):
            args_list = [args_list]
    except json.JSONDecodeError:
        return "Error: Invalid JSON format for arguments. Please provide a valid JSON array."
    
    # Execute the method
    try:
        result = odoo_ctx.odoo_client.execute(model_name, method, args_list)
        
        # Format the result
        if isinstance(result, (dict, list)):
            return json.dumps(result, indent=2)
        else:
            return str(result)
    except Exception as e:
        return f"Error executing method: {str(e)}"

# Tool for getting field importance
@mcp.tool()
def analyze_field_importance(model_name: str, use_nlp: bool = True, ctx: Context) -> str:
    """Analyze the importance of fields in an Odoo model.
    
    Args:
        model_name: The technical name of the Odoo model
        use_nlp: Whether to use NLP for analysis
    
    Returns:
        A formatted string with field importance analysis
    """
    odoo_ctx = ctx.request_context.lifespan_context
    
    if use_nlp:
        importance = odoo_ctx.nlp_analyzer.analyze_field_importance(model_name)
    else:
        importance = odoo_ctx.field_analyzer.get_field_importance(model_name)
    
    # Format the importance as a readable string
    result = f"# Field Importance Analysis for {model_name}\n\n"
    
    # Sort fields by importance
    sorted_fields = sorted(importance.items(), key=lambda x: x[1], reverse=True)
    
    # Create a table
    result += "| Field | Importance |\n"
    result += "|-------|-----------|\n"
    
    for field, score in sorted_fields[:20]:  # Limit to 20 fields
        result += f"| {field} | {score} |\n"
    
    if len(sorted_fields) > 20:
        result += f"\n*...and {len(sorted_fields) - 20} more fields*\n"
    
    return result

# Tool for getting field groups
@mcp.tool()
def get_field_groups(model_name: str, ctx: Context) -> str:
    """Get field groups for an Odoo model.
    
    Args:
        model_name: The technical name of the Odoo model
    
    Returns:
        A formatted string with field groups
    """
    odoo_ctx = ctx.request_context.lifespan_context
    
    groups = odoo_ctx.nlp_analyzer.suggest_field_groups(model_name)
    
    # Format the groups as a readable string
    result = f"# Field Groups for {model_name}\n\n"
    
    for group_name, fields in groups.items():
        result += f"## {group_name.replace('_', ' ').title()}\n\n"
        for field in fields[:10]:  # Limit to 10 fields per group
            result += f"- `{field}`\n"
        
        if len(fields) > 10:
            result += f"\n*...and {len(fields) - 10} more fields*\n"
        
        result += "\n"
    
    return result

# Tool for getting a record template
@mcp.tool()
def get_record_template(model_name: str, ctx: Context) -> str:
    """Get a template for creating a record in an Odoo model.
    
    Args:
        model_name: The technical name of the Odoo model
    
    Returns:
        A JSON template for creating a record
    """
    odoo_ctx = ctx.request_context.lifespan_context
    
    template = odoo_ctx.crud_generator.get_record_template(model_name)
    
    # Format the template as JSON
    return json.dumps(template, indent=2)

# Add a prompt for creating a new record
@mcp.prompt()
def create_record_prompt(model_name: str) -> str:
    """Create a prompt for creating a new record in an Odoo model."""
    return f"""
I need to create a new record in the Odoo model '{model_name}'.

Please help me by:
1. Showing me the template for this model using the get_record_template tool
2. Guiding me through filling in the required and important fields
3. Creating the record using the create_record tool once I've provided all the necessary information
"""

# Add a prompt for searching records
@mcp.prompt()
def search_records_prompt(model_name: str) -> str:
    """Create a prompt for searching records in an Odoo model."""
    return f"""
I need to search for records in the Odoo model '{model_name}'.

Please help me by:
1. Asking me what I'm looking for
2. Using the search_records tool to find matching records
3. Explaining the results to me
"""

# Main entry point
if __name__ == "__main__":
    mcp.run()