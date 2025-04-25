#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vendor Bill Analytic Line Generator

This script reads vendor bills and bill refunds, processes their invoice lines with subtotals,
and generates analytic lines for each invoice line with the following sign convention:
- For vendor bills (in_invoice): uses minus sign entries
- For bill refunds (in_refund): uses positive sign entries

Before processing bills, the script will:
1. Check all projects in the system and ensure they have analytic accounts
2. If a project has a blank analytic account, create a new one or assign an existing one with the same name

For invoice lines without analytic distributions, the script will:
1. First check if there's a project linked to the partner with an analytic account
2. If not, check for any existing analytic account for this partner
3. If still not found, create a new analytic account with the project name

This script is designed for generating historic data costing entries. For new bills,
analytic entries will be automatically generated from the purchase order cycle with linked bills.

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
        # First, get the invoice to check if it has invoice_line_ids field
        invoice = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.move', 'read',
            [invoice_id],
            {'fields': ['invoice_line_ids']}
        )

        if not invoice or not invoice[0].get('invoice_line_ids'):
            logger.warning(f"No invoice_line_ids found for invoice {invoice_id}")
            return []

        # Get invoice lines using the invoice_line_ids field
        invoice_line_ids = invoice[0]['invoice_line_ids']

        # Get invoice lines
        lines = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.move.line', 'read',
            [invoice_line_ids],
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


def get_project_for_bill(uid: int, models: xmlrpc.client.ServerProxy, bill: Dict) -> Optional[Dict]:
    """
    Try to find a project associated with the bill's partner.
    Returns the project record if found, None otherwise.

    Note: This function first checks if the project.project model exists in the Odoo installation.
    """
    try:
        # First check if the project.project model exists
        model_exists = False
        try:
            # Try to get the model's fields to check if it exists
            models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'project.project', 'fields_get',
                [], {'attributes': ['string']}
            )
            model_exists = True
        except Exception:
            logger.info("The project.project model is not installed in this Odoo instance")
            return None

        # If the model doesn't exist, return None
        if not model_exists:
            return None

        partner_id = bill['partner_id'][0]
        partner_name = bill['partner_id'][1]

        # Search for projects linked to this partner
        projects = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'project.project', 'search_read',
            [[('partner_id', '=', partner_id)]],
            {'fields': ['id', 'name', 'analytic_account_id'], 'limit': 1}
        )

        if projects and projects[0].get('analytic_account_id'):
            logger.info(f"Found project for partner {partner_name}: {projects[0]['name']} (ID: {projects[0]['id']})")
            return projects[0]

        return None

    except Exception as e:
        logger.error(f"Error finding project for bill: {str(e)}")
        return None


def get_or_create_analytic_account(uid: int, models: xmlrpc.client.ServerProxy, bill: Dict) -> Optional[int]:
    """
    Get or create an analytic account based on vendor name and project.
    Returns the analytic account ID.

    Process:
    1. First, check if there's a project linked to the partner with an analytic account
    2. If not, check for any existing analytic account for this partner
    3. If still not found, create a new analytic account
    """
    try:
        partner_id = bill['partner_id'][0]
        partner_name = bill['partner_id'][1]

        # Step 1: Check for project with analytic account
        project = get_project_for_bill(uid, models, bill)
        if project and project.get('analytic_account_id'):
            analytic_account_id = project['analytic_account_id'][0]
            logger.info(f"Using project's analytic account: {project['analytic_account_id'][1]} (ID: {analytic_account_id})")
            return analytic_account_id

        # Step 2: Try to find an existing analytic account for this partner
        analytic_accounts = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.analytic.account', 'search_read',
            [[('partner_id', '=', partner_id)]],
            {'fields': ['id', 'name'], 'limit': 1}
        )

        if analytic_accounts:
            logger.info(f"Found existing analytic account for partner {partner_name}: {analytic_accounts[0]['name']} (ID: {analytic_accounts[0]['id']})")
            return analytic_accounts[0]['id']

        # Step 3: No existing account, create a new one
        # First, get the default analytic plan
        analytic_plans = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.analytic.plan', 'search_read',
            [[]],
            {'fields': ['id', 'name'], 'limit': 1}
        )

        if not analytic_plans:
            logger.error("No analytic plan found. Cannot create analytic account.")
            return None

        plan_id = analytic_plans[0]['id']

        # Create a new analytic account with project name if available
        account_name = f"Project - {partner_name}"
        if project:
            account_name = f"Project - {project['name']}"

        new_account_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.analytic.account', 'create',
            [{
                'name': account_name,
                'partner_id': partner_id,
                'plan_id': plan_id,
                'code': f"P-{partner_id}"
            }]
        )

        logger.info(f"Created new analytic account: {account_name} (ID: {new_account_id})")
        return new_account_id

    except Exception as e:
        logger.error(f"Error creating analytic account: {str(e)}")
        return None


def create_analytic_line(uid: int, models: xmlrpc.client.ServerProxy, move_line: Dict, bill: Dict) -> Optional[int]:
    """
    Create an analytic line for an invoice line.
    - For vendor bills (in_invoice): use minus sign
    - For bill refunds (in_refund): use positive sign
    - If no analytic distribution exists, create one based on vendor name and project
    """
    try:
        # Determine sign based on move_type
        # For vendor bills (in_invoice): use minus sign
        # For bill refunds (in_refund): use positive sign
        sign = 1 if bill['move_type'] == 'in_refund' else -1

        # Initialize analytic_line_ids list
        analytic_line_ids = []

        # Check if analytic distribution exists
        if move_line.get('analytic_distribution'):
            # Get analytic distribution
            analytic_distribution = move_line.get('analytic_distribution', {})

            # For each analytic account in the distribution, create an analytic line
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
        else:
            # No analytic distribution, create one based on vendor name and project
            logger.info(f"No analytic distribution for line {move_line['id']} - Creating based on vendor")

            # Get or create analytic account
            analytic_account_id = get_or_create_analytic_account(uid, models, bill)

            if not analytic_account_id:
                logger.error(f"Could not get or create analytic account for bill {bill['name']}")
                return None

            # Calculate amount with appropriate sign (100% to this account)
            amount = sign * move_line['price_subtotal']

            # Prepare analytic line values
            values = {
                'name': move_line['name'] or f"Line for {bill['name']}",
                'date': bill['invoice_date'],
                'amount': amount,
                'unit_amount': move_line['quantity'],
                'product_id': move_line['product_id'] and move_line['product_id'][0] or False,
                'account_id': analytic_account_id,  # Analytic account ID
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
            logger.info(f"Created analytic line {analytic_line_id} for move line {move_line['id']} with amount {amount} (auto-created)")

            return analytic_line_ids

    except Exception as e:
        logger.error(f"Error creating analytic line for move line {move_line['id']}: {str(e)}")
        return None


def check_and_setup_project_analytics(uid: int, models: xmlrpc.client.ServerProxy) -> bool:
    """
    Check all projects in the system and ensure they have analytic accounts.
    If a project has a blank analytic account, create a new one or assign an existing one with the same name.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if the project.project model exists
        model_exists = False
        try:
            # Try to get the model's fields to check if it exists
            models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'project.project', 'fields_get',
                [], {'attributes': ['string']}
            )
            model_exists = True
        except Exception as e:
            logger.warning(f"The project.project model is not installed in this Odoo instance: {str(e)}")
            return False

        if not model_exists:
            logger.warning("Project module is not installed. Skipping project analytics setup.")
            return False

        # Get all projects
        projects = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'project.project', 'search_read',
            [[]],
            {'fields': ['id', 'name', 'partner_id', 'analytic_account_id']}
        )

        logger.info(f"Found {len(projects)} projects in the system")

        # Get default analytic plan
        analytic_plans = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'account.analytic.plan', 'search_read',
            [[]],
            {'fields': ['id', 'name'], 'limit': 1}
        )

        if not analytic_plans:
            logger.error("No analytic plan found. Cannot create analytic accounts.")
            return False

        plan_id = analytic_plans[0]['id']

        # Process each project
        for project in projects:
            project_id = project['id']
            project_name = project['name']

            # Skip if project already has an analytic account
            if project.get('analytic_account_id'):
                logger.info(f"Project {project_name} (ID: {project_id}) already has analytic account: {project['analytic_account_id'][1]}")
                continue

            # Check if an analytic account with the same name exists
            analytic_accounts = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'account.analytic.account', 'search_read',
                [[('name', '=', project_name)]],
                {'fields': ['id', 'name'], 'limit': 1}
            )

            if analytic_accounts:
                # Assign existing analytic account to project
                analytic_account_id = analytic_accounts[0]['id']
                logger.info(f"Found existing analytic account with name {project_name} (ID: {analytic_account_id})")

                # Update project with analytic account
                models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    'project.project', 'write',
                    [[project_id], {'analytic_account_id': analytic_account_id}]
                )

                logger.info(f"Assigned existing analytic account {project_name} (ID: {analytic_account_id}) to project {project_name} (ID: {project_id})")
            else:
                # Create new analytic account for project
                partner_id = project.get('partner_id') and project['partner_id'][0] or False

                # Create a new analytic account
                new_account_values = {
                    'name': project_name,
                    'plan_id': plan_id,
                    'code': f"P-{project_id}"
                }

                if partner_id:
                    new_account_values['partner_id'] = partner_id

                new_account_id = models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    'account.analytic.account', 'create',
                    [new_account_values]
                )

                # Update project with new analytic account
                models.execute_kw(
                    ODOO_DB, uid, ODOO_PASSWORD,
                    'project.project', 'write',
                    [[project_id], {'analytic_account_id': new_account_id}]
                )

                logger.info(f"Created new analytic account {project_name} (ID: {new_account_id}) for project {project_name} (ID: {project_id})")

        return True

    except Exception as e:
        logger.error(f"Error setting up project analytics: {str(e)}")
        return False


def process_vendor_bills(limit: int = 100, domain_str: str = None):
    """Process vendor bills and create analytic lines."""
    # Connect to Odoo
    uid, models = connect_to_odoo()
    if not uid or not models:
        logger.error("Failed to connect to Odoo")
        return False

    # First, check and setup project analytics
    logger.info("Checking and setting up project analytics...")
    check_and_setup_project_analytics(uid, models)

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