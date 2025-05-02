#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to check available fields in Odoo models.
"""

import logging
import sys
import os
import argparse
import xmlrpc.client
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("check_fields")

def main():
    """Main function to check fields in Odoo models."""
    # Load environment variables
    load_dotenv()
    
    # Parse CLI args for model names
    parser = argparse.ArgumentParser(description="Check Odoo model fields via XML-RPC")
    parser.add_argument('--required', action='store_true', help='Only list required fields')
    parser.add_argument('models', nargs='+', help='Odoo model technical names to inspect')
    args = parser.parse_args()
    required_only = args.required
    model_names = args.models
    
    # Get Odoo connection details from environment variables
    ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
    ODOO_DB = os.getenv("ODOO_DB", "llmdb18")
    ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
    ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")
    
    logger.info(f"Connecting to Odoo at {ODOO_URL}, database {ODOO_DB}")
    
    try:
        # Connect to Odoo
        common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
        uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})
        
        if not uid:
            logger.error("Authentication failed")
            sys.exit(1)
        
        logger.info(f"Connected to Odoo as user ID {uid}")
        
        # Connect to the models API
        models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
        
        # Inspect each requested model via ir.model.fields
        for model_name in model_names:
            logger.info(f"Checking fields for model: {model_name}")
            # Fetch field definitions from ir.model.fields
            fields = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'ir.model.fields', 'search_read',
                [[('model', '=', model_name)]],
                {'fields': ['name', 'ttype', 'field_description', 'required', 'help'], 'order': 'name'}
            )
            print(f"\n{'='*80}")
            print(f"FIELDS FOR MODEL: {model_name}")
            print(f"{'='*80}")
            for f in fields:
                # Skip non-required if filter enabled
                if required_only and not f['required']:
                    continue
                print(f"{f['name']:<30} | {f['ttype']:<10} | {f['field_description']:<30} | Required: {f['required']} | Help: {f.get('help','')}")
            print(f"{'='*80}\n")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()