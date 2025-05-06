#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for specific queries in the Odoo Documentation RAG module.

This script tests the functionality of the Odoo Documentation RAG module
with specific queries related to taxes and Indian localization.
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_specific_queries")

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the Odoo Documentation RAG module
    from src.odoo_docs_rag import OdooDocsRetriever
    
    def test_specific_queries():
        """Test specific queries in the Odoo Documentation RAG module."""
        logger.info("Testing specific queries in Odoo Documentation RAG module...")
        
        # Set up directories
        docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "odoo_docs")
        index_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "odoo_docs_index")
        
        # Create directories if they don't exist
        os.makedirs(docs_dir, exist_ok=True)
        os.makedirs(index_dir, exist_ok=True)
        
        # Initialize the retriever (don't rebuild the index)
        logger.info("Initializing Odoo Documentation Retriever...")
        try:
            retriever = OdooDocsRetriever(
                docs_dir=docs_dir,
                index_dir=index_dir,
                force_rebuild=False  # Don't rebuild the index
            )
        except Exception as e:
            logger.error(f"Error initializing Odoo Documentation Retriever: {e}")
            return
        
        # Test specific queries
        test_queries = [
            "How to configure Odoo taxes with 18.0",
            "How to configure taxes with indian localization part",
            "Indian GST configuration in Odoo 18",
            "E-invoicing setup for India in Odoo",
            "TDS TCS threshold in Indian localization"
        ]
        
        for query in test_queries:
            logger.info(f"\nTesting query: {query}")
            try:
                result = retriever.query(query, max_results=3)
                
                # Print the first 500 characters of the result
                logger.info(f"Result: {result[:500]}...")
                
                # Check if we got relevant results
                if "No relevant information found" in result:
                    logger.warning("No relevant information found for this query")
                else:
                    logger.info("Found relevant information for this query")
            except Exception as e:
                logger.error(f"Error querying: {e}")
            logger.info("=" * 80)
        
        logger.info("Specific query tests completed!")
        
    if __name__ == "__main__":
        test_specific_queries()
        
except ImportError as e:
    logger.error(f"Error importing Odoo Documentation RAG module: {e}")
    logger.error("Make sure you have installed the required dependencies")
    sys.exit(1)
except Exception as e:
    logger.error(f"Error testing specific queries: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
