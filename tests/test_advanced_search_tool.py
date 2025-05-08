#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the advanced search functionality.
"""

import logging
import sys
import os
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_advanced_search_tool")

# Import the OdooModelDiscovery class
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from advanced_search import AdvancedSearch

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

    # Import the OdooModelDiscovery class
    from mcp_server import OdooModelDiscovery

    # Initialize the model discovery
    model_discovery = OdooModelDiscovery(ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
    logger.info("Odoo model discovery initialized successfully")

    # Initialize the advanced search
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

    for i, query in enumerate(test_queries):
        logger.info(f"Testing query {i+1}: {query}")

        try:
            # Execute the query
            result = advanced_search.execute_query(query, limit=10)

            # Print a short excerpt of the result
            excerpt = result.split("\n")[:10]
            logger.info("Result excerpt:\n" + "\n".join(excerpt) + "\n...")

        except Exception as e:
            logger.error(f"Error testing query {i+1}: {str(e)}")

if __name__ == "__main__":
    main()