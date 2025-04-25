#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to check available fields in Odoo models.
"""

import logging
import sys
from dotenv import load_dotenv
import os
import xmlrpc.client

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("check_fields")

def main():
    """Main function to check fields in Odoo models."""
    # Load environment variables
    load_dotenv()
    
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
        
        # Models to check
        model_names = ["project.project", "project.task"]
        
        for model_name in model_names:
            logger.info(f"Checking fields for model: {model_name}")
            
            # Get fields for the model
            fields_data = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                model_name, 'fields_get',
                [], {'attributes': ['string', 'help', 'type']}
            )
            
            # Print field information
            print(f"\n{'='*80}")
            print(f"FIELDS FOR MODEL: {model_name}")
            print(f"{'='*80}")
            
            for field_name, field_info in sorted(fields_data.items()):
                field_type = field_info.get('type', 'unknown')
                field_string = field_info.get('string', 'No Label')
                print(f"{field_name:<30} | {field_type:<15} | {field_string}")
            
            print(f"{'='*80}\n")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()