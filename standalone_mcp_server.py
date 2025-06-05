#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Standalone MCP server for testing MCP tools.
"""

import os
import sys
import json
import logging
import asyncio
import importlib.util
import xmlrpc.client # Added xmlrpc.client import
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Load environment variables
load_dotenv()


# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("standalone_mcp_server")

# Create FastAPI app
app = FastAPI(
    title="Standalone MCP Server",
    description="A standalone server for testing MCP tools",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load the MCP server module
def load_mcp_server():
    """Load the MCP server module."""
    try:
        # Get the path to the MCP server module
        mcp_server_path = os.path.join(os.path.dirname(__file__), "mcp_server.py")

        # Load the module
        spec = importlib.util.spec_from_file_location("mcp_server", mcp_server_path)
        mcp_server = importlib.util.module_from_spec(spec)
        if spec and spec.loader:
            spec.loader.exec_module(mcp_server)
        else:
            logger.error("Failed to load MCP server module spec")
            return None

        # Get the MCP server instance
        mcp = getattr(mcp_server, "mcp", None)

        if not mcp:
            logger.error("Failed to get MCP server instance")
            return None

        return mcp
    except Exception as e:
        logger.error(f"Failed to load MCP server module: {str(e)}")
        return None


# Get the MCP server instance
mcp = load_mcp_server()

if not mcp:
    logger.error("Failed to load MCP server. Exiting...")
    sys.exit(1)

# Get the tools from the MCP server
tools = {}
try:
    # Import all necessary tools in a single block
    from mcp_server import (
        retrieve_odoo_documentation,
        advanced_search,
        search_records,
        create_record,
        update_record,
        delete_record,
        execute_method,
        export_records_to_csv,
        import_records_from_csv,
        export_related_records_to_csv,
        import_related_records_from_csv,
        validate_field_value,
        analyze_field_importance,
        get_field_groups,
        get_record_template,
        generate_npx,
        query_deepwiki,
        improved_generate_odoo_module,
    )

    # Register all imported tools
    tools["retrieve_odoo_documentation"] = retrieve_odoo_documentation
    tools["advanced_search"] = advanced_search
    tools["search_records"] = search_records
    tools["create_record"] = create_record
    tools["update_record"] = update_record
    tools["delete_record"] = delete_record
    tools["execute_method"] = execute_method
    tools["export_records_to_csv"] = export_records_to_csv
    tools["import_records_from_csv"] = import_records_from_csv
    tools["export_related_records_to_csv"] = export_related_records_to_csv
    tools["import_related_records_from_csv"] = import_related_records_from_csv
    tools["validate_field_value"] = validate_field_value
    tools["analyze_field_importance"] = analyze_field_importance
    tools["get_field_groups"] = get_field_groups
    tools["get_record_template"] = get_record_template
    tools["generate_npx"] = generate_npx
    tools["query_deepwiki"] = query_deepwiki
    tools["improved_generate_odoo_module"] = improved_generate_odoo_module

    logger.info(f"Successfully imported and registered {len(tools)} tools from mcp_server")

except Exception as e:
    logger.error(f"Error importing tools from mcp_server: {str(e)}")
    # Create placeholder functions for all expected tools to avoid KeyError later
    expected_tools = [
        "retrieve_odoo_documentation", "advanced_search", "search_records",
        "create_record", "update_record", "delete_record", "execute_method",
        "export_records_to_csv", "import_records_from_csv", "export_related_records_to_csv",
        "import_related_records_from_csv", "validate_field_value", "analyze_field_importance",
        "get_field_groups", "get_record_template", "generate_npx", "query_deepwiki",
        "improved_generate_odoo_module"
    ]
    for tool_name in expected_tools:
        tools[tool_name] = lambda **kwargs: {"success": False, "error": f"Tool '{tool_name}' not available due to import error: {str(e)}"}
    logger.warning(f"Placeholder functions created for {len(expected_tools)} tools due to import error.")


logger.info(f"Loaded {len(tools)} tools from MCP server: {', '.join(tools.keys())}")


@app.post("/call_tool")
async def call_tool(request: Request):
    """Call an MCP tool."""
    try:
        # Parse the request body
        body = await request.json()

        # Get the tool name and parameters
        # Accept both "tool" and "tool_name" for compatibility
        tool_name = body.get("tool") or body.get("tool_name")
        params = body.get("params", {})

        if not tool_name:
            raise HTTPException(status_code=400, detail="Tool name is required")

        if tool_name not in tools:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        # Call the tool
        logger.info(f"Calling tool '{tool_name}' with parameters: {params}")
        
        # Check if the tool is an async function and await it if necessary
        result = tools[tool_name](**params)
        
        # Check if the result is a coroutine (async function) and await it
        if asyncio.iscoroutine(result):
            logger.info(f"Tool '{tool_name}' is async, awaiting result")
            result = await result
        
        # Ensure result is properly formatted as a JSON string if it's a dict
        if isinstance(result, dict):
            if "result" in result and not isinstance(result["result"], str):
                try:
                    # If the result has a nested result dict, ensure it's properly serialized
                    result["result"] = json.dumps(result["result"], default=str)
                except (TypeError, ValueError) as e:
                    logger.warning(f"Failed to serialize result: {str(e)}")
                    # If serialization fails, create a simple error response
                    result = {
                        "success": False,
                        "error": f"Failed to serialize result: {str(e)}",
                        "result": "{}"
                    }
        
        # Return the result
        return {"success": True, "result": result}

    except Exception as e:
        logger.error(f"Error calling tool: {str(e)}")
        return JSONResponse(
            status_code=500, content={"success": False, "error": str(e)}
        )


@app.get("/list_tools")
async def list_tools():
    """List all available tools."""
    tool_info = {}
    for tool_name, tool_func in tools.items():
        tool_info[tool_name] = {"description": tool_func.__doc__, "parameters": {}}

    return {"success": True, "tools": tool_info}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


if __name__ == "__main__":
    # Get host and port from environment variables
    host = os.environ.get("MCP_HOST", "0.0.0.0")
    port = 8001  # Explicitly set to 8001

    logger.info(f"Starting standalone MCP server at {host}:{port}")
    uvicorn.run(app, host=host, port=port)
