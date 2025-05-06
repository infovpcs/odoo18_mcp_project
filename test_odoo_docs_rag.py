#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the Odoo Documentation RAG module.

This script tests the functionality of the Odoo Documentation RAG module
by initializing the retriever and performing a few test queries.
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_odoo_docs_rag")

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the Odoo Documentation RAG module
    from src.odoo_docs_rag import OdooDocsRetriever

    def test_odoo_docs_retriever():
        """Test the Odoo Documentation RAG module."""
        logger.info("Testing Odoo Documentation RAG module...")

        # Set up directories
        docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "odoo_docs")
        index_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "odoo_docs_index")

        # Create directories if they don't exist
        os.makedirs(docs_dir, exist_ok=True)
        os.makedirs(index_dir, exist_ok=True)

        # Check if the required dependencies are available
        try:
            import sentence_transformers
            import faiss
            import bs4
            import markdown
            import git
            logger.info("All required dependencies for Odoo documentation retriever are available")
        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            logger.error("Please install the required dependencies: sentence-transformers, faiss-cpu, beautifulsoup4, markdown, gitpython")
            return

        # Initialize the retriever
        logger.info("Initializing Odoo Documentation Retriever...")
        try:
            retriever = OdooDocsRetriever(
                docs_dir=docs_dir,
                index_dir=index_dir,
                force_rebuild=True  # Force rebuilding the index with our improved implementation
            )
        except Exception as e:
            logger.error(f"Error initializing Odoo Documentation Retriever: {e}")
            return

        # Test queries
        test_queries = [
            "How to create a custom module in Odoo 18",
            "Odoo 18 ORM API reference",
            "Odoo 18 view inheritance",
            "How to implement a wizard in Odoo 18",
            "Odoo 18 security and access rights",
            # Add our specific test cases
            "How to configure Odoo taxes with 18.0",
            "How to configure taxes with indian localization part",
            "Indian GST configuration in Odoo 18",
            "E-invoicing setup for India in Odoo"
        ]

        for query in test_queries:
            logger.info(f"Testing query: {query}")
            try:
                result = retriever.query(query, max_results=3)

                # Print the first 200 characters of the result
                logger.info(f"Result: {result[:200]}...")
            except Exception as e:
                logger.error(f"Error querying: {e}")
            logger.info("-" * 80)

        logger.info("Odoo Documentation RAG module tests completed successfully!")

    if __name__ == "__main__":
        test_odoo_docs_retriever()

except ImportError as e:
    logger.error(f"Error importing Odoo Documentation RAG module: {e}")
    logger.error("Make sure you have installed the required dependencies:")
    logger.error("  - sentence-transformers")
    logger.error("  - faiss-cpu")
    logger.error("  - beautifulsoup4")
    logger.error("  - markdown")
    logger.error("  - gitpython")
    sys.exit(1)
except Exception as e:
    logger.error(f"Error testing Odoo Documentation RAG module: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)