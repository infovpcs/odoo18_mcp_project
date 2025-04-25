#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Standalone MCP server for testing MCP tools.
"""

import os
import sys
import json
import logging
import importlib.util
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("standalone_mcp_server")

# Create FastAPI app
app = FastAPI(title="Standalone MCP Server", description="A standalone server for testing MCP tools")

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
        spec.loader.exec_module(mcp_server)

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
for tool_name, tool_func in mcp._tools.items():
    tools[tool_name] = tool_func

logger.info(f"Loaded {len(tools)} tools from MCP server: {', '.join(tools.keys())}")

@app.post("/call_tool")
async def call_tool(request: Request):
    """Call an MCP tool."""
    try:
        # Parse the request body
        body = await request.json()

        # Get the tool name and parameters
        tool_name = body.get("tool")
        params = body.get("params", {})

        if not tool_name:
            raise HTTPException(status_code=400, detail="Tool name is required")

        if tool_name not in tools:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        # Call the tool
        logger.info(f"Calling tool '{tool_name}' with parameters: {params}")
        result = tools[tool_name](**params)

        # Return the result
        return {"success": True, "result": result}

    except Exception as e:
        logger.error(f"Error calling tool: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/list_tools")
async def list_tools():
    """List all available tools."""
    tool_info = {}
    for tool_name, tool_func in tools.items():
        tool_info[tool_name] = {
            "description": tool_func.__doc__,
            "parameters": {}
        }

    return {"success": True, "tools": tool_info}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

if __name__ == "__main__":
    logger.info("Starting standalone MCP server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)