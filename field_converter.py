#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Field Converter Module

This module provides utilities for converting field values between Python and Odoo formats,
inspired by Odoo's ir.fields.converter class.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class FieldConverter:
    """Class for converting field values between Python and Odoo formats."""

    def __init__(self, model_discovery):
        """Initialize the field converter.

        Args:
            model_discovery: ModelDiscovery instance for accessing Odoo models and fields
        """
        self.model_discovery = model_discovery
        self._field_cache = {}

    def _get_field_info(self, model_name: str, field_name: str) -> Dict[str, Any]:
        """Get field information for a specific field.

        Args:
            model_name: Name of the model
            field_name: Name of the field

        Returns:
            Dictionary with field information
        """
        # Check if we have the model fields in cache
        if model_name not in self._field_cache:
            try:
                # Use a simpler approach to get fields to avoid the parameter error
                fields = self.model_discovery.get_model_fields(model_name)
                self._field_cache[model_name] = fields
            except Exception as e:
                logger.error(f"Error getting field info for {model_name}.{field_name}: {str(e)}")
                # Return a default field info to avoid further errors
                return {
                    'string': field_name,
                    'ttype': 'char',
                    'relation': False,
                    'required': False,
                    'readonly': False,
                    'store': True
                }

        # Return the field info if available
        if model_name in self._field_cache and field_name in self._field_cache[model_name]:
            return self._field_cache[model_name][field_name]

        # If field not found in cache, try to get it directly
        try:
            # Get all fields for the model using the model_discovery adapter
            fields = self.model_discovery.get_model_fields(model_name)
            if fields and field_name in fields:
                self._field_cache[model_name] = fields
                return fields[field_name]

            # If we couldn't get the field info, return a default field info
            return {
                'string': field_name,
                'ttype': 'char',
                'relation': False,
                'required': False,
                'readonly': False,
                'store': True
            }
        except Exception as e:
            logger.error(f"Error getting direct field info for {model_name}.{field_name}: {str(e)}")

        # Return a default field info as fallback
        return {
            'string': field_name,
            'ttype': 'char',
            'relation': False,
            'required': False,
            'readonly': False,
            'store': True
        }

    def convert_to_odoo(self, model_name: str, field_name: str, value: Any) -> Any:
        """Convert a Python value to an Odoo-compatible value.

        Args:
            model_name: Name of the model
            field_name: Name of the field
            value: Python value to convert

        Returns:
            Odoo-compatible value
        """
        if value is None:
            return False

        # Get field information
        field_info = self._get_field_info(model_name, field_name)
        if not field_info:
            return value

        field_type = field_info.get('ttype')

        # Handle different field types
        if field_type == 'many2one':
            # Handle many2one fields - convert name to ID if needed
            if isinstance(value, str) and value:
                relation = field_info.get('relation')
                if relation:
                    # Check if it's a JSON string representation of [id, name]
                    if value.startswith('[') and value.endswith(']'):
                        try:
                            value_list = json.loads(value)
                            if isinstance(value_list, list) and len(value_list) >= 1:
                                return value_list[0]
                        except json.JSONDecodeError:
                            pass

                    # Try to extract ID from string like "[id, name]"
                    import re
                    id_match = re.search(r'\[(\d+)', value)
                    if id_match:
                        return int(id_match.group(1))

                    # Search for the record by name
                    try:
                        records = self.model_discovery.models_proxy.execute_kw(
                            self.model_discovery.db,
                            self.model_discovery.uid,
                            self.model_discovery.password,
                            relation, 'search',
                            [[('name', '=', value)]]
                        )
                        if records:
                            return records[0]
                    except Exception as e:
                        logger.error(f"Error searching for {relation} with name '{value}': {str(e)}")
            elif isinstance(value, int):
                return value
            elif isinstance(value, list) and len(value) >= 1:
                return value[0]
        elif field_type == 'many2many':
            # Handle many2many fields
            if isinstance(value, str):
                # Check if it's a JSON string
                if value.startswith('[') and value.endswith(']'):
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        pass

                # Try comma-separated values
                return [(6, 0, [int(v.strip()) for v in value.split(',') if v.strip().isdigit()])]
            elif isinstance(value, list):
                if all(isinstance(v, int) for v in value):
                    return [(6, 0, value)]
                elif all(isinstance(v, list) and len(v) >= 1 for v in value):
                    return [(6, 0, [v[0] for v in value])]
        elif field_type == 'one2many':
            # Handle one2many fields
            if isinstance(value, str):
                # Check if it's a JSON string
                if value.startswith('[') and value.endswith(']'):
                    try:
                        ids = json.loads(value)
                        if isinstance(ids, list) and all(isinstance(id, int) for id in ids):
                            return [(6, 0, ids)]
                    except json.JSONDecodeError:
                        pass
            elif isinstance(value, list):
                if all(isinstance(v, int) for v in value):
                    return [(6, 0, value)]
                elif all(isinstance(v, dict) for v in value):
                    # Handle list of dictionaries (create/update commands)
                    commands = []
                    for v in value:
                        if 'id' in v:
                            # Update existing record
                            record_id = v.pop('id')
                            commands.append((1, record_id, v))
                        else:
                            # Create new record
                            commands.append((0, 0, v))
                    return commands
        elif field_type == 'boolean':
            # Convert string to boolean
            if isinstance(value, str):
                return value.lower() in ('true', 'yes', '1', 't', 'y')
            return bool(value)
        elif field_type == 'integer':
            # Convert string to integer
            if isinstance(value, str):
                try:
                    return int(value)
                except ValueError:
                    return 0
            return int(value) if value else 0
        elif field_type == 'float':
            # Convert string to float
            if isinstance(value, str):
                try:
                    return float(value)
                except ValueError:
                    return 0.0
            return float(value) if value else 0.0
        elif field_type == 'date':
            # Ensure proper date format
            if isinstance(value, str):
                try:
                    dt = datetime.strptime(value, '%Y-%m-%d')
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    try:
                        # Try other common formats
                        for fmt in ['%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y']:
                            try:
                                dt = datetime.strptime(value, fmt)
                                return dt.strftime('%Y-%m-%d')
                            except ValueError:
                                continue
                    except Exception:
                        pass
            return value
        elif field_type == 'datetime':
            # Ensure proper datetime format
            if isinstance(value, str):
                try:
                    dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        # Try other common formats
                        for fmt in ['%Y-%m-%dT%H:%M:%S', '%d/%m/%Y %H:%M:%S', '%m/%d/%Y %H:%M:%S']:
                            try:
                                dt = datetime.strptime(value, fmt)
                                return dt.strftime('%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                continue
                    except Exception:
                        pass
            return value
        elif field_type == 'selection':
            # Handle selection fields
            return value

        # Default: return the value as is
        return value

    def convert_from_odoo(self, model_name: str, field_name: str, value: Any) -> Any:
        """Convert an Odoo value to a Python-friendly value.

        Args:
            model_name: Name of the model
            field_name: Name of the field
            value: Odoo value to convert

        Returns:
            Python-friendly value
        """
        if value is False or value is None:
            return None

        # Get field information
        field_info = self._get_field_info(model_name, field_name)
        if not field_info:
            return value

        field_type = field_info.get('ttype')

        # Handle different field types
        if field_type == 'many2one':
            # Convert [id, name] to name for display
            if isinstance(value, list) and len(value) >= 2:
                return value[1]
            return value
        elif field_type == 'many2many':
            # Convert list of IDs to list of names if possible
            if isinstance(value, list) and all(isinstance(v, int) for v in value):
                relation = field_info.get('relation')
                if relation:
                    try:
                        records = self.model_discovery.models_proxy.execute_kw(
                            self.model_discovery.db,
                            self.model_discovery.uid,
                            self.model_discovery.password,
                            relation, 'read',
                            [value],
                            {'fields': ['name']}
                        )
                        return [r['name'] for r in records]
                    except Exception as e:
                        logger.error(f"Error reading {relation} records: {str(e)}")
            return value
        elif field_type == 'boolean':
            return bool(value)
        elif field_type == 'integer':
            return int(value) if value else 0
        elif field_type == 'float':
            return float(value) if value else 0.0
        elif field_type in ('date', 'datetime') and value:
            # Ensure proper date format for display
            return str(value)
        elif field_type == 'selection':
            # For selection fields, return the value as is
            return value

        # Default: return the value as is
        return value

    def validate_record(self, model_name: str, record_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """Validate a record against model constraints.

        Args:
            model_name: Name of the model
            record_data: Record data to validate

        Returns:
            Tuple of (is_valid, error_message, validated_data)
        """
        try:
            # Get model fields using fields_get which is more reliable
            model_fields = {}
            try:
                # Try to get fields from cache first
                if model_name in self._field_cache and self._field_cache[model_name]:
                    model_fields = self._field_cache[model_name]
                else:
                    # Get fields using the model_discovery adapter
                    model_fields = self.model_discovery.get_model_fields(model_name)

                    # Cache the fields
                    if model_fields:
                        self._field_cache[model_name] = model_fields
            except Exception as e:
                logger.error(f"Error getting fields for model {model_name}: {str(e)}")
                # Use model_discovery as fallback
                model_fields = self.model_discovery.get_model_fields(model_name)

            if not model_fields:
                return False, f"Could not get fields for model: {model_name}", {}

            # Check required fields
            missing_fields = []
            for field_name, field_info in model_fields.items():
                if field_info.get('required', False) and field_name not in record_data and field_name != 'id':
                    # Skip computed fields that are required
                    if not field_info.get('readonly', False):
                        missing_fields.append(field_name)

            if missing_fields:
                return False, f"Missing required fields: {', '.join(missing_fields)}", {}

            # Validate and convert field values
            validated_data = {}
            invalid_fields = []

            for field_name, value in record_data.items():
                if field_name not in model_fields:
                    # Skip fields that don't exist in the model
                    continue

                # Skip readonly fields for updates
                if model_fields[field_name].get('readonly', False) and field_name != 'id':
                    continue

                try:
                    # Convert the value to Odoo format
                    converted_value = self.convert_to_odoo(model_name, field_name, value)
                    validated_data[field_name] = converted_value
                except Exception as e:
                    logger.error(f"Error converting {field_name}: {str(e)}")
                    invalid_fields.append(f"{field_name} ({str(e)})")

            if invalid_fields:
                return False, f"Invalid field values: {', '.join(invalid_fields)}", {}

            return True, "", validated_data
        except Exception as e:
            logger.error(f"Error validating record: {str(e)}")
            return False, str(e), {}
