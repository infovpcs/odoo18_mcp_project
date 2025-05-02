#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Export nodes for the Export/Import agent flow.
"""

import os
import logging
import xmlrpc.client
from typing import Dict, List, Any, Tuple, Optional

from langchain.schema import HumanMessage, AIMessage
from src.agents.export_import.state import AgentState
from src.agents.export_import.utils.csv_handler import export_to_csv

logger = logging.getLogger(__name__)


def select_model(state: AgentState, message: Optional[str] = None) -> AgentState:
    """
    Select the Odoo model to export.

    Args:
        state: The current agent state
        message: Optional message from the user

    Returns:
        Updated agent state
    """
    # If model is already selected, move to next step
    if state.export_state.model_name:
        state.current_step = "select_fields"
        return state

    # If message contains a model name, use it
    if message and "model_name" in message:
        import re
        model_match = re.search(r"model_name\s*[=:]\s*['\"]?([a-zA-Z0-9_.]+)['\"]?", message)
        if model_match:
            state.export_state.model_name = model_match.group(1)
            state.current_step = "select_fields"
            return state

    # Connect to Odoo to get available models
    try:
        common = xmlrpc.client.ServerProxy(f"{state.odoo_url}/xmlrpc/2/common")
        uid = common.authenticate(state.odoo_db, state.odoo_username, state.odoo_password, {})

        if not uid:
            state.export_state.error = "Authentication failed"
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

        # If message contains a hint about the model, try to find a match
        if message:
            message_lower = message.lower()
            for model in model_data:
                if model['model'].lower() in message_lower or model['name'].lower() in message_lower:
                    state.export_state.model_name = model['model']
                    state.current_step = "select_fields"
                    return state

        # If no model is selected, keep the current step
        state.current_step = "select_model"

    except Exception as e:
        logger.error(f"Error in select_model: {str(e)}")
        state.export_state.error = f"Error selecting model: {str(e)}"
        state.current_step = "error"

    return state


def select_fields(state: AgentState, message: Optional[str] = None) -> AgentState:
    """
    Select fields to export from the Odoo model.

    Args:
        state: The current agent state
        message: Optional message from the user

    Returns:
        Updated agent state
    """
    # If fields are already selected, move to next step
    if state.export_state.selected_fields:
        state.current_step = "set_filter"
        return state

    # If no model is selected, go back to select_model
    if not state.export_state.model_name:
        state.current_step = "select_model"
        return state

    # Connect to Odoo to get available fields
    try:
        common = xmlrpc.client.ServerProxy(f"{state.odoo_url}/xmlrpc/2/common")
        uid = common.authenticate(state.odoo_db, state.odoo_username, state.odoo_password, {})

        if not uid:
            state.export_state.error = "Authentication failed"
            state.current_step = "error"
            return state

        models = xmlrpc.client.ServerProxy(f"{state.odoo_url}/xmlrpc/2/object")

        # Get available fields
        fields = models.execute_kw(
            state.odoo_db, uid, state.odoo_password,
            state.export_state.model_name, 'fields_get',
            [],
            {'attributes': ['string', 'help', 'type']}
        )

        # Store available fields in state for reference
        field_names = list(fields.keys())
        state.history.append(f"Available fields for {state.export_state.model_name}: {', '.join(field_names[:10])}")

        # If message contains field selections, parse them
        if message and ("fields" in message.lower() or "select" in message.lower()):
            import re

            # Try to find field names in the message
            # Look for patterns like "fields: field1, field2, field3" or "select field1, field2, field3"
            field_match = re.search(r"(?:fields|select)[:\s]\s*([a-zA-Z0-9_, ]+)", message.lower())

            if field_match:
                field_str = field_match.group(1)
                selected_fields = [f.strip() for f in field_str.split(',')]

                # Validate fields
                valid_fields = [f for f in selected_fields if f in fields]

                if valid_fields:
                    state.export_state.selected_fields = valid_fields
                    state.current_step = "set_filter"
                    return state

            # If "all fields" or similar is mentioned, select all fields
            if "all fields" in message.lower() or "every field" in message.lower():
                state.export_state.selected_fields = field_names
                state.current_step = "set_filter"
                return state

        # If no fields are selected, keep the current step
        state.current_step = "select_fields"

    except Exception as e:
        logger.error(f"Error in select_fields: {str(e)}")
        state.export_state.error = f"Error selecting fields: {str(e)}"
        state.current_step = "error"

    return state


def set_filter(state: AgentState, message: Optional[str] = None) -> AgentState:
    """
    Set filter criteria for the export.

    Args:
        state: The current agent state
        message: Optional message from the user

    Returns:
        Updated agent state
    """
    # If no model or fields are selected, go back
    if not state.export_state.model_name:
        state.current_step = "select_model"
        return state

    if not state.export_state.selected_fields:
        state.current_step = "select_fields"
        return state

    # Parse filter from message
    if message:
        message_lower = message.lower()

        # Check for "all records" or similar
        if "all records" in message_lower or "no filter" in message_lower:
            state.export_state.filter_domain = []
            state.current_step = "execute_export"
            return state

        # Check for limit
        import re
        limit_match = re.search(r"limit\s*[=:]\s*(\d+)", message_lower)
        if limit_match:
            state.export_state.limit = int(limit_match.group(1))

        # Check for simple domain filters
        # This is a simplified parser for basic domain filters
        # Format: field_name operator value
        # Example: "name = Test" or "customer_rank > 0"
        domain = []

        # Common operators
        operators = {
            "=": "=",
            "==": "=",
            "!=": "!=",
            "<>": "!=",
            ">": ">",
            "<": "<",
            ">=": ">=",
            "<=": "<=",
            "like": "like",
            "ilike": "ilike",
            "contains": "ilike",
            "in": "in",
            "not in": "not in"
        }

        # Look for patterns like "field operator value"
        for op_text, op_symbol in operators.items():
            if op_text in message_lower:
                parts = message.split(op_text, 1)
                if len(parts) == 2:
                    field = parts[0].strip()
                    value = parts[1].strip()

                    # Handle quoted values
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]

                    # Convert value to appropriate type
                    if value.isdigit():
                        value = int(value)
                    elif value.lower() == "true":
                        value = True
                    elif value.lower() == "false":
                        value = False

                    # For 'like' and 'ilike' operators, add wildcards if not present
                    if op_symbol in ["like", "ilike"] and "%" not in value:
                        value = f"%{value}%"

                    domain.append((field, op_symbol, value))

        if domain:
            state.export_state.filter_domain = domain

        # Move to next step
        state.current_step = "execute_export"
        return state

    # If no filter is set, keep the current step
    state.current_step = "set_filter"
    return state


def execute_export(state: AgentState, message: Optional[str] = None) -> AgentState:
    """
    Execute the export operation.

    Args:
        state: The current agent state
        message: Optional message from the user

    Returns:
        Updated agent state
    """
    # If no model or fields are selected, go back
    if not state.export_state.model_name:
        state.current_step = "select_model"
        return state

    # If no fields are selected, use default fields or all fields
    if not state.export_state.selected_fields:
        try:
            # Connect to Odoo to get fields
            common = xmlrpc.client.ServerProxy(f"{state.odoo_url}/xmlrpc/2/common")
            uid = common.authenticate(state.odoo_db, state.odoo_username, state.odoo_password, {})

            if uid:
                models = xmlrpc.client.ServerProxy(f"{state.odoo_url}/xmlrpc/2/object")

                # Get fields
                fields = models.execute_kw(
                    state.odoo_db, uid, state.odoo_password,
                    state.export_state.model_name, 'fields_get',
                    [],
                    {'attributes': ['string', 'help', 'type']}
                )

                # Use default fields based on model
                if state.export_state.model_name == 'res.partner':
                    state.export_state.selected_fields = ['id', 'name', 'email', 'phone', 'street', 'city', 'country_id']
                elif state.export_state.model_name == 'product.product':
                    state.export_state.selected_fields = ['id', 'name', 'default_code', 'list_price', 'standard_price', 'type', 'categ_id']
                else:
                    # Use all fields (limited to first 20)
                    state.export_state.selected_fields = list(fields.keys())[:20]
            else:
                # If authentication fails, go back to select fields
                state.current_step = "select_fields"
                return state
        except Exception as e:
            logger.error(f"Error getting fields: {str(e)}")
            state.current_step = "select_fields"
            return state

    # Set export path if not already set
    if not state.export_state.export_path:
        model_name_safe = state.export_state.model_name.replace('.', '_')
        state.export_state.export_path = f"exports/{model_name_safe}_export.csv"

    # If message contains a custom export path, use it
    if message and "export_path" in message:
        import re
        path_match = re.search(r"export_path\s*[=:]\s*['\"]?([^'\"]+)['\"]?", message)
        if path_match:
            state.export_state.export_path = path_match.group(1)

    # Connect to Odoo and export records
    try:
        common = xmlrpc.client.ServerProxy(f"{state.odoo_url}/xmlrpc/2/common")
        uid = common.authenticate(state.odoo_db, state.odoo_username, state.odoo_password, {})

        if not uid:
            state.export_state.error = "Authentication failed"
            state.current_step = "error"
            return state

        models = xmlrpc.client.ServerProxy(f"{state.odoo_url}/xmlrpc/2/object")

        # Get total count of records matching the filter
        record_count = models.execute_kw(
            state.odoo_db, uid, state.odoo_password,
            state.export_state.model_name, 'search_count',
            [state.export_state.filter_domain]
        )

        state.export_state.total_records = record_count

        # Get records
        records = models.execute_kw(
            state.odoo_db, uid, state.odoo_password,
            state.export_state.model_name, 'search_read',
            [state.export_state.filter_domain],
            {
                'fields': state.export_state.selected_fields,
                'limit': state.export_state.limit,
                'offset': state.export_state.offset
            }
        )

        state.export_state.records = records
        state.export_state.exported_records = len(records)

        # Create exports directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(state.export_state.export_path)), exist_ok=True)

        # Export to CSV
        export_path = export_to_csv(
            records=records,
            export_path=state.export_state.export_path,
            fields=state.export_state.selected_fields
        )

        state.export_state.export_path = export_path
        state.export_state.status = "completed"
        state.current_step = "complete"

    except Exception as e:
        logger.error(f"Error in execute_export: {str(e)}")
        state.export_state.error = f"Error executing export: {str(e)}"
        state.current_step = "error"

    return state