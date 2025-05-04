# tests/test_odoo_code_agent.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the Odoo Code Agent.
"""

import os
import sys
import logging
import argparse
from dotenv import load_dotenv

from src.agents.odoo_code_agent.main import run_odoo_code_agent

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_odoo_code_agent")

# Load environment variables
load_dotenv()

# Get Odoo connection details from environment variables
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "llmdb18")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")


def test_odoo_code_agent():
    """Test the Odoo Code Agent with a sample query."""
    logger.info("Testing Odoo Code Agent")

    # Sample query
    query = "Create an Odoo 18 module for managing customer feedback with ratings and comments"

    # Run the agent
    result = run_odoo_code_agent(
        query=query,
        odoo_url=ODOO_URL,
        odoo_db=ODOO_DB,
        odoo_username=ODOO_USERNAME,
        odoo_password=ODOO_PASSWORD,
        use_gemini=False,
        use_ollama=False
    )

    # Print the result
    logger.info("Odoo Code Agent result:")
    logger.info(f"Query: {result['query']}")
    logger.info(f"Plan: {result['plan']}")
    logger.info(f"Tasks: {result['tasks']}")
    logger.info(f"Module name: {result['module_name']}")
    logger.info(f"Module structure: {result['module_structure']}")
    logger.info(f"Files to create: {len(result['files_to_create'])}")
    logger.info(f"Feedback: {result['feedback']}")
    
    if result['error']:
        logger.error(f"Error: {result['error']}")
        return False
    
    return True


def test_odoo_code_agent_with_gemini():
    """Test the Odoo Code Agent with Google Gemini as a fallback."""
    logger.info("Testing Odoo Code Agent with Google Gemini")

    # Sample query
    query = "Create an Odoo 18 module for inventory management with barcode scanning"

    # Run the agent
    result = run_odoo_code_agent(
        query=query,
        odoo_url=ODOO_URL,
        odoo_db=ODOO_DB,
        odoo_username=ODOO_USERNAME,
        odoo_password=ODOO_PASSWORD,
        use_gemini=True,
        use_ollama=False
    )

    # Print the result
    logger.info("Odoo Code Agent with Gemini result:")
    logger.info(f"Query: {result['query']}")
    logger.info(f"Plan: {result['plan']}")
    logger.info(f"Tasks: {result['tasks']}")
    logger.info(f"Module name: {result['module_name']}")
    logger.info(f"Module structure: {result['module_structure']}")
    logger.info(f"Files to create: {len(result['files_to_create'])}")
    logger.info(f"Feedback: {result['feedback']}")
    
    if result['error']:
        logger.error(f"Error: {result['error']}")
        return False
    
    return True


def test_odoo_code_agent_with_ollama():
    """Test the Odoo Code Agent with Ollama as a fallback."""
    logger.info("Testing Odoo Code Agent with Ollama")

    # Sample query
    query = "Create an Odoo 18 module for project management with Gantt charts"

    # Run the agent
    result = run_odoo_code_agent(
        query=query,
        odoo_url=ODOO_URL,
        odoo_db=ODOO_DB,
        odoo_username=ODOO_USERNAME,
        odoo_password=ODOO_PASSWORD,
        use_gemini=False,
        use_ollama=True
    )

    # Print the result
    logger.info("Odoo Code Agent with Ollama result:")
    logger.info(f"Query: {result['query']}")
    logger.info(f"Plan: {result['plan']}")
    logger.info(f"Tasks: {result['tasks']}")
    logger.info(f"Module name: {result['module_name']}")
    logger.info(f"Module structure: {result['module_structure']}")
    logger.info(f"Files to create: {len(result['files_to_create'])}")
    logger.info(f"Feedback: {result['feedback']}")
    
    if result['error']:
        logger.error(f"Error: {result['error']}")
        return False
    
    return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test the Odoo Code Agent")
    parser.add_argument("--gemini", action="store_true", help="Test with Google Gemini")
    parser.add_argument("--ollama", action="store_true", help="Test with Ollama")
    args = parser.parse_args()

    if args.gemini:
        test_odoo_code_agent_with_gemini()
    elif args.ollama:
        test_odoo_code_agent_with_ollama()
    else:
        test_odoo_code_agent()


if __name__ == "__main__":
    main()