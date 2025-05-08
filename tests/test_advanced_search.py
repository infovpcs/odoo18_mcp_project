#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the advanced search functionality.

This script tests the advanced search implementation by executing
various natural language queries and displaying the results.
"""

import logging
import sys
from dotenv import load_dotenv
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_advanced_search")

# Import the necessary modules
from query_parser import QueryParser
from relationship_handler import RelationshipHandler
from advanced_search import AdvancedSearch

# Import the OdooModelDiscovery class from mcp_server.py
from mcp_server import OdooModelDiscovery

def main():
    """Main function to test the advanced search functionality."""
    # Load environment variables
    load_dotenv()
    
    # Get Odoo connection details from environment variables
    ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
    ODOO_DB = os.getenv("ODOO_DB", "llmdb18")
    ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
    ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")
    
    logger.info(f"Connecting to Odoo at {ODOO_URL}, database {ODOO_DB}")
    
    try:
        # Initialize Odoo model discovery
        model_discovery = OdooModelDiscovery(ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
        logger.info("Odoo model discovery initialized successfully")
        
        # Initialize advanced search
        advanced_search = AdvancedSearch(model_discovery)
        logger.info("Advanced search initialized successfully")
        
        # Test queries
        test_queries = [
            "List all sales orders under the customer's name, Gemini Furniture",
            "List all customer invoices for the customer name Wood Corner",
            "List out all projects",
            "List out all Project tasks for project name Research & Development",
            "List all unpaid bills with respect of vendor details",
            "List all project tasks according to their deadline date"
        ]
        
        # Execute each query and display the results
        for i, query in enumerate(test_queries):
            logger.info(f"Executing query {i+1}: {query}")
            
            try:
                # Execute the query
                result = advanced_search.execute_query(query)
                
                # Display the result
                print("\n" + "="*80)
                print(f"QUERY {i+1}: {query}")
                print("="*80)
                print(result)
                print("="*80 + "\n")
            except Exception as e:
                logger.error(f"Error executing query: {str(e)}")
                print(f"Error executing query: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error initializing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()