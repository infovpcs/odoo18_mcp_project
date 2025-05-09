#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for AdvancedSearch class.
"""

import logging
import sys
import os
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Try to import AdvancedSearch
    logger.info("Attempting to import AdvancedSearch...")
    try:
        from advanced_search import AdvancedSearch
        logger.info("Successfully imported AdvancedSearch from root directory")
    except ImportError as e:
        logger.error(f"Failed to import AdvancedSearch from root directory: {str(e)}")
        try:
            from src.odoo.dynamic.advanced_search import AdvancedSearch
            logger.info("Successfully imported AdvancedSearch from src.odoo.dynamic.advanced_search")
        except ImportError as e2:
            logger.error(f"Failed to import AdvancedSearch from src.odoo.dynamic.advanced_search: {str(e2)}")
            sys.exit(1)

    # Try to import ModelDiscovery
    logger.info("Attempting to import ModelDiscovery...")
    try:
        from src.odoo.dynamic.model_discovery import ModelDiscovery
        logger.info("Successfully imported ModelDiscovery")
    except ImportError as e:
        logger.error(f"Failed to import ModelDiscovery: {str(e)}")
        sys.exit(1)

    # Try to import OdooClient
    logger.info("Attempting to import OdooClient...")
    try:
        from src.odoo.client import OdooClient
        from src.odoo.schemas import OdooConfig
        logger.info("Successfully imported OdooClient")
    except ImportError as e:
        logger.error(f"Failed to import OdooClient: {str(e)}")
        sys.exit(1)

    # Initialize OdooClient
    logger.info("Initializing OdooClient...")
    try:
        config = OdooConfig(
            url="http://localhost:8069",
            db=os.getenv("ODOO_DB", "llmdb18"),
            username=os.getenv("ODOO_USERNAME", "admin"),
            password=os.getenv("ODOO_PASSWORD", "admin")
        )
        odoo_client = OdooClient(config)
        logger.info("Successfully initialized OdooClient")
    except Exception as e:
        logger.error(f"Failed to initialize OdooClient: {str(e)}")
        sys.exit(1)

    # Initialize ModelDiscovery
    logger.info("Initializing ModelDiscovery...")
    try:
        model_discovery = ModelDiscovery(odoo_client)
        logger.info("Successfully initialized ModelDiscovery")
    except Exception as e:
        logger.error(f"Failed to initialize ModelDiscovery: {str(e)}")
        sys.exit(1)

    # Initialize AdvancedSearch
    logger.info("Initializing AdvancedSearch...")
    try:
        advanced_search = AdvancedSearch(model_discovery)
        logger.info("Successfully initialized AdvancedSearch")
    except Exception as e:
        logger.error(f"Failed to initialize AdvancedSearch: {str(e)}")
        sys.exit(1)

    # Test AdvancedSearch
    logger.info("Testing AdvancedSearch...")
    try:
        search_query = "Get sample data for CRM leads"
        logger.info(f"Using search query: {search_query}")
        search_results = advanced_search.search(search_query, limit=5)
        logger.info(f"Search results: {search_results}")
    except Exception as e:
        logger.error(f"Failed to execute search: {str(e)}")
        sys.exit(1)

    logger.info("Test completed successfully")

except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    sys.exit(1)
