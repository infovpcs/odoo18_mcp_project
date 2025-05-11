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
    sys.exit(1)

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
        if "module" in result.lower() and "odoo" in result.lower():
            logger.info("Basic retrieval test passed")
            return True, result
        else:
            logger.error("Basic retrieval test failed: Result doesn't contain relevant information")
            return False, result
    except Exception as e:
        logger.error(f"Error testing basic retrieval: {str(e)}")
        return False, str(e)


def test_online_search():
    """Test the online search functionality."""
    logger.info("Testing online search functionality...")

    try:
        # Initialize the online search
        online_search = OnlineSearch()
        
        # Check if online search is available
        if not online_search.is_available:
            logger.warning("Online search is not available, skipping test")
            return False, "Online search is not available"
        
        # Test a simple query
        query = "Odoo 18 module development guide"
        results = online_search.search(query, count=3)
        
        logger.info(f"Query: {query}")
        logger.info(f"Found {len(results)} results")
        
        if results:
            # Format the results
            formatted_results = online_search.format_results(results)
            logger.info(f"Formatted results snippet: {formatted_results[:200]}...")  # Show first 200 chars
            
            logger.info("Online search test passed")
            return True, formatted_results
        else:
            logger.error("Online search test failed: No results found")
            return False, "No results found"
    except Exception as e:
        logger.error(f"Error testing online search: {str(e)}")
        return False, str(e)


def test_gemini_summarizer():
    """Test the Gemini summarizer."""
    logger.info("Testing Gemini summarizer...")

    try:
        # Initialize the Gemini summarizer
        gemini_summarizer = GeminiSummarizer()
        
        # Check if Gemini is available
        if not gemini_summarizer.is_available:
            logger.warning("Gemini summarizer is not available, skipping test")
            return False, "Gemini summarizer is not available"
        
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
        if "module" in result.lower() and "odoo" in result.lower():
            logger.info("Gemini summarizer test passed")
            return True, result
        else:
            logger.error("Gemini summarizer test failed: Result doesn't contain relevant information")
            return False, result
    except Exception as e:
        logger.error(f"Error testing Gemini summarizer: {str(e)}")
        return False, str(e)


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
            if "module" in result.lower() and "odoo" in result.lower():
                logger.info("Enhanced query test passed")
                return True, result
            else:
                logger.error("Enhanced query test failed: Result doesn't contain relevant information")
                return False, result
        else:
            logger.warning("Enhanced query is not available, skipping test")
            return False, "Enhanced query is not available"
    except Exception as e:
        logger.error(f"Error testing enhanced query: {str(e)}")
        return False, str(e)


def test_mcp_tool():
    """Test the MCP tool for retrieving Odoo documentation."""
    logger.info("Testing MCP tool for retrieving Odoo documentation...")

    try:
        # Check if the MCP server is running
        try:
            response = requests.get(f"{MCP_SERVER_URL}/health", timeout=5)
            if response.status_code != 200:
                logger.warning("MCP server is not running, skipping test")
                return False, "MCP server is not running"
        except Exception as e:
            logger.warning(f"Error connecting to MCP server: {str(e)}")
            return False, f"Error connecting to MCP server: {str(e)}"
        
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
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("success", False):
                result = data.get("data") or data.get("result")
                logger.info(f"MCP tool result snippet: {result[:200]}...")  # Show first 200 chars
                
                # Check if the result contains relevant information
                if "module" in result.lower() and "odoo" in result.lower():
                    logger.info("MCP tool test passed")
                    return True, result
                else:
                    logger.error("MCP tool test failed: Result doesn't contain relevant information")
                    return False, result
            else:
                error = data.get("error", "Unknown error")
                logger.error(f"MCP tool failed: {error}")
                return False, error
        else:
            logger.error(f"MCP tool failed with status code {response.status_code}")
            return False, f"Status code: {response.status_code}"
    except Exception as e:
        logger.error(f"Error testing MCP tool: {str(e)}")
        return False, str(e)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test the enhanced RAG tool")
    parser.add_argument("--basic", action="store_true", help="Test basic retrieval")
    parser.add_argument("--online", action="store_true", help="Test online search")
    parser.add_argument("--gemini", action="store_true", help="Test Gemini summarizer")
    parser.add_argument("--enhanced", action="store_true", help="Test enhanced query")
    parser.add_argument("--mcp", action="store_true", help="Test MCP tool")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    args = parser.parse_args()

    logger.info("Testing enhanced RAG tool")

    # Run the tests
    tests = []
    
    if args.all or args.basic:
        tests.append(("Basic Retrieval", test_basic_retrieval))
    
    if args.all or args.online:
        tests.append(("Online Search", test_online_search))
    
    if args.all or args.gemini:
        tests.append(("Gemini Summarizer", test_gemini_summarizer))
    
    if args.all or args.enhanced:
        tests.append(("Enhanced Query", test_enhanced_query))
    
    if args.all or args.mcp:
        tests.append(("MCP Tool", test_mcp_tool))
    
    # If no tests were specified, run all tests
    if not tests:
        tests = [
            ("Basic Retrieval", test_basic_retrieval),
            ("Online Search", test_online_search),
            ("Gemini Summarizer", test_gemini_summarizer),
            ("Enhanced Query", test_enhanced_query),
            ("MCP Tool", test_mcp_tool)
        ]
    
    # Run the tests
    results = []
    for test_name, test_func in tests:
        logger.info(f"Running test: {test_name}")
        try:
            success, result = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.error(f"Error running test {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Print the results
    logger.info("\n=== Test Results ===")
    all_passed = True
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if not success:
            all_passed = False
    
    # Exit with appropriate status code
    if all_passed:
        logger.info("\nAll tests passed!")
        sys.exit(0)
    else:
        logger.error("\nSome tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()