#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dynamic Model Test Script

This script tests the dynamic model handling functionality of the Odoo 18 MCP integration.
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

def make_request(operation: str, model: str = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make a request to the MCP server.
    
    Args:
        operation: Operation type
        model: Odoo model name (optional for some operations)
        params: Operation parameters
        
    Returns:
        Dict[str, Any]: Response from the MCP server
    """
    data = {
        "operation": operation
    }
    
    if model:
        data["model"] = model
    
    if params:
        data["params"] = params
    
    try:
        response = requests.post(MCP_URL, headers=HEADERS, data=json.dumps(data))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {str(e)}")
        sys.exit(1)

def test_discover_models() -> None:
    """Test discovering available models."""
    print("\n=== Testing Model Discovery ===")
    
    # Discover all models
    response = make_request("discover_models")
    
    if response.get("success"):
        models = response.get("data")
        print(f"Found {len(models)} models")
        print("Sample models:")
        for model in models[:5]:  # Show first 5 models
            print(f"  - {model.get('name')} ({model.get('model')})")
    else:
        print(f"Model discovery failed: {response.get('error')}")
    
    # Discover models with filter
    print("\n--- Discovering models with filter ---")
    response = make_request("discover_models", params={"filter": "partner"})
    
    if response.get("success"):
        models = response.get("data")
        print(f"Found {len(models)} models matching 'partner'")
        for model in models:
            print(f"  - {model.get('name')} ({model.get('model')})")
    else:
        print(f"Model discovery with filter failed: {response.get('error')}")

def test_model_metadata(model_name: str) -> None:
    """Test getting model metadata.
    
    Args:
        model_name: Name of the model to test
    """
    print(f"\n=== Testing Model Metadata for {model_name} ===")
    
    response = make_request("model_metadata", model_name)
    
    if response.get("success"):
        metadata = response.get("data")
        if not metadata:
            print("No metadata returned")
            return
            
        # Print model info
        model_info = metadata.get("model")
        if model_info:
            print(f"Model: {model_info.get('name', 'Unknown')} ({model_info.get('model', 'Unknown')})")
        else:
            print("Model info not available")
        
        # Print field counts
        fields = metadata.get("fields", {})
        print(f"Total fields: {len(fields)}")
        
        # Print required fields
        required_fields = metadata.get("required_fields", [])
        if required_fields:
            print(f"Required fields: {', '.join(required_fields)}")
        else:
            print("No required fields")
        
        # Print readonly fields
        readonly_fields = metadata.get("readonly_fields", [])
        if readonly_fields:
            print(f"Readonly fields: {', '.join(readonly_fields[:5])}{'...' if len(readonly_fields) > 5 else ''}")
        else:
            print("No readonly fields")
        
        # Print relational fields
        relational_fields = metadata.get("relational_fields", {})
        print(f"Relational fields: {len(relational_fields)}")
        if relational_fields:
            for field, relation in list(relational_fields.items())[:3]:  # Show first 3
                print(f"  - {field} -> {relation}")
        
        # Print selection fields
        selection_fields = metadata.get("selection_fields", {})
        print(f"Selection fields: {len(selection_fields)}")
        if selection_fields:
            for field, options in list(selection_fields.items())[:3]:  # Show first 3
                print(f"  - {field}: {options}")
        
        # Print create fields
        create_fields = metadata.get("create_fields", [])
        if create_fields:
            print(f"Recommended create fields: {', '.join(create_fields[:5])}{'...' if len(create_fields) > 5 else ''}")
        else:
            print("No recommended create fields")
        
        # Print read fields
        read_fields = metadata.get("read_fields", [])
        if read_fields:
            print(f"Recommended read fields: {', '.join(read_fields[:5])}{'...' if len(read_fields) > 5 else ''}")
        else:
            print("No recommended read fields")
    else:
        print(f"Model metadata failed: {response.get('error')}")
        # Try a simpler approach
        print("\n--- Trying direct field discovery ---")
        fields_response = make_request("execute", model_name, {
            "method": "fields_get",
            "args": [],
            "kwargs": {"attributes": ["string", "type", "required"]}
        })
        
        if fields_response.get("success"):
            fields = fields_response.get("data")
            print(f"Found {len(fields)} fields using fields_get")
            print("Sample fields:")
            for field_name, field_info in list(fields.items())[:5]:  # Show first 5
                print(f"  - {field_name} ({field_info.get('type')}): {field_info.get('string')}")
                if field_info.get('required'):
                    print(f"    Required: {field_info.get('required')}")
        else:
            print(f"Direct field discovery failed: {fields_response.get('error')}")


def test_field_importance(model_name: str) -> None:
    """Test getting field importance.
    
    Args:
        model_name: Name of the model to test
    """
    print(f"\n=== Testing Field Importance for {model_name} ===")
    
    # Test basic field importance
    response = make_request("field_importance", model_name)
    
    if response.get("success"):
        importance = response.get("data")
        print("Field importance scores:")
        
        # Sort fields by importance
        sorted_fields = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        
        # Show top 10 most important fields
        print("Top 10 most important fields:")
        for field, score in sorted_fields[:10]:
            print(f"  - {field}: {score}")
        
        # Show 5 least important fields
        print("\nLeast important fields:")
        for field, score in sorted_fields[-5:]:
            print(f"  - {field}: {score}")
    else:
        print(f"Field importance failed: {response.get('error')}")
    
    # Test NLP-based field importance
    print("\n--- Testing NLP-based field importance ---")
    response = make_request("field_importance", model_name, {"use_nlp": True})
    
    if response.get("success"):
        importance = response.get("data")
        
        # Sort fields by importance
        sorted_fields = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        
        # Show top 10 most important fields
        print("Top 10 most important fields (NLP):")
        for field, score in sorted_fields[:10]:
            print(f"  - {field}: {score}")
    else:
        print(f"NLP field importance failed: {response.get('error')}")

def test_record_template(model_name: str) -> None:
    """Test getting a record template.
    
    Args:
        model_name: Name of the model to test
    """
    print(f"\n=== Testing Record Template for {model_name} ===")
    
    response = make_request("record_template", model_name)
    
    if response.get("success"):
        template = response.get("data")
        print(f"Record template with {len(template)} fields:")
        for field, value in template.items():
            print(f"  - {field}: {value}")
    else:
        print(f"Record template failed: {response.get('error')}")

def test_field_groups(model_name: str) -> None:
    """Test getting field groups.
    
    Args:
        model_name: Name of the model to test
    """
    print(f"\n=== Testing Field Groups for {model_name} ===")
    
    response = make_request("field_groups", model_name)
    
    if response.get("success"):
        groups = response.get("data")
        print(f"Found {len(groups)} field groups:")
        for group, fields in groups.items():
            print(f"  - {group}: {', '.join(fields[:3])}{'...' if len(fields) > 3 else ''}")
    else:
        print(f"Field groups failed: {response.get('error')}")

def test_search_fields(model_name: str) -> None:
    """Test getting search fields.
    
    Args:
        model_name: Name of the model to test
    """
    print(f"\n=== Testing Search Fields for {model_name} ===")
    
    response = make_request("search_fields", model_name)
    
    if response.get("success"):
        search_fields = response.get("data")
        print(f"Recommended search fields: {', '.join(search_fields)}")
    else:
        print(f"Search fields failed: {response.get('error')}")

def test_dynamic_crud(model_name: str) -> None:
    """Test dynamic CRUD operations.
    
    Args:
        model_name: Name of the model to test
    """
    print(f"\n=== Testing Dynamic CRUD for {model_name} ===")
    
    # Get record template
    template_response = make_request("record_template", model_name)
    
    if not template_response.get("success"):
        print(f"Failed to get record template: {template_response.get('error')}")
        return
    
    template = template_response.get("data")
    
    # Customize template for testing
    if model_name == "res.partner":
        template["name"] = "Dynamic Test Partner"
        template["email"] = "dynamic.test@example.com"
        template["phone"] = "+1234567890"
        template["is_company"] = True
        template["comment"] = "<p>Created via Dynamic Test</p>"
    elif model_name == "product.product":
        template["name"] = "Dynamic Test Product"
        template["default_code"] = "DYN-TEST-001"
        template["list_price"] = 199.99
        template["type"] = "consu"  # Valid values: 'consu', 'service', 'combo'
    
    # CREATE: Create a record
    print("\n--- Creating a record ---")
    create_response = make_request("dynamic_create", model_name, {"values": template})
    
    if not create_response.get("success"):
        print(f"Dynamic create failed: {create_response.get('error')}")
        return
    
    record_id = create_response.get("data")
    print(f"Created record with ID: {record_id}")
    
    # READ: Read the record
    print("\n--- Reading the record ---")
    read_response = make_request("dynamic_read", model_name, {
        "domain": [["id", "=", record_id]]
    })
    
    if not read_response.get("success"):
        print(f"Dynamic read failed: {read_response.get('error')}")
        return
    
    records = read_response.get("data")
    if not records:
        print("No record found with the given ID")
        return
    
    print("Record details:")
    record = records[0]
    for key, value in list(record.items())[:10]:  # Show first 10 fields
        print(f"  - {key}: {value}")
    
    # UPDATE: Update the record
    print("\n--- Updating the record ---")
    update_values = {}
    
    if model_name == "res.partner":
        update_values = {
            "name": "Updated Dynamic Test Partner",
            "comment": "<p>Updated via Dynamic Test</p>"
        }
    elif model_name == "product.product":
        update_values = {
            "name": "Updated Dynamic Test Product",
            "list_price": 249.99
        }
    
    update_response = make_request("dynamic_update", model_name, {
        "id": record_id,
        "values": update_values
    })
    
    if not update_response.get("success"):
        print(f"Dynamic update failed: {update_response.get('error')}")
        return
    
    print("Record updated successfully")
    
    # READ AGAIN: Read the updated record
    print("\n--- Reading the updated record ---")
    read_response = make_request("dynamic_read", model_name, {
        "domain": [["id", "=", record_id]]
    })
    
    if not read_response.get("success"):
        print(f"Dynamic read failed: {read_response.get('error')}")
        return
    
    records = read_response.get("data")
    if not records:
        print("No record found with the given ID")
        return
    
    print("Updated record details:")
    record = records[0]
    for key, value in list(record.items())[:10]:  # Show first 10 fields
        print(f"  - {key}: {value}")
    
    # DELETE: Delete the record
    print("\n--- Deleting the record ---")
    delete_response = make_request("dynamic_delete", model_name, {
        "id": record_id
    })
    
    if not delete_response.get("success"):
        print(f"Dynamic delete failed: {delete_response.get('error')}")
        return
    
    print("Record deleted successfully")
    
    # VERIFY DELETION: Try to read the deleted record
    print("\n--- Verifying deletion ---")
    read_response = make_request("dynamic_read", model_name, {
        "domain": [["id", "=", record_id]]
    })
    
    if not read_response.get("success"):
        print(f"Verification failed: {read_response.get('error')}")
        return
    
    records = read_response.get("data")
    if not records:
        print("Record successfully deleted (no records found)")
    else:
        print("Record still exists!")

def main() -> None:
    """Main function."""
    print("=== Dynamic Model Test ===")
    
    # Test model discovery
    test_discover_models()
    
    # Test with res.partner model
    test_model_metadata("res.partner")
    test_field_importance("res.partner")
    test_record_template("res.partner")
    test_field_groups("res.partner")
    test_search_fields("res.partner")
    test_dynamic_crud("res.partner")
    
    # Test with product.product model
    test_model_metadata("product.product")
    test_field_importance("product.product")
    test_record_template("product.product")
    test_field_groups("product.product")
    test_search_fields("product.product")
    test_dynamic_crud("product.product")
    
    print("\n=== Test completed successfully ===")

if __name__ == "__main__":
    main()