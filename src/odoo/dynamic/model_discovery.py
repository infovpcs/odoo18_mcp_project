#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model Discovery Module

This module provides functionality for discovering Odoo models and their metadata.
"""

import logging
from typing import Dict, List, Any, Optional, Union, Set
from ..client import OdooClient

logger = logging.getLogger(__name__)

class ModelDiscovery:
    """Class for discovering Odoo models and their metadata."""
    
    def __init__(self, odoo_client: OdooClient):
        """Initialize the model discovery.
        
        Args:
            odoo_client: Odoo client instance
        """
        self.client = odoo_client
        self._models_cache: Dict[str, Dict[str, Any]] = {}
        self._fields_cache: Dict[str, Dict[str, Dict[str, Any]]] = {}
    
    def get_available_models(self, filter_keyword: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get a list of available models.
        
        Args:
            filter_keyword: Optional keyword to filter models by name or description
            
        Returns:
            List of model information dictionaries
        """
        domain = []
        if filter_keyword:
            domain = [
                '|',
                ('model', 'ilike', filter_keyword),
                ('name', 'ilike', filter_keyword)
            ]
        
        try:
            models = self.client.execute(
                'ir.model',
                'search_read',
                [domain],
                {'fields': ['name', 'model', 'info']}
            )
            
            # Update cache
            for model in models:
                model_name = model.get('model')
                if model_name:
                    self._models_cache[model_name] = model
            
            return models
        except Exception as e:
            logger.error(f"Failed to get available models: {str(e)}")
            return []
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            
        Returns:
            Model information dictionary or None if not found
        """
        # Check cache first
        if model_name in self._models_cache:
            return self._models_cache[model_name]
        
        try:
            models = self.client.execute(
                'ir.model',
                'search_read',
                [[('model', '=', model_name)]],
                {'fields': ['name', 'model', 'info']}
            )
            
            if models and len(models) > 0:
                model = models[0]
                self._models_cache[model_name] = model
                return model
            
            return None
        except Exception as e:
            logger.error(f"Failed to get model info for {model_name}: {str(e)}")
            return None
    
    def get_model_fields(self, model_name: str) -> Dict[str, Dict[str, Any]]:
        """Get fields for a specific model.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            
        Returns:
            Dictionary of field information
        """
        # Check cache first
        if model_name in self._fields_cache:
            return self._fields_cache[model_name]
        
        try:
            # Use fields_get method to get comprehensive field information
            fields = self.client.execute(
                model_name,
                'fields_get',
                [],
                {'attributes': ['string', 'help', 'type', 'required', 'readonly', 'selection', 'relation']}
            )
            
            # Get additional field information from ir.model.fields
            model_id = self._get_model_id(model_name)
            if model_id:
                ir_fields = self.client.execute(
                    'ir.model.fields',
                    'search_read',
                    [[('model_id', '=', model_id)]],
                    {'fields': ['name', 'field_description', 'ttype', 'required', 'readonly', 'selection', 'relation']}
                )
                
                # Enhance fields with additional information
                for ir_field in ir_fields:
                    field_name = ir_field.get('name')
                    if field_name and field_name in fields:
                        fields[field_name]['required'] = ir_field.get('required', fields[field_name].get('required', False))
                        fields[field_name]['readonly'] = ir_field.get('readonly', fields[field_name].get('readonly', False))
            
            # Update cache
            self._fields_cache[model_name] = fields
            
            return fields
        except Exception as e:
            logger.error(f"Failed to get fields for {model_name}: {str(e)}")
            return {}
    
    def get_required_fields(self, model_name: str) -> List[str]:
        """Get required fields for a specific model.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            
        Returns:
            List of required field names
        """
        fields = self.get_model_fields(model_name)
        return [name for name, info in fields.items() if info.get('required', False)]
    
    def get_readonly_fields(self, model_name: str) -> List[str]:
        """Get readonly fields for a specific model.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            
        Returns:
            List of readonly field names
        """
        fields = self.get_model_fields(model_name)
        return [name for name, info in fields.items() if info.get('readonly', False)]
    
    def get_relational_fields(self, model_name: str) -> Dict[str, str]:
        """Get relational fields for a specific model.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            
        Returns:
            Dictionary mapping field names to related model names
        """
        fields = self.get_model_fields(model_name)
        relational_fields = {}
        
        for name, info in fields.items():
            field_type = info.get('type')
            if field_type in ('many2one', 'one2many', 'many2many') and 'relation' in info:
                relational_fields[name] = info['relation']
        
        return relational_fields
    
    def get_selection_fields(self, model_name: str) -> Dict[str, List[tuple]]:
        """Get selection fields for a specific model.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            
        Returns:
            Dictionary mapping field names to selection options
        """
        fields = self.get_model_fields(model_name)
        selection_fields = {}
        
        for name, info in fields.items():
            if info.get('type') == 'selection' and 'selection' in info:
                selection_fields[name] = info['selection']
        
        return selection_fields
    
    def _get_model_id(self, model_name: str) -> Optional[int]:
        """Get the ID of a model from its name.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            
        Returns:
            Model ID or None if not found
        """
        try:
            models = self.client.execute(
                'ir.model',
                'search_read',
                [[('model', '=', model_name)]],
                {'fields': ['id']}
            )
            
            if models and len(models) > 0:
                return models[0].get('id')
            
            return None
        except Exception as e:
            logger.error(f"Failed to get model ID for {model_name}: {str(e)}")
            return None