#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Get Product Fields Script

This script gets all available fields for the product.product model.
"""

import xmlrpc.client
import sys
from pprint import pprint
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Odoo server configuration
URL = os.getenv("ODOO_URL", "http://localhost:8069")
DB = os.getenv("ODOO_DB", "llmdb18")
USERNAME = os.getenv("ODOO_USERNAME", "admin")
PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

def main():
    """Main function."""
    print("=== Get Product Fields ===")
    
    # Connect to Odoo
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common", allow_none=True)
    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)
    
    # Authenticate
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    
    if not uid:
        print("Authentication failed")
        sys.exit(1)
        
    print(f"Authenticated as user ID: {uid}")
    
    # Get all fields for product.product
    print("\nGetting all fields for product.product...")
    fields = models.execute_kw(
        DB, uid, PASSWORD,
        'product.product',
        'fields_get',
        [],
        {'attributes': ['string', 'help', 'type', 'selection']}
    )
    
    print(f"Found {len(fields)} fields for product.product")
    
    # Find type-related fields
    type_fields = {name: info for name, info in fields.items() if 'type' in name.lower()}
    print("\nType-related fields:")
    pprint(type_fields)
    
    # Get a sample product to see its values
    print("\nGetting a sample product...")
    products = models.execute_kw(
        DB, uid, PASSWORD,
        'product.product',
        'search_read',
        [[['active', '=', True]]],
        {'fields': list(type_fields.keys()), 'limit': 1}
    )
    
    if products:
        print("Sample product type fields:")
        pprint(products[0])

if __name__ == "__main__":
    main()