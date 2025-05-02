#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Direct test script for the MCP server.
"""

import sys
import os
import json
import requests
import subprocess
from typing import Dict, Any, List, Optional

def test_odoo_connection():
    """Test the Odoo connection directly."""
    print("Testing Odoo connection directly...")
    
    try:
        # Run the test_odoo_connection.py script
        result = subprocess.run(
            [sys.executable, "test_odoo_connection.py"],
            capture_output=True,
            text=True
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Output: {result.stdout}")
        
        if result.returncode == 0:
            print("✅ Odoo connection test passed!")
            return True
        else:
            print(f"❌ Odoo connection test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error running Odoo connection test: {str(e)}")
        return False

def test_search_records():
    """Test the search_records function directly."""
    print("\nTesting search_records function directly...")
    
    try:
        # Import the function from mcp_server.py
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from mcp_server import search_records
        
        # Call the function
        result = search_records(model_name="res.partner", query="company")
        
        print(f"Result: {result[:500]}...")  # Show first 500 chars
        
        if "Search Results" in result:
            print("✅ search_records test passed!")
            return True
        else:
            print("❌ search_records test failed!")
            return False
    except Exception as e:
        print(f"❌ Error testing search_records: {str(e)}")
        return False

def test_advanced_search():
    """Test the advanced_search function directly."""
    print("\nTesting advanced_search function directly...")
    
    try:
        # Import the function from mcp_server.py
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from mcp_server import advanced_search
        
        # Call the function
        result = advanced_search(query="List all customers")
        
        print(f"Result: {result[:500]}...")  # Show first 500 chars
        
        if "Advanced Search Results" in result:
            print("✅ advanced_search test passed!")
            return True
        else:
            print("❌ advanced_search test failed!")
            return False
    except Exception as e:
        print(f"❌ Error testing advanced_search: {str(e)}")
        return False

def test_retrieve_odoo_documentation():
    """Test the retrieve_odoo_documentation function directly."""
    print("\nTesting retrieve_odoo_documentation function directly...")
    
    try:
        # Import the function from mcp_server.py
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from mcp_server import retrieve_odoo_documentation
        
        # Call the function
        result = retrieve_odoo_documentation(
            query="How to create a custom module in Odoo 18",
            max_results=2
        )
        
        print(f"Result: {result[:500]}...")  # Show first 500 chars
        
        if "Odoo Documentation" in result:
            print("✅ retrieve_odoo_documentation test passed!")
            return True
        else:
            print("❌ retrieve_odoo_documentation test failed!")
            return False
    except Exception as e:
        print(f"❌ Error testing retrieve_odoo_documentation: {str(e)}")
        return False

def test_export_records():
    """Test the export_records_to_csv function directly."""
    print("\nTesting export_records_to_csv function directly...")
    
    try:
        # Import the function from mcp_server.py
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from mcp_server import export_records_to_csv
        
        # Call the function
        result = export_records_to_csv(
            model_name="res.partner",
            fields=["id", "name", "email", "phone"],
            filter_domain=None,
            limit=10,
            export_path="./tmp/test_export.csv"
        )
        
        print(f"Result: {result}")
        
        if os.path.exists("./tmp/test_export.csv"):
            print("✅ export_records_to_csv test passed!")
            return True
        else:
            print("❌ export_records_to_csv test failed!")
            return False
    except Exception as e:
        print(f"❌ Error testing export_records_to_csv: {str(e)}")
        return False

def main():
    """Main function."""
    print("Testing MCP server functions directly...")
    
    # Test Odoo connection
    test_odoo_connection()
    
    # Test search_records
    test_search_records()
    
    # Test advanced_search
    test_advanced_search()
    
    # Test retrieve_odoo_documentation
    test_retrieve_odoo_documentation()
    
    # Test export_records
    test_export_records()
    
    print("\nTests completed!")

if __name__ == "__main__":
    main()