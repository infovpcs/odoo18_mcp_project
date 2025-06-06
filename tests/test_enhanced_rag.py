#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the enhanced RAG tool with Gemini integration and online search.

This script tests the enhanced RAG tool functionality:
1. Basic retrieval functionality
2. Gemini integration for summarization
3. Online search integration
4. Combined functionality (local docs + online search + Gemini)
"""

import os
import sys
import logging
import argparse
import json
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import pytest

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_enhanced_rag")

# Load environment variables
load_dotenv()

# Import the RAG components
try:
    from src.odoo_docs_rag import (
        OdooDocsRetriever,
        OnlineSearch,
        GeminiSummarizer
    )
except ImportError as e:
    logger.error(f"Failed to import RAG components: {str(e)}")
    logger.error("Make sure the package is installed.")
    pass # Allow pytest to continue collection

# Import the MCP server components for testing the MCP tool
import requests

# MCP server URL
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8001")


def test_basic_retrieval():
    """Test the basic retrieval functionality."""
    logger.info("Testing basic retrieval functionality...")

    try:
        # Use the existing documentation repository
        docs_dir = os.path.join(project_root, "odoo_docs")
        
        # Initialize the retriever
        retriever = OdooDocsRetriever(
            docs_dir=docs_dir,
            force_rebuild=False  # Don't force rebuild to save time
        )
        
        # Test a simple query
        query = "How to create a custom module in Odoo 18"
        result = retriever.query(query, max_results=3)
        
        logger.info(f"Query: {query}")
        logger.info(f"Result snippet: {result[:200]}...")  # Show first 200 chars
        
        # Check if the result contains relevant information
        assert "module" in result.lower() and "odoo" in result.lower(), "Result doesn't contain relevant information"

    except Exception as e:
        logger.error(f"Error testing basic retrieval: {str(e)}")
        pytest.fail(f"Error testing basic retrieval: {str(e)}")


def test_online_search():
    """Test the online search functionality."""
    logger.info("Testing online search functionality...")

    try:
        # Initialize the online search
        online_search = OnlineSearch()
        
        # Check if online search is available
        if not online_search.is_available:
            logger.warning("Online search is not available, skipping test")
            pytest.skip("Online search is not available")
        
        # Test a simple query
        query = "Odoo 18 module development guide"
        results = online_search.search(query, count=3)
        
        logger.info(f"Query: {query}")
        logger.info(f"Found {len(results)} results")
        
        assert results, "No results found"
        
        # Format the results
        formatted_results = online_search.format_results(results)
        logger.info(f"Formatted results snippet: {formatted_results[:200]}...")  # Show first 200 chars
        
    except Exception as e:
        logger.error(f"Error testing online search: {str(e)}")
        pytest.fail(f"Error testing online search: {str(e)}")


def test_gemini_summarizer():
    """Test the Gemini summarizer."""
    logger.info("Testing Gemini summarizer...")

    try:
        # Initialize the Gemini summarizer
        gemini_summarizer = GeminiSummarizer()
        
        # Check if Gemini is available
        if not gemini_summarizer.is_available:
            logger.warning("Gemini summarizer is not available, skipping test")
            pytest.skip("Gemini summarizer is not available")
        
        # Create some sample results
        doc_results = [
            {
                "title": "Creating a Module",
                "text": "To create a module in Odoo 18, you need to define a manifest file and create the necessary directory structure.",
                "source": "odoo_docs/developer/howtos/creating_modules.rst"
            },
            {
                "title": "Module Structure",
                "text": "An Odoo module is organized as a directory containing various files and subdirectories.",
                "source": "odoo_docs/developer/reference/module_structure.rst"
            }
        ]
        
        online_results = [
            {
                "title": "Odoo 18 Module Development Guide",
                "description": "Learn how to develop custom modules for Odoo 18 with this comprehensive guide.",
                "url": "https://example.com/odoo18-guide"
            }
        ]
        
        # Test summarization
        query = "How to create a custom module in Odoo 18"
        result = gemini_summarizer.summarize(query, doc_results, online_results)
        
        logger.info(f"Query: {query}")
        logger.info(f"Summarized result snippet: {result[:200]}...")  # Show first 200 chars
        
        # Check if the result contains relevant information
        assert "module" in result.lower() and "odoo" in result.lower(), "Result doesn't contain relevant information"

    except Exception as e:
        logger.error(f"Error testing Gemini summarizer: {str(e)}")
        pytest.fail(f"Error testing Gemini summarizer: {str(e)}")


def test_enhanced_query():
    """Test the enhanced query functionality."""
    logger.info("Testing enhanced query functionality...")

    try:
        # Use the existing documentation repository
        docs_dir = os.path.join(project_root, "odoo_docs")
        
        # Initialize the retriever with all components
        retriever = OdooDocsRetriever(
            docs_dir=docs_dir,
            force_rebuild=False,  # Don't force rebuild to save time
            use_gemini=True,
            use_online_search=True
        )
        
        # Test a simple query
        query = "How to create a custom module in Odoo 18"
        
        # Check if enhanced query is available
        if hasattr(retriever, 'enhanced_query'):
            result = retriever.enhanced_query(
                query, 
                max_results=3,
                use_gemini=True,
                use_online_search=True
            )
            
            logger.info(f"Query: {query}")
            logger.info(f"Enhanced result snippet: {result[:200]}...")  # Show first 200 chars
            
            # Check if the result contains relevant information
            assert "module" in result.lower() and "odoo" in result.lower(), "Result doesn't contain relevant information"
        else:
            logger.warning("Enhanced query is not available, skipping test")
            pytest.skip("Enhanced query is not available")
    except Exception as e:
        logger.error(f"Error testing enhanced query: {str(e)}")
        pytest.fail(f"Error testing enhanced query: {str(e)}")


def test_mcp_tool():
    """Test the MCP tool for retrieving Odoo documentation."""
    logger.info("Testing MCP tool for retrieving Odoo documentation...")

    try:
        # Check if the MCP server is running
        try:
            response = requests.get(f"{MCP_SERVER_URL}/health", timeout=5)
            assert response.status_code == 200, "MCP server is not running"
        except Exception as e:
            logger.warning(f"Error connecting to MCP server: {str(e)}")
            pytest.skip(f"MCP server is not running or accessible: {str(e)}")
        
        # Call the MCP tool
        payload = {
            "tool": "retrieve_odoo_documentation",
            "params": {
                "query": "How to create a custom module in Odoo 18",
                "max_results": 3,
                "use_gemini": True,
                "use_online_search": True
            }
        }
        
        logger.info(f"Calling MCP tool with parameters: {json.dumps(payload['params'], indent=2)}")
        
        response = requests.post(
            f"{MCP_SERVER_URL}/call_tool",
            json=payload,
            timeout=120  # Longer timeout for documentation retrieval
        )
        
        assert response.status_code == 200, f"MCP tool failed with status code {response.status_code}"
        
        data = response.json()
        
        assert data.get("success", False), f"MCP tool returned success: False. Error: {data.get('error', 'Unknown error')}"
        
        result = data.get("data") or data.get("result")
        logger.info(f"MCP tool result snippet: {result[:200]}...")  # Show first 200 chars
        
        # Check if the result contains relevant information
        assert "module" in result.lower() and "odoo" in result.lower(), "Result doesn't contain relevant information"

    except Exception as e:
        logger.error(f"Error testing MCP tool: {str(e)}")
        pytest.fail(f"Error testing MCP tool: {str(e)}")


# Modify the main function to avoid running tests directly
# This file is now intended to be run by pytest
def main_for_pytest():
    """Placeholder main function to avoid direct execution of tests."""
    pass

if __name__ == "__main__":
    # This block will not be executed by pytest
    print("This script is intended to be run using pytest.")
    sys.exit(1)