"""
Documentation Helper

This module provides utilities for retrieving and formatting Odoo documentation.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import from odoo_docs_rag, but provide fallback if not available
try:
    from src.odoo_docs_rag.docs_retriever import OdooDocsRetriever

    # Use the existing documentation repository
    docs_dir = "/Users/vinusoft85/workspace/odoo18_mcp_project/odoo_docs"
    # Force rebuild to ensure index dimensions match the model
    _retriever = OdooDocsRetriever(docs_dir=docs_dir, force_rebuild=True)
    _has_retriever = True
except ImportError:
    logger.warning("Could not import OdooDocsRetriever, using fallback documentation")
    _has_retriever = False
    _retriever = None


def get_formatted_results(query: str, max_results: int = 5) -> str:
    """Get formatted documentation results for a query.

    Args:
        query: The query to search for
        max_results: Maximum number of results to return

    Returns:
        Formatted string with the results
    """
    if not _has_retriever:
        return f"Documentation retrieval is not available. Query: {query}"

    try:
        return _retriever.query(query, max_results=max_results)
    except Exception as e:
        logger.error(f"Error retrieving documentation: {str(e)}")
        return f"Error retrieving documentation: {str(e)}"


def get_model_documentation(model_name: str) -> str:
    """Get documentation for a specific Odoo model.

    Args:
        model_name: The name of the model (e.g., 'res.partner')

    Returns:
        Formatted string with the model documentation
    """
    if not _has_retriever:
        return f"Model documentation is not available. Model: {model_name}"

    try:
        # Query for model-specific documentation
        query = f"Odoo 18 model {model_name} fields and methods"
        return _retriever.query(query, max_results=3)
    except Exception as e:
        logger.error(f"Error retrieving model documentation: {str(e)}")
        return f"Error retrieving model documentation: {str(e)}"


def force_rebuild_index() -> bool:
    """Force rebuild the documentation index.

    This is useful when the index is corrupted or the model has changed.

    Returns:
        True if the index was rebuilt successfully, False otherwise
    """
    if not _has_retriever:
        logger.error("Documentation retriever is not available")
        return False

    try:
        logger.info("Forcing rebuild of documentation index")
        return _retriever.initialize_index()
    except Exception as e:
        logger.error(f"Error rebuilding documentation index: {str(e)}")
        return False