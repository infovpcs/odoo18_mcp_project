#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Odoo 18 MCP Client Test

This script performs comprehensive testing of the Odoo 18 MCP integration,
including CRUD operations, model discovery, and custom method execution.
"""

import json
import sys
import time
import requests
from pprint import pprint
from typing import Dict, Any, List, Optional, Union

# MCP server configuration
MCP_URL = "http://localhost:8000/api/v1/odoo"
HEADERS = {
    "Content-Type": "application/json"
}

def make_request(operation: str, model: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Make a request to the MCP server.
    
    Args:
        operation: Operation type (read, create, update, delete, execute)
        model: Odoo model name
        params: Operation parameters
        
    Returns:
        Dict[str, Any]: Response from the MCP server
    """
    data = {
        "operation": operation,
        "model": model,
        "params": params
    }
    
    try:
        response = requests.post(MCP_URL, headers=HEADERS, data=json.dumps(data))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {str(e)}")
        sys.exit(1)

def test_connection() -> None:
    """Test connection to the MCP server."""
    print("\n=== Testing Connection ===")
    
    # Simple read operation to test connection
    response = make_request("execute", "res.partner", {
        "method": "search_count",
        "args": [[["active", "=", True]]],
        "kwargs": {}
    })
    
    if response.get("success"):
        count = response.get("data")
        print(f"Connection successful! Found {count} active partners.")
    else:
        print(f"Connection failed: {response.get('error')}")
        sys.exit(1)

def test_model_discovery() -> None:
    """Test model discovery using ir.model."""
    print("\n=== Testing Model Discovery ===")
    
    # Get information about res.partner and product.product models
    response = make_request("read", "ir.model", {
        "domain": [[
            "model", "in", ["res.partner", "product.product"]
        ]],
        "fields": ["name", "model", "info"]
    })
    
    if response.get("success"):
        models = response.get("data")
        print(f"Found {len(models)} models:")
        for model in models:
            # Handle the case where model might be a string or a dictionary
            if isinstance(model, dict):
                print(f"  - {model.get('name')} ({model.get('model')})")
                if model.get("info"):
                    print(f"    Info: {model.get('info')}")
            else:
                print(f"  - {model}")
    else:
        print(f"Model discovery failed: {response.get('error')}")
        
    # Alternative approach: use execute method to get model info
    print("\n--- Using execute method for model discovery ---")
    response = make_request("execute", "ir.model", {
        "method": "search_read",
        "args": [[["model", "in", ["res.partner", "product.product"]]]],
        "kwargs": {"fields": ["name", "model"]}
    })
    
    if response.get("success"):
        models = response.get("data")
        print(f"Found {len(models)} models using execute method:")
        for model in models:
            print(f"  - {model.get('name')} ({model.get('model')})")
    else:
        print(f"Model discovery failed: {response.get('error')}")


def test_field_discovery() -> None:
    """Test field discovery using ir.model.fields."""
    print("\n=== Testing Field Discovery ===")
    
    # Use execute method for field discovery
    print("\n--- Using execute method for field discovery ---")
    
    # Get fields for res.partner
    response = make_request("execute", "ir.model.fields", {
        "method": "search_read",
        "args": [[
            ["model_id.model", "=", "res.partner"],
            ["name", "in", ["name", "email", "phone"]]
        ]],
        "kwargs": {"fields": ["name", "field_description", "ttype"]}
    })
    
    if response.get("success"):
        fields = response.get("data")
        print(f"Found {len(fields)} fields for res.partner:")
        for field in fields:
            print(f"  - {field.get('name')} ({field.get('ttype')}): {field.get('field_description')}")
    else:
        print(f"Field discovery failed: {response.get('error')}")
    
    # Get fields for product.product
    response = make_request("execute", "ir.model.fields", {
        "method": "search_read",
        "args": [[
            ["model_id.model", "=", "product.product"],
            ["name", "in", ["name", "default_code", "list_price", "type"]]
        ]],
        "kwargs": {"fields": ["name", "field_description", "ttype"]}
    })
    
    if response.get("success"):
        fields = response.get("data")
        print(f"\nFound {len(fields)} fields for product.product:")
        for field in fields:
            print(f"  - {field.get('name')} ({field.get('ttype')}): {field.get('field_description')}")
    else:
        print(f"Field discovery failed: {response.get('error')}")
        
    # Alternative approach: use fields_get method
    print("\n--- Using fields_get method ---")
    
    # Get fields for res.partner
    response = make_request("execute", "res.partner", {
        "method": "fields_get",
        "args": [["name", "email", "phone"]],
        "kwargs": {"attributes": ["string", "type"]}
    })
    
    if response.get("success"):
        fields = response.get("data")
        print(f"Found {len(fields)} fields for res.partner using fields_get:")
        for field_name, field_info in fields.items():
            print(f"  - {field_name} ({field_info.get('type')}): {field_info.get('string')}")
    else:
        print(f"Field discovery failed: {response.get('error')}")
        
    # Get fields for product.product
    response = make_request("execute", "product.product", {
        "method": "fields_get",
        "args": [["name", "default_code", "list_price", "type"]],
        "kwargs": {"attributes": ["string", "type"]}
    })
    
    if response.get("success"):
        fields = response.get("data")
        print(f"\nFound {len(fields)} fields for product.product using fields_get:")
        for field_name, field_info in fields.items():
            print(f"  - {field_name} ({field_info.get('type')}): {field_info.get('string')}")
    else:
        print(f"Field discovery failed: {response.get('error')}")


def test_custom_method_execution() -> None:
    """Test custom method execution."""
    print("\n=== Testing Custom Method Execution ===")
    
    # Get all fields for res.partner using fields_get method
    response = make_request("execute", "res.partner", {
        "method": "fields_get",
        "args": [],
        "kwargs": {"attributes": ["string", "help", "type"]}
    })
    
    if response.get("success"):
        fields = response.get("data")
        print(f"Successfully retrieved {len(fields)} fields using fields_get method")
        print("Sample fields:")
        for field_name in list(fields.keys())[:5]:  # Show first 5 fields
            field = fields[field_name]
            print(f"  - {field_name} ({field['type']}): {field['string']}")
            if 'help' in field and field['help']:
                print(f"    Help: {field['help']}")
    else:
        print(f"Custom method execution failed: {response.get('error')}")

def test_partner_crud() -> None:
    """Test CRUD operations on res.partner."""
    print("\n=== Testing CRUD Operations on res.partner ===")
    
    # CREATE: Create a new partner
    print("\n--- Creating a new partner ---")
    create_response = make_request("create", "res.partner", {
        "values": {
            "name": "Advanced Test Partner",
            "email": "advanced.test@example.com",
            "phone": "+1234567890",
            "is_company": True,
            "comment": "<p>Created via Advanced MCP Test</p>"
        }
    })
    
    if not create_response.get("success"):
        print(f"Partner creation failed: {create_response.get('error')}")
        return
    
    # Extract the partner ID from the response
    partner_id = create_response.get("data")
    if isinstance(partner_id, dict) and 'id' in partner_id:
        partner_id = partner_id['id']
    print(f"Created partner with ID: {partner_id}")
    
    # READ: Read the created partner using execute method
    print("\n--- Reading the created partner ---")
    read_response = make_request("execute", "res.partner", {
        "method": "search_read",
        "args": [[["id", "=", partner_id]]],
        "kwargs": {"fields": ["name", "email", "phone", "is_company", "comment"]}
    })
    
    if not read_response.get("success"):
        print(f"Partner read failed: {read_response.get('error')}")
        return
    
    partners = read_response.get("data")
    if not partners:
        print("No partner found with the given ID")
        return
    
    print("Partner details:")
    partner = partners[0]
    for key, value in partner.items():
        if key not in ["id", "display_name"]:
            print(f"  - {key}: {value}")
    
    # UPDATE: Update the partner
    print("\n--- Updating the partner ---")
    update_response = make_request("update", "res.partner", {
        "id": partner_id,
        "values": {
            "name": "Updated Advanced Test Partner",
            "comment": "<p>Updated via Advanced MCP Test</p>"
        }
    })
    
    if not update_response.get("success"):
        print(f"Partner update failed: {update_response.get('error')}")
        return
    
    print("Partner updated successfully")
    
    # READ AGAIN: Read the updated partner
    print("\n--- Reading the updated partner ---")
    read_response = make_request("execute", "res.partner", {
        "method": "search_read",
        "args": [[["id", "=", partner_id]]],
        "kwargs": {"fields": ["name", "email", "phone", "is_company", "comment"]}
    })
    
    if not read_response.get("success"):
        print(f"Partner read failed: {read_response.get('error')}")
        return
    
    partners = read_response.get("data")
    if not partners:
        print("No partner found with the given ID")
        return
    
    print("Updated partner details:")
    partner = partners[0]
    for key, value in partner.items():
        if key not in ["id", "display_name"]:
            print(f"  - {key}: {value}")
    
    # DELETE: Delete the partner
    print("\n--- Deleting the partner ---")
    delete_response = make_request("delete", "res.partner", {
        "ids": [partner_id]
    })
    
    if not delete_response.get("success"):
        print(f"Partner deletion failed: {delete_response.get('error')}")
        return
    
    print("Partner deleted successfully")
    
    # VERIFY DELETION: Try to read the deleted partner
    print("\n--- Verifying deletion ---")
    read_response = make_request("execute", "res.partner", {
        "method": "search_read",
        "args": [[["id", "=", partner_id]]],
        "kwargs": {"fields": ["name"]}
    })
    
    if not read_response.get("success"):
        print(f"Verification failed: {read_response.get('error')}")
        return
    
    partners = read_response.get("data")
    if not partners:
        print("Partner successfully deleted (no records found)")
    else:
        print("Partner still exists!")

def test_product_crud() -> None:
    """Test CRUD operations on product.product."""
    print("\n=== Testing CRUD Operations on product.product ===")
    
    # Get a product category using execute method
    print("\n--- Getting a product category ---")
    category_response = make_request("execute", "product.category", {
        "method": "search_read",
        "args": [[["name", "=", "All"]]],
        "kwargs": {"fields": ["id"], "limit": 1}
    })
    
    if not category_response.get("success"):
        print(f"Category retrieval failed: {category_response.get('error')}")
        return
    
    categories = category_response.get("data")
    if not categories or len(categories) == 0:
        print("No product category found")
        return
    
    category_id = categories[0].get("id")
    print(f"Using category ID: {category_id}")
    
    # CREATE: Create a new product
    print("\n--- Creating a new product ---")
    create_response = make_request("create", "product.product", {
        "values": {
            "name": "Advanced Test Product",
            "default_code": "ADV-TEST-001",
            "list_price": 149.99,
            "type": "consu",  # Valid values: 'consu', 'service', 'combo'
            "categ_id": category_id,
            "description": "<p>Created via Advanced MCP Test</p>"
        }
    })
    
    if not create_response.get("success"):
        print(f"Product creation failed: {create_response.get('error')}")
        return
    
    product_id = create_response.get("data")
    if isinstance(product_id, dict) and 'id' in product_id:
        product_id = product_id['id']
    print(f"Created product with ID: {product_id}")
    
    # READ: Read the created product
    print("\n--- Reading the created product ---")
    read_response = make_request("execute", "product.product", {
        "method": "search_read",
        "args": [[["id", "=", product_id]]],
        "kwargs": {"fields": ["name", "default_code", "list_price", "type", "categ_id", "description"]}
    })
    
    if not read_response.get("success"):
        print(f"Product read failed: {read_response.get('error')}")
        return
    
    products = read_response.get("data")
    if not products:
        print("No product found with the given ID")
        return
    
    print("Product details:")
    product = products[0]
    for key, value in product.items():
        if key not in ["id", "display_name"]:
            print(f"  - {key}: {value}")
    
    # UPDATE: Update the product
    print("\n--- Updating the product ---")
    update_response = make_request("update", "product.product", {
        "id": product_id,
        "values": {
            "name": "Updated Advanced Test Product",
            "list_price": 199.99,
            "description": "<p>Updated via Advanced MCP Test</p>"
        }
    })
    
    if not update_response.get("success"):
        print(f"Product update failed: {update_response.get('error')}")
        return
    
    print("Product updated successfully")
    
    # READ AGAIN: Read the updated product
    print("\n--- Reading the updated product ---")
    read_response = make_request("execute", "product.product", {
        "method": "search_read",
        "args": [[["id", "=", product_id]]],
        "kwargs": {"fields": ["name", "default_code", "list_price", "type", "categ_id", "description"]}
    })
    
    if not read_response.get("success"):
        print(f"Product read failed: {read_response.get('error')}")
        return
    
    products = read_response.get("data")
    if not products:
        print("No product found with the given ID")
        return
    
    print("Updated product details:")
    product = products[0]
    for key, value in product.items():
        if key not in ["id", "display_name"]:
            print(f"  - {key}: {value}")
    
    # DELETE: Delete the product
    print("\n--- Deleting the product ---")
    delete_response = make_request("delete", "product.product", {
        "ids": [product_id]
    })
    
    if not delete_response.get("success"):
        print(f"Product deletion failed: {delete_response.get('error')}")
        return
    
    print("Product deleted successfully")
    
    # VERIFY DELETION: Try to read the deleted product
    print("\n--- Verifying deletion ---")
    read_response = make_request("execute", "product.product", {
        "method": "search_read",
        "args": [[["id", "=", product_id]]],
        "kwargs": {"fields": ["name"]}
    })
    
    if not read_response.get("success"):
        print(f"Verification failed: {read_response.get('error')}")
        return
    
    products = read_response.get("data")
    if not products:
        print("Product successfully deleted (no records found)")
    else:
        print("Product still exists!")

def main() -> None:
    """Main function."""
    print("=== Advanced Odoo 18 MCP Client Test ===")
    
    # Test connection
    test_connection()
    
    # Test model discovery
    test_model_discovery()
    
    # Test field discovery
    test_field_discovery()
    
    # Test custom method execution
    test_custom_method_execution()
    
    # Test CRUD operations on res.partner
    test_partner_crud()
    
    # Test CRUD operations on product.product
    test_product_crud()
    
    print("\n=== Test completed successfully ===")

if __name__ == "__main__":
    main()