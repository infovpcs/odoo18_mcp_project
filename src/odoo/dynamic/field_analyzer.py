#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Field Analyzer Module

This module provides functionality for analyzing Odoo model fields and determining
their importance, default values, and validation rules.
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from .model_discovery import ModelDiscovery

logger = logging.getLogger(__name__)

class FieldAnalyzer:
    """Class for analyzing Odoo model fields."""
    
    def __init__(self, model_discovery: ModelDiscovery):
        """Initialize the field analyzer.
        
        Args:
            model_discovery: ModelDiscovery instance
        """
        self.model_discovery = model_discovery
    
    def get_field_importance(self, model_name: str) -> Dict[str, int]:
        """Get importance scores for fields of a model.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            
        Returns:
            Dictionary mapping field names to importance scores (0-100)
        """
        fields = self.model_discovery.get_model_fields(model_name)
        required_fields = self.model_discovery.get_required_fields(model_name)
        readonly_fields = self.model_discovery.get_readonly_fields(model_name)
        
        importance_scores = {}
        
        for field_name, field_info in fields.items():
            # Skip readonly fields
            if field_name in readonly_fields:
                importance_scores[field_name] = 0
                continue
            
            # Base score
            score = 50
            
            # Required fields are more important
            if field_name in required_fields:
                score += 30
            
            # Name and description fields are important
            if field_name in ('name', 'description', 'display_name'):
                score += 20
            
            # ID fields are less important for user input
            if field_name == 'id' or field_name.endswith('_id'):
                score -= 10
            
            # Adjust based on field type
            field_type = field_info.get('type')
            if field_type in ('char', 'text'):
                score += 5
            elif field_type in ('many2one', 'one2many', 'many2many'):
                score -= 5
            
            # Ensure score is within 0-100 range
            importance_scores[field_name] = max(0, min(100, score))
        
        return importance_scores
    
    def get_create_fields(self, model_name: str, min_importance: int = 50) -> List[str]:
        """Get fields that should be included in create operations.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            min_importance: Minimum importance score for inclusion
            
        Returns:
            List of field names
        """
        importance_scores = self.get_field_importance(model_name)
        readonly_fields = self.model_discovery.get_readonly_fields(model_name)
        
        # Include required fields and fields with sufficient importance
        create_fields = []
        for field_name, score in importance_scores.items():
            if field_name in readonly_fields:
                continue
                
            if score >= min_importance:
                create_fields.append(field_name)
        
        return create_fields
    
    def get_read_fields(self, model_name: str, min_importance: int = 30) -> List[str]:
        """Get fields that should be included in read operations.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            min_importance: Minimum importance score for inclusion
            
        Returns:
            List of field names
        """
        importance_scores = self.get_field_importance(model_name)
        
        # Include fields with sufficient importance
        read_fields = []
        for field_name, score in importance_scores.items():
            if score >= min_importance:
                read_fields.append(field_name)
        
        # Always include id field
        if 'id' not in read_fields:
            read_fields.append('id')
        
        return read_fields
    
    def get_update_fields(self, model_name: str, min_importance: int = 50) -> List[str]:
        """Get fields that should be included in update operations.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            min_importance: Minimum importance score for inclusion
            
        Returns:
            List of field names
        """
        importance_scores = self.get_field_importance(model_name)
        readonly_fields = self.model_discovery.get_readonly_fields(model_name)
        
        # Include fields with sufficient importance, excluding readonly fields
        update_fields = []
        for field_name, score in importance_scores.items():
            if field_name in readonly_fields:
                continue
                
            if score >= min_importance:
                update_fields.append(field_name)
        
        return update_fields
    
    def get_field_defaults(self, model_name: str) -> Dict[str, Any]:
        """Get default values for fields of a model.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            
        Returns:
            Dictionary mapping field names to default values
        """
        fields = self.model_discovery.get_model_fields(model_name)
        defaults = {}
        
        for field_name, field_info in fields.items():
            field_type = field_info.get('type')
            
            # Set sensible defaults based on field type
            if field_type == 'boolean':
                defaults[field_name] = False
            elif field_type == 'integer':
                defaults[field_name] = 0
            elif field_type == 'float':
                defaults[field_name] = 0.0
            elif field_type == 'char':
                defaults[field_name] = ''
            elif field_type == 'text':
                defaults[field_name] = ''
            elif field_type == 'selection' and 'selection' in field_info and field_info['selection']:
                # Use first selection option as default
                defaults[field_name] = field_info['selection'][0][0]
            elif field_type == 'many2one':
                defaults[field_name] = False
            
        return defaults
    
    def get_field_validation_rules(self, model_name: str) -> Dict[str, Dict[str, Any]]:
        """Get validation rules for fields of a model.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            
        Returns:
            Dictionary mapping field names to validation rules
        """
        fields = self.model_discovery.get_model_fields(model_name)
        validation_rules = {}
        
        for field_name, field_info in fields.items():
            field_type = field_info.get('type')
            rules = {}
            
            # Set validation rules based on field type
            if field_type == 'char':
                rules['type'] = 'string'
                rules['max_length'] = 256  # Default max length for char fields
            elif field_type == 'text':
                rules['type'] = 'string'
            elif field_type == 'integer':
                rules['type'] = 'integer'
            elif field_type == 'float':
                rules['type'] = 'number'
            elif field_type == 'boolean':
                rules['type'] = 'boolean'
            elif field_type == 'date':
                rules['type'] = 'date'
            elif field_type == 'datetime':
                rules['type'] = 'datetime'
            elif field_type == 'selection':
                rules['type'] = 'string'
                if 'selection' in field_info:
                    rules['allowed_values'] = [option[0] for option in field_info['selection']]
            elif field_type == 'many2one':
                rules['type'] = 'integer'
                rules['relation'] = field_info.get('relation')
            
            # Add required rule if applicable
            if field_info.get('required', False):
                rules['required'] = True
            
            if rules:
                validation_rules[field_name] = rules
        
        return validation_rules