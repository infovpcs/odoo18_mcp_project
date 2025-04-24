#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Field mapping utilities for Export/Import agent flow.
"""

import logging
from typing import Dict, List, Any, Tuple, Optional

logger = logging.getLogger(__name__)


def suggest_field_mapping(csv_fields: List[str], 
                          odoo_fields: Dict[str, Any]) -> Dict[str, str]:
    """
    Suggest field mapping between CSV fields and Odoo fields.
    
    Args:
        csv_fields: List of field names from the CSV file
        odoo_fields: Dictionary of Odoo field information
        
    Returns:
        Dictionary mapping CSV field names to Odoo field names
    """
    mapping = {}
    
    # Create a normalized version of Odoo field names for better matching
    normalized_odoo_fields = {}
    for field_name, field_info in odoo_fields.items():
        # Use the string (label) and the technical name for matching
        normalized_name = field_name.lower().replace('_', '')
        normalized_odoo_fields[normalized_name] = field_name
        
        if 'string' in field_info:
            normalized_label = field_info['string'].lower().replace(' ', '').replace('_', '')
            normalized_odoo_fields[normalized_label] = field_name
    
    # Try to match CSV fields to Odoo fields
    for csv_field in csv_fields:
        # Try exact match first
        if csv_field in odoo_fields:
            mapping[csv_field] = csv_field
            continue
        
        # Try normalized match
        normalized_csv_field = csv_field.lower().replace('_', '')
        if normalized_csv_field in normalized_odoo_fields:
            mapping[csv_field] = normalized_odoo_fields[normalized_csv_field]
            continue
        
        # Try partial match
        for norm_odoo_field, odoo_field in normalized_odoo_fields.items():
            if normalized_csv_field in norm_odoo_field or norm_odoo_field in normalized_csv_field:
                mapping[csv_field] = odoo_field
                break
    
    logger.info(f"Suggested field mapping: {mapping}")
    return mapping


def validate_field_mapping(field_mapping: Dict[str, str], 
                           odoo_fields: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate field mapping against Odoo fields.
    
    Args:
        field_mapping: Dictionary mapping CSV field names to Odoo field names
        odoo_fields: Dictionary of Odoo field information
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check if all mapped Odoo fields exist
    for csv_field, odoo_field in field_mapping.items():
        if odoo_field not in odoo_fields:
            errors.append(f"Odoo field '{odoo_field}' mapped from CSV field '{csv_field}' does not exist")
    
    # Check if required fields are mapped
    required_fields = [field for field, info in odoo_fields.items() 
                      if info.get('required', False) and field != 'id']
    
    mapped_odoo_fields = set(field_mapping.values())
    missing_required = [field for field in required_fields if field not in mapped_odoo_fields]
    
    if missing_required:
        errors.append(f"Required Odoo fields not mapped: {', '.join(missing_required)}")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def get_field_type_compatibility(csv_fields: List[Dict[str, Any]], 
                                odoo_fields: Dict[str, Any],
                                field_mapping: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
    """
    Check compatibility between CSV field values and Odoo field types.
    
    Args:
        csv_fields: List of dictionaries with sample values from CSV
        odoo_fields: Dictionary of Odoo field information
        field_mapping: Dictionary mapping CSV field names to Odoo field names
        
    Returns:
        Dictionary of compatibility information for each mapped field
    """
    compatibility = {}
    
    for csv_field, odoo_field in field_mapping.items():
        if odoo_field not in odoo_fields:
            compatibility[csv_field] = {
                'odoo_field': odoo_field,
                'compatible': False,
                'reason': f"Odoo field '{odoo_field}' does not exist"
            }
            continue
        
        odoo_field_info = odoo_fields[odoo_field]
        odoo_field_type = odoo_field_info.get('type', 'unknown')
        
        # Get sample values from CSV
        sample_values = [record.get(csv_field) for record in csv_fields[:5] if csv_field in record]
        
        # Check compatibility based on field type
        is_compatible = True
        reason = None
        
        if odoo_field_type in ['integer', 'float', 'monetary']:
            # Check if values can be converted to numbers
            for value in sample_values:
                if value is not None and value != '':
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        is_compatible = False
                        reason = f"Value '{value}' cannot be converted to a number"
                        break
        
        elif odoo_field_type == 'boolean':
            # Check if values can be converted to booleans
            for value in sample_values:
                if value is not None and value != '':
                    if not isinstance(value, bool) and value.lower() not in ['true', 'false', '0', '1', 'yes', 'no']:
                        is_compatible = False
                        reason = f"Value '{value}' cannot be converted to a boolean"
                        break
        
        elif odoo_field_type == 'date':
            # Check if values can be converted to dates
            for value in sample_values:
                if value is not None and value != '':
                    try:
                        from datetime import datetime
                        datetime.strptime(value, '%Y-%m-%d')
                    except (ValueError, TypeError):
                        is_compatible = False
                        reason = f"Value '{value}' is not in YYYY-MM-DD format"
                        break
        
        elif odoo_field_type == 'datetime':
            # Check if values can be converted to datetimes
            for value in sample_values:
                if value is not None and value != '':
                    try:
                        from datetime import datetime
                        datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    except (ValueError, TypeError):
                        is_compatible = False
                        reason = f"Value '{value}' is not in YYYY-MM-DD HH:MM:SS format"
                        break
        
        compatibility[csv_field] = {
            'odoo_field': odoo_field,
            'odoo_type': odoo_field_type,
            'compatible': is_compatible,
            'reason': reason
        }
    
    return compatibility


def convert_value_for_odoo(value: Any, odoo_field_type: str) -> Any:
    """
    Convert a value to the appropriate type for an Odoo field.
    
    Args:
        value: The value to convert
        odoo_field_type: The Odoo field type
        
    Returns:
        The converted value
    """
    if value is None or value == '':
        return False
    
    if odoo_field_type in ['integer', 'float', 'monetary']:
        try:
            if odoo_field_type == 'integer':
                return int(float(value))
            return float(value)
        except (ValueError, TypeError):
            return False
    
    elif odoo_field_type == 'boolean':
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ['true', '1', 'yes']
        return bool(value)
    
    elif odoo_field_type == 'date':
        try:
            from datetime import datetime
            return datetime.strptime(value, '%Y-%m-%d').strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            return False
    
    elif odoo_field_type == 'datetime':
        try:
            from datetime import datetime
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return False
    
    elif odoo_field_type == 'many2one':
        # If it's a numeric ID, return it as integer
        try:
            return int(float(value))
        except (ValueError, TypeError):
            # Otherwise, return as is (could be a string name to be resolved)
            return value
    
    # For other types, return as is
    return value