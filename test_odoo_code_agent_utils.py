#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the Odoo Code Agent utilities.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_odoo_code_agent_utils")

# Load environment variables
load_dotenv()

# Import the utilities
try:
    from src.odoo_code_agent.utils import documentation_helper, odoo_connector
except ImportError:
    logger.error("Failed to import Odoo Code Agent utilities. Make sure the package is installed.")
    sys.exit(1)


def test_documentation_helper():
    """Test the documentation helper."""
    logger.info("Testing documentation helper...")

    # Test querying documentation
    query = "Odoo 18 module structure"
    result = documentation_helper.get_formatted_results(query, max_results=2)

    logger.info(f"Query: {query}")
    logger.info(f"Result: {result[:200]}...")  # Show first 200 chars

    # Test getting model documentation
    model_name = "res.partner"
    result = documentation_helper.get_model_documentation(model_name)

    logger.info(f"Model documentation for {model_name}")
    logger.info(f"Result: {result[:200]}...")  # Show first 200 chars

    logger.info("Documentation helper test completed")


def test_odoo_connector():
    """Test the Odoo connector."""
    logger.info("Testing Odoo connector...")

    try:
        # Test getting models list - fix the fields to match Odoo 18
        models = odoo_connector.search_read(
            'ir.model',
            [('state', '=', 'base')],
            ['name', 'model', 'info', 'modules']
        )
        logger.info(f"Found {len(models)} models")

        if models:
            # Show first 5 models
            for i, model in enumerate(models[:5]):
                logger.info(f"Model {i+1}: {model['model']} - {model['name']}")

        # Test getting model fields
        model_name = "res.partner"
        fields = odoo_connector.get_model_fields(model_name)
        logger.info(f"Found {len(fields)} fields for model {model_name}")

        if fields:
            # Show first 5 fields
            for i, (field_name, field_info) in enumerate(list(fields.items())[:5]):
                logger.info(f"Field {i+1}: {field_name} - {field_info.get('type')} - {field_info.get('string')}")

        # Test getting field groups
        field_groups = odoo_connector.get_field_groups(model_name)
        logger.info(f"Field groups for model {model_name}:")

        for field_type, field_names in field_groups.items():
            logger.info(f"  {field_type}: {len(field_names)} fields")

        # Test getting record template
        template = odoo_connector.get_record_template(model_name)
        logger.info(f"Record template for model {model_name} has {len(template)} fields")

        logger.info("Odoo connector test completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error testing Odoo connector: {str(e)}")
        return False


def main():
    """Main function."""
    logger.info("Testing Odoo Code Agent utilities")

    # Test documentation helper
    test_documentation_helper()

    # Test Odoo connector
    test_odoo_connector()

    logger.info("All tests completed")


if __name__ == "__main__":
    main()
