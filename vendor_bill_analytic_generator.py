#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vendor Bill Analytic Line Generator

This script reads vendor bills and bill refunds, processes their invoice lines with subtotals,
and generates analytic lines for each invoice line with the following sign convention:
- For vendor bills (in_invoice): uses minus sign entries
- For bill refunds (in_refund): uses positive sign entries

Usage:
    python vendor_bill_analytic_generator.py [--limit=N] [--filter=domain]

Example:
    python vendor_bill_analytic_generator.py --limit=10 --filter="[('invoice_date', '>=', '2025-01-01')]"
"""

import os
import logging
import argparse
import json
import xmlrpc.client
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("vendor_bill_analytic_generator")

# Load environment variables
load_dotenv()

# Get Odoo connection details from environment variables
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "llmdb18")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")


def connect_to_odoo() -> Tuple[int, xmlrpc.client.ServerProxy]:
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


def parse_domain(domain_str: str) -> List:
    """Parse domain string to domain list."""
    if not domain_str:
        return []

    try:
        # Replace date strings with actual date objects
        domain_str = domain_str.replace("'", '"')
        domain = json.loads(domain_str)

        # Process date values in the domain
        for i, condition in enumerate(domain):
            if len(condition) == 3 and isinstance(condition[2], str):
                if condition[2].startswith('20') and '-' in condition[2]:  # Simple date detection
                    try:
                        # Convert date string to date object
                        date_obj = datetime.strptime(condition[2], '%Y-%m-%d').date()
                        domain[i] = (condition[0], condition[1], date_obj)
                    except ValueError:
                        pass

        return domain
    except json.JSONDecodeError:
        logger.error(f"Invalid domain format: {domain_str}")
        return []


def get_vendor_bills(uid: int, models: xmlrpc.client.ServerProxy, limit: int = 100, domain: List = None) -> List[Dict]:
    """Get vendor bills and bill refunds."""
    try:
        # Set default domain if not provided
        if domain is None:
            domain = []

        # Add filter for vendor bills and bill refunds
        bill_domain = [
            ('move_type', 'in', ['in_invoice', 'in_refund']),  # Vendor bills and bill refunds
            ('state', '=', 'posted')  # Only posted bills
        ]

        # Combine with provided domain
        full_domain = domain + bill_domain

        # Get vendor bills
        bills = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.move', 'search_read',
            [full_domain],
            {
                'fields': [
                    'id', 'name', 'move_type', 'state', 'partner_id', 'invoice_date',
                    'journal_id', 'currency_id', 'amount_untaxed', 'amount_tax', 'amount_total'
                ],
                'limit': limit
            }
        )

        return bills
    except Exception as e:
        logger.error(f"Error getting vendor bills: {str(e)}")
        return []


def get_invoice_lines(uid: int, models: xmlrpc.client.ServerProxy, invoice_id: int) -> List[Dict]:
    """Get invoice lines for a specific invoice."""
    try:
        # Get invoice lines
        lines = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.move.line', 'search_read',
            [[
                ('move_id', '=', invoice_id),
                ('exclude_from_invoice_tab', '=', False)  # Only invoice lines, not tax/payment lines
            ]],
            {
                'fields': [
                    'id', 'name', 'account_id', 'analytic_distribution', 'product_id',
                    'quantity', 'price_unit', 'discount', 'tax_ids', 'price_subtotal',
                    'price_total', 'currency_id', 'partner_id'
                ]
            }
        )

        return lines
    except Exception as e:
        logger.error(f"Error getting invoice lines for invoice {invoice_id}: {str(e)}")
        return []


def create_analytic_line(uid: int, models: xmlrpc.client.ServerProxy, move_line: Dict, bill: Dict) -> Optional[int]:
    """
    Create an analytic line for an invoice line.
    - For vendor bills (in_invoice): use minus sign
    - For bill refunds (in_refund): use positive sign
    """
    try:
        # Skip if no analytic distribution
        if not move_line.get('analytic_distribution'):
            logger.info(f"Skipping line {move_line['id']} - No analytic distribution")
            return None

        # Get analytic distribution
        analytic_distribution = move_line.get('analytic_distribution', {})

        # Determine sign based on move_type
        # For vendor bills (in_invoice): use minus sign
        # For bill refunds (in_refund): use positive sign
        sign = 1 if bill['move_type'] == 'in_refund' else -1

        # For each analytic account in the distribution, create an analytic line
        analytic_line_ids = []
        for analytic_account_id, percentage in analytic_distribution.items():
            # Calculate amount with appropriate sign
            amount = sign * (move_line['price_subtotal'] * percentage / 100)

            # Prepare analytic line values
            values = {
                'name': move_line['name'] or f"Line for {bill['name']}",
                'date': bill['invoice_date'],
                'amount': amount,
                'unit_amount': move_line['quantity'],
                'product_id': move_line['product_id'] and move_line['product_id'][0] or False,
                'account_id': int(analytic_account_id),  # Analytic account ID
                'partner_id': move_line['partner_id'] and move_line['partner_id'][0] or bill['partner_id'][0],
                'move_line_id': move_line['id'],
                'ref': bill['name'],
                'company_id': 1,  # Default company ID, adjust if needed
                'general_account_id': move_line['account_id'][0],  # General account from move line
                'currency_id': move_line['currency_id'][0]
            }

            # Create analytic line
            analytic_line_id = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'account.analytic.line', 'create',
                [values]
            )

            analytic_line_ids.append(analytic_line_id)
            logger.info(f"Created analytic line {analytic_line_id} for move line {move_line['id']} with amount {amount}")

        return analytic_line_ids
    except Exception as e:
        logger.error(f"Error creating analytic line for move line {move_line['id']}: {str(e)}")
        return None


def process_vendor_bills(limit: int = 100, domain_str: str = None):
    """Process vendor bills and create analytic lines."""
    # Connect to Odoo
    uid, models = connect_to_odoo()
    if not uid or not models:
        logger.error("Failed to connect to Odoo")
        return False

    # Parse domain
    domain = parse_domain(domain_str)

    # Get vendor bills
    bills = get_vendor_bills(uid, models, limit, domain)
    logger.info(f"Found {len(bills)} vendor bills/refunds")

    # Process each bill
    for bill in bills:
        # Determine sign convention based on bill type
        sign_convention = "positive" if bill['move_type'] == 'in_refund' else "negative"
        logger.info(f"Processing bill {bill['name']} (ID: {bill['id']}, Type: {bill['move_type']}, Sign: {sign_convention})")

        # Get invoice lines
        lines = get_invoice_lines(uid, models, bill['id'])
        logger.info(f"Found {len(lines)} lines for bill {bill['name']}")

        # Process each line
        for line in lines:
            # Skip lines without price_subtotal (section, note, etc.)
            if not line.get('price_subtotal'):
                logger.info(f"Skipping line {line['id']} - No price subtotal")
                continue

            # Create analytic line
            analytic_line_ids = create_analytic_line(uid, models, line, bill)

            if analytic_line_ids:
                logger.info(f"Created {len(analytic_line_ids)} analytic lines for invoice line {line['id']} with {sign_convention} sign")
            else:
                logger.info(f"No analytic lines created for invoice line {line['id']}")

    logger.info("Vendor bill processing completed")
    return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Vendor Bill Analytic Line Generator")
    parser.add_argument('--limit', type=int, default=100, help='Limit number of bills to process')
    parser.add_argument('--filter', type=str, help='Filter domain for bills (JSON format)')

    args = parser.parse_args()

    # Process vendor bills
    process_vendor_bills(args.limit, args.filter)


if __name__ == "__main__":
    main()