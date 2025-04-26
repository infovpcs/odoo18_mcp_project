#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for comparing the results of export_records_to_csv and advanced_search
for Gemini Furniture sales orders.
"""

import logging
import sys
import os
import json
import ast
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_gemini_furniture")

def main():
    """Main function to test the Gemini Furniture sales orders case."""

    # Load environment variables
    load_dotenv()

    # Get Odoo connection details from environment variables
    ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
    ODOO_DB = os.getenv("ODOO_DB", "llmdb18")
    ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
    ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

    logger.info(f"Connecting to Odoo at {ODOO_URL}, database {ODOO_DB}")

    # Import the necessary classes
    from mcp_server import OdooModelDiscovery
    from advanced_search import AdvancedSearch
    from direct_export_import import export_records

    # Initialize the model discovery
    model_discovery = OdooModelDiscovery(ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
    logger.info("Odoo model discovery initialized successfully")

    # Initialize the advanced search
    advanced_search = AdvancedSearch(model_discovery)
    logger.info("Advanced search initialized successfully")

    # Test 1: Export sales orders for Gemini Furniture
    logger.info("Test 1: Export sales orders for Gemini Furniture")

    # Create a temporary export file
    export_path = "./tmp/gemini_furniture_export_test.csv"
    os.makedirs("./tmp", exist_ok=True)

    # Export records using the direct export function
    filter_domain = [('partner_id', '=', 11)]  # Gemini Furniture ID
    export_result = export_records(
        model_name="sale.order",
        filter_domain=filter_domain,
        export_path=export_path
    )

    logger.info(f"Export result: {export_result}")
    logger.info(f"Total records from export: {export_result.get('total_records', 0)}")

    # Test 2: Advanced search for Gemini Furniture sales orders
    logger.info("Test 2: Advanced search for Gemini Furniture sales orders")

    query = "List all sales orders under the customer's name, Gemini Furniture"
    search_result = advanced_search.execute_query(query, limit=100)

    # Print the search result
    logger.info("Advanced search result excerpt:")
    excerpt = search_result.split("\n")[:20]
    logger.info("\n".join(excerpt))

    # Count the number of records in the search result
    record_count = search_result.count("**Related sale.order Records")
    logger.info(f"Advanced search found approximately {record_count} records")

    # Print a comparison
    logger.info("Comparison:")
    logger.info(f"Export records count: {export_result.get('total_records', 0)}")
    logger.info(f"Advanced search records count: {record_count}")

    # Test 3: Direct search using the Odoo API
    logger.info("Test 3: Direct search using the Odoo API")

    try:
        # Search for Gemini Furniture partner
        partner_records = model_discovery.models_proxy.execute_kw(
            model_discovery.db,
            model_discovery.uid,
            model_discovery.password,
            'res.partner',
            'search_read',
            [[("name", "=", "Gemini Furniture")]],
            {'fields': ['id', 'name']}
        )

        if partner_records:
            partner_id = partner_records[0]['id']
            logger.info(f"Found Gemini Furniture with ID: {partner_id}")

            # Search for all sales orders for this partner
            sale_orders = model_discovery.models_proxy.execute_kw(
                model_discovery.db,
                model_discovery.uid,
                model_discovery.password,
                'sale.order',
                'search_read',
                [[("partner_id", "=", partner_id)]],
                {'fields': ['id', 'name']}
            )

            logger.info(f"Direct API search found {len(sale_orders)} sales orders")
            logger.info(f"First few orders: {sale_orders[:5]}")
        else:
            logger.info("Gemini Furniture partner not found")
    except Exception as e:
        logger.error(f"Error in direct API search: {str(e)}")

if __name__ == "__main__":
    main()
