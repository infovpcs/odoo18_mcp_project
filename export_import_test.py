#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
import xmlrpc.client
import pandas as pd
import ast
import re
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Odoo connection parameters
ODOO_URL = os.environ.get('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.environ.get('ODOO_DB', 'llmdb18')
ODOO_USER = os.environ.get('ODOO_USER', 'admin')
ODOO_PASSWORD = os.environ.get('ODOO_PASSWORD', 'admin')

def connect_to_odoo():
    """Connect to Odoo server."""
    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common', allow_none=True)
        uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object', allow_none=True)
        return uid, models
    except Exception as e:
        logger.error(f"Error connecting to Odoo: {str(e)}")
        return None, None

def extract_id_from_many2one(value):
    """Extract ID from many2one field value."""
    if isinstance(value, list) and len(value) > 0:
        return value[0]
    elif isinstance(value, str):
        # Try to extract ID from string like "[38, 'Local Sales']"
        match = re.match(r'\[(\d+),\s*.*\]', value)
        if match:
            return int(match.group(1))
        
        # Try to parse as a list
        try:
            if value.startswith('[') and value.endswith(']'):
                parsed = ast.literal_eval(value)
                if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], int):
                    return parsed[0]
        except (SyntaxError, ValueError):
            pass
    elif isinstance(value, float):
        # Convert float to integer
        return int(value)
    return value

def export_invoices():
    """Export customer invoices to CSV."""
    uid, models = connect_to_odoo()
    if not uid or not models:
        return False
    
    export_path = "/tmp/customer_invoices.csv"
    logger.info(f"Exporting customer invoices to {export_path}")
    
    # Define fields to export
    invoice_fields = [
        'id', 'name', 'move_type', 'state', 'partner_id', 'journal_id',
        'invoice_date', 'date', 'payment_state', 'amount_total', 'currency_id', 'ref'
    ]
    
    line_fields = [
        'id', 'move_id', 'name', 'sequence', 'display_type', 'product_id', 'product_uom_id',
        'account_id', 'analytic_distribution', 'partner_id', 'currency_id',
        'quantity', 'price_unit', 'discount', 'tax_ids', 'price_subtotal', 'price_total',
        'amount_currency', 'balance', 'date', 'date_maturity', 'reconciled', 'payment_id'
    ]
    
    # Get invoices
    invoices = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'account.move', 'search_read',
        [[('move_type', '=', 'out_invoice')]],
        {'fields': invoice_fields, 'limit': 10}
    )
    
    if not invoices:
        logger.error("No invoices found")
        return False
    
    # Get invoice IDs
    invoice_ids = [inv['id'] for inv in invoices]
    
    # Get invoice lines
    lines = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'account.move.line', 'search_read',
        [[('move_id', 'in', invoice_ids)]],
        {'fields': line_fields}
    )
    
    # Group lines by invoice
    lines_by_invoice = {}
    for line in lines:
        move_id = line['move_id'][0] if isinstance(line['move_id'], list) else line['move_id']
        if move_id not in lines_by_invoice:
            lines_by_invoice[move_id] = []
        lines_by_invoice[move_id].append(line)
    
    # Create combined records
    combined_records = []
    
    for invoice in invoices:
        invoice_id = invoice['id']
        invoice_lines = lines_by_invoice.get(invoice_id, [])
        
        if not invoice_lines:
            # Add parent record
            record = {
                '_model': 'account.move',
                '_record_type': 'parent',
                '_child_count': 0
            }
            
            # Add invoice fields
            for field in invoice_fields:
                record[f'parent_{field}'] = invoice.get(field)
            
            combined_records.append(record)
        else:
            # Add combined records (parent + child)
            for i, line in enumerate(invoice_lines):
                record = {
                    '_model': 'account.move,account.move.line',
                    '_record_type': 'combined',
                    '_child_index': i + 1,
                    '_child_count': len(invoice_lines)
                }
                
                # Add invoice fields
                for field in invoice_fields:
                    record[f'parent_{field}'] = invoice.get(field)
                
                # Add line fields
                for field in line_fields:
                    record[f'child_{field}'] = line.get(field)
                
                combined_records.append(record)
    
    # Export to CSV
    df = pd.DataFrame(combined_records)
    df.to_csv(export_path, index=False)
    
    logger.info(f"Exported {len(combined_records)} records to {export_path}")
    return export_path

def import_invoices(import_path):
    """Import invoices from CSV."""
    uid, models = connect_to_odoo()
    if not uid or not models:
        return False
    
    logger.info(f"Importing invoices from {import_path}")
    
    # Read CSV
    df = pd.read_csv(import_path)
    
    if df.empty:
        logger.error("CSV file is empty")
        return False
    
    # Get parent and child fields
    parent_fields = [col[7:] for col in df.columns if col.startswith('parent_')]
    child_fields = [col[6:] for col in df.columns if col.startswith('child_')]
    
    # Process records
    parent_updated = 0
    parent_failed = 0
    child_updated = 0
    child_failed = 0
    
    # Group records by parent ID
    parent_records = {}
    child_records = {}
    
    for _, row in df.iterrows():
        record_type = row['_record_type']
        
        # Extract parent data
        parent_data = {}
        parent_id = None
        
        for field in parent_fields:
            if f'parent_{field}' in row:
                value = row[f'parent_{field}']
                
                # Handle many2one fields
                if field in ['partner_id', 'journal_id', 'currency_id']:
                    value = extract_id_from_many2one(value)
                
                parent_data[field] = value
                if field == 'id':
                    # Ensure ID is an integer
                    if isinstance(value, float):
                        parent_id = int(value)
                    else:
                        parent_id = value
        
        # Skip if no parent ID
        if parent_id is None:
            continue
        
        # Add or update parent record
        if parent_id not in parent_records:
            parent_records[parent_id] = parent_data
        
        # If it's a combined record, extract child data
        if record_type == 'combined':
            child_data = {}
            
            for field in child_fields:
                if f'child_{field}' in row:
                    value = row[f'child_{field}']
                    
                    # Handle many2one fields
                    if field in ['account_id', 'product_id', 'move_id', 'partner_id', 'currency_id', 'product_uom_id']:
                        value = extract_id_from_many2one(value)
                    
                    # Handle many2many fields
                    if field == 'tax_ids' and isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                        try:
                            # Try to parse as a list
                            tax_ids = ast.literal_eval(value)
                            if isinstance(tax_ids, list):
                                value = [(6, 0, tax_ids)]
                        except (SyntaxError, ValueError):
                            pass
                    
                    # Handle date fields
                    if field in ['date', 'date_maturity']:
                        if value == 'False' or value is False or value == '':
                            continue  # Skip this field
                    
                    # Ensure ID is an integer
                    if field == 'id' and isinstance(value, float):
                        value = int(value)
                    
                    child_data[field] = value
            
            # Add move_id if not present
            if 'move_id' not in child_data and parent_id is not None:
                child_data['move_id'] = parent_id
            
            # Get child ID
            child_id = child_data.get('id')
            if isinstance(child_id, float):
                child_id = int(child_id)
            
            # Add to child records
            if parent_id not in child_records:
                child_records[parent_id] = []
            
            child_records[parent_id].append(child_data)
    
    # Update parent records (invoices)
    for parent_id, parent_data in parent_records.items():
        try:
            # Remove readonly fields
            for field in ['amount_total', 'amount_untaxed', 'amount_tax', 'payment_state']:
                if field in parent_data:
                    del parent_data[field]
            
            # Remove the ID field from the data
            if 'id' in parent_data:
                del parent_data[field]
            
            # Update the invoice
            models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'account.move', 'write',
                [[parent_id], parent_data]
            )
            parent_updated += 1
            logger.info(f"Updated invoice {parent_id}")
        except Exception as e:
            parent_failed += 1
            logger.error(f"Error updating invoice {parent_id}: {str(e)}")
    
    # Update invoice lines
    for parent_id, children in child_records.items():
        # First, try to reset the invoice to draft if it's posted
        try:
            invoice_state = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'account.move', 'read',
                [[parent_id]], {'fields': ['state']}
            )[0]['state']
            
            if invoice_state == 'posted':
                logger.info(f"Resetting invoice {parent_id} to draft")
                models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    'account.move', 'button_draft',
                    [[parent_id]]
                )
        except Exception as e:
            logger.warning(f"Could not reset invoice {parent_id} to draft: {str(e)}")
        
        # Now update each line
        for child_data in children:
            try:
                child_id = child_data.get('id')
                if child_id:
                    # Convert child_id to integer if it's a float
                    if isinstance(child_id, float):
                        child_id = int(child_id)
                    
                    # Remove readonly fields
                    for field in ['price_subtotal', 'price_total', 'balance', 'amount_currency']:
                        if field in child_data:
                            del child_data[field]
                    
                    # Make sure account_id is an integer
                    if 'account_id' in child_data:
                        account_id = child_data['account_id']
                        if isinstance(account_id, str):
                            # Try to extract ID from string
                            account_id = extract_id_from_many2one(account_id)
                            if isinstance(account_id, int):
                                child_data['account_id'] = account_id
                            else:
                                # If we can't extract a valid ID, remove the field
                                logger.warning(f"Removing invalid account_id: {account_id}")
                                del child_data['account_id']
                    
                    # Make sure move_id is an integer
                    if 'move_id' in child_data:
                        move_id = child_data['move_id']
                        if isinstance(move_id, str) or isinstance(move_id, float):
                            move_id = extract_id_from_many2one(move_id)
                            if isinstance(move_id, int):
                                child_data['move_id'] = move_id
                    
                    # Remove the ID field from the data
                    if 'id' in child_data:
                        del child_data['id']
                    
                    # Skip empty data
                    if not child_data:
                        logger.warning(f"Skipping empty data for line {child_id}")
                        continue
                    
                    # Update the line
                    logger.info(f"Updating invoice line {child_id} with data: {json.dumps(child_data)}")
                    models.execute_kw(
                        ODOO_DB, uid, ODOO_PASSWORD,
                        'account.move.line', 'write',
                        [[child_id], child_data]
                    )
                    child_updated += 1
                    logger.info(f"Updated invoice line {child_id}")
            except Exception as e:
                child_failed += 1
                logger.error(f"Error updating invoice line: {str(e)}")
    
    logger.info(f"Import results: {parent_updated} invoices updated, {parent_failed} invoices failed, {child_updated} lines updated, {child_failed} lines failed")
    return True

def main():
    # Export invoices
    export_path = export_invoices()
    if not export_path:
        return
    
    # Import invoices
    import_invoices(export_path)

if __name__ == "__main__":
    main()