#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo Client Implementation

This module provides the Odoo client implementation for the MCP integration.
"""

import logging
from typing import Any, Dict, List, Optional, Union
import xmlrpc.client
from datetime import datetime

from .schemas import (
    OdooConfig,
    MCPRequest,
    MCPResponse,
    SearchParams,
    CreateParams,
    UpdateParams,
    DeleteParams,
)

logger = logging.getLogger(__name__)


class OdooClient:
    """Odoo client for XML-RPC API."""

    def __init__(self, config: OdooConfig):
        """Initialize the Odoo client.
        
        Args:
            config: Odoo configuration
        """
        self.config = config
        self.common = None
        self.models = None
        self.uid = None
        
        self._setup_connection()
    
    def _setup_connection(self) -> None:
        """Set up the XML-RPC connection to Odoo."""
        try:
            # Enable allow_none to handle None values in XML-RPC calls
            self.common = xmlrpc.client.ServerProxy(
                f"{self.config.url}/xmlrpc/2/common",
                allow_none=True
            )
            self.models = xmlrpc.client.ServerProxy(
                f"{self.config.url}/xmlrpc/2/object",
                allow_none=True
            )
            logger.info(f"Connected to Odoo server at {self.config.url}")
        except Exception as e:
            logger.error(f"Failed to connect to Odoo server: {str(e)}")
            raise ConnectionError(f"Odoo connection failed: {str(e)}")
    
    def authenticate(self) -> None:
        """Authenticate with the Odoo server."""
        try:
            self.uid = self.common.authenticate(
                self.config.db,
                self.config.username,
                self.config.password,
                {}
            )
            
            if not self.uid:
                raise AuthenticationError("Authentication failed: Invalid credentials")
                
            logger.info(f"Authenticated as user ID: {self.uid}")
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise AuthenticationError(f"Authentication failed: {str(e)}")
    
    def execute(
        self,
        model: str,
        method: str,
        args: List[Any] = None,
        kwargs: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Execute a method on an Odoo model.
        
        Args:
            model: Odoo model name
            method: Method name
            args: Method arguments as a list
            kwargs: Method keyword arguments as a dict
            
        Returns:
            Any: Method result
        """
        if not self.uid:
            self.authenticate()

        try:
            # Ensure args is a list
            pos_args = args if args is not None else []
            kw_args = kwargs if kwargs is not None else {}
            
            result = self.models.execute_kw(
                self.config.db,
                self.uid,
                self.config.password,
                model,
                method,
                pos_args,
                kw_args
            )
            return result
        except Exception as e:
            logger.error(f"Error executing {method} on {model}: {str(e)}")
            raise OperationError(f"Operation failed: {str(e)}")
    
    def search_read(
        self,
        model: str,
        params: SearchParams,
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search and read records from an Odoo model.
        
        Args:
            model: Model name
            params: Search parameters
            fields: Fields to return
            
        Returns:
            List[Dict[str, Any]]: Matching records
        """
        try:
            # Clean up domain to ensure no None values without explicit comparison
            domain = params.domain if params.domain else []
            
            # Prepare options for search_read
            options = {}
            if fields is not None:
                options['fields'] = fields
            if params.offset is not None:
                options['offset'] = params.offset
            if params.limit is not None:
                options['limit'] = params.limit
            if params.order is not None:
                options['order'] = params.order
            
            # Use search_read method directly as per Odoo documentation
            # The domain must be wrapped in a list as the first argument
            return self.models.execute_kw(
                self.config.db,
                self.uid,
                self.config.password,
                model,
                'search_read',
                [domain],  # Domain must be wrapped in a list
                options
            )
        except Exception as e:
            logger.error(f"Search_read failed for {model}: {str(e)}")
            raise OperationError(f"Search operation failed: {str(e)}")
    
    def create(self, model: str, params: CreateParams) -> int:
        """Create a new record.
        
        Args:
            model: Model name
            params: Create parameters
            
        Returns:
            int: Created record ID
        """
        try:
            return self.models.execute_kw(
                self.config.db,
                self.uid,
                self.config.password,
                model,
                'create',
                [params.values]
            )
        except Exception as e:
            logger.error(f"Create failed for {model}: {str(e)}")
            raise OperationError(f"Create operation failed: {str(e)}")
    
    def update(self, model: str, params: UpdateParams) -> bool:
        """Update an existing record.
        
        Args:
            model: Model name
            params: Update parameters
            
        Returns:
            bool: True if successful
        """
        try:
            self.models.execute_kw(
                self.config.db,
                self.uid,
                self.config.password,
                model,
                'write',
                [[params.id], params.values]
            )
            return True
        except Exception as e:
            logger.error(f"Update failed for {model}: {str(e)}")
            raise OperationError(f"Update operation failed: {str(e)}")
    
    def delete(self, model: str, params: DeleteParams) -> bool:
        """Delete records.
        
        Args:
            model: Model name
            params: Delete parameters
            
        Returns:
            bool: True if successful
        """
        try:
            self.models.execute_kw(
                self.config.db,
                self.uid,
                self.config.password,
                model,
                'unlink',
                [params.ids]
            )
            return True
        except Exception as e:
            logger.error(f"Delete failed for {model}: {str(e)}")
            raise OperationError(f"Delete operation failed: {str(e)}")


class OdooError(Exception):
    """Base class for Odoo client errors."""
    pass


class AuthenticationError(OdooError):
    """Authentication error."""
    pass


class OperationError(OdooError):
    """Operation error."""
    pass


class ConnectionError(OdooError):
    """Connection error."""
    pass