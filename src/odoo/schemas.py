#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo 18 Schemas for MCP Integration

This module defines the Pydantic models for data validation and serialization
in the Odoo 18 MCP integration project.
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field
from datetime import datetime

class OdooConfig(BaseModel):
    """Odoo connection configuration."""
    url: str = Field(..., description="Odoo server URL")
    db: str = Field(..., description="Database name")
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")
    api_key: Optional[str] = Field(None, description="API key for authentication")
    timeout: int = Field(default=300, description="Connection timeout in seconds")

class MCPRequest(BaseModel):
    """Base model for MCP requests."""
    operation: str = Field(..., description="Operation to perform")
    model: Optional[str] = Field(None, description="Odoo model name")
    params: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")
    context: Dict[str, Any] = Field(default_factory=dict, description="Operation context")

class MCPResponse(BaseModel):
    """Base model for MCP responses."""
    success: bool = Field(..., description="Operation success status")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message if any")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class SearchParams(BaseModel):
    """Search parameters for Odoo."""
    domain: List[List[Any]] = Field(default_factory=list, description="Search domain")
    offset: int = Field(default=0, description="Result offset")
    limit: Optional[int] = Field(None, description="Result limit")
    order: Optional[str] = Field(None, description="Sort order")

class CreateParams(BaseModel):
    """Create parameters for Odoo."""
    values: Dict[str, Any] = Field(..., description="Values to create")

class UpdateParams(BaseModel):
    """Update parameters for Odoo."""
    id: int = Field(..., description="Record ID")
    values: Dict[str, Any] = Field(..., description="Values to update")

class DeleteParams(BaseModel):
    """Delete parameters for Odoo."""
    ids: List[int] = Field(..., description="Record IDs to delete")