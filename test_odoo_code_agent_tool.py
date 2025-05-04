#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the Odoo code agent MCP tool.
"""

import os
import sys
import json
import logging
import requests
import argparse
from typing import Dict, Any, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("odoo_code_agent_tool_test")

# MCP server URL (standalone server)
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8001")

def test_odoo_code_agent_tool(query: str, use_gemini: bool = False, use_ollama: bool = False, feedback: Optional[str] = None, save_to_files: bool = False, output_dir: Optional[str] = None) -> Tuple[bool, Any]:
    """Test the run_odoo_code_agent tool with the given parameters"""
    url = f"{MCP_SERVER_URL}/call_tool"

    params = {
        "query": query,
        "use_gemini": use_gemini,
        "use_ollama": use_ollama
    }

    if feedback:
        params["feedback"] = feedback

    if save_to_files:
        params["save_to_files"] = save_to_files

    if output_dir:
        params["output_dir"] = output_dir

    logger.info(f"Testing run_odoo_code_agent tool")
    logger.info(f"Parameters: {json.dumps(params, indent=2)}")

    try:
        response = requests.post(
            url,
            json={
                "tool": "run_odoo_code_agent",
                "params": params
            }
        )

        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            logger.info(f"Success! Response received.")
            # Print a summary of the response instead of the full response
            if "result" in result:
                # Extract key information from the result
                result_text = result["result"]
                # Print the first 500 characters of the result
                logger.info(f"Result summary: {result_text[:500]}...")
                # Check if the result contains expected sections
                expected_sections = ["Query", "Plan", "Tasks", "Module Information", "Generated Files"]
                found_sections = []
                for section in expected_sections:
                    if f"## {section}" in result_text:
                        found_sections.append(section)
                logger.info(f"Found sections: {', '.join(found_sections)}")
                # Count the number of files to be created
                if "Generated Files" in found_sections:
                    files_count = result_text.count("### ")
                    logger.info(f"Number of generated files: {files_count}")
            return True, result
        else:
            logger.error(f"Error: Status code {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False, response.text
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        return False, str(e)

def test_with_feedback(query: str, feedback: str, use_gemini: bool = False) -> Tuple[bool, Any]:
    """Test the run_odoo_code_agent tool with feedback"""
    logger.info("\n=== Testing run_odoo_code_agent with feedback ===")
    return test_odoo_code_agent_tool(query, use_gemini, False, feedback)

def main():
    """Main function to run the tests"""
    parser = argparse.ArgumentParser(description="Test the Odoo code agent MCP tool")
    parser.add_argument("--gemini", action="store_true", help="Use Google Gemini as a fallback")
    parser.add_argument("--ollama", action="store_true", help="Use Ollama as a fallback")
    parser.add_argument("--feedback", action="store_true", help="Test with feedback")
    parser.add_argument("--save", action="store_true", help="Test saving files to disk")
    parser.add_argument("--output-dir", help="Directory to save files to")
    args = parser.parse_args()

    logger.info("Starting Odoo code agent tool tests")

    # Test 1: Basic query
    logger.info("\n=== Test 1: Basic query ===")
    success1, result1 = test_odoo_code_agent_tool(
        "Create a simple Odoo 18 module for managing customer feedback with ratings and comments",
        args.gemini,
        args.ollama
    )

    # Test 2: More complex query
    logger.info("\n=== Test 2: More complex query ===")
    success2, result2 = test_odoo_code_agent_tool(
        "Create an Odoo 18 module for project task management with time tracking and reporting",
        args.gemini,
        args.ollama
    )

    # Test 3: With feedback (if requested)
    if args.feedback:
        logger.info("\n=== Test 3: With feedback ===")
        success3, result3 = test_with_feedback(
            "Create a simple Odoo 18 module for managing customer feedback",
            "Please add a rating field with stars from 1 to 5 and make it required",
            args.gemini
        )

    # Test 4: With file saving (if requested)
    if args.save:
        logger.info("\n=== Test 4: With file saving ===")
        output_dir = args.output_dir or os.path.join(os.getcwd(), "generated_modules")
        success4, result4 = test_odoo_code_agent_tool(
            "Create a simple Odoo 18 module for a todo list application",
            args.gemini,
            args.ollama,
            None,  # No feedback
            True,  # Save to files
            output_dir
        )

        # Check if files were saved successfully
        if success4 and "result" in result4 and "Files Saved to Disk" in result4["result"]:
            logger.info("Files were saved successfully!")
            # Extract the module directory from the result
            result_text = result4["result"]
            if "module_dir" in result_text:
                module_dir_line = [line for line in result_text.split("\n") if "`" in line and "module_dir" in line]
                if module_dir_line:
                    module_dir = module_dir_line[0].split("`")[1]
                    logger.info(f"Module directory: {module_dir}")

                    # Check if the directory exists
                    if os.path.exists(module_dir):
                        logger.info(f"Directory exists: {module_dir}")
                        # List the files in the directory
                        files = os.listdir(module_dir)
                        logger.info(f"Files in directory: {files}")
                    else:
                        logger.error(f"Directory does not exist: {module_dir}")
        else:
            logger.error("Failed to save files!")

    logger.info("\nAll tests completed!")

if __name__ == "__main__":
    main()
