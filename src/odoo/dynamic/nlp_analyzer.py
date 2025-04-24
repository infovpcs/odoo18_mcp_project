#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NLP Analyzer Module

This module provides functionality for analyzing field names and descriptions
using NLP techniques to determine their importance and relationships.
"""

import logging
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from .model_discovery import ModelDiscovery

logger = logging.getLogger(__name__)

class NlpAnalyzer:
    """Class for analyzing field names and descriptions using NLP techniques."""
    
    def __init__(self, model_discovery: ModelDiscovery):
        """Initialize the NLP analyzer.
        
        Args:
            model_discovery: ModelDiscovery instance
        """
        self.model_discovery = model_discovery
        self._important_terms = {
            'high': {
                'name', 'title', 'description', 'code', 'reference', 'email', 
                'phone', 'address', 'date', 'amount', 'price', 'cost', 'quantity',
                'active', 'state', 'status', 'priority', 'sequence'
            },
            'medium': {
                'note', 'comment', 'tag', 'category', 'group', 'type', 'user',
                'partner', 'customer', 'supplier', 'vendor', 'company', 'currency',
                'tax', 'discount', 'payment', 'invoice', 'order', 'product'
            },
            'low': {
                'color', 'image', 'icon', 'attachment', 'message', 'follower',
                'activity', 'access', 'permission', 'log', 'history', 'archive'
            }
        }
    
    def analyze_field_importance(self, model_name: str) -> Dict[str, int]:
        """Analyze the importance of fields based on their names and descriptions.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            
        Returns:
            Dictionary mapping field names to importance scores (0-100)
        """
        fields = self.model_discovery.get_model_fields(model_name)
        importance_scores = {}
        
        for field_name, field_info in fields.items():
            # Base score
            score = 50
            
            # Analyze field name
            name_score = self._analyze_term(field_name)
            score += name_score
            
            # Analyze field label/string
            field_label = field_info.get('string', '')
            if field_label:
                label_score = self._analyze_term(field_label.lower())
                score += label_score * 0.5  # Label is less important than name
            
            # Analyze field help text
            help_text = field_info.get('help', '')
            if help_text:
                # Check for important phrases in help text
                if re.search(r'(required|mandatory|must|important|necessary)', help_text, re.IGNORECASE):
                    score += 10
                if re.search(r'(optional|not required|not mandatory)', help_text, re.IGNORECASE):
                    score -= 5
            
            # Adjust based on field type
            field_type = field_info.get('type')
            if field_type in ('char', 'text'):
                score += 5
            elif field_type in ('many2one', 'one2many', 'many2many'):
                score -= 5
            elif field_type == 'boolean' and 'active' in field_name:
                score += 15
            
            # Adjust for common important fields
            if field_name in ('name', 'display_name'):
                score += 20
            elif field_name == 'active':
                score += 15
            elif field_name == 'sequence':
                score += 10
            
            # Ensure score is within 0-100 range
            importance_scores[field_name] = max(0, min(100, score))
        
        return importance_scores
    
    def suggest_field_groups(self, model_name: str) -> Dict[str, List[str]]:
        """Suggest logical groups for fields based on their names and types.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            
        Returns:
            Dictionary mapping group names to lists of field names
        """
        fields = self.model_discovery.get_model_fields(model_name)
        groups = {
            'basic_info': [],
            'contact_info': [],
            'address_info': [],
            'dates': [],
            'numeric_values': [],
            'descriptions': [],
            'relations': [],
            'status': [],
            'other': []
        }
        
        # Define patterns for each group
        patterns = {
            'basic_info': r'(name|code|reference|title|type|category|tag)',
            'contact_info': r'(email|phone|mobile|fax|website)',
            'address_info': r'(street|city|zip|state|country|address)',
            'dates': r'(date|time|day|month|year|deadline|schedule)',
            'numeric_values': r'(amount|price|cost|quantity|number|count|total|sum|discount|tax)',
            'descriptions': r'(description|note|comment|remark|detail)',
            'status': r'(state|status|stage|active|archived|priority|sequence)'
        }
        
        for field_name, field_info in fields.items():
            field_type = field_info.get('type')
            
            # Check if field belongs to a specific group based on name
            assigned = False
            for group, pattern in patterns.items():
                if re.search(pattern, field_name, re.IGNORECASE):
                    groups[group].append(field_name)
                    assigned = True
                    break
            
            # If not assigned based on name, try to assign based on type
            if not assigned:
                if field_type in ('many2one', 'one2many', 'many2many'):
                    groups['relations'].append(field_name)
                elif field_type in ('date', 'datetime'):
                    groups['dates'].append(field_name)
                elif field_type in ('float', 'integer', 'monetary'):
                    groups['numeric_values'].append(field_name)
                else:
                    groups['other'].append(field_name)
        
        # Remove empty groups
        return {group: fields for group, fields in groups.items() if fields}
    
    def suggest_search_fields(self, model_name: str) -> List[str]:
        """Suggest fields that are good candidates for search operations.
        
        Args:
            model_name: Name of the model (e.g., 'res.partner')
            
        Returns:
            List of field names
        """
        fields = self.model_discovery.get_model_fields(model_name)
        search_fields = []
        
        for field_name, field_info in fields.items():
            field_type = field_info.get('type')
            
            # Text fields are good for searching
            if field_type in ('char', 'text'):
                # Name and description fields are particularly good
                if re.search(r'(name|code|reference|description)', field_name, re.IGNORECASE):
                    search_fields.append(field_name)
                # Other text fields might be useful too
                elif not field_name.startswith('_') and not field_info.get('readonly', False):
                    search_fields.append(field_name)
            
            # Selection fields can be good for filtering
            elif field_type == 'selection':
                search_fields.append(field_name)
            
            # Boolean fields for active/inactive filtering
            elif field_type == 'boolean' and field_name in ('active', 'archived'):
                search_fields.append(field_name)
        
        return search_fields
    
    def _analyze_term(self, term: str) -> int:
        """Analyze a term to determine its importance.
        
        Args:
            term: Term to analyze
            
        Returns:
            Importance score adjustment
        """
        # Convert to lowercase and split by non-alphanumeric characters
        words = re.findall(r'[a-z0-9]+', term.lower())
        
        score = 0
        for word in words:
            if word in self._important_terms['high']:
                score += 15
            elif word in self._important_terms['medium']:
                score += 10
            elif word in self._important_terms['low']:
                score += 5
        
        return score