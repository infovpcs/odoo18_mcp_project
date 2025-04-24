#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import xmlrpc.client
import os
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# Get Odoo connection details from environment variables
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "llmdb18")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

def test_odoo_connection():
    """Test connection to Odoo server"""
    print(f"Testing connection to Odoo at {ODOO_URL}")
    print(f"Database: {ODOO_DB}")
    print(f"Username: {ODOO_USERNAME}")
    print(f"Password: {'*' * len(ODOO_PASSWORD)}")
    
    try:
        # Connect to Odoo
        print("\nStep 1: Connecting to common endpoint...")
        common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
        
        # Get server info
        print("\nStep 2: Getting server info...")
        server_info = common.version()
        print(f"Server info: {server_info}")
        
        # Authenticate
        print("\nStep 3: Authenticating...")
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if not uid:
            print("Authentication failed. Please check your credentials.")
            return False
            
        print(f"Authentication successful. User ID: {uid}")
        
        # Connect to object endpoint
        print("\nStep 4: Connecting to object endpoint...")
        models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
        
        # Test a simple call
        print("\nStep 5: Testing a simple call (listing res.partner records)...")
        partner_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'res.partner', 'search',
            [[]], {'limit': 5}
        )
        
        print(f"Found {len(partner_ids)} partner IDs: {partner_ids}")
        
        # Get partner details
        if partner_ids:
            print("\nStep 6: Getting details for the first partner...")
            partners = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'res.partner', 'read',
                [partner_ids], {'fields': ['name', 'email', 'phone']}
            )
            
            for partner in partners:
                print(f"Partner: {partner}")
        
        print("\nConnection test completed successfully!")
        return True
        
    except xmlrpc.client.Fault as e:
        print(f"XML-RPC Fault: {e.faultCode} - {e.faultString}")
        return False
    except ConnectionRefusedError:
        print(f"Connection refused. Is the Odoo server running at {ODOO_URL}?")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_odoo_connection()
    sys.exit(0 if success else 1)