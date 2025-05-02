#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Import nodes for the Export/Import agent flow.
"""

import os
import logging
import xmlrpc.client
from typing import Dict, List, Any, Tuple, Optional

from langchain.schema import HumanMessage, AIMessage

from src.agents.export_import.state import AgentState
from src.agents.export_import.utils.csv_handler import import_from_csv, apply_field_mapping
from src.agents.export_import.utils.field_mapper import (
    suggest_field_mapping,
    validate_field_mapping,
    get_field_type_compatibility,
    convert_value_for_odoo
)

logger = logging.getLogger(__name__)


def select_import_file(state: AgentState, message: Optional[str] = None) -> AgentState:
    """
    Select the CSV file to import.

    Args:
        state: The current agent state
        message: Optional message from the user

    Returns:
        Updated agent state
    """
    # If import path is already set, move to next step
    if state.import_state.import_path and os.path.exists(state.import_state.import_path):
        state.current_step = "select_model"
        return state

    # If message contains a file path, use it
    if message and ("file" in message.lower() or "path" in message.lower() or "csv" in message.lower()):
        import re
        path_match = re.search(r"(?:file|path|csv)[:\s]\s*['\"]?([^'\"]+\.csv)['\"]?", message)

        if path_match:
            file_path = path_match.group(1)

            # Check if file exists
            if os.path.exists(file_path):
                state.import_state.import_path = file_path
                state.current_step = "select_model"
                return state
            else:
                state.import_state.error = f"File not found: {file_path}"
                # Stay on the same step to try again

    # If no file is selected, keep the current step
    state.current_step = "select_import_file"
    return state


def select_import_model(state: AgentState, message: Optional[str] = None) -> AgentState:
    """
    Select the Odoo model to import into.

    Args:
        state: The current agent state
        message: Optional message from the user

    Returns:
        Updated agent state
    """
    # If no import file is selected, go back
    if not state.import_state.import_path or not os.path.exists(state.import_state.import_path):
        state.current_step = "select_import_file"
        return state

    # If model is already selected, move to next step
    if state.import_state.model_name:
        state.current_step = "map_fields"
        return state

    # If message contains a model name, use it
    if message and "model" in message.lower():
        import re
        model_match = re.search(r"model[:\s]\s*['\"]?([a-zA-Z0-9_.]+)['\"]?", message)

        if model_match:
            state.import_state.model_name = model_match.group(1)
            state.current_step = "map_fields"
            return state

    # Connect to Odoo to get available models
    try:
        common = xmlrpc.client.ServerProxy(f"{state.odoo_url}/xmlrpc/2/common")
        uid = common.authenticate(state.odoo_db, state.odoo_username, state.odoo_password, {})

        if not uid:
            state.import_state.error = "Authentication failed"
            state.current_step = "error"
            return state

        models = xmlrpc.client.ServerProxy(f"{state.odoo_url}/xmlrpc/2/object")

        # Get available models
        model_ids = models.execute_kw(
            state.odoo_db, uid, state.odoo_password,
            'ir.model', 'search',
            [[('transient', '=', False)]],
            {'order': 'model'}
        )

        model_data = models.execute_kw(
            state.odoo_db, uid, state.odoo_password,
            'ir.model', 'read',
            [model_ids[:100]],  # Limit to 100 models
            {'fields': ['name', 'model']}
        )

        # Store available models in state for reference
        state.history.append(f"Available models: {', '.join([m['model'] for m in model_data[:10]])}")

        # Try to guess model from CSV filename
        import_filename = os.path.basename(state.import_state.import_path)
        filename_base = os.path.splitext(import_filename)[0].lower().replace('_', '.')

        for model in model_data:
            model_name = model['model'].lower()
            if model_name in filename_base or filename_base in model_name:
                state.import_state.model_name = model['model']
                state.current_step = "map_fields"
                return state

        # If message contains a hint about the model, try to find a match
        if message:
            message_lower = message.lower()
            for model in model_data:
                if model['model'].lower() in message_lower or model['name'].lower() in message_lower:
                    state.import_state.model_name = model['model']
                    state.current_step = "map_fields"
                    return state

        # If no model is selected, keep the current step
        state.current_step = "select_import_model"

    except Exception as e:
        logger.error(f"Error in select_import_model: {str(e)}")
        state.import_state.error = f"Error selecting model: {str(e)}"
        state.current_step = "error"

    return state


def map_fields(state: AgentState, message: Optional[str] = None) -> AgentState:
    """
    Map CSV fields to Odoo model fields.

    Args:
        state: The current agent state
        message: Optional message from the user

    Returns:
        Updated agent state
    """
    # If no import file or model is selected, go back
    if not state.import_state.import_path or not os.path.exists(state.import_state.import_path):
        state.current_step = "select_import_file"
        return state

    if not state.import_state.model_name:
        state.current_step = "select_import_model"
        return state

    # If field mapping is already set, move to next step
    if state.import_state.field_mapping:
        state.current_step = "validate_mapping"
        return state

    # Connect to Odoo to get model fields
    try:
        common = xmlrpc.client.ServerProxy(f"{state.odoo_url}/xmlrpc/2/common")
        uid = common.authenticate(state.odoo_db, state.odoo_username, state.odoo_password, {})

        if not uid:
            state.import_state.error = "Authentication failed"
            state.current_step = "error"
            return state

        models = xmlrpc.client.ServerProxy(f"{state.odoo_url}/xmlrpc/2/object")

        # Get model fields
        odoo_fields = models.execute_kw(
            state.odoo_db, uid, state.odoo_password,
            state.import_state.model_name, 'fields_get',
            [],
            {'attributes': ['string', 'help', 'type', 'required']}
        )

        # Get CSV fields
        from src.agents.export_import.utils.csv_handler import get_csv_fields
        csv_fields = get_csv_fields(state.import_state.import_path)

        # If message contains field mapping, parse it
        if message and "mapping" in message.lower():
            import re
            import json

            # Try to find JSON mapping in the message
            mapping_match = re.search(r"\{[^}]+\}", message)
            if mapping_match:
                try:
                    mapping_json = mapping_match.group(0)
                    mapping = json.loads(mapping_json)

                    # Validate mapping
                    is_valid, errors = validate_field_mapping(mapping, odoo_fields)

                    if is_valid:
                        state.import_state.field_mapping = mapping
                        state.current_step = "validate_mapping"
                        return state
                    else:
                        state.import_state.error = f"Invalid field mapping: {', '.join(errors)}"
                        # Stay on the same step to try again
                except json.JSONDecodeError:
                    state.import_state.error = "Invalid JSON format for field mapping"
                    # Stay on the same step to try again

            # Try to find mapping in format "csv_field:odoo_field, csv_field:odoo_field"
            mapping_list_match = re.search(r"mapping[:\s]\s*([^}]+)", message)
            if mapping_list_match:
                mapping_str = mapping_list_match.group(1)
                mapping_pairs = [pair.strip() for pair in mapping_str.split(',')]

                mapping = {}
                for pair in mapping_pairs:
                    if ':' in pair:
                        csv_field, odoo_field = [p.strip() for p in pair.split(':', 1)]
                        mapping[csv_field] = odoo_field

                if mapping:
                    # Validate mapping
                    is_valid, errors = validate_field_mapping(mapping, odoo_fields)

                    if is_valid:
                        state.import_state.field_mapping = mapping
                        state.current_step = "validate_mapping"
                        return state
                    else:
                        state.import_state.error = f"Invalid field mapping: {', '.join(errors)}"
                        # Stay on the same step to try again

        # If no mapping is provided, suggest one
        suggested_mapping = suggest_field_mapping(csv_fields, odoo_fields)

        if suggested_mapping:
            state.import_state.field_mapping = suggested_mapping
            state.current_step = "validate_mapping"
            return state

        # If no mapping is suggested, keep the current step
        state.current_step = "map_fields"

    except Exception as e:
        logger.error(f"Error in map_fields: {str(e)}")
        state.import_state.error = f"Error mapping fields: {str(e)}"
        state.current_step = "error"

    return state


def validate_mapping(state: AgentState, message: Optional[str] = None) -> AgentState:
    """
    Validate the field mapping.

    Args:
        state: The current agent state
        message: Optional message from the user

    Returns:
        Updated agent state
    """
    # If no import file, model, or mapping is selected, go back
    if not state.import_state.import_path or not os.path.exists(state.import_state.import_path):
        state.current_step = "select_import_file"
        return state

    if not state.import_state.model_name:
        state.current_step = "select_import_model"
        return state

    # If no field mapping is provided, try to create one automatically
    if not state.import_state.field_mapping:
        try:
            # Connect to Odoo to get model fields
            common = xmlrpc.client.ServerProxy(f"{state.odoo_url}/xmlrpc/2/common")
            uid = common.authenticate(state.odoo_db, state.odoo_username, state.odoo_password, {})

            if uid:
                models = xmlrpc.client.ServerProxy(f"{state.odoo_url}/xmlrpc/2/object")

                # Get model fields
                odoo_fields = models.execute_kw(
                    state.odoo_db, uid, state.odoo_password,
                    state.import_state.model_name, 'fields_get',
                    [],
                    {'attributes': ['string', 'help', 'type', 'required']}
                )

                # Get CSV fields
                from src.agents.export_import.utils.csv_handler import get_csv_fields
                csv_fields = get_csv_fields(state.import_state.import_path)

                # Suggest field mapping
                suggested_mapping = suggest_field_mapping(csv_fields, odoo_fields)

                if suggested_mapping:
                    state.import_state.field_mapping = suggested_mapping
                else:
                    # If no mapping could be suggested, go back to map_fields
                    state.current_step = "map_fields"
                    return state
            else:
                # If authentication fails, go back to map_fields
                state.current_step = "map_fields"
                return state
        except Exception as e:
            logger.error(f"Error creating field mapping: {str(e)}")
            state.current_step = "map_fields"
            return state

    # Connect to Odoo to validate mapping
    try:
        common = xmlrpc.client.ServerProxy(f"{state.odoo_url}/xmlrpc/2/common")
        uid = common.authenticate(state.odoo_db, state.odoo_username, state.odoo_password, {})

        if not uid:
            state.import_state.error = "Authentication failed"
            state.current_step = "error"
            return state

        models = xmlrpc.client.ServerProxy(f"{state.odoo_url}/xmlrpc/2/object")

        # Get model fields
        odoo_fields = models.execute_kw(
            state.odoo_db, uid, state.odoo_password,
            state.import_state.model_name, 'fields_get',
            [],
            {'attributes': ['string', 'help', 'type', 'required']}
        )

        # Validate mapping
        is_valid, errors = validate_field_mapping(state.import_state.field_mapping, odoo_fields)

        if not is_valid:
            state.import_state.error = f"Invalid field mapping: {', '.join(errors)}"
            state.current_step = "map_fields"
            return state

        # Get sample records from CSV
        from src.agents.export_import.utils.csv_handler import import_from_csv
        csv_records = import_from_csv(state.import_state.import_path)[:5]  # Get first 5 records

        # Check field type compatibility
        compatibility = get_field_type_compatibility(
            csv_records,
            odoo_fields,
            state.import_state.field_mapping
        )

        # Check for incompatible fields
        incompatible_fields = [
            f"{csv_field} -> {info['odoo_field']}: {info['reason']}"
            for csv_field, info in compatibility.items()
            if not info['compatible'] and info['reason']
        ]

        if incompatible_fields:
            state.import_state.error = f"Incompatible field types: {', '.join(incompatible_fields)}"
            state.current_step = "map_fields"
            return state

        # If message contains import options, parse them
        if message:
            message_lower = message.lower()

            if "create" in message_lower:
                if "don't create" in message_lower or "do not create" in message_lower:
                    state.import_state.create_if_not_exists = False
                else:
                    state.import_state.create_if_not_exists = True

            if "update" in message_lower:
                if "don't update" in message_lower or "do not update" in message_lower:
                    state.import_state.update_if_exists = False
                else:
                    state.import_state.update_if_exists = True

        # Load all records from CSV
        state.import_state.records_to_import = import_from_csv(state.import_state.import_path)
        state.import_state.total_records = len(state.import_state.records_to_import)

        # Move to next step
        state.current_step = "execute_import"

    except Exception as e:
        logger.error(f"Error in validate_mapping: {str(e)}")
        state.import_state.error = f"Error validating mapping: {str(e)}"
        state.current_step = "error"

    return state


def execute_import(state: AgentState, message: Optional[str] = None) -> AgentState:
    """
    Execute the import operation.

    Args:
        state: The current agent state
        message: Optional message from the user

    Returns:
        Updated agent state
    """
    # If no import file, model, mapping, or records are selected, go back
    if not state.import_state.import_path or not os.path.exists(state.import_state.import_path):
        state.current_step = "select_import_file"
        return state

    if not state.import_state.model_name:
        state.current_step = "select_import_model"
        return state

    if not state.import_state.field_mapping:
        state.current_step = "map_fields"
        return state

    if not state.import_state.records_to_import:
        state.current_step = "validate_mapping"
        return state

    # Connect to Odoo to execute import
    try:
        common = xmlrpc.client.ServerProxy(f"{state.odoo_url}/xmlrpc/2/common")
        uid = common.authenticate(state.odoo_db, state.odoo_username, state.odoo_password, {})

        if not uid:
            state.import_state.error = "Authentication failed"
            state.current_step = "error"
            return state

        models = xmlrpc.client.ServerProxy(f"{state.odoo_url}/xmlrpc/2/object")

        # Get model fields
        odoo_fields = models.execute_kw(
            state.odoo_db, uid, state.odoo_password,
            state.import_state.model_name, 'fields_get',
            [],
            {'attributes': ['string', 'help', 'type', 'required']}
        )

        # Apply field mapping to records
        mapped_records = []

        for record in state.import_state.records_to_import:
            mapped_record = {}

            for csv_field, odoo_field in state.import_state.field_mapping.items():
                if csv_field in record and odoo_field in odoo_fields:
                    # Convert value to appropriate type for Odoo
                    value = record[csv_field]
                    odoo_field_type = odoo_fields[odoo_field]['type']

                    converted_value = convert_value_for_odoo(value, odoo_field_type)
                    mapped_record[odoo_field] = converted_value

            mapped_records.append(mapped_record)

        # Process records
        created_count = 0
        updated_count = 0
        failed_count = 0
        validation_errors = []

        for record in mapped_records:
            try:
                # Check if record exists (if it has an ID or a unique field)
                record_id = None

                if 'id' in record and record['id']:
                    # Check if record with this ID exists
                    record_exists = models.execute_kw(
                        state.odoo_db, uid, state.odoo_password,
                        state.import_state.model_name, 'search',
                        [[('id', '=', record['id'])]]
                    )

                    if record_exists:
                        record_id = record['id']
                        # Remove ID from record to avoid error
                        record_data = {k: v for k, v in record.items() if k != 'id'}
                    else:
                        record_id = None
                        record_data = record
                else:
                    # Try to find record by other unique fields
                    # Common unique fields by model
                    unique_fields = {
                        'res.partner': ['email', 'vat'],
                        'product.product': ['default_code', 'barcode'],
                        'product.template': ['default_code', 'barcode'],
                    }

                    model_unique_fields = unique_fields.get(state.import_state.model_name, [])

                    for field in model_unique_fields:
                        if field in record and record[field]:
                            record_exists = models.execute_kw(
                                state.odoo_db, uid, state.odoo_password,
                                state.import_state.model_name, 'search',
                                [[
                                    (field, '=', record[field]),
                                    ('active', 'in', [True, False])  # Include archived records
                                ]]
                            )

                            if record_exists:
                                record_id = record_exists[0]
                                break

                    record_data = record

                # Create or update record
                if record_id and state.import_state.update_if_exists:
                    # Update existing record
                    result = models.execute_kw(
                        state.odoo_db, uid, state.odoo_password,
                        state.import_state.model_name, 'write',
                        [[record_id], record_data]
                    )

                    if result:
                        updated_count += 1
                    else:
                        failed_count += 1
                        validation_errors.append({
                            'record': record,
                            'error': 'Failed to update record'
                        })

                elif not record_id and state.import_state.create_if_not_exists:
                    # Create new record
                    new_id = models.execute_kw(
                        state.odoo_db, uid, state.odoo_password,
                        state.import_state.model_name, 'create',
                        [record_data]
                    )

                    if new_id:
                        created_count += 1
                    else:
                        failed_count += 1
                        validation_errors.append({
                            'record': record,
                            'error': 'Failed to create record'
                        })

                else:
                    # Skip record
                    failed_count += 1
                    validation_errors.append({
                        'record': record,
                        'error': 'Record skipped due to import options'
                    })

            except Exception as e:
                failed_count += 1
                validation_errors.append({
                    'record': record,
                    'error': str(e)
                })

        # Update state with results
        state.import_state.imported_records = created_count
        state.import_state.updated_records = updated_count
        state.import_state.failed_records = failed_count
        state.import_state.validation_errors = validation_errors
        state.import_state.status = "completed"
        state.current_step = "complete"

    except Exception as e:
        logger.error(f"Error in execute_import: {str(e)}")
        state.import_state.error = f"Error executing import: {str(e)}"
        state.current_step = "error"

    return state