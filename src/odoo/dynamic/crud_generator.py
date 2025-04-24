#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CRUD Generator Module

This module provides functionality for generating CRUD operations for Odoo models.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from ..client import OdooClient
from .model_discovery import ModelDiscovery
from .field_analyzer import FieldAnalyzer

logger = logging.getLogger(__name__)

class CrudGenerator:
    """Class for generating CRUD operations for Odoo models."""
    
    def __init__(self, odoo_client: OdooClient, model_discovery: ModelDiscovery, field_analyzer: FieldAnalyzer):
        """Initialize the CRUD generator.
        
        Args:
            odoo_client: OdooClient instance
            model_discovery: ModelDiscovery instance
            field_analyzer: FieldAnalyzer instance
        """
        self.client = odoo_client
        self.model_discovery = model_discovery
        self.field_analyzer = field_analyzer
    
    def create_record(self, model_name: str, values: Dict[str, Any]) -> Union[int, Dict[str, Any]]:
        """Create a record in the specified model.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            values: Values for the record
            
        Returns:
            ID of the created record or error information
        """
        try:
            # Get required fields
            required_fields = self.model_discovery.get_required_fields(model_name)
            
            # Check if all required fields are provided
            missing_fields = [field for field in required_fields if field not in values]
            if missing_fields:
                return {
                    'success': False,
                    'error': f"Missing required fields: {', '.join(missing_fields)}"
                }
            
            # Create the record
            record_id = self.client.execute(model_name, 'create', [values])
            
            return record_id
        except Exception as e:
            logger.error(f"Failed to create record in {model_name}: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to create record: {str(e)}"
            }
    
    def read_records(
        self, 
        model_name: str, 
        domain: Optional[List] = None, 
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order: Optional[str] = None
    ) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
        """Read records from the specified model.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            domain: Search domain
            fields: Fields to include in the result
            limit: Maximum number of records to return
            offset: Number of records to skip
            order: Sorting order
            
        Returns:
            List of records or error information
        """
        try:
            # If fields not specified, use field analyzer to determine important fields
            if not fields:
                fields = self.field_analyzer.get_read_fields(model_name)
            
            # Prepare kwargs
            kwargs = {}
            if fields:
                kwargs['fields'] = fields
            if limit is not None:
                kwargs['limit'] = limit
            if offset is not None:
                kwargs['offset'] = offset
            if order:
                kwargs['order'] = order
            
            # Read the records
            records = self.client.execute(
                model_name, 
                'search_read', 
                [domain or []], 
                kwargs
            )
            
            return records
        except Exception as e:
            logger.error(f"Failed to read records from {model_name}: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to read records: {str(e)}"
            }
    
    def update_record(self, model_name: str, record_id: int, values: Dict[str, Any]) -> Union[bool, Dict[str, Any]]:
        """Update a record in the specified model.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            record_id: ID of the record to update
            values: Values to update
            
        Returns:
            Success status or error information
        """
        try:
            # Get readonly fields
            readonly_fields = self.model_discovery.get_readonly_fields(model_name)
            
            # Remove readonly fields from values
            for field in readonly_fields:
                if field in values:
                    del values[field]
            
            # Update the record
            result = self.client.execute(model_name, 'write', [[record_id], values])
            
            return result
        except Exception as e:
            logger.error(f"Failed to update record {record_id} in {model_name}: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to update record: {str(e)}"
            }
    
    def delete_record(self, model_name: str, record_id: int) -> Union[bool, Dict[str, Any]]:
        """Delete a record from the specified model.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            record_id: ID of the record to delete
            
        Returns:
            Success status or error information
        """
        try:
            # Delete the record
            result = self.client.execute(model_name, 'unlink', [[record_id]])
            
            return result
        except Exception as e:
            logger.error(f"Failed to delete record {record_id} from {model_name}: {str(e)}")
            return {
                'success': False,
                'error': f"Failed to delete record: {str(e)}"
            }
    
    def get_record_template(self, model_name: str) -> Dict[str, Any]:
        """Get a template for creating a record in the specified model.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            
        Returns:
            Template with default values
        """
        # Get important fields for creation
        create_fields = self.field_analyzer.get_create_fields(model_name)
        
        # Get default values
        defaults = self.field_analyzer.get_field_defaults(model_name)
        
        # Create template with defaults for important fields
        template = {}
        for field in create_fields:
            if field in defaults:
                template[field] = defaults[field]
        
        return template
    
    def get_model_metadata(self, model_name: str) -> Dict[str, Any]:
        """Get metadata for the specified model.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            
        Returns:
            Model metadata
        """
        # Get model info
        model_info = self.model_discovery.get_model_info(model_name)
        
        # Get field information
        fields = self.model_discovery.get_model_fields(model_name)
        
        # Get field importance
        importance = self.field_analyzer.get_field_importance(model_name)
        
        # Get validation rules
        validation = self.field_analyzer.get_field_validation_rules(model_name)
        
        # Combine all metadata
        metadata = {
            'model': model_info,
            'fields': fields,
            'importance': importance,
            'validation': validation,
            'required_fields': self.model_discovery.get_required_fields(model_name),
            'readonly_fields': self.model_discovery.get_readonly_fields(model_name),
            'relational_fields': self.model_discovery.get_relational_fields(model_name),
            'selection_fields': self.model_discovery.get_selection_fields(model_name),
            'create_fields': self.field_analyzer.get_create_fields(model_name),
            'read_fields': self.field_analyzer.get_read_fields(model_name),
            'update_fields': self.field_analyzer.get_update_fields(model_name),
            'defaults': self.field_analyzer.get_field_defaults(model_name)
        }
        
        return metadata