#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odoo 18 Client Test Script

This script demonstrates how to use the MCP client to perform CRUD operations
on res.partner and product.product models in Odoo 18.
"""

import json
import requests
import sys
from pprint import pprint
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# MCP Server configuration
MCP_HOST = os.getenv("MCP_HOST", "0.0.0.0")
MCP_PORT = os.getenv("MCP_PORT", "8000")
MCP_URL = f"http://{MCP_HOST}:{MCP_PORT}/api/v1/odoo"

# Headers for API requests
HEADERS = {
    "Content-Type": "application/json"
}

def make_request(operation, model, params=None, context=None):
    """Make a request to the MCP server.
    
    Args:
        operation: Operation to perform (create, read, update, delete)
        model: Odoo model name
        params: Operation parameters
        context: Operation context
        
    Returns:
        dict: Response data
    """
    if params is None:
        params = {}
    if context is None:
        context = {}
        
    data = {
        "operation": operation,
        "model": model,
        "params": params,
        "context": context
    }
    
    response = requests.post(MCP_URL, headers=HEADERS, data=json.dumps(data))
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None
        
    return response.json()

def test_partner_crud():
    """Test CRUD operations on res.partner."""
    print("\n=== Testing CRUD operations on res.partner ===\n")
    
    # CREATE: Create a new partner
    print("Creating a new partner...")
    create_params = {
        "values": {
            "name": "Test Partner MCP",
            "email": "test.partner@example.com",
            "phone": "+1234567890",
            "is_company": True
        }
    }
    create_response = make_request("create", "res.partner", create_params)
    
    if not create_response or not create_response.get("success"):
        print("Failed to create partner")
        print(create_response)
        return
        
    partner_id = create_response["data"]["id"]
    print(f"Partner created with ID: {partner_id}")
    
    # READ: Read the created partner
    print("\nReading the created partner...")
    read_params = {
        "domain": [["id", "=", partner_id]],
        "limit": 1
    }
    read_response = make_request("read", "res.partner", read_params)
    
    if not read_response or not read_response.get("success"):
        print("Failed to read partner")
        print(read_response)
        return
        
    print("Partner details:")
    pprint(read_response["data"]["records"][0])
    
    # UPDATE: Update the partner
    print("\nUpdating the partner...")
    update_params = {
        "id": partner_id,
        "values": {
            "name": "Updated Test Partner MCP",
            "comment": "This partner was updated via MCP"
        }
    }
    update_response = make_request("update", "res.partner", update_params)
    
    if not update_response or not update_response.get("success"):
        print("Failed to update partner")
        print(update_response)
        return
        
    print(f"Partner updated: {update_response['success']}")
    
    # READ AGAIN: Read the updated partner
    print("\nReading the updated partner...")
    read_response = make_request("read", "res.partner", read_params)
    
    if not read_response or not read_response.get("success"):
        print("Failed to read updated partner")
        print(read_response)
        return
        
    print("Updated partner details:")
    pprint(read_response["data"]["records"][0])
    
    # DELETE: Delete the partner
    print("\nDeleting the partner...")
    delete_params = {
        "ids": [partner_id]
    }
    delete_response = make_request("delete", "res.partner", delete_params)
    
    if not delete_response or not delete_response.get("success"):
        print("Failed to delete partner")
        print(delete_response)
        return
        
    print(f"Partner deleted: {delete_response['success']}")
    
    # VERIFY DELETION: Try to read the deleted partner
    print("\nVerifying deletion...")
    read_response = make_request("read", "res.partner", read_params)
    
    if not read_response or not read_response.get("success"):
        print("Failed to verify deletion")
        print(read_response)
        return
        
    if not read_response["data"]["records"]:
        print("Partner successfully deleted (no records found)")
    else:
        print("Partner still exists!")
        pprint(read_response["data"]["records"][0])

def test_product_crud():
    """Test CRUD operations on product.product."""
    print("\n=== Testing CRUD operations on product.product ===\n")
    
    # CREATE: Create a new product
    print("Creating a new product...")
    create_params = {
        "values": {
            "name": "Test Product MCP",
            "default_code": "TEST-MCP-001",
            "list_price": 99.99,
            "type": "consu",  # Valid values: 'consu', 'service', 'combo'
            "description": "This is a test product created via MCP"
        }
    }
    create_response = make_request("create", "product.product", create_params)
    
    if not create_response or not create_response.get("success"):
        print("Failed to create product")
        print(create_response)
        return
        
    product_id = create_response["data"]["id"]
    print(f"Product created with ID: {product_id}")
    
    # READ: Read the created product
    print("\nReading the created product...")
    read_params = {
        "domain": [["id", "=", product_id]],
        "limit": 1
    }
    read_response = make_request("read", "product.product", read_params)
    
    if not read_response or not read_response.get("success"):
        print("Failed to read product")
        print(read_response)
        return
        
    print("Product details:")
    pprint(read_response["data"]["records"][0])
    
    # UPDATE: Update the product
    print("\nUpdating the product...")
    update_params = {
        "id": product_id,
        "values": {
            "name": "Updated Test Product MCP",
            "list_price": 149.99,
            "description": "This product was updated via MCP"
        }
    }
    update_response = make_request("update", "product.product", update_params)
    
    if not update_response or not update_response.get("success"):
        print("Failed to update product")
        print(update_response)
        return
        
    print(f"Product updated: {update_response['success']}")
    
    # READ AGAIN: Read the updated product
    print("\nReading the updated product...")
    read_response = make_request("read", "product.product", read_params)
    
    if not read_response or not read_response.get("success"):
        print("Failed to read updated product")
        print(read_response)
        return
        
    print("Updated product details:")
    pprint(read_response["data"]["records"][0])
    
    # DELETE: Delete the product
    print("\nDeleting the product...")
    delete_params = {
        "ids": [product_id]
    }
    delete_response = make_request("delete", "product.product", delete_params)
    
    if not delete_response or not delete_response.get("success"):
        print("Failed to delete product")
        print(delete_response)
        return
        
    print(f"Product deleted: {delete_response['success']}")
    
    # VERIFY DELETION: Try to read the deleted product
    print("\nVerifying deletion...")
    read_response = make_request("read", "product.product", read_params)
    
    if not read_response or not read_response.get("success"):
        print("Failed to verify deletion")
        print(read_response)
        return
        
    if not read_response["data"]["records"]:
        print("Product successfully deleted (no records found)")
    else:
        print("Product still exists!")
        pprint(read_response["data"]["records"][0])

def get_model_info(model_name):
    """Get model information using ir.model.
    
    Args:
        model_name: Technical name of the model
        
    Returns:
        dict: Model information
    """
    print(f"\n=== Getting information for model: {model_name} ===\n")
    
    # Search for the model
    search_params = {
        "domain": [["model", "=", model_name]],
        "limit": 1
    }
    search_response = make_request("read", "ir.model", search_params)
    
    if not search_response or not search_response.get("success") or not search_response["data"]["records"]:
        print(f"Model {model_name} not found")
        return None
        
    model_info = search_response["data"]["records"][0]
    print(f"Model name: {model_info['name']}")
    print(f"Model description: {model_info.get('description', 'N/A')}")
    
    # Get model fields
    fields_params = {
        "domain": [["model_id.model", "=", model_name]],
        "limit": 100
    }
    fields_response = make_request("read", "ir.model.fields", fields_params)
    
    if not fields_response or not fields_response.get("success"):
        print("Failed to get model fields")
        return model_info
        
    print(f"\nFields for model {model_name}:")
    for field in fields_response["data"]["records"]:
        print(f"  - {field['name']} ({field['ttype']}): {field['field_description']}")
    
    return model_info

def main():
    """Main function."""
    print("=== Odoo 18 Client Test ===")
    
    # Test connection
    print("\nTesting connection to MCP server...")
    test_response = make_request("execute", "res.partner", {
        "method": "search",
        "args": [[["id", ">", 0]]],
        "kwargs": {"limit": 1}
    })
    
    if not test_response or not test_response.get("success"):
        print("Failed to connect to MCP server")
        sys.exit(1)
        
    print("Connection successful!")
    
    # Get model information
    get_model_info("res.partner")
    get_model_info("product.product")
    
    # Test CRUD operations
    test_partner_crud()
    test_product_crud()
    
    print("\n=== Test completed ===")

if __name__ == "__main__":
    main()