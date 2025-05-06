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

def test_odoo_code_agent_tool(query: str, use_gemini: bool = False, use_ollama: bool = False,
                         feedback: Optional[str] = None, save_to_files: bool = False,
                         output_dir: Optional[str] = None, wait_for_validation: bool = False,
                         current_phase: Optional[str] = None, state_dict: Optional[Dict[str, Any]] = None) -> Tuple[bool, Any]:
    """Test the run_odoo_code_agent_tool tool with the given parameters"""
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

    if wait_for_validation:
        params["wait_for_validation"] = wait_for_validation

    if current_phase:
        params["current_phase"] = current_phase

    if state_dict:
        params["state_dict"] = state_dict

    logger.info(f"Testing run_odoo_code_agent_tool tool")
    logger.info(f"Parameters: {json.dumps(params, indent=2)}")

    try:
        response = requests.post(
            url,
            json={
                "tool": "run_odoo_code_agent_tool",
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
    """Test the run_odoo_code_agent_tool tool with feedback"""
    logger.info("\n=== Testing run_odoo_code_agent_tool with feedback ===")
    return test_odoo_code_agent_tool(query, use_gemini, False, feedback)

def test_human_validation_workflow(query: str, use_gemini: bool = False) -> None:
    """Test the complete human validation workflow"""
    logger.info("\n=== Testing human validation workflow ===")

    # Step 1: Initial analysis with wait_for_validation=True
    logger.info("Step 1: Initial analysis with wait_for_validation=True")
    success1, result1 = test_odoo_code_agent_tool(
        query=query,
        use_gemini=use_gemini,
        wait_for_validation=True
    )

    if not success1:
        logger.error("Step 1 failed!")
        return

    # Extract state_dict and current_phase from the result
    result_data = result1.get("result", "")

    # Check if we're at the first validation point
    if "Requires Validation: Yes" not in result_data:
        logger.error("Step 1 did not stop at validation point!")
        return

    logger.info("Step 1 successful - stopped at first validation point")

    # For a real test, we would extract the state_dict here
    # But for simplicity, we'll just continue with a new request

    # Step 2: Continue with feedback after first validation
    logger.info("Step 2: Continue with feedback after first validation")
    feedback1 = "Please add a dashboard with key metrics and make sure the module is mobile-friendly."
    success2, result2 = test_odoo_code_agent_tool(
        query=query,
        use_gemini=use_gemini,
        feedback=feedback1,
        wait_for_validation=True,
        current_phase="human_feedback_1"
    )

    if not success2:
        logger.error("Step 2 failed!")
        return

    # Check if we're at the second validation point
    if "Requires Validation: Yes" not in result2.get("result", ""):
        logger.error("Step 2 did not stop at validation point!")
        return

    logger.info("Step 2 successful - stopped at second validation point")

    # Step 3: Continue with feedback after second validation
    logger.info("Step 3: Continue with feedback after second validation")
    feedback2 = "The code looks good, but please add more comments to explain the complex parts."
    success3, result3 = test_odoo_code_agent_tool(
        query=query,
        use_gemini=use_gemini,
        feedback=feedback2,
        wait_for_validation=False,  # No need to wait for validation in the final step
        current_phase="human_feedback_2"
    )

    if not success3:
        logger.error("Step 3 failed!")
        return

    # Check if the process is complete
    if "Is Complete: Yes" not in result3.get("result", ""):
        logger.error("Step 3 did not complete the process!")
        return

    logger.info("Step 3 successful - process completed")
    logger.info("Human validation workflow test completed successfully!")

def main():
    """Main function to run the tests"""
    parser = argparse.ArgumentParser(description="Test the Odoo code agent MCP tool")
    parser.add_argument("--gemini", action="store_true", help="Use Google Gemini as a fallback")
    parser.add_argument("--ollama", action="store_true", help="Use Ollama as a fallback")
    parser.add_argument("--feedback", action="store_true", help="Test with feedback")
    parser.add_argument("--save", action="store_true", help="Test saving files to disk")
    parser.add_argument("--output-dir", help="Directory to save files to")
    parser.add_argument("--validation", action="store_true", help="Test human validation workflow")
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

    # Test 5: Human validation workflow (if requested)
    if args.validation:
        logger.info("\n=== Test 5: Human validation workflow ===")
        test_human_validation_workflow(
            "Create a simple Odoo 18 module for an employee directory with skills tracking",
            args.gemini
        )

    logger.info("\nAll tests completed!")

if __name__ == "__main__":
    main()
