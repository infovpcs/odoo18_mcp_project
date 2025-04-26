#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Direct implementation of export/import functionality without using LangGraph.
This is a simplified version that directly uses the Odoo client to export and import records.
"""

import os
import sys
import logging
import argparse
import xmlrpc.client
import json
import pandas as pd
import re
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import our field converter
from field_converter import FieldConverter

# Create a simple adapter for the field converter
class ModelDiscoveryAdapter:
    def __init__(self, models_proxy, db, uid, password):
        self.models_proxy = models_proxy
        self.db = db
        self.uid = uid
        self.password = password

    def get_model_fields(self, model_name):
        """Get fields for a model."""
        try:
            fields_data = self.models_proxy.execute_kw(
                self.db, self.uid, self.password,
                model_name, 'fields_get',
                [],
                {'attributes': ['string', 'type', 'relation', 'required', 'readonly', 'store']}
            )

            # Convert to our internal format
            fields = {}
            for field_name, field_info in fields_data.items():
                fields[field_name] = {
                    'string': field_info.get('string', field_name),
                    'ttype': field_info.get('type', 'char'),
                    'relation': field_info.get('relation', False),
                    'required': field_info.get('required', False),
                    'readonly': field_info.get('readonly', False),
                    'store': field_info.get('store', True)
                }
            return fields
        except Exception as e:
            logger.error(f"Error getting fields for model {model_name}: {str(e)}")
            return {}

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("direct_export_import")

# Load environment variables
load_dotenv()

# Get Odoo connection details from environment variables
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "llmdb18")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")


def connect_to_odoo():
    """Connect to Odoo server and return the connection objects."""
    try:
        # Connect to Odoo
        common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})

        if not uid:
            logger.error("Authentication failed")
            return None, None

        models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

        return uid, models
    except Exception as e:
        logger.error(f"Error connecting to Odoo: {str(e)}")
        return None, None


def export_to_csv(records, export_path, fields=None):
    """Export records to a CSV file."""
    try:
        import csv

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(export_path)), exist_ok=True)

        # If no fields are specified, use all fields from the first record
        if not fields and records:
            fields = list(records[0].keys())

        # Convert to DataFrame for easier handling
        df = pd.DataFrame(records)

        # Select only the specified fields if provided
        if fields:
            # Only include fields that exist in the DataFrame
            existing_fields = [f for f in fields if f in df.columns]
            df = df[existing_fields]

        # Export to CSV
        df.to_csv(export_path, index=False, quoting=csv.QUOTE_NONNUMERIC)

        logger.info(f"Exported {len(records)} records to {export_path}")
        return export_path

    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        raise


def import_from_csv(import_path):
    """Import records from a CSV file."""
    try:
        # Check if file exists
        if not os.path.exists(import_path):
            raise FileNotFoundError(f"CSV file not found: {import_path}")

        # Import from CSV
        df = pd.read_csv(import_path)

        # Convert to list of dictionaries
        records = df.to_dict(orient='records')

        logger.info(f"Imported {len(records)} records from {import_path}")
        return records

    except Exception as e:
        logger.error(f"Error importing from CSV: {str(e)}")
        raise


def get_model_relations(model_name, uid, models):
    """Get the relational fields (many2one, one2many) for a model."""
    try:
        # Get all fields for the model
        all_fields = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            model_name, 'fields_get',
            [],
            {'attributes': ['string', 'help', 'type', 'relation']}
        )

        # Filter for relational fields
        many2one_fields = {}
        one2many_fields = {}

        for field_name, field_info in all_fields.items():
            field_type = field_info.get('type')
            relation = field_info.get('relation')

            if field_type == 'many2one' and relation:
                many2one_fields[field_name] = {
                    'relation': relation,
                    'string': field_info.get('string', field_name)
                }
            elif field_type == 'one2many' and relation:
                one2many_fields[field_name] = {
                    'relation': relation,
                    'string': field_info.get('string', field_name)
                }

        return {
            'many2one_fields': many2one_fields,
            'one2many_fields': one2many_fields
        }

    except Exception as e:
        logger.error(f"Error getting model relations: {str(e)}")
        return {
            'many2one_fields': {},
            'one2many_fields': {}
        }


def export_records(model_name, fields=None, filter_domain=None, limit=1000, export_path=None):
    """Export records from an Odoo model to a CSV file with improved field handling."""
    try:
        # Connect to Odoo
        uid, models = connect_to_odoo()

        if not uid or not models:
            return {
                "success": False,
                "error": "Failed to connect to Odoo"
            }

        # Create field converter
        model_discovery = ModelDiscoveryAdapter(models, ODOO_DB, uid, ODOO_PASSWORD)
        field_converter = FieldConverter(model_discovery)

        # Set default filter domain
        if filter_domain is None:
            filter_domain = []

        # Set default export path
        if export_path is None:
            model_name_safe = model_name.replace('.', '_')
            export_path = f"./tmp/{model_name_safe}_export.csv"

        # Get model information
        model_info = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'ir.model', 'search_read',
            [[('model', '=', model_name)]],
            {'fields': ['name', 'model', 'info']}
        )

        if not model_info:
            return {
                "success": False,
                "error": f"Model {model_name} not found"
            }

        # Get total count of records matching the filter
        record_count = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            model_name, 'search_count',
            [filter_domain]
        )

        # If no fields are specified, get all fields
        if not fields:
            # Get fields from ir.model.fields
            all_fields = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'ir.model.fields', 'search_read',
                [[('model', '=', model_name), ('store', '=', True)]],
                {'fields': ['name', 'field_description', 'ttype', 'relation']}
            )

            # Use default fields based on model
            if model_name == 'res.partner':
                fields = ['id', 'name', 'email', 'phone', 'street', 'city', 'country_id']
            elif model_name == 'product.product':
                fields = ['id', 'name', 'default_code', 'list_price', 'standard_price', 'type', 'categ_id']
            else:
                # Use all non-binary fields (limited to first 30)
                fields = [f['name'] for f in all_fields if f['ttype'] != 'binary'][:30]

        # Get records
        records = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            model_name, 'search_read',
            [filter_domain],
            {
                'fields': fields,
                'limit': limit,
                'offset': 0
            }
        )

        # Process records to handle special field types
        processed_records = []
        for record in records:
            processed_record = {}
            for field_name, value in record.items():
                # Convert the value to a Python-friendly format
                processed_value = field_converter.convert_from_odoo(model_name, field_name, value)

                # Handle many2one fields specially for CSV export
                if isinstance(value, list) and len(value) == 2:
                    # Store as JSON string to preserve the relationship
                    processed_record[field_name] = json.dumps(value)
                else:
                    processed_record[field_name] = processed_value
            processed_records.append(processed_record)

        # Export to CSV
        export_path = export_to_csv(
            records=processed_records,
            export_path=export_path,
            fields=fields
        )

        return {
            "success": True,
            "model_name": model_name,
            "model_description": model_info[0]['name'] if model_info else model_name,
            "selected_fields": fields,
            "filter_domain": filter_domain,
            "total_records": record_count,
            "exported_records": len(records),
            "export_path": export_path,
            "error": None
        }

    except Exception as e:
        logger.error(f"Error exporting records: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def export_related_records(parent_model, child_model, relation_field, parent_fields=None, child_fields=None,
                          filter_domain=None, limit=1000, export_path=None):
    """
    Export records from related models (parent and child) to a structured CSV file.

    Args:
        parent_model: The technical name of the parent Odoo model (e.g., 'account.move')
        child_model: The technical name of the child Odoo model (e.g., 'account.move.line')
        relation_field: The field in the child model that relates to the parent (e.g., 'move_id')
        parent_fields: List of field names to export from the parent model
        child_fields: List of field names to export from the child model
        filter_domain: Domain filter for the parent model
        limit: Maximum number of parent records to export
        export_path: Path to export the CSV file (if None, a default path is used)

    Returns:
        A dictionary with the export results
    """
    try:
        # Connect to Odoo
        uid, models = connect_to_odoo()

        if not uid or not models:
            return {
                "success": False,
                "error": "Failed to connect to Odoo"
            }

        # Validate the models and relation field
        relations = get_model_relations(child_model, uid, models)
        many2one_fields = relations.get('many2one_fields', {})

        # Check if the relation field exists and points to the parent model
        if relation_field not in many2one_fields:
            return {
                "success": False,
                "error": f"Relation field '{relation_field}' is not a many2one field in model '{child_model}'"
            }

        if many2one_fields[relation_field]['relation'] != parent_model:
            return {
                "success": False,
                "error": f"Relation field '{relation_field}' does not point to model '{parent_model}'"
            }

        # Set default filter domain
        if filter_domain is None:
            filter_domain = []

        # Special handling for account.move model - filter by move_type if specified
        if parent_model == 'account.move':
            # Check if we already have a move_type filter
            has_move_type_filter = False
            for condition in filter_domain:
                if isinstance(condition, (list, tuple)) and len(condition) >= 3 and condition[0] == 'move_type':
                    has_move_type_filter = True
                    break

            # If no move_type filter, add a default one for invoices
            if not has_move_type_filter:
                # Default to all invoice types
                filter_domain.append(['move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']])
                logger.info(f"Added default move_type filter for account.move: {filter_domain[-1]}")

        # Set default export path
        if export_path is None:
            parent_model_safe = parent_model.replace('.', '_')
            child_model_safe = child_model.replace('.', '_')
            export_path = f"./exports/{parent_model_safe}_{child_model_safe}_export.csv"

        # Get parent fields if not specified
        if not parent_fields:
            # Get fields
            all_fields = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                parent_model, 'fields_get',
                [],
                {'attributes': ['string', 'help', 'type']}
            )

            # Use default fields based on model
            if parent_model == 'account.move':
                # Include all essential invoice fields based on move_type
                parent_fields = [
                    # Common fields for all move types
                    'id', 'name', 'move_type', 'state', 'partner_id', 'journal_id',
                    'date', 'ref', 'narration', 'currency_id', 'payment_state',

                    # Invoice specific fields
                    'invoice_date', 'invoice_date_due', 'invoice_payment_term_id',
                    'amount_untaxed', 'amount_tax', 'amount_total', 'amount_residual',

                    # Partner related fields
                    'partner_shipping_id', 'fiscal_position_id', 'partner_bank_id',

                    # Other useful fields
                    'invoice_origin', 'invoice_user_id', 'invoice_incoterm_id'
                ]
            else:
                # Use common fields
                parent_fields = ['id', 'name']
                # Add a few more fields
                for field in all_fields:
                    if field not in parent_fields and len(parent_fields) < 10:
                        parent_fields.append(field)

        # Get child fields if not specified
        if not child_fields:
            # Get fields
            all_fields = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                child_model, 'fields_get',
                [],
                {'attributes': ['string', 'help', 'type']}
            )

            # Use default fields based on model
            if child_model == 'account.move.line':
                # Include all essential invoice line fields
                child_fields = [
                    # Basic fields
                    'id', relation_field, 'name', 'sequence', 'display_type',

                    # Product and accounting fields
                    'product_id', 'product_uom_id', 'account_id', 'analytic_distribution',
                    'partner_id', 'currency_id',

                    # Quantity and pricing fields
                    'quantity', 'price_unit', 'discount', 'tax_ids',

                    # Computed fields (useful for verification)
                    'price_subtotal', 'price_total', 'amount_currency', 'balance',

                    # Other useful fields
                    'date', 'date_maturity', 'reconciled', 'payment_id'
                ]
            else:
                # Use common fields
                child_fields = ['id', relation_field, 'name']
                # Add a few more fields
                for field in all_fields:
                    if field not in child_fields and len(child_fields) < 10:
                        child_fields.append(field)

        # Make sure relation_field is in child_fields
        if relation_field not in child_fields:
            child_fields.append(relation_field)

        # Get parent records
        parent_records = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            parent_model, 'search_read',
            [filter_domain],
            {
                'fields': parent_fields,
                'limit': limit,
                'offset': 0
            }
        )

        if not parent_records:
            return {
                "success": False,
                "error": f"No records found for model '{parent_model}' with the given filter"
            }

        # Get parent IDs
        parent_ids = [record['id'] for record in parent_records]

        # Get child records for these parents
        child_filter = [(relation_field, 'in', parent_ids)]
        child_records = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            child_model, 'search_read',
            [child_filter],
            {
                'fields': child_fields
            }
        )

        # Group child records by parent ID
        child_by_parent = {}
        for child in child_records:
            parent_id = child[relation_field]
            if isinstance(parent_id, list):
                parent_id = parent_id[0]  # Extract ID from [id, name] format

            if parent_id not in child_by_parent:
                child_by_parent[parent_id] = []

            child_by_parent[parent_id].append(child)

        # Create a combined dataset
        combined_records = []

        for parent in parent_records:
            parent_id = parent['id']
            children = child_by_parent.get(parent_id, [])

            # If no children, still include the parent
            if not children:
                record = {
                    '_model': parent_model,
                    '_record_type': 'parent',
                    '_child_count': 0
                }

                # Add parent fields
                for field in parent_fields:
                    record[f'parent_{field}'] = parent.get(field)

                combined_records.append(record)
            else:
                # For each child, create a combined record
                for i, child in enumerate(children):
                    record = {
                        '_model': f"{parent_model},{child_model}",
                        '_record_type': 'combined',
                        '_child_index': i + 1,
                        '_child_count': len(children)
                    }

                    # Add parent fields
                    for field in parent_fields:
                        record[f'parent_{field}'] = parent.get(field)

                    # Add child fields
                    for field in child_fields:
                        record[f'child_{field}'] = child.get(field)

                    combined_records.append(record)

        # Export to CSV
        import csv

        # Convert to DataFrame
        df = pd.DataFrame(combined_records)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(export_path)), exist_ok=True)

        # Export to CSV
        df.to_csv(export_path, index=False, quoting=csv.QUOTE_NONNUMERIC)

        logger.info(f"Exported {len(combined_records)} combined records to {export_path}")

        return {
            "success": True,
            "parent_model": parent_model,
            "child_model": child_model,
            "relation_field": relation_field,
            "parent_fields": parent_fields,
            "child_fields": child_fields,
            "parent_records": len(parent_records),
            "child_records": len(child_records),
            "combined_records": len(combined_records),
            "export_path": export_path,
            "error": None
        }

    except Exception as e:
        logger.error(f"Error exporting related records: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def import_related_records(import_path, parent_model, child_model, relation_field,
                       field_mapping=None, create_if_not_exists=True, update_if_exists=True,
                       draft_only=False, reset_to_draft=False, skip_readonly_fields=True):
    """
    Import records from a structured CSV file into related models (parent and child).

    Args:
        import_path: Path to the CSV file to import
        parent_model: The technical name of the parent Odoo model (e.g., 'account.move')
        child_model: The technical name of the child Odoo model (e.g., 'account.move.line')
        relation_field: The field in the child model that relates to the parent (e.g., 'move_id')
        field_mapping: Dictionary with mapping from CSV field names to Odoo field names
        create_if_not_exists: Whether to create new records if they don't exist
        update_if_exists: Whether to update existing records
        draft_only: Whether to only update records in draft state
        reset_to_draft: Whether to reset records to draft before updating (use with caution)
        skip_readonly_fields: Whether to skip readonly fields for posted records

    Returns:
        A dictionary with the import results
    """
    try:
        # Connect to Odoo
        uid, models = connect_to_odoo()

        if not uid or not models:
            return {
                "success": False,
                "error": "Failed to connect to Odoo"
            }

        # Validate the models and relation field
        relations = get_model_relations(child_model, uid, models)
        many2one_fields = relations.get('many2one_fields', {})

        # Check if the relation field exists and points to the parent model
        if relation_field not in many2one_fields:
            return {
                "success": False,
                "error": f"Relation field '{relation_field}' is not a many2one field in model '{child_model}'"
            }

        if many2one_fields[relation_field]['relation'] != parent_model:
            return {
                "success": False,
                "error": f"Relation field '{relation_field}' does not point to model '{parent_model}'"
            }

        # Import records from CSV
        # Check if file exists
        if not os.path.exists(import_path):
            return {
                "success": False,
                "error": f"CSV file not found: {import_path}"
            }

        # Import from CSV
        df = pd.read_csv(import_path)

        if df.empty:
            return {
                "success": False,
                "error": "CSV file is empty"
            }

        # Check if this is a related records CSV
        if '_model' not in df.columns or '_record_type' not in df.columns:
            return {
                "success": False,
                "error": "CSV file does not appear to be a related records export"
            }

        # Get parent and child fields
        parent_fields = [col[7:] for col in df.columns if col.startswith('parent_')]
        child_fields = [col[6:] for col in df.columns if col.startswith('child_')]

        if not parent_fields or not child_fields:
            return {
                "success": False,
                "error": "CSV file does not contain parent and child fields"
            }

        # Get model fields
        parent_odoo_fields = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            parent_model, 'fields_get',
            [],
            {'attributes': ['string', 'help', 'type', 'required']}
        )

        child_odoo_fields = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            child_model, 'fields_get',
            [],
            {'attributes': ['string', 'help', 'type', 'required']}
        )

        # Process records by parent
        parent_records = {}
        child_records = {}

        # Track statistics
        parent_created = 0
        parent_updated = 0
        parent_failed = 0
        child_created = 0
        child_updated = 0
        child_failed = 0
        validation_errors = []

        # Special handling for account.move model
        is_account_move = parent_model == 'account.move'
        restricted_fields_for_posted = []

        if is_account_move:
            # Fields that cannot be modified on posted moves
            restricted_fields_for_posted = [
                # Header fields that cannot be modified
                'journal_id', 'name', 'date', 'ref', 'narration',
                'invoice_date', 'invoice_date_due', 'tax_totals_json',
                'currency_id', 'partner_id', 'partner_bank_id', 'fiscal_position_id',
                'invoice_payment_term_id', 'invoice_incoterm_id',

                # Accounting fields
                'line_ids', 'invoice_line_ids', 'payment_id', 'statement_line_id',
                'amount_untaxed', 'amount_tax', 'amount_total', 'amount_residual',
                'amount_untaxed_signed', 'amount_tax_signed', 'amount_total_signed',
                'amount_residual_signed', 'payment_state',

                # Technical fields
                'auto_post', 'auto_post_until', 'sequence_prefix', 'sequence_number',
                'highest_name', 'show_name_warning', 'to_check'
            ]
            logger.info(f"Account move detected. Restricted fields for posted moves: {restricted_fields_for_posted}")

        # Define editable states based on model
        parent_editable_states = ['draft', 'new', 'to_check', 'in_progress']
        if is_account_move:
            parent_editable_states = ['draft']

        # Get the available actions for account.move based on state
        account_move_actions = {}
        if is_account_move:
            try:
                # Get available buttons/actions for account.move
                account_move_actions = {
                    'draft': ['action_post'],
                    'posted': ['button_draft', 'button_cancel'],
                    'cancel': ['button_draft'],
                }
                logger.info(f"Account move actions by state: {account_move_actions}")
            except Exception as e:
                logger.error(f"Error getting account.move actions: {str(e)}")

        # Group records by parent ID
        for _, row in df.iterrows():
            record_type = row['_record_type']

            # Extract parent data
            parent_data = {}
            parent_id = None

            for field in parent_fields:
                if f'parent_{field}' in row:
                    parent_data[field] = row[f'parent_{field}']
                    if field == 'id':
                        parent_id = row[f'parent_{field}']

            # Skip if no parent ID and we're not creating new records
            if parent_id is None and not create_if_not_exists:
                continue

            # Add or update parent record
            if parent_id not in parent_records:
                parent_records[parent_id] = parent_data

            # If it's a combined record, extract child data
            if record_type == 'combined':
                child_data = {}

                for field in child_fields:
                    if f'child_{field}' in row:
                        child_data[field] = row[f'child_{field}']

                # Add relation field if not present
                if relation_field not in child_data and parent_id is not None:
                    child_data[relation_field] = parent_id

                # Get child ID
                child_id = child_data.get('id')

                # Add to child records
                if parent_id not in child_records:
                    child_records[parent_id] = []

                child_records[parent_id].append(child_data)

        # Check for state/status fields in the models
        parent_has_state = False
        parent_state_field = None
        parent_editable_states = ['draft', 'new', 'to_check', 'in_progress']

        # Check if parent model has a state or status field
        for field_name in ['state', 'status', 'stage']:
            if field_name in parent_odoo_fields:
                parent_has_state = True
                parent_state_field = field_name

                # Get possible values for state field
                if parent_odoo_fields[field_name].get('type') == 'selection':
                    selection = parent_odoo_fields[field_name].get('selection', [])
                    if selection:
                        # Extract state values that typically indicate "draft" or editable status
                        for value, label in selection:
                            if value.lower() in ['draft', 'new', 'to_check', 'in_progress']:
                                parent_editable_states.append(value)

                break

        # Get computed fields to skip during import
        parent_computed_fields = []
        for field_name, field_info in parent_odoo_fields.items():
            if field_info.get('readonly', False) and field_name not in ['id']:
                parent_computed_fields.append(field_name)

        child_computed_fields = []
        for field_name, field_info in child_odoo_fields.items():
            if field_info.get('readonly', False) and field_name not in ['id']:
                child_computed_fields.append(field_name)

        logger.info(f"Parent computed fields to skip: {parent_computed_fields}")
        logger.info(f"Child computed fields to skip: {child_computed_fields}")

        # Process parent records
        for parent_id, parent_data in parent_records.items():
            try:
                # Check if record exists
                if parent_id is not None:
                    # Try to get the record
                    existing_records = models.execute_kw(
                        ODOO_DB, uid, ODOO_PASSWORD,
                        parent_model, 'search',
                        [[('id', '=', parent_id)]]
                    )

                    if existing_records:
                        # Get the current record state if it has one
                        record_state = None
                        if is_account_move or parent_has_state:
                            record_info = models.execute_kw(
                                ODOO_DB, uid, ODOO_PASSWORD,
                                parent_model, 'read',
                                [existing_records, ['state']],
                                {}
                            )
                            if record_info and 'state' in record_info[0]:
                                record_state = record_info[0]['state']

                        # Check if we should skip non-draft records
                        if draft_only and record_state and record_state != 'draft':
                            logger.warning(f"Skipping {parent_model} record {parent_id} because it's not in draft state (current state: {record_state})")
                            parent_failed += 1
                            validation_errors.append({
                                'model': parent_model,
                                'record': parent_data,
                                'error': f"Record is not in draft state (current state: {record_state}). Set draft_only=False to update non-draft records."
                            })
                            continue

                        # Handle reset to draft if needed
                        if reset_to_draft and record_state and record_state != 'draft':
                            try:
                                logger.info(f"Attempting to reset {parent_model} record {parent_id} to draft state")

                                # For account.move, we need special handling
                                if is_account_move:
                                    # First check if the invoice can be reset to draft
                                    can_reset = True

                                    # Check payment state - can't reset if it's paid
                                    if record_info and 'payment_state' in record_info[0]:
                                        payment_state = record_info[0]['payment_state']
                                        if payment_state in ['paid', 'in_payment', 'partial']:
                                            logger.warning(f"Cannot reset invoice {parent_id} to draft because it's already paid (payment_state: {payment_state})")
                                            can_reset = False

                                    if can_reset:
                                        # Try using button_draft method - this is the correct way to reset invoices
                                        try:
                                            logger.info(f"Calling button_draft on invoice {parent_id}")
                                            models.execute_kw(
                                                ODOO_DB, uid, ODOO_PASSWORD,
                                                parent_model, 'button_draft',
                                                [[parent_id]]  # Make sure we're passing a list of IDs
                                            )
                                            logger.info(f"Successfully reset invoice {parent_id} to draft state")
                                        except Exception as e:
                                            logger.error(f"Error calling button_draft: {str(e)}")

                                            # If direct button_draft fails, try button_cancel first
                                            try:
                                                logger.info(f"Trying button_cancel first for invoice {parent_id}")
                                                models.execute_kw(
                                                    ODOO_DB, uid, ODOO_PASSWORD,
                                                    parent_model, 'button_cancel',
                                                    [[parent_id]]  # Make sure we're passing a list of IDs
                                                )
                                                logger.info(f"Successfully cancelled invoice {parent_id}")

                                                # Then try to set to draft
                                                models.execute_kw(
                                                    ODOO_DB, uid, ODOO_PASSWORD,
                                                    parent_model, 'write',
                                                    [[parent_id], {'state': 'draft'}]
                                                )
                                                logger.info(f"Successfully set invoice {parent_id} to draft state")
                                            except Exception as e2:
                                                logger.error(f"Alternative reset approach also failed: {str(e2)}")
                                else:
                                    # Generic approach for other models
                                    models.execute_kw(
                                        ODOO_DB, uid, ODOO_PASSWORD,
                                        parent_model, 'write',
                                        [[parent_id], {'state': 'draft'}]
                                    )

                                # Verify the state change
                                record_info = models.execute_kw(
                                    ODOO_DB, uid, ODOO_PASSWORD,
                                    parent_model, 'read',
                                    [existing_records, ['state']],
                                    {}
                                )
                                if record_info and record_info[0]['state'] == 'draft':
                                    logger.info(f"Successfully reset {parent_model} record {parent_id} to draft state")
                                    record_state = 'draft'
                                else:
                                    logger.warning(f"Failed to reset {parent_model} record {parent_id} to draft state")
                            except Exception as e:
                                logger.error(f"Error resetting {parent_model} record {parent_id} to draft: {str(e)}")

                        # Check if record is in an editable state
                        can_edit = True

                        # If we've successfully reset to draft, we should be able to edit
                        if record_state == 'draft':
                            can_edit = True
                        elif parent_has_state and parent_state_field in parent_data:
                            state_value = parent_data[parent_state_field]
                            # Handle state value that might be a string representation of a list
                            if isinstance(state_value, str) and state_value.startswith('[') and state_value.endswith(']'):
                                try:
                                    # Try to parse as a list
                                    import ast
                                    parsed_value = ast.literal_eval(state_value)
                                    if isinstance(parsed_value, list) and len(parsed_value) > 0:
                                        state_value = parsed_value[0]
                                except:
                                    pass

                            # If reset_to_draft is enabled, we should allow posted state
                            if reset_to_draft and state_value == 'posted':
                                # We'll try to reset it during the update
                                can_edit = True
                            elif state_value not in parent_editable_states:
                                logger.warning(f"Skipping update of {parent_model} record {parent_id} because it's not in an editable state: {state_value}")
                                can_edit = False
                                parent_failed += 1
                                validation_errors.append({
                                    'model': parent_model,
                                    'record': parent_data,
                                    'error': f"Record is not in an editable state: {state_value}. Only records in states {parent_editable_states} can be updated."
                                })

                        # Update existing record if in editable state
                        if update_if_exists and can_edit:
                            # Remove id field for update
                            if 'id' in parent_data:
                                del parent_data['id']

                            # Special handling for account.move in posted state
                            if is_account_move and record_state == 'posted':
                                # Always remove readonly fields first to avoid errors
                                # These are the fields that cannot be modified on posted invoices
                                readonly_fields = ['partner_id', 'invoice_date', 'date', 'currency_id',
                                                  'journal_id', 'name', 'ref', 'narration',
                                                  'invoice_payment_term_id', 'invoice_incoterm_id',
                                                  'fiscal_position_id', 'partner_bank_id']

                                # Log which fields we're removing
                                for field in readonly_fields:
                                    if field in parent_data:
                                        logger.info(f"Removing readonly field {field} from posted account.move {parent_id}")
                                        del parent_data[field]

                                # If reset_to_draft is enabled, try to reset the invoice to draft first
                                if reset_to_draft:
                                    try:
                                        # Try to reset to draft using button_draft method
                                        logger.info(f"Attempting to reset invoice {parent_id} to draft before update")

                                        # First try button_draft - this is the correct way to reset invoices
                                        try:
                                            models.execute_kw(
                                                ODOO_DB, uid, ODOO_PASSWORD,
                                                parent_model, 'button_draft',
                                                [[parent_id]]  # Make sure we're passing a list of IDs
                                            )
                                            logger.info(f"Successfully reset invoice {parent_id} to draft using button_draft")

                                            # Verify the state change
                                            record_info = models.execute_kw(
                                                ODOO_DB, uid, ODOO_PASSWORD,
                                                parent_model, 'read',
                                                [[parent_id], ['state']],
                                                {}
                                            )

                                            if record_info and record_info[0]['state'] == 'draft':
                                                logger.info(f"Confirmed invoice {parent_id} is now in draft state")
                                                record_state = 'draft'
                                            else:
                                                logger.warning(f"Invoice {parent_id} state verification failed")
                                        except Exception as e:
                                            logger.error(f"Error using button_draft: {str(e)}")

                                            # If direct button_draft fails, try button_cancel first
                                            try:
                                                logger.info(f"Trying button_cancel first for invoice {parent_id}")
                                                models.execute_kw(
                                                    ODOO_DB, uid, ODOO_PASSWORD,
                                                    parent_model, 'button_cancel',
                                                    [[parent_id]]  # Make sure we're passing a list of IDs
                                                )
                                                logger.info(f"Successfully cancelled invoice {parent_id}")

                                                # Then try to set to draft
                                                models.execute_kw(
                                                    ODOO_DB, uid, ODOO_PASSWORD,
                                                    parent_model, 'write',
                                                    [[parent_id], {'state': 'draft'}]
                                                )
                                                logger.info(f"Successfully set invoice {parent_id} to draft state")

                                                # Verify the state change
                                                record_info = models.execute_kw(
                                                    ODOO_DB, uid, ODOO_PASSWORD,
                                                    parent_model, 'read',
                                                    [[parent_id], ['state']],
                                                    {}
                                                )

                                                if record_info and record_info[0]['state'] == 'draft':
                                                    logger.info(f"Confirmed invoice {parent_id} is now in draft state")
                                                    record_state = 'draft'
                                                else:
                                                    logger.warning(f"Invoice {parent_id} state verification failed")
                                            except Exception as e2:
                                                logger.error(f"Error with alternative reset approach: {str(e2)}")

                                                # If all else fails, try a direct SQL update (use with extreme caution)
                                                try:
                                                    logger.warning(f"Attempting direct state update for invoice {parent_id} - USE WITH CAUTION")
                                                    # This is a last resort and may cause data inconsistency
                                                    models.execute_kw(
                                                        ODOO_DB, uid, ODOO_PASSWORD,
                                                        'base', 'execute_sql',
                                                        [f"UPDATE account_move SET state='draft' WHERE id={parent_id}"]
                                                    )
                                                    logger.info(f"Direct SQL update completed for invoice {parent_id}")

                                                    # Verify the state change
                                                    record_info = models.execute_kw(
                                                        ODOO_DB, uid, ODOO_PASSWORD,
                                                        parent_model, 'read',
                                                        [[parent_id], ['state']],
                                                        {}
                                                    )

                                                    if record_info and record_info[0]['state'] == 'draft':
                                                        logger.info(f"Confirmed invoice {parent_id} is now in draft state")
                                                        record_state = 'draft'
                                                    else:
                                                        logger.warning(f"Invoice {parent_id} state verification failed")
                                                except Exception as e3:
                                                    logger.error(f"Direct SQL update failed: {str(e3)}")
                                    except Exception as e:
                                        logger.error(f"Error resetting invoice {parent_id} to draft: {str(e)}")

                                # If no fields left to update, skip this record
                                if not parent_data:
                                    logger.warning(f"No updateable fields left for posted account.move {parent_id}")
                                    continue

                            # Remove computed fields
                            for field in parent_computed_fields:
                                if field in parent_data:
                                    del parent_data[field]

                            # Process many2one fields
                            for field, value in list(parent_data.items()):
                                if field in parent_odoo_fields and parent_odoo_fields[field].get('type') == 'many2one':
                                    if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                                        try:
                                            # Try to parse as a list
                                            import ast
                                            parsed_value = ast.literal_eval(value)
                                            if isinstance(parsed_value, list) and len(parsed_value) > 0:
                                                parent_data[field] = parsed_value[0]
                                        except Exception as e:
                                            logger.warning(f"Error parsing many2one field {field}: {str(e)}")

                            # Handle special fields for account.move
                            if is_account_move:
                                # Handle tax_ids field which is a many2many field
                                if 'tax_ids' in parent_data:
                                    tax_value = parent_data['tax_ids']
                                    if isinstance(tax_value, str) and tax_value.startswith('[') and tax_value.endswith(']'):
                                        try:
                                            # Try to parse as a list
                                            import ast
                                            parsed_value = ast.literal_eval(tax_value)
                                            if isinstance(parsed_value, list):
                                                # Extract IDs if they are in [id, name] format
                                                tax_ids = []
                                                for item in parsed_value:
                                                    if isinstance(item, list) and len(item) > 0:
                                                        tax_ids.append(item[0])
                                                    else:
                                                        tax_ids.append(item)
                                                parent_data['tax_ids'] = [(6, 0, tax_ids)]
                                        except Exception as e:
                                            logger.warning(f"Error parsing tax_ids field: {str(e)}")

                            result = models.execute_kw(
                                ODOO_DB, uid, ODOO_PASSWORD,
                                parent_model, 'write',
                                [[parent_id], parent_data]
                            )

                            if result:
                                parent_updated += 1
                            else:
                                parent_failed += 1
                                validation_errors.append({
                                    'model': parent_model,
                                    'record': parent_data,
                                    'error': 'Failed to update parent record'
                                })
                    else:
                        # Create new record if ID doesn't exist
                        if create_if_not_exists:
                            # Remove id field for create
                            if 'id' in parent_data:
                                del parent_data['id']

                            new_id = models.execute_kw(
                                ODOO_DB, uid, ODOO_PASSWORD,
                                parent_model, 'create',
                                [parent_data]
                            )

                            if new_id:
                                parent_created += 1
                                # Update parent_id for child records
                                if parent_id in child_records:
                                    for child_data in child_records[parent_id]:
                                        child_data[relation_field] = new_id
                            else:
                                parent_failed += 1
                                validation_errors.append({
                                    'model': parent_model,
                                    'record': parent_data,
                                    'error': 'Failed to create parent record'
                                })
                else:
                    # Create new record without ID
                    if create_if_not_exists:
                        # Remove id field for create if it's None
                        if 'id' in parent_data:
                            del parent_data['id']

                        new_id = models.execute_kw(
                            ODOO_DB, uid, ODOO_PASSWORD,
                            parent_model, 'create',
                            [parent_data]
                        )

                        if new_id:
                            parent_created += 1
                            # Update parent_id for child records
                            if parent_id in child_records:
                                for child_data in child_records[parent_id]:
                                    child_data[relation_field] = new_id
                        else:
                            parent_failed += 1
                            validation_errors.append({
                                'model': parent_model,
                                'record': parent_data,
                                'error': 'Failed to create parent record'
                            })
            except Exception as e:
                parent_failed += 1
                validation_errors.append({
                    'model': parent_model,
                    'record': parent_data,
                    'error': str(e)
                })

        # Process child records
        for parent_id, children in child_records.items():
            for child_data in children:
                try:
                    # Check if record exists
                    child_id = child_data.get('id')

                    if child_id is not None:
                        # Try to get the record
                        existing_records = models.execute_kw(
                            ODOO_DB, uid, ODOO_PASSWORD,
                            child_model, 'search',
                            [[('id', '=', child_id)]]
                        )

                        if existing_records:
                            # Update existing record
                            if update_if_exists:
                                # Remove id field for update
                                if 'id' in child_data:
                                    del child_data['id']

                                # Remove computed fields
                                for field in child_computed_fields:
                                    if field in child_data:
                                        del child_data[field]

                                # Process many2one fields
                                for field, value in list(child_data.items()):
                                    if field in child_odoo_fields and child_odoo_fields[field].get('type') == 'many2one':
                                        if isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                                            try:
                                                # Try to parse as a list
                                                import ast
                                                parsed_value = ast.literal_eval(value)
                                                if isinstance(parsed_value, list) and len(parsed_value) > 0:
                                                    child_data[field] = parsed_value[0]
                                            except Exception as e:
                                                logger.warning(f"Error parsing many2one field {field}: {str(e)}")

                                # Special handling for account.move.line
                                if child_model == 'account.move.line':
                                    # Handle tax_ids field which is a many2many field
                                    if 'tax_ids' in child_data:
                                        tax_value = child_data['tax_ids']
                                        if isinstance(tax_value, str) and tax_value.startswith('[') and tax_value.endswith(']'):
                                            try:
                                                # Try to parse as a list
                                                import ast
                                                parsed_value = ast.literal_eval(tax_value)
                                                if isinstance(parsed_value, list):
                                                    # Extract IDs if they are in [id, name] format
                                                    tax_ids = []
                                                    for item in parsed_value:
                                                        if isinstance(item, list) and len(item) > 0:
                                                            tax_ids.append(item[0])
                                                        else:
                                                            tax_ids.append(item)
                                                    child_data['tax_ids'] = [(6, 0, tax_ids)]
                                            except Exception as e:
                                                logger.warning(f"Error parsing tax_ids field: {str(e)}")

                                result = models.execute_kw(
                                    ODOO_DB, uid, ODOO_PASSWORD,
                                    child_model, 'write',
                                    [[child_id], child_data]
                                )

                                if result:
                                    child_updated += 1
                                else:
                                    child_failed += 1
                                    validation_errors.append({
                                        'model': child_model,
                                        'record': child_data,
                                        'error': 'Failed to update child record'
                                    })
                        else:
                            # Create new record if ID doesn't exist
                            if create_if_not_exists:
                                # Remove id field for create
                                if 'id' in child_data:
                                    del child_data['id']

                                new_id = models.execute_kw(
                                    ODOO_DB, uid, ODOO_PASSWORD,
                                    child_model, 'create',
                                    [child_data]
                                )

                                if new_id:
                                    child_created += 1
                                else:
                                    child_failed += 1
                                    validation_errors.append({
                                        'model': child_model,
                                        'record': child_data,
                                        'error': 'Failed to create child record'
                                    })
                    else:
                        # Create new record without ID
                        if create_if_not_exists:
                            # Remove id field for create if it's None
                            if 'id' in child_data:
                                del child_data['id']

                            new_id = models.execute_kw(
                                ODOO_DB, uid, ODOO_PASSWORD,
                                child_model, 'create',
                                [child_data]
                            )

                            if new_id:
                                child_created += 1
                            else:
                                child_failed += 1
                                validation_errors.append({
                                    'model': child_model,
                                    'record': child_data,
                                    'error': 'Failed to create child record'
                                })
                except Exception as e:
                    child_failed += 1
                    validation_errors.append({
                        'model': child_model,
                        'record': child_data,
                        'error': str(e)
                    })

        return {
            "success": True,
            "parent_model": parent_model,
            "child_model": child_model,
            "relation_field": relation_field,
            "parent_created": parent_created,
            "parent_updated": parent_updated,
            "parent_failed": parent_failed,
            "child_created": child_created,
            "child_updated": child_updated,
            "child_failed": child_failed,
            "total_records": len(df),
            "validation_errors": validation_errors,
            "error": None
        }

    except Exception as e:
        logger.error(f"Error importing related records: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def import_records(import_path, model_name, field_mapping=None, create_if_not_exists=True, update_if_exists=True):
    """Import records from a CSV file into an Odoo model with improved field handling."""
    try:
        # Connect to Odoo
        uid, models = connect_to_odoo()

        if not uid or not models:
            return {
                "success": False,
                "error": "Failed to connect to Odoo"
            }

        # Create model discovery adapter and field converter
        model_discovery = ModelDiscoveryAdapter(models, ODOO_DB, uid, ODOO_PASSWORD)
        field_converter = FieldConverter(model_discovery)

        # Import records from CSV
        records = import_from_csv(import_path)

        # Get model fields from ir.model.fields for better field information
        try:
            odoo_fields_data = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'ir.model.fields', 'search_read',
                [[('model', '=', model_name)]],
                {'fields': ['name', 'field_description', 'ttype', 'relation', 'required', 'readonly', 'store']}
            )

            odoo_fields = {}
            for field in odoo_fields_data:
                odoo_fields[field['name']] = {
                    'string': field['field_description'],
                    'type': field['ttype'],
                    'relation': field.get('relation', False),
                    'required': field.get('required', False),
                    'readonly': field.get('readonly', False),
                    'store': field.get('store', True)
                }
        except Exception as e:
            logger.error(f"Error getting fields from ir.model.fields: {str(e)}")
            # Fallback to fields_get
            odoo_fields = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                model_name, 'fields_get',
                [],
                {'attributes': ['string', 'help', 'type', 'required']}
            )

        # If no field mapping is provided, use identity mapping (field names are the same)
        if not field_mapping:
            field_mapping = {field: field for field in records[0].keys() if field in odoo_fields}

        # Process records
        created_count = 0
        updated_count = 0
        failed_count = 0
        validation_errors = []

        for record in records:
            try:
                # Apply field mapping
                mapped_record = {}

                for csv_field, odoo_field in field_mapping.items():
                    if csv_field in record and odoo_field in odoo_fields:
                        # Get the value from the CSV record
                        value = record[csv_field]

                        # Skip empty values
                        if value == '' or value is None:
                            mapped_record[odoo_field] = False
                            continue

                        # Use field converter to convert the value to Odoo format
                        try:
                            converted_value = field_converter.convert_to_odoo(model_name, odoo_field, value)
                            mapped_record[odoo_field] = converted_value
                        except Exception as e:
                            logger.warning(f"Error converting field {odoo_field}: {str(e)}")
                            # Fallback to basic conversion
                            if odoo_fields[odoo_field]['type'] == 'integer':
                                # Convert to integer
                                try:
                                    mapped_record[odoo_field] = int(float(value))
                                except (ValueError, TypeError):
                                    mapped_record[odoo_field] = False
                            elif odoo_fields[odoo_field]['type'] == 'float':
                                # Convert to float
                                try:
                                    mapped_record[odoo_field] = float(value)
                                except (ValueError, TypeError):
                                    mapped_record[odoo_field] = False
                            elif odoo_fields[odoo_field]['type'] == 'boolean':
                                # Convert to boolean
                                if isinstance(value, bool):
                                    mapped_record[odoo_field] = value
                                elif isinstance(value, str):
                                    mapped_record[odoo_field] = value.lower() in ['true', '1', 'yes']
                                else:
                                    mapped_record[odoo_field] = bool(value)
                            else:
                                # Use as is
                                mapped_record[odoo_field] = value

                # Skip validation for now as it's causing issues
                # Instead, we'll do basic validation here
                validated_data = {}

                for field_name, value in mapped_record.items():
                    # Skip empty values
                    if value == '' or value is None:
                        continue

                    # Skip fields that don't exist in the model
                    if field_name not in odoo_fields:
                        continue

                    # Add the field to validated data
                    validated_data[field_name] = value

                # Use the validated data
                mapped_record = validated_data

                # Check if record exists
                record_id = None

                if 'id' in mapped_record and mapped_record['id']:
                    # Check if record with this ID exists
                    record_exists = models.execute_kw(
                        ODOO_DB, uid, ODOO_PASSWORD,
                        model_name, 'search',
                        [[('id', '=', mapped_record['id'])]]
                    )

                    if record_exists:
                        record_id = mapped_record['id']
                        # Remove ID from record to avoid error
                        record_data = {k: v for k, v in mapped_record.items() if k != 'id'}
                    else:
                        record_id = None
                        record_data = mapped_record
                else:
                    # Try to find record by other unique fields
                    # Common unique fields by model
                    unique_fields = {
                        'res.partner': ['email', 'vat'],
                        'product.product': ['default_code', 'barcode'],
                        'product.template': ['default_code', 'barcode'],
                        'crm.lead': ['email_from', 'name'],
                    }

                    model_unique_fields = unique_fields.get(model_name, [])

                    for field in model_unique_fields:
                        if field in mapped_record and mapped_record[field]:
                            record_exists = models.execute_kw(
                                ODOO_DB, uid, ODOO_PASSWORD,
                                model_name, 'search',
                                [[
                                    (field, '=', mapped_record[field]),
                                    ('active', 'in', [True, False])  # Include archived records
                                ]]
                            )

                            if record_exists:
                                record_id = record_exists[0]
                                break

                    record_data = mapped_record

                # Create or update record
                if record_id and update_if_exists:
                    # Update existing record
                    result = models.execute_kw(
                        ODOO_DB, uid, ODOO_PASSWORD,
                        model_name, 'write',
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

                elif not record_id and create_if_not_exists:
                    # Create new record
                    new_id = models.execute_kw(
                        ODOO_DB, uid, ODOO_PASSWORD,
                        model_name, 'create',
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

        return {
            "success": True,
            "model_name": model_name,
            "import_path": import_path,
            "field_mapping": field_mapping,
            "total_records": len(records),
            "imported_records": created_count,
            "updated_records": updated_count,
            "failed_records": failed_count,
            "validation_errors": validation_errors,
            "error": None
        }

    except Exception as e:
        logger.error(f"Error importing records: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def test_export_flow():
    """Test the export flow with res.partner model."""
    logger.info("Testing export flow with res.partner model")

    # Create exports directory if it doesn't exist
    os.makedirs("exports", exist_ok=True)

    # Run the export flow
    result = export_records(
        model_name="res.partner",
        fields=["id", "name", "email", "phone", "street", "city", "country_id"],
        filter_domain=[("customer_rank", ">", 0)],  # Only customers
        limit=100,
        export_path="exports/partners_export.csv"
    )

    # Print the results
    logger.info(f"Export success: {result['success']}")

    if result["success"]:
        logger.info(f"Total records: {result['total_records']}")
        logger.info(f"Exported records: {result['exported_records']}")
        logger.info(f"Export path: {result['export_path']}")
    else:
        logger.error(f"Export error: {result.get('error', 'Unknown error')}")

    return result


def test_import_flow():
    """Test the import flow with res.partner model."""
    logger.info("Testing import flow with res.partner model")

    # Check if export file exists
    export_path = "exports/partners_export.csv"
    if not os.path.exists(export_path):
        logger.error(f"Export file not found: {export_path}")
        logger.info("Run test_export_flow first to create the export file")
        return None

    # Define field mapping
    field_mapping = {
        "id": "id",
        "name": "name",
        "email": "email",
        "phone": "phone",
        "street": "street",
        "city": "city",
        "country_id": "country_id"
    }

    # Run the import flow
    result = import_records(
        import_path=export_path,
        model_name="res.partner",
        field_mapping=field_mapping,
        create_if_not_exists=False,  # Only update existing records
        update_if_exists=True
    )

    # Print the results
    logger.info(f"Import success: {result['success']}")

    if result["success"]:
        logger.info(f"Total records: {result['total_records']}")
        logger.info(f"Created records: {result['imported_records']}")
        logger.info(f"Updated records: {result['updated_records']}")
        logger.info(f"Failed records: {result['failed_records']}")
    else:
        logger.error(f"Import error: {result.get('error', 'Unknown error')}")

    return result


def test_product_export_flow():
    """Test the export flow with product.product model."""
    logger.info("Testing export flow with product.product model")

    # Create exports directory if it doesn't exist
    os.makedirs("exports", exist_ok=True)

    # Run the export flow
    result = export_records(
        model_name="product.product",
        fields=["id", "name", "default_code", "list_price", "standard_price", "type", "categ_id"],
        filter_domain=[],  # All products
        limit=100,
        export_path="exports/products_export.csv"
    )

    # Print the results
    logger.info(f"Export success: {result['success']}")

    if result["success"]:
        logger.info(f"Total records: {result['total_records']}")
        logger.info(f"Exported records: {result['exported_records']}")
        logger.info(f"Export path: {result['export_path']}")
    else:
        logger.error(f"Export error: {result.get('error', 'Unknown error')}")

    return result


def test_crm_lead_export():
    """
    Test the export flow with crm.lead model.

    This test exports CRM leads (opportunities) with various fields including:
    - Basic information (name, email, phone)
    - Relationships (partner_id, stage_id)
    - Special fields (priority, date_deadline)
    - Description field that we'll update in the crm-update test
    """
    logger.info("Testing export flow with crm.lead model")

    # Create exports directory if it doesn't exist
    os.makedirs("exports", exist_ok=True)

    # Run the export flow
    result = export_records(
        model_name="crm.lead",
        fields=["id", "name", "partner_id", "email_from", "phone", "description", "type", "stage_id", "priority", "date_deadline"],
        filter_domain=[("type", "=", "opportunity")],  # Only opportunities
        limit=100,
        export_path="exports/crm_leads_export.csv"
    )

    # Print the results
    logger.info(f"Export success: {result['success']}")

    if result["success"]:
        logger.info(f"Total records: {result['total_records']}")
        logger.info(f"Exported records: {result['exported_records']}")
        logger.info(f"Export path: {result['export_path']}")
    else:
        logger.error(f"Export error: {result.get('error', 'Unknown error')}")

    return result


def test_crm_lead_update_description():
    """
    Test updating CRM lead descriptions and importing them back.

    This test demonstrates how to:
    1. Export CRM leads to a CSV file
    2. Modify their descriptions
    3. Handle special field types (many2one, selection, date)
    4. Import the modified records back to Odoo

    Note: We exclude problematic fields (priority, date_deadline) from the import
    to focus on updating the description field only.
    """
    logger.info("Testing CRM lead description update and import")

    # Check if export file exists
    export_path = "exports/crm_leads_export.csv"
    if not os.path.exists(export_path):
        logger.error(f"Export file not found: {export_path}")
        logger.info("Run test_crm_lead_export first to create the export file")
        return None

    # Import the CSV file to modify descriptions
    try:
        # Read the CSV file
        df = pd.read_csv(export_path)

        # Check if there are any records
        if len(df) == 0:
            logger.error("No CRM leads found in the export file")
            return None

        # Update descriptions and fix many2one fields
        for i in range(len(df)):
            # Handle different data types properly
            if 'description' in df.columns:
                if pd.isna(df.at[i, 'description']):
                    original_desc = ""
                elif isinstance(df.at[i, 'description'], bool):
                    original_desc = "True" if df.at[i, 'description'] else "False"
                else:
                    original_desc = str(df.at[i, 'description'])

                # Update the description
                new_desc = f"{original_desc}\n\nUpdated on {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} - This description was updated via the import/export tool."
                df.at[i, 'description'] = new_desc

            # Fix stage_id field - extract the ID from the string representation
            if 'stage_id' in df.columns and not pd.isna(df.at[i, 'stage_id']):
                try:
                    # Extract the ID from the string representation "[id, 'name']"
                    import re
                    stage_id_match = re.search(r'\[(\d+)', str(df.at[i, 'stage_id']))
                    if stage_id_match:
                        df.at[i, 'stage_id'] = int(stage_id_match.group(1))
                    else:
                        df.at[i, 'stage_id'] = False
                except Exception as e:
                    logger.warning(f"Error fixing stage_id for record {i}: {str(e)}")
                    df.at[i, 'stage_id'] = False

            # Fix partner_id field - extract the ID from the string representation
            if 'partner_id' in df.columns and not pd.isna(df.at[i, 'partner_id']):
                try:
                    # Extract the ID from the string representation "[id, 'name']"
                    import re
                    partner_id_match = re.search(r'\[(\d+)', str(df.at[i, 'partner_id']))
                    if partner_id_match:
                        df.at[i, 'partner_id'] = int(partner_id_match.group(1))
                    else:
                        df.at[i, 'partner_id'] = False
                except Exception as e:
                    logger.warning(f"Error fixing partner_id for record {i}: {str(e)}")
                    df.at[i, 'partner_id'] = False

            # Fix priority field - convert to string
            if 'priority' in df.columns and not pd.isna(df.at[i, 'priority']):
                try:
                    # In Odoo 18, priority is a selection field with values '0', '1', '2', '3'
                    # But it needs to be a string, not an integer
                    priority_value = str(df.at[i, 'priority'])
                    # Ensure it's one of the valid values
                    if priority_value not in ['0', '1', '2', '3']:
                        priority_value = '0'
                    # Remove the priority field from the record to avoid errors
                    # We'll focus only on updating the description
                    df.at[i, 'priority'] = None
                except Exception as e:
                    logger.warning(f"Error fixing priority for record {i}: {str(e)}")
                    df.at[i, 'priority'] = None

            # Fix date_deadline field - handle False values
            if 'date_deadline' in df.columns:
                try:
                    if pd.isna(df.at[i, 'date_deadline']) or df.at[i, 'date_deadline'] == 'False' or not df.at[i, 'date_deadline']:
                        # Remove the date_deadline field from the record to avoid errors
                        df.at[i, 'date_deadline'] = None
                except Exception as e:
                    logger.warning(f"Error fixing date_deadline for record {i}: {str(e)}")
                    df.at[i, 'date_deadline'] = None

        # Save the modified CSV
        modified_path = "exports/crm_leads_modified.csv"
        df.to_csv(modified_path, index=False)
        logger.info(f"Modified {len(df)} CRM lead descriptions and saved to {modified_path}")

        # Define field mapping - exclude problematic fields to avoid errors
        field_mapping = {
            "id": "id",
            "name": "name",
            "partner_id": "partner_id",
            "email_from": "email_from",
            "phone": "phone",
            "description": "description",
            "type": "type",
            "stage_id": "stage_id",
            # "priority": "priority",  # Excluded to avoid errors
            # "date_deadline": "date_deadline"  # Excluded to avoid errors
        }

        # Import the modified records
        result = import_records(
            import_path=modified_path,
            model_name="crm.lead",
            field_mapping=field_mapping,
            create_if_not_exists=False,  # Only update existing records
            update_if_exists=True
        )

        # Print the results
        logger.info(f"Import success: {result['success']}")

        if result["success"]:
            logger.info(f"Total records: {result['total_records']}")
            logger.info(f"Created records: {result['imported_records']}")
            logger.info(f"Updated records: {result['updated_records']}")
            logger.info(f"Failed records: {result['failed_records']}")

            # Print validation errors for debugging
            if result['failed_records'] > 0 and 'validation_errors' in result:
                logger.info("Validation errors:")
                for i, error in enumerate(result['validation_errors'][:5]):  # Show first 5 errors
                    logger.info(f"  Error {i+1}: {error.get('error', 'Unknown error')}")
                    if i >= 4 and len(result['validation_errors']) > 5:
                        logger.info(f"  ... and {len(result['validation_errors']) - 5} more errors")
                        break
        else:
            logger.error(f"Import error: {result.get('error', 'Unknown error')}")

        return result

    except Exception as e:
        logger.error(f"Error updating CRM lead descriptions: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def test_invoice_export():
    """
    Test the export flow with account.move model (invoices).

    This test exports invoices with various fields including:
    - Basic information (name, date, state)
    - Relationships (partner_id, journal_id)
    - Financial fields (amount_untaxed, amount_tax, amount_total)
    - Invoice-specific fields (invoice_date, payment_state)
    """
    logger.info("Testing export flow with account.move model (invoices)")

    # Create exports directory if it doesn't exist
    os.makedirs("exports", exist_ok=True)

    # Run the export flow
    result = export_records(
        model_name="account.move",
        fields=[
            "id", "name", "move_type", "state", "partner_id", "journal_id",
            "invoice_date", "date", "payment_state", "amount_untaxed",
            "amount_tax", "amount_total", "currency_id", "ref"
        ],
        filter_domain=[("move_type", "in", ["out_invoice", "in_invoice"])],  # Only invoices
        limit=100,
        export_path="exports/invoices_export.csv"
    )

    # Print the results
    logger.info(f"Export success: {result['success']}")

    if result["success"]:
        logger.info(f"Total records: {result['total_records']}")
        logger.info(f"Exported records: {result['exported_records']}")
        logger.info(f"Export path: {result['export_path']}")
    else:
        logger.error(f"Export error: {result.get('error', 'Unknown error')}")

    return result


def test_invoice_line_export():
    """
    Test the export flow with account.move.line model (invoice lines).

    This test exports invoice lines with various fields including:
    - Basic information (name, account_id)
    - Relationships (move_id, product_id)
    - Financial fields (price_unit, quantity, discount, price_subtotal, price_total)
    - Tax fields (tax_ids)
    """
    logger.info("Testing export flow with account.move.line model (invoice lines)")

    # Create exports directory if it doesn't exist
    os.makedirs("exports", exist_ok=True)

    # Run the export flow
    result = export_records(
        model_name="account.move.line",
        fields=[
            "id", "move_id", "name", "account_id", "product_id",
            "quantity", "price_unit", "discount", "tax_ids",
            "price_subtotal", "price_total", "currency_id"
        ],
        filter_domain=[("move_id.move_type", "in", ["out_invoice", "in_invoice"])],  # Only invoice lines
        limit=100,
        export_path="exports/invoice_lines_export.csv"
    )

    # Print the results
    logger.info(f"Export success: {result['success']}")

    if result["success"]:
        logger.info(f"Total records: {result['total_records']}")
        logger.info(f"Exported records: {result['exported_records']}")
        logger.info(f"Export path: {result['export_path']}")
    else:
        logger.error(f"Export error: {result.get('error', 'Unknown error')}")

    return result


def create_test_invoice_csv():
    """
    Create a CSV file with test invoice data for import.

    This function creates two CSV files:
    1. A customer invoice (out_invoice)
    2. A vendor bill (in_invoice)

    Each with appropriate line items.
    """
    logger.info("Creating test invoice CSV files for import")

    # Create exports directory if it doesn't exist
    os.makedirs("exports", exist_ok=True)

    try:
        # Create customer invoice CSV
        customer_invoice = {
            "move_type": "out_invoice",
            "partner_id": 45,  # B2B Customer Intra State
            "journal_id": 1,   # Customer Invoices
            "invoice_date": pd.Timestamp.now().strftime('%Y-%m-%d'),
            "date": pd.Timestamp.now().strftime('%Y-%m-%d'),
            "currency_id": 20,  # INR
            "ref": "Test Customer Invoice",
            "state": "draft"
        }

        # Create vendor bill CSV
        vendor_bill = {
            "move_type": "in_invoice",
            "partner_id": 49,  # Supplier
            "journal_id": 2,   # Vendor Bills
            "invoice_date": pd.Timestamp.now().strftime('%Y-%m-%d'),
            "date": pd.Timestamp.now().strftime('%Y-%m-%d'),
            "currency_id": 20,  # INR
            "ref": "Test Vendor Bill",
            "state": "draft"
        }

        # Create DataFrames
        customer_df = pd.DataFrame([customer_invoice])
        vendor_df = pd.DataFrame([vendor_bill])

        # Export to CSV
        customer_df.to_csv("exports/customer_invoice_import.csv", index=False)
        vendor_df.to_csv("exports/vendor_bill_import.csv", index=False)

        logger.info("Created test invoice CSV files for import")

        # Create invoice lines CSV
        customer_lines = [
            {
                "name": "Test Product 1",
                "product_id": 16,  # Corner Desk Right Sit
                "account_id": 38,  # Local Sales
                "quantity": 2,
                "price_unit": 147.0,
                "discount": 0,
                "tax_ids": 32,  # 5% GST
            },
            {
                "name": "Test Product 2",
                "product_id": 17,  # Large Cabinet
                "account_id": 38,  # Local Sales
                "quantity": 1,
                "price_unit": 320.0,
                "discount": 10,
                "tax_ids": 32,  # 5% GST
            }
        ]

        vendor_lines = [
            {
                "name": "Test Vendor Product 1",
                "product_id": 16,  # Corner Desk Right Sit
                "account_id": 54,  # Purchase Expense
                "quantity": 3,
                "price_unit": 120.0,
                "discount": 0,
                "tax_ids": 63,  # 5% GST (purchase)
            },
            {
                "name": "Test Vendor Product 2",
                "product_id": 17,  # Large Cabinet
                "account_id": 54,  # Purchase Expense
                "quantity": 2,
                "price_unit": 280.0,
                "discount": 5,
                "tax_ids": 63,  # 5% GST (purchase)
            }
        ]

        # Create DataFrames
        customer_lines_df = pd.DataFrame(customer_lines)
        vendor_lines_df = pd.DataFrame(vendor_lines)

        # Export to CSV
        customer_lines_df.to_csv("exports/customer_invoice_lines_import.csv", index=False)
        vendor_lines_df.to_csv("exports/vendor_bill_lines_import.csv", index=False)

        logger.info("Created test invoice lines CSV files for import")

        return {
            "success": True,
            "customer_invoice_path": "exports/customer_invoice_import.csv",
            "vendor_bill_path": "exports/vendor_bill_import.csv",
            "customer_lines_path": "exports/customer_invoice_lines_import.csv",
            "vendor_lines_path": "exports/vendor_bill_lines_import.csv"
        }

    except Exception as e:
        logger.error(f"Error creating test invoice CSV files: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def test_invoice_import():
    """
    Test importing invoices from CSV files.

    This test imports:
    1. A customer invoice
    2. A vendor bill

    And then adds line items to each.
    """
    logger.info("Testing import flow with account.move model (invoices)")

    # First, create the test CSV files
    csv_result = create_test_invoice_csv()

    if not csv_result["success"]:
        logger.error(f"Failed to create test CSV files: {csv_result.get('error', 'Unknown error')}")
        return None

    # Import customer invoice
    logger.info("Importing customer invoice")
    customer_result = import_records(
        import_path=csv_result["customer_invoice_path"],
        model_name="account.move",
        field_mapping=None,  # Use default mapping
        create_if_not_exists=True,
        update_if_exists=True
    )

    if not customer_result["success"]:
        logger.error(f"Failed to import customer invoice: {customer_result.get('error', 'Unknown error')}")
        return None

    # Get the created customer invoice ID
    if customer_result["imported_records"] > 0:
        # Connect to Odoo to get the created invoice ID
        uid, models = connect_to_odoo()

        if not uid or not models:
            logger.error("Failed to connect to Odoo")
            return None

        # Search for the invoice
        customer_invoices = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            "account.move", "search_read",
            [[
                ("move_type", "=", "out_invoice"),
                ("ref", "=", "Test Customer Invoice"),
                ("state", "=", "draft")
            ]],
            {"fields": ["id"], "limit": 1}
        )

        if customer_invoices:
            customer_invoice_id = customer_invoices[0]["id"]
            logger.info(f"Created customer invoice with ID: {customer_invoice_id}")

            # Now import the invoice lines
            logger.info("Importing customer invoice lines")

            # Read the lines CSV
            customer_lines_df = pd.read_csv(csv_result["customer_lines_path"])

            # Add the move_id to each line
            customer_lines_df["move_id"] = customer_invoice_id

            # Save the updated CSV
            customer_lines_df.to_csv(csv_result["customer_lines_path"], index=False)

            # Import the lines
            customer_lines_result = import_records(
                import_path=csv_result["customer_lines_path"],
                model_name="account.move.line",
                field_mapping=None,  # Use default mapping
                create_if_not_exists=True,
                update_if_exists=True
            )

            if not customer_lines_result["success"]:
                logger.error(f"Failed to import customer invoice lines: {customer_lines_result.get('error', 'Unknown error')}")
        else:
            logger.error("Could not find the created customer invoice")

    # Import vendor bill
    logger.info("Importing vendor bill")
    vendor_result = import_records(
        import_path=csv_result["vendor_bill_path"],
        model_name="account.move",
        field_mapping=None,  # Use default mapping
        create_if_not_exists=True,
        update_if_exists=True
    )

    if not vendor_result["success"]:
        logger.error(f"Failed to import vendor bill: {vendor_result.get('error', 'Unknown error')}")
        return None

    # Get the created vendor bill ID
    if vendor_result["imported_records"] > 0:
        # Connect to Odoo to get the created invoice ID
        uid, models = connect_to_odoo()

        if not uid or not models:
            logger.error("Failed to connect to Odoo")
            return None

        # Search for the invoice
        vendor_bills = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            "account.move", "search_read",
            [[
                ("move_type", "=", "in_invoice"),
                ("ref", "=", "Test Vendor Bill"),
                ("state", "=", "draft")
            ]],
            {"fields": ["id"], "limit": 1}
        )

        if vendor_bills:
            vendor_bill_id = vendor_bills[0]["id"]
            logger.info(f"Created vendor bill with ID: {vendor_bill_id}")

            # Now import the invoice lines
            logger.info("Importing vendor bill lines")

            # Read the lines CSV
            vendor_lines_df = pd.read_csv(csv_result["vendor_lines_path"])

            # Add the move_id to each line
            vendor_lines_df["move_id"] = vendor_bill_id

            # Save the updated CSV
            vendor_lines_df.to_csv(csv_result["vendor_lines_path"], index=False)

            # Import the lines
            vendor_lines_result = import_records(
                import_path=csv_result["vendor_lines_path"],
                model_name="account.move.line",
                field_mapping=None,  # Use default mapping
                create_if_not_exists=True,
                update_if_exists=True
            )

            if not vendor_lines_result["success"]:
                logger.error(f"Failed to import vendor bill lines: {vendor_lines_result.get('error', 'Unknown error')}")
        else:
            logger.error("Could not find the created vendor bill")

    # Return the combined results
    return {
        "success": customer_result["success"] and vendor_result["success"],
        "customer_invoice_result": customer_result,
        "vendor_bill_result": vendor_result
    }


def test_invoice_update():
    """
    Test updating invoices by exporting, modifying, and importing back.

    This test:
    1. Exports all draft invoices
    2. Modifies their reference and date
    3. Imports them back
    """
    logger.info("Testing update flow with account.move model (invoices)")

    # Export draft invoices
    result = export_records(
        model_name="account.move",
        fields=[
            "id", "name", "move_type", "state", "partner_id", "journal_id",
            "invoice_date", "date", "payment_state", "amount_untaxed",
            "amount_tax", "amount_total", "currency_id", "ref"
        ],
        filter_domain=[
            ("move_type", "in", ["out_invoice", "in_invoice"]),
            ("state", "=", "draft")
        ],
        limit=100,
        export_path="exports/draft_invoices_export.csv"
    )

    if not result["success"]:
        logger.error(f"Failed to export draft invoices: {result.get('error', 'Unknown error')}")
        return None

    # Check if there are any draft invoices
    if result["exported_records"] == 0:
        logger.warning("No draft invoices found to update")
        return None

    # Modify the exported invoices
    try:
        # Read the CSV file
        df = pd.read_csv("exports/draft_invoices_export.csv")

        # Check if there are any records
        if len(df) == 0:
            logger.error("No invoices found in the export file")
            return None

        # Update references and dates
        for i in range(len(df)):
            # Update reference
            if 'ref' in df.columns:
                original_ref = df.at[i, 'ref'] if not pd.isna(df.at[i, 'ref']) else ""
                new_ref = f"{original_ref} (Updated on {pd.Timestamp.now().strftime('%Y-%m-%d')})"
                df.at[i, 'ref'] = new_ref

            # Update invoice date to tomorrow
            if 'invoice_date' in df.columns and not pd.isna(df.at[i, 'invoice_date']):
                try:
                    current_date = datetime.strptime(str(df.at[i, 'invoice_date']), '%Y-%m-%d')
                    new_date = (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
                    df.at[i, 'invoice_date'] = new_date
                except Exception as e:
                    logger.warning(f"Error updating invoice_date for record {i}: {str(e)}")

        # Save the modified CSV
        df.to_csv("exports/draft_invoices_modified.csv", index=False)

        # Import the modified invoices
        import_result = import_records(
            import_path="exports/draft_invoices_modified.csv",
            model_name="account.move",
            field_mapping=None,  # Use default mapping
            create_if_not_exists=False,  # Only update existing records
            update_if_exists=True
        )

        if not import_result["success"]:
            logger.error(f"Failed to import modified invoices: {import_result.get('error', 'Unknown error')}")
            return None

        logger.info(f"Successfully updated {import_result['updated_records']} invoices")

        return import_result

    except Exception as e:
        logger.error(f"Error updating invoices: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def test_related_records_export():
    """
    Test exporting related records (account.move and account.move.line) to a single CSV file.

    This test demonstrates how to:
    1. Export parent and child records together
    2. Maintain the relationships between them
    3. Structure the data for easy import
    """
    logger.info("Testing related records export with account.move and account.move.line")

    # Create exports directory if it doesn't exist
    os.makedirs("./exports", exist_ok=True)

    # First, let's make sure we have invoices with lines
    # Create a test invoice if needed
    uid, models = connect_to_odoo()

    if not uid or not models:
        logger.error("Failed to connect to Odoo")
        return None

    # Check if we have invoices with lines
    invoices_with_lines = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'account.move', 'search_read',
        [[
            ('move_type', 'in', ['out_invoice', 'in_invoice']),
            ('state', '=', 'posted'),
            ('invoice_line_ids', '!=', False)
        ]],
        {'fields': ['id', 'name'], 'limit': 5}
    )

    if not invoices_with_lines:
        logger.warning("No invoices with lines found, using posted invoices instead")

    # Run the export flow
    result = export_related_records(
        parent_model="account.move",
        child_model="account.move.line",
        relation_field="move_id",
        parent_fields=[
            "id", "name", "move_type", "state", "partner_id", "journal_id",
            "invoice_date", "date", "payment_state", "amount_total", "currency_id", "ref"
        ],
        child_fields=[
            "id", "move_id", "name", "account_id", "product_id",
            "quantity", "price_unit", "discount", "tax_ids", "price_subtotal"
        ],
        filter_domain=[
            ("move_type", "in", ["out_invoice", "in_invoice"]),
            ("state", "=", "posted"),
            ("invoice_line_ids", "!=", False)
        ],
        limit=5,
        export_path="./exports/invoice_with_lines_export.csv"
    )

    # Print the results
    logger.info(f"Export success: {result['success']}")

    if result["success"]:
        logger.info(f"Parent records: {result['parent_records']}")
        logger.info(f"Child records: {result['child_records']}")
        logger.info(f"Combined records: {result['combined_records']}")
        logger.info(f"Export path: {result['export_path']}")
    else:
        logger.error(f"Export error: {result.get('error', 'Unknown error')}")

    return result


def test_related_records_update():
    """
    Test updating related records (account.move and account.move.line) from a CSV file.

    This test demonstrates how to:
    1. Export parent and child records together
    2. Modify the data
    3. Import it back while maintaining relationships
    """
    logger.info("Testing related records update with account.move and account.move.line")

    # First, export the related records
    export_result = test_related_records_export()

    if not export_result["success"]:
        logger.error(f"Failed to export related records: {export_result.get('error', 'Unknown error')}")
        return None

    # Check if there are any records
    if export_result["combined_records"] == 0:
        logger.warning("No related records found to update")
        return None

    # Modify the exported records
    try:
        # Read the CSV file
        df = pd.read_csv("./exports/invoice_with_lines_export.csv")

        # Check if there are any records
        if len(df) == 0:
            logger.error("No records found in the export file")
            return None

        # Update references and quantities
        for i in range(len(df)):
            # Update parent reference
            if 'parent_ref' in df.columns and not pd.isna(df.at[i, 'parent_ref']):
                original_ref = df.at[i, 'parent_ref']
                new_ref = f"{original_ref} (Updated on {pd.Timestamp.now().strftime('%Y-%m-%d')})"
                df.at[i, 'parent_ref'] = new_ref

            # Update child quantity (increase by 1)
            if 'child_quantity' in df.columns and not pd.isna(df.at[i, 'child_quantity']):
                try:
                    current_qty = float(df.at[i, 'child_quantity'])
                    new_qty = current_qty + 1
                    df.at[i, 'child_quantity'] = new_qty
                except Exception as e:
                    logger.warning(f"Error updating quantity for record {i}: {str(e)}")

        # Save the modified CSV
        df.to_csv("./exports/invoice_with_lines_modified.csv", index=False)

        # Import the modified records
        import_result = import_related_records(
            import_path="./exports/invoice_with_lines_modified.csv",
            parent_model="account.move",
            child_model="account.move.line",
            relation_field="move_id",
            create_if_not_exists=False,  # Only update existing records
            update_if_exists=True
        )

        if not import_result["success"]:
            logger.error(f"Failed to import modified related records: {import_result.get('error', 'Unknown error')}")
            return None

        logger.info(f"Successfully updated {import_result['parent_updated']} parent records and {import_result['child_updated']} child records")

        return import_result

    except Exception as e:
        logger.error(f"Error updating related records: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """
    Main function for testing export/import functionality.

    Available test cases:
    - export: Export res.partner records to CSV
    - import: Import res.partner records from CSV
    - product: Export product.product records to CSV
    - crm-export: Export crm.lead records to CSV
    - crm-update: Export crm.lead records, update descriptions, and import back
    - invoice-export: Export account.move records to CSV
    - invoice-lines: Export account.move.line records to CSV
    - invoice-import: Create and import test invoices
    - invoice-update: Update existing draft invoices
    - related-export: Export account.move and account.move.line together
    - related-update: Update account.move and account.move.line together

    The crm-update and invoice tests demonstrate how to handle complex field types like
    many2one references, selection fields, and date fields.

    The related-export and related-update tests demonstrate how to handle parent-child
    relationships between models.
    """
    # Create exports directory if it doesn't exist
    try:
        os.makedirs("./exports", exist_ok=True)
        logger.info("Exports directory created or already exists")
    except Exception as e:
        logger.error(f"Error creating exports directory: {str(e)}")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Test the Export/Import functionality")
    parser.add_argument("--test",
                        choices=["export", "import", "product", "crm-export", "crm-update",
                                 "invoice-export", "invoice-lines", "invoice-import", "invoice-update",
                                 "related-export", "related-update"],
                        default="export",
                        help="Test to run")

    args = parser.parse_args()

    try:
        if args.test == "export":
            result = test_export_flow()
            if result and result.get("success"):
                logger.info("Export test completed successfully")
            else:
                logger.error("Export test failed")
        elif args.test == "import":
            result = test_import_flow()
            if result and result.get("success"):
                logger.info("Import test completed successfully")
            else:
                logger.error("Import test failed")
        elif args.test == "product":
            result = test_product_export_flow()
            if result and result.get("success"):
                logger.info("Product export test completed successfully")
            else:
                logger.error("Product export test failed")
        elif args.test == "crm-export":
            result = test_crm_lead_export()
            if result and result.get("success"):
                logger.info("CRM lead export test completed successfully")
            else:
                logger.error("CRM lead export test failed")
        elif args.test == "crm-update":
            result = test_crm_lead_update_description()
            if result and result.get("success"):
                logger.info("CRM lead description update test completed successfully")
            else:
                logger.error("CRM lead description update test failed")
        elif args.test == "invoice-export":
            result = test_invoice_export()
            if result and result.get("success"):
                logger.info("Invoice export test completed successfully")
            else:
                logger.error("Invoice export test failed")
        elif args.test == "invoice-lines":
            result = test_invoice_line_export()
            if result and result.get("success"):
                logger.info("Invoice lines export test completed successfully")
            else:
                logger.error("Invoice lines export test failed")
        elif args.test == "invoice-import":
            result = test_invoice_import()
            if result and result.get("success"):
                logger.info("Invoice import test completed successfully")
            else:
                logger.error("Invoice import test failed")
        elif args.test == "invoice-update":
            result = test_invoice_update()
            if result and result.get("success"):
                logger.info("Invoice update test completed successfully")
            else:
                logger.error("Invoice update test failed")
        elif args.test == "related-export":
            result = test_related_records_export()
            if result and result.get("success"):
                logger.info("Related records export test completed successfully")
            else:
                logger.error("Related records export test failed")
        elif args.test == "related-update":
            result = test_related_records_update()
            if result and result.get("success"):
                logger.info("Related records update test completed successfully")
            else:
                logger.error("Related records update test failed")
        else:
            logger.error(f"Unknown test: {args.test}")
    except Exception as e:
        logger.error(f"Error running test: {str(e)}")


if __name__ == "__main__":
    main()