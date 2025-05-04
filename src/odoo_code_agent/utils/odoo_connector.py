#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo Connector for Code Agent

This module provides utilities for connecting to and interacting with Odoo
to assist with code generation.
"""

import logging
import os
import xmlrpc.client
from typing import Any, Dict, List, Optional, Union, Tuple

# Import Odoo client if available
try:
    from src.odoo.client import OdooClient
    from src.odoo.schemas import OdooConfig
    odoo_client_available = True
except ImportError:
    odoo_client_available = False

logger = logging.getLogger(__name__)


class OdooConnector:
    """Connector class for interacting with Odoo."""

    def __init__(
        self,
        url: str = "http://localhost:8069",
        db: str = "llmdb18",
        username: str = "admin",
        password: str = "admin",
    ):
        """Initialize the Odoo connector.

        Args:
            url: URL of the Odoo server
            db: Name of the Odoo database
            username: Odoo username
            password: Odoo password
        """
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.client = None
        self.common = None
        self.models = None
        self.uid = None

        # Initialize the client if available
        if odoo_client_available:
            self._initialize_client()
        else:
            self._initialize_xmlrpc()

    def _initialize_client(self) -> bool:
        """Initialize the Odoo client.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            config = OdooConfig(
                url=self.url,
                db=self.db,
                username=self.username,
                password=self.password
            )
            self.client = OdooClient(config)
            self.client.authenticate()
            logger.info("Odoo client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Odoo client: {str(e)}")
            self.client = None
            return False

    def _initialize_xmlrpc(self) -> bool:
        """Initialize the XML-RPC connection to Odoo.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Connect to common endpoint
            self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common", allow_none=True)

            # Authenticate
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})

            if not self.uid:
                logger.error("Authentication failed: Invalid credentials")
                return False

            # Connect to object endpoint
            self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object", allow_none=True)

            logger.info(f"XML-RPC connection initialized successfully. User ID: {self.uid}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize XML-RPC connection: {str(e)}")
            self.common = None
            self.models = None
            self.uid = None
            return False

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
            Method result
        """
        if self.client:
            # Use the OdooClient if available
            return self.client.execute(model, method, args, kwargs)
        elif self.models and self.uid:
            # Use XML-RPC directly
            try:
                # Ensure args is a list
                pos_args = args if args is not None else []
                kw_args = kwargs if kwargs is not None else {}

                return self.models.execute_kw(
                    self.db,
                    self.uid,
                    self.password,
                    model,
                    method,
                    pos_args,
                    kw_args
                )
            except Exception as e:
                logger.error(f"Error executing {method} on {model}: {str(e)}")
                raise Exception(f"Operation failed: {str(e)}")
        else:
            raise Exception("Odoo connection not initialized")

    def search(
        self,
        model: str,
        domain: List[List[Any]] = None,
        offset: int = 0,
        limit: Optional[int] = None,
        order: Optional[str] = None
    ) -> List[int]:
        """Search for records.

        Args:
            model: Model name
            domain: Search domain
            offset: Result offset
            limit: Result limit
            order: Sort order

        Returns:
            List of record IDs
        """
        domain = domain or []
        kwargs = {}
        if offset:
            kwargs['offset'] = offset
        if limit is not None:
            kwargs['limit'] = limit
        if order:
            kwargs['order'] = order

        return self.execute(model, 'search', [domain], kwargs)

    def search_read(
        self,
        model: str,
        domain: List[List[Any]] = None,
        fields: List[str] = None,
        offset: int = 0,
        limit: Optional[int] = None,
        order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for records and read their data.

        Args:
            model: Model name
            domain: Search domain
            fields: Fields to read
            offset: Result offset
            limit: Result limit
            order: Sort order

        Returns:
            List of records with their data
        """
        domain = domain or []
        kwargs = {}
        if fields is not None:
            kwargs['fields'] = fields
        if offset:
            kwargs['offset'] = offset
        if limit is not None:
            kwargs['limit'] = limit
        if order:
            kwargs['order'] = order

        return self.execute(model, 'search_read', [domain], kwargs)

    def read(
        self,
        model: str,
        ids: List[int],
        fields: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Read record data.

        Args:
            model: Model name
            ids: Record IDs
            fields: Fields to read

        Returns:
            List of records with their data
        """
        kwargs = {}
        if fields is not None:
            kwargs['fields'] = fields

        return self.execute(model, 'read', [ids], kwargs)

    def create(
        self,
        model: str,
        values: Dict[str, Any]
    ) -> int:
        """Create a new record.

        Args:
            model: Model name
            values: Values for the new record

        Returns:
            ID of the created record
        """
        return self.execute(model, 'create', [values])

    def write(
        self,
        model: str,
        ids: List[int],
        values: Dict[str, Any]
    ) -> bool:
        """Update records.

        Args:
            model: Model name
            ids: Record IDs
            values: Values to update

        Returns:
            True if successful
        """
        return self.execute(model, 'write', [ids, values])

    def unlink(
        self,
        model: str,
        ids: List[int]
    ) -> bool:
        """Delete records.

        Args:
            model: Model name
            ids: Record IDs

        Returns:
            True if successful
        """
        return self.execute(model, 'unlink', [ids])

    def get_model_fields(self, model_name: str) -> Dict[str, Dict[str, Any]]:
        """Get the fields of a model.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary of fields with their attributes
        """
        return self.execute(model_name, 'fields_get')

    def get_model_metadata(self, model_name: str) -> Dict[str, Any]:
        """Get metadata for a model.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary with model metadata
        """
        # Get model information from ir.model
        model_info = self.search_read(
            'ir.model',
            [('model', '=', model_name)],
            ['name', 'model', 'info', 'description', 'state', 'transient', 'modules']
        )

        if not model_info:
            return {}

        # Get fields information
        fields_info = self.get_model_fields(model_name)

        # Combine information
        metadata = model_info[0]
        metadata['fields'] = fields_info

        return metadata

    def get_models_list(self) -> List[Dict[str, Any]]:
        """Get a list of all models.

        Returns:
            List of models with their information
        """
        return self.search_read(
            'ir.model',
            [('state', '=', 'base')],
            ['name', 'model', 'info', 'description', 'modules']
        )

    def get_module_list(self) -> List[Dict[str, Any]]:
        """Get a list of all installed modules.

        Returns:
            List of modules with their information
        """
        return self.search_read(
            'ir.module.module',
            [('state', '=', 'installed')],
            ['name', 'shortdesc', 'summary', 'description', 'author', 'website', 'version']
        )

    def get_field_groups(self, model_name: str) -> Dict[str, List[str]]:
        """Get field groups for a model.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary with field groups
        """
        fields_info = self.get_model_fields(model_name)

        # Group fields by type
        groups = {}
        for field_name, field_info in fields_info.items():
            field_type = field_info.get('type', 'unknown')
            if field_type not in groups:
                groups[field_type] = []
            groups[field_type].append(field_name)

        return groups

    def get_record_template(self, model_name: str) -> Dict[str, Any]:
        """Get a template for creating a record.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary with field names and default values
        """
        fields_info = self.get_model_fields(model_name)

        # Create a template with default values
        template = {}
        for field_name, field_info in fields_info.items():
            # Skip computed fields and related fields
            if field_info.get('readonly', False) and not field_info.get('store', True):
                continue

            # Skip fields with default values
            if 'default' in field_info:
                continue

            # Add field to template with appropriate default value
            field_type = field_info.get('type', 'unknown')
            if field_type == 'char':
                template[field_name] = ""
            elif field_type == 'text':
                template[field_name] = ""
            elif field_type == 'integer':
                template[field_name] = 0
            elif field_type == 'float':
                template[field_name] = 0.0
            elif field_type == 'boolean':
                template[field_name] = False
            elif field_type == 'date':
                template[field_name] = "2023-01-01"
            elif field_type == 'datetime':
                template[field_name] = "2023-01-01 00:00:00"
            elif field_type == 'selection':
                # Get the first selection option
                selection = field_info.get('selection', [])
                if selection and isinstance(selection, list) and len(selection) > 0:
                    template[field_name] = selection[0][0]
                else:
                    template[field_name] = False
            elif field_type == 'many2one':
                template[field_name] = False
            elif field_type in ['one2many', 'many2many']:
                template[field_name] = []

        return template


# Create a singleton instance
odoo_connector = OdooConnector(
    url=os.environ.get("ODOO_URL", "http://localhost:8069"),
    db=os.environ.get("ODOO_DB", "llmdb18"),
    username=os.environ.get("ODOO_USERNAME", "admin"),
    password=os.environ.get("ODOO_PASSWORD", "admin")
)