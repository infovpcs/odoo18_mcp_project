#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Odoo 18 Client Test Script

This script demonstrates basic operations with the Odoo 18 client.
"""

import xmlrpc.client
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Odoo server configuration
URL = os.getenv("ODOO_URL", "http://localhost:8069")
DB = os.getenv("ODOO_DB", "odoo")
USERNAME = os.getenv("ODOO_USERNAME", "admin")
PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

def main():
    """Main function."""
    print("=== Simple Odoo 18 Client Test ===")
    
    # Connect to Odoo
    print("\nConnecting to Odoo server...")
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common", allow_none=True)
    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)
    
    # Authenticate
    print("Authenticating...")
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    
    if not uid:
        print("Authentication failed")
        sys.exit(1)
        
    print(f"Authenticated as user ID: {uid}")
    
    # Test search_read on res.partner
    print("\nSearching for partners...")
    partners = models.execute_kw(
        DB, uid, PASSWORD,
        'res.partner',
        'search_read',
        [[['is_company', '=', True]]],
        {'fields': ['name', 'email', 'phone'], 'limit': 5}
    )
    
    print(f"Found {len(partners)} partners:")
    for partner in partners:
        print(f"  - {partner['name']} (ID: {partner['id']})")
    
    # Test search_read on product.product
    print("\nSearching for products...")
    products = models.execute_kw(
        DB, uid, PASSWORD,
        'product.product',
        'search_read',
        [[['active', '=', True]]],
        {'fields': ['name', 'default_code', 'list_price'], 'limit': 5}
    )
    
    print(f"Found {len(products)} products:")
    for product in products:
        print(f"  - {product['name']} (ID: {product['id']}, Price: {product.get('list_price', 'N/A')})")
    
    # Get model information using ir.model
    print("\nGetting model information...")
    models_info = models.execute_kw(
        DB, uid, PASSWORD,
        'ir.model',
        'search_read',
        [[['model', 'in', ['res.partner', 'product.product']]]],
        {'fields': ['name', 'model', 'info']}
    )
    
    print("Model information:")
    for model_info in models_info:
        print(f"  - {model_info['name']} ({model_info['model']})")
        print(f"    Info: {model_info.get('info', 'N/A')}")
        
    # Get field information using ir.model.fields
    print("\nGetting field information for res.partner...")
    field_info = models.execute_kw(
        DB, uid, PASSWORD,
        'ir.model.fields',
        'search_read',
        [[['model_id.model', '=', 'res.partner'], ['name', 'in', ['name', 'email', 'phone']]]],
        {'fields': ['name', 'field_description', 'ttype']}
    )
    
    print("Field information:")
    for field in field_info:
        print(f"  - {field['name']} ({field['ttype']}): {field['field_description']}")
        
    # Get field information for product.product
    print("\nGetting field information for product.product...")
    field_info = models.execute_kw(
        DB, uid, PASSWORD,
        'ir.model.fields',
        'search_read',
        [[['model_id.model', '=', 'product.product'], ['name', 'in', ['name', 'default_code', 'list_price']]]],
        {'fields': ['name', 'field_description', 'ttype']}
    )
    
    print("Field information:")
    for field in field_info:
        print(f"  - {field['name']} ({field['ttype']}): {field['field_description']}")
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    main()