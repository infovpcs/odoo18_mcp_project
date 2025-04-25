#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for Vendor Bill Analytic Line Generator

This script tests the vendor_bill_analytic_generator.py script with a small number of bills.

Usage:
    python test_vendor_bill_analytic.py
"""

import os
import logging
import xmlrpc.client
from dotenv import load_dotenv
from vendor_bill_analytic_generator import (
    connect_to_odoo,
    get_vendor_bills,
    get_invoice_lines,
    create_analytic_line,
    process_vendor_bills
)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_vendor_bill_analytic")

# Load environment variables
load_dotenv()


def test_connection():
    """Test connection to Odoo."""
    logger.info("Testing connection to Odoo...")
    uid, models = connect_to_odoo()
    
    if uid and models:
        logger.info(f"Connection successful. User ID: {uid}")
        return True
    else:
        logger.error("Connection failed")
        return False


def test_get_vendor_bills():
    """Test getting vendor bills."""
    logger.info("Testing get_vendor_bills...")
    uid, models = connect_to_odoo()
    
    if not uid or not models:
        logger.error("Connection failed")
        return False
    
    # Get a small number of bills
    bills = get_vendor_bills(uid, models, limit=5)
    
    if bills:
        logger.info(f"Found {len(bills)} vendor bills")
        for bill in bills:
            logger.info(f"Bill: {bill['name']} (ID: {bill['id']}, Type: {bill['move_type']})")
        return True
    else:
        logger.warning("No vendor bills found")
        return False


def test_get_invoice_lines():
    """Test getting invoice lines."""
    logger.info("Testing get_invoice_lines...")
    uid, models = connect_to_odoo()
    
    if not uid or not models:
        logger.error("Connection failed")
        return False
    
    # Get a small number of bills
    bills = get_vendor_bills(uid, models, limit=1)
    
    if not bills:
        logger.warning("No vendor bills found")
        return False
    
    # Get invoice lines for the first bill
    bill = bills[0]
    lines = get_invoice_lines(uid, models, bill['id'])
    
    if lines:
        logger.info(f"Found {len(lines)} lines for bill {bill['name']}")
        for line in lines:
            logger.info(f"Line: {line['name']} (ID: {line['id']}, Subtotal: {line['price_subtotal']})")
            logger.info(f"Analytic Distribution: {line.get('analytic_distribution', {})}")
        return True
    else:
        logger.warning(f"No invoice lines found for bill {bill['name']}")
        return False


def test_create_analytic_line():
    """Test creating analytic lines."""
    logger.info("Testing create_analytic_line...")
    uid, models = connect_to_odoo()
    
    if not uid or not models:
        logger.error("Connection failed")
        return False
    
    # Get a small number of bills
    bills = get_vendor_bills(uid, models, limit=1)
    
    if not bills:
        logger.warning("No vendor bills found")
        return False
    
    # Get invoice lines for the first bill
    bill = bills[0]
    lines = get_invoice_lines(uid, models, bill['id'])
    
    if not lines:
        logger.warning(f"No invoice lines found for bill {bill['name']}")
        return False
    
    # Find a line with analytic distribution
    for line in lines:
        if line.get('analytic_distribution'):
            # Create analytic line
            analytic_line_ids = create_analytic_line(uid, models, line, bill)
            
            if analytic_line_ids:
                sign_convention = "positive" if bill['move_type'] == 'in_refund' else "negative"
                logger.info(f"Created {len(analytic_line_ids)} analytic lines for invoice line {line['id']} with {sign_convention} sign")
                
                # Verify created analytic lines
                for analytic_line_id in analytic_line_ids:
                    analytic_line = models.execute_kw(
                        os.getenv("ODOO_DB"), uid, os.getenv("ODOO_PASSWORD"),
                        'account.analytic.line', 'read',
                        [analytic_line_id],
                        {'fields': ['name', 'amount', 'account_id', 'move_line_id']}
                    )
                    
                    logger.info(f"Analytic line: {analytic_line[0]['name']} (ID: {analytic_line_id}, Amount: {analytic_line[0]['amount']})")
                
                return True
    
    logger.warning("No lines with analytic distribution found")
    return False


def test_process_vendor_bills():
    """Test processing vendor bills."""
    logger.info("Testing process_vendor_bills...")
    
    # Process a small number of bills
    result = process_vendor_bills(limit=2)
    
    if result:
        logger.info("Vendor bill processing completed successfully")
        return True
    else:
        logger.error("Vendor bill processing failed")
        return False


def test_bill_refund_sign():
    """Test that bill refunds use positive sign."""
    logger.info("Testing bill refund sign convention...")
    uid, models = connect_to_odoo()
    
    if not uid or not models:
        logger.error("Connection failed")
        return False
    
    # Get bill refunds
    refunds = get_vendor_bills(uid, models, limit=2, domain=[('move_type', '=', 'in_refund')])
    
    if not refunds:
        logger.warning("No bill refunds found")
        return False
    
    # Process each refund
    for refund in refunds:
        logger.info(f"Processing refund {refund['name']} (ID: {refund['id']})")
        
        # Get invoice lines
        lines = get_invoice_lines(uid, models, refund['id'])
        
        if not lines:
            logger.warning(f"No invoice lines found for refund {refund['name']}")
            continue
        
        # Find a line with analytic distribution
        for line in lines:
            if line.get('analytic_distribution') and line.get('price_subtotal'):
                # Create analytic line
                analytic_line_ids = create_analytic_line(uid, models, line, refund)
                
                if analytic_line_ids:
                    logger.info(f"Created {len(analytic_line_ids)} analytic lines for refund line {line['id']}")
                    
                    # Verify created analytic lines have positive amount
                    for analytic_line_id in analytic_line_ids:
                        analytic_line = models.execute_kw(
                            os.getenv("ODOO_DB"), uid, os.getenv("ODOO_PASSWORD"),
                            'account.analytic.line', 'read',
                            [analytic_line_id],
                            {'fields': ['name', 'amount', 'account_id', 'move_line_id']}
                        )
                        
                        amount = analytic_line[0]['amount']
                        logger.info(f"Refund analytic line: {analytic_line[0]['name']} (ID: {analytic_line_id}, Amount: {amount})")
                        
                        # Check if amount is positive
                        if amount > 0:
                            logger.info(f"PASS: Refund analytic line has positive amount ({amount})")
                            return True
                        else:
                            logger.error(f"FAIL: Refund analytic line has negative amount ({amount})")
                            return False
    
    logger.warning("No suitable refund lines with analytic distribution found")
    return False


def main():
    """Main function."""
    logger.info("Starting tests...")
    
    # Test connection
    if not test_connection():
        logger.error("Connection test failed. Aborting.")
        return
    
    # Test getting vendor bills
    if not test_get_vendor_bills():
        logger.warning("Get vendor bills test failed or no bills found.")
    
    # Test getting invoice lines
    if not test_get_invoice_lines():
        logger.warning("Get invoice lines test failed or no lines found.")
    
    # Test creating analytic lines
    if not test_create_analytic_line():
        logger.warning("Create analytic line test failed or no suitable lines found.")
    
    # Test bill refund sign convention
    if not test_bill_refund_sign():
        logger.warning("Bill refund sign test failed or no suitable refunds found.")
    
    # Test processing vendor bills
    if not test_process_vendor_bills():
        logger.error("Process vendor bills test failed.")
    
    logger.info("Tests completed.")


if __name__ == "__main__":
    main()