#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the human validation workflow in the Odoo code agent.

This script tests the human validation workflow by simulating the complete process:
1. Initial analysis with wait_for_validation=True (stops at first validation point)
2. Continue with feedback after first validation (stops at second validation point)
3. Continue with feedback after second validation (completes the process)
"""

import os
import sys
import json
import logging
import argparse
from typing import Dict, Any, Optional, Tuple
import requests
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_human_validation")

# Load environment variables
load_dotenv()

# MCP server URL (standalone server)
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8001")


def call_odoo_code_agent_tool(
    query: str,
    use_gemini: bool = False,
    use_ollama: bool = False,
    feedback: Optional[str] = None,
    save_to_files: bool = False,
    output_dir: Optional[str] = None,
    wait_for_validation: bool = False,
    current_phase: Optional[str] = None,
    state_dict: Optional[Dict[str, Any]] = None
) -> Tuple[bool, Any]:
    """Call the run_odoo_code_agent_tool tool with the given parameters."""
    url = f"{MCP_SERVER_URL}/call_tool"

    params = {
        "query": query,
        "use_gemini": use_gemini,
        "use_ollama": use_ollama,
        "wait_for_validation": wait_for_validation
    }

    if feedback:
        params["feedback"] = feedback

    if save_to_files:
        params["save_to_files"] = save_to_files

    if output_dir:
        params["output_dir"] = output_dir

    if current_phase:
        params["current_phase"] = current_phase

    if state_dict:
        params["state_dict"] = state_dict

    logger.info(f"Calling run_odoo_code_agent_tool with parameters:")
    logger.info(f"  query: {query}")
    logger.info(f"  use_gemini: {use_gemini}")
    logger.info(f"  use_ollama: {use_ollama}")
    logger.info(f"  wait_for_validation: {wait_for_validation}")
    logger.info(f"  current_phase: {current_phase}")
    logger.info(f"  feedback: {feedback}")

    try:
        # Call the tool
        response = requests.post(
            url,
            json={
                "tool": "run_odoo_code_agent_tool",
                "params": params
            },
            timeout=300  # 5 minutes timeout
        )

        # Check if the request was successful
        if response.status_code == 200:
            result = response.json()
            return True, result
        else:
            logger.error(f"Error calling tool: {response.status_code} - {response.text}")
            return False, response.text
    except Exception as e:
        logger.error(f"Exception: {str(e)}")
        return False, str(e)


def test_human_validation_workflow(query: str, use_gemini: bool = False) -> None:
    """Test the complete human validation workflow."""
    logger.info("\n=== Testing human validation workflow ===")
    
    # Step 1: Initial analysis with wait_for_validation=True
    logger.info("Step 1: Initial analysis with wait_for_validation=True")
    success1, result1 = call_odoo_code_agent_tool(
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
    success2, result2 = call_odoo_code_agent_tool(
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
    success3, result3 = call_odoo_code_agent_tool(
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
    """Main function to run the tests."""
    parser = argparse.ArgumentParser(description="Test the human validation workflow in the Odoo code agent")
    parser.add_argument("--gemini", action="store_true", help="Use Google Gemini as a fallback")
    parser.add_argument("--query", default="Create a simple CRM module with mass mailing feature", help="Query to use for testing")
    args = parser.parse_args()

    logger.info("Starting human validation workflow test")
    
    # Test the human validation workflow
    test_human_validation_workflow(args.query, args.gemini)
    
    logger.info("All tests completed!")


if __name__ == "__main__":
    main()
