#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Client Implementation for Odoo 18 Integration

This module provides the MCP client implementation for the Odoo 18 integration project.
"""

import json
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Depends, Request
from pydantic import ValidationError

from ..core import get_logger, get_settings
from ..odoo.client import OdooClient
from ..odoo.schemas import (
    OdooConfig,
    MCPRequest,
    MCPResponse,
    SearchParams,
    CreateParams,
    UpdateParams,
    DeleteParams,
)
from .handlers import handle_request

logger = get_logger(__name__)


class MCPClient:
    """MCP Client for Odoo 18 integration."""

    def __init__(self):
        """Initialize the MCP client."""
        self.settings = get_settings()
        self.app = FastAPI(
            title=self.settings.app_name,
            description="MCP Integration for Odoo 18",
            version="0.1.0",
            debug=self.settings.mcp.debug,
        )
        self._setup_routes()
        self._odoo_client = None

    def _setup_routes(self) -> None:
        """Set up API routes."""
        self.app.post("/api/v1/odoo", response_model=MCPResponse)(self.handle_request)
        self.app.get("/health")(self.health_check)

    def get_odoo_client(self) -> OdooClient:
        """Get or create an Odoo client.

        Returns:
            OdooClient: Odoo client instance
        """
        if self._odoo_client is None:
            config = OdooConfig(**self.settings.dict_for_odoo_client())
            self._odoo_client = OdooClient(config)
            self._odoo_client.authenticate()
        return self._odoo_client

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle an MCP request.

        Args:
            request: MCP request

        Returns:
            MCPResponse: MCP response
        """
        try:
            odoo_client = self.get_odoo_client()
            
            # Use the unified request handler
            return handle_request(odoo_client, request)
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return MCPResponse(
                success=False,
                error=f"Validation error: {str(e)}",
            )
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}")
            return MCPResponse(
                success=False,
                error=f"Error handling request: {str(e)}",
            )

    async def health_check(self) -> Dict[str, Any]:
        """Health check endpoint.

        Returns:
            Dict[str, Any]: Health status
        """
        return {
            "status": "ok",
            "app_name": self.settings.app_name,
            "environment": self.settings.environment,
        }

    def run(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        """Run the MCP server.

        Args:
            host: Host to bind to
            port: Port to bind to
        """
        import uvicorn
        
        host = host or self.settings.mcp.host
        port = port or self.settings.mcp.port
        
        logger.info(f"Starting MCP server at {host}:{port}")
        uvicorn.run(
            self.app,
            host=host,
            port=port,
            log_level=self.settings.mcp.log_level.lower(),
        )