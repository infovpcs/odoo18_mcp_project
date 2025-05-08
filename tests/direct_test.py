#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct Odoo 18 Test Script

This script directly tests the Odoo 18 API without going through the MCP server.
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
    print("=== Direct Odoo 18 Test ===")
    
    # Connect to Odoo
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common", allow_none=True)
    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)
    
    # Authenticate
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    
    if not uid:
        print("Authentication failed")
        sys.exit(1)
        
    print(f"Authenticated as user ID: {uid}")
    
    # Test CRUD operations on res.partner
    print("\n=== Testing CRUD operations on res.partner ===")
    
    # CREATE: Create a new partner
    print("\nCreating a new partner...")
    partner_data = {
        'name': 'Test Partner Direct',
        'email': 'test.partner.direct@example.com',
        'phone': '+1234567890',
        'is_company': True,
        'comment': 'Created via Direct API'
    }
    
    partner_id = models.execute_kw(
        DB, uid, PASSWORD,
        'res.partner',
        'create',
        [partner_data]
    )
    
    print(f"Created partner with ID: {partner_id}")
    
    # READ: Read the created partner
    print("\nReading the created partner...")
    partners = models.execute_kw(
        DB, uid, PASSWORD,
        'res.partner',
        'read',
        [partner_id],
        {'fields': ['name', 'email', 'phone', 'is_company', 'comment']}
    )
    
    print("Partner details:")
    pprint(partners[0])
    
    # UPDATE: Update the partner
    print("\nUpdating the partner...")
    result = models.execute_kw(
        DB, uid, PASSWORD,
        'res.partner',
        'write',
        [[partner_id], {'name': 'Updated Test Partner Direct', 'comment': 'Updated via Direct API'}]
    )
    
    print(f"Update result: {result}")
    
    # READ AGAIN: Read the updated partner
    print("\nReading the updated partner...")
    partners = models.execute_kw(
        DB, uid, PASSWORD,
        'res.partner',
        'read',
        [partner_id],
        {'fields': ['name', 'email', 'phone', 'is_company', 'comment']}
    )
    
    print("Updated partner details:")
    pprint(partners[0])
    
    # DELETE: Delete the partner
    print("\nDeleting the partner...")
    result = models.execute_kw(
        DB, uid, PASSWORD,
        'res.partner',
        'unlink',
        [[partner_id]]
    )
    
    print(f"Delete result: {result}")
    
    # VERIFY DELETION: Try to read the deleted partner
    print("\nVerifying deletion...")
    partners = models.execute_kw(
        DB, uid, PASSWORD,
        'res.partner',
        'search_read',
        [[['id', '=', partner_id]]],
        {'fields': ['name']}
    )
    
    if not partners:
        print("Partner successfully deleted (no records found)")
    else:
        print("Partner still exists!")
        pprint(partners[0])
    
    # Test CRUD operations on product.product
    print("\n=== Testing CRUD operations on product.product ===")
    
    # Get a product category
    print("\nGetting a product category...")
    categories = models.execute_kw(
        DB, uid, PASSWORD,
        'product.category',
        'search_read',
        [[['name', '=', 'All']]],
        {'fields': ['id'], 'limit': 1}
    )
    
    if not categories:
        print("No product category found")
        return
        
    category_id = categories[0]['id']
    print(f"Using category ID: {category_id}")
    
    # CREATE: Create a new product
    print("\nCreating a new product...")
    product_data = {
        'name': 'Test Product Direct',
        'default_code': 'TEST-DIRECT-001',
        'list_price': 99.99,
        'type': 'consu',  # Valid values: 'consu', 'service', 'combo'
        'categ_id': category_id,
        'description': 'Created via Direct API'
    }
    
    product_id = models.execute_kw(
        DB, uid, PASSWORD,
        'product.product',
        'create',
        [product_data]
    )
    
    print(f"Created product with ID: {product_id}")
    
    # READ: Read the created product
    print("\nReading the created product...")
    products = models.execute_kw(
        DB, uid, PASSWORD,
        'product.product',
        'read',
        [product_id],
        {'fields': ['name', 'default_code', 'list_price', 'type', 'categ_id', 'description']}
    )
    
    print("Product details:")
    pprint(products[0])
    
    # UPDATE: Update the product
    print("\nUpdating the product...")
    result = models.execute_kw(
        DB, uid, PASSWORD,
        'product.product',
        'write',
        [[product_id], {'name': 'Updated Test Product Direct', 'list_price': 149.99, 'description': 'Updated via Direct API'}]
    )
    
    print(f"Update result: {result}")
    
    # READ AGAIN: Read the updated product
    print("\nReading the updated product...")
    products = models.execute_kw(
        DB, uid, PASSWORD,
        'product.product',
        'read',
        [product_id],
        {'fields': ['name', 'default_code', 'list_price', 'type', 'categ_id', 'description']}
    )
    
    print("Updated product details:")
    pprint(products[0])
    
    # DELETE: Delete the product
    print("\nDeleting the product...")
    result = models.execute_kw(
        DB, uid, PASSWORD,
        'product.product',
        'unlink',
        [[product_id]]
    )
    
    print(f"Delete result: {result}")
    
    # VERIFY DELETION: Try to read the deleted product
    print("\nVerifying deletion...")
    products = models.execute_kw(
        DB, uid, PASSWORD,
        'product.product',
        'search_read',
        [[['id', '=', product_id]]],
        {'fields': ['name']}
    )
    
    if not products:
        print("Product successfully deleted (no records found)")
    else:
        print("Product still exists!")
        pprint(products[0])
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    main()