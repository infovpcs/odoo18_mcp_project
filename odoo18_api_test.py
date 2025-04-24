#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo 18 External API Test Script

This script demonstrates how to use the Odoo 18 External API for CRUD operations
following the official documentation: https://www.odoo.com/documentation/18.0/developer/reference/external_api.html
"""

import xmlrpc.client
import sys
import os
from pprint import pprint
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Odoo server configuration
URL = os.getenv("ODOO_URL", "http://localhost:8069")
DB = os.getenv("ODOO_DB", "llmdb18")
USERNAME = os.getenv("ODOO_USERNAME", "admin")
PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

def test_connection():
    """Test connection to Odoo server."""
    print("\n=== Testing Connection ===")
    
    # Connect to Odoo
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common", allow_none=True)
    
    # Get server info
    info = common.version()
    print(f"Server info: {info['server_version']}")
    
    # Authenticate
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    if not uid:
        print("Authentication failed")
        sys.exit(1)
        
    print(f"Authenticated as user ID: {uid}")
    return uid

def test_partner_operations(uid):
    """Test CRUD operations on res.partner."""
    print("\n=== Testing CRUD Operations on res.partner ===")
    
    # Connect to Odoo
    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)
    
    # CREATE: Create a new partner
    print("\n--- Creating a new partner ---")
    partner_data = {
        'name': 'Test Partner API',
        'email': 'test.partner.api@example.com',
        'phone': '+1234567890',
        'is_company': True,
        'comment': 'Created via External API'
    }
    
    partner_id = models.execute_kw(
        DB, uid, PASSWORD,
        'res.partner',
        'create',
        [partner_data]
    )
    
    print(f"Created partner with ID: {partner_id}")
    
    # READ: Read the created partner
    print("\n--- Reading the created partner ---")
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
    print("\n--- Updating the partner ---")
    result = models.execute_kw(
        DB, uid, PASSWORD,
        'res.partner',
        'write',
        [[partner_id], {'name': 'Updated Test Partner API', 'comment': 'Updated via External API'}]
    )
    
    print(f"Update result: {result}")
    
    # READ AGAIN: Read the updated partner
    print("\n--- Reading the updated partner ---")
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
    print("\n--- Deleting the partner ---")
    result = models.execute_kw(
        DB, uid, PASSWORD,
        'res.partner',
        'unlink',
        [[partner_id]]
    )
    
    print(f"Delete result: {result}")
    
    # VERIFY DELETION: Try to read the deleted partner
    print("\n--- Verifying deletion ---")
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

def test_product_operations(uid):
    """Test CRUD operations on product.product."""
    print("\n=== Testing CRUD Operations on product.product ===")
    
    # Connect to Odoo
    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)
    
    # Get a product category
    print("\n--- Getting a product category ---")
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
    print("\n--- Creating a new product ---")
    product_data = {
        'name': 'Test Product API',
        'default_code': 'TEST-API-001',
        'list_price': 99.99,
        'type': 'consu',  # Valid values: 'consu', 'service', 'combo'
        'categ_id': category_id,
        'description': 'Created via External API'
    }
    
    product_id = models.execute_kw(
        DB, uid, PASSWORD,
        'product.product',
        'create',
        [product_data]
    )
    
    print(f"Created product with ID: {product_id}")
    
    # READ: Read the created product
    print("\n--- Reading the created product ---")
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
    print("\n--- Updating the product ---")
    result = models.execute_kw(
        DB, uid, PASSWORD,
        'product.product',
        'write',
        [[product_id], {'name': 'Updated Test Product API', 'list_price': 149.99, 'description': 'Updated via External API'}]
    )
    
    print(f"Update result: {result}")
    
    # READ AGAIN: Read the updated product
    print("\n--- Reading the updated product ---")
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
    print("\n--- Deleting the product ---")
    result = models.execute_kw(
        DB, uid, PASSWORD,
        'product.product',
        'unlink',
        [[product_id]]
    )
    
    print(f"Delete result: {result}")
    
    # VERIFY DELETION: Try to read the deleted product
    print("\n--- Verifying deletion ---")
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

def test_model_discovery(uid):
    """Test model discovery using ir.model and ir.model.fields."""
    print("\n=== Testing Model Discovery ===")
    
    # Connect to Odoo
    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)
    
    # Get model information
    print("\n--- Getting model information ---")
    model_info = models.execute_kw(
        DB, uid, PASSWORD,
        'ir.model',
        'search_read',
        [[['model', 'in', ['res.partner', 'product.product']]]],
        {'fields': ['name', 'model']}
    )
    
    print("Model information:")
    for model in model_info:
        print(f"  - {model['name']} ({model['model']})")
    
    # Get field information for res.partner
    print("\n--- Getting field information for res.partner ---")
    field_info = models.execute_kw(
        DB, uid, PASSWORD,
        'ir.model.fields',
        'search_read',
        [[['model_id.model', '=', 'res.partner'], ['name', 'in', ['name', 'email', 'phone']]]],
        {'fields': ['name', 'field_description', 'ttype']}
    )
    
    print("Field information for res.partner:")
    for field in field_info:
        print(f"  - {field['name']} ({field['ttype']}): {field['field_description']}")
    
    # Get field information for product.product
    print("\n--- Getting field information for product.product ---")
    field_info = models.execute_kw(
        DB, uid, PASSWORD,
        'ir.model.fields',
        'search_read',
        [[['model_id.model', '=', 'product.product'], ['name', 'in', ['name', 'default_code', 'list_price']]]],
        {'fields': ['name', 'field_description', 'ttype']}
    )
    
    print("Field information for product.product:")
    for field in field_info:
        print(f"  - {field['name']} ({field['ttype']}): {field['field_description']}")
    
    # Get all fields for a model using fields_get
    print("\n--- Getting all fields for res.partner using fields_get ---")
    fields = models.execute_kw(
        DB, uid, PASSWORD,
        'res.partner',
        'fields_get',
        [],
        {'attributes': ['string', 'help', 'type']}
    )
    
    print(f"Found {len(fields)} fields for res.partner")
    print("Sample fields:")
    for field_name in list(fields.keys())[:5]:  # Show first 5 fields
        field = fields[field_name]
        print(f"  - {field_name} ({field['type']}): {field['string']}")
        if 'help' in field and field['help']:
            print(f"    Help: {field['help']}")

def main():
    """Main function."""
    print("=== Odoo 18 External API Test ===")
    
    # Test connection
    uid = test_connection()
    
    # Test CRUD operations on res.partner
    test_partner_operations(uid)
    
    # Test CRUD operations on product.product
    test_product_operations(uid)
    
    # Test model discovery
    test_model_discovery(uid)
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    main()