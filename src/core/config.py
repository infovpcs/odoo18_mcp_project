#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Management for Odoo 18 MCP Integration

This module handles configuration loading from environment variables
and provides a centralized settings management system.
"""

import os
from functools import lru_cache
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class OdooConfig(BaseModel):
    """Odoo connection settings."""

    url: str
    db: str
    username: str
    password: str
    api_key: Optional[str] = None
    timeout: int = 300


class MCPConfig(BaseModel):
    """MCP connection settings."""

    host: str
    port: int
    debug: bool
    log_level: str
    api_key: Optional[str] = None


class Settings(BaseModel):
    """Application settings."""

    app_name: str
    environment: str
    odoo: OdooConfig
    mcp: MCPConfig

    def dict_for_odoo_client(self) -> Dict[str, Any]:
        """Convert settings to a dict suitable for OdooClient."""
        return {
            "url": self.odoo.url,
            "db": self.odoo.db,
            "username": self.odoo.username,
            "password": self.odoo.password,
            "api_key": self.odoo.api_key,
            "timeout": self.odoo.timeout,
        }


@lru_cache()
def get_settings() -> Settings:
    """Get application settings from environment variables.

    Returns:
        Settings: Application settings
    """
    # Normalize URL
    odoo_url = os.getenv("ODOO_URL", "http://localhost:8069")
    if not odoo_url.startswith(("http://", "https://")):
        odoo_url = f"http://{odoo_url}"
    odoo_url = odoo_url.rstrip("/")
    
    # Create Odoo config
    odoo_config = OdooConfig(
        url=odoo_url,
        db=os.getenv("ODOO_DB", "odoo18"),
        username=os.getenv("ODOO_USERNAME", "admin"),
        password=os.getenv("ODOO_PASSWORD", "admin"),
        api_key=os.getenv("ODOO_API_KEY"),
        timeout=int(os.getenv("ODOO_TIMEOUT", "300")),
    )
    
    # Create MCP config
    mcp_config = MCPConfig(
        host=os.getenv("MCP_HOST", "0.0.0.0"),
        port=int(os.getenv("MCP_PORT", "8000")),
        debug=os.getenv("MCP_DEBUG", "false").lower() in ("true", "1", "yes"),
        log_level=os.getenv("MCP_LOG_LEVEL", "INFO"),
        api_key=os.getenv("MCP_API_KEY"),
    )
    
    # Create settings
    return Settings(
        app_name=os.getenv("APP_NAME", "odoo18-mcp-project"),
        environment=os.getenv("ENVIRONMENT", "development"),
        odoo=odoo_config,
        mcp=mcp_config,
    )