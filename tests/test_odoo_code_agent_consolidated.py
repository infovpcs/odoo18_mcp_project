#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolidated test script for the Odoo Code Agent.

This script provides comprehensive testing for the Odoo Code Agent:
1. Basic functionality test
2. Testing with feedback
3. Testing with Gemini fallback
4. Testing with Ollama fallback
5. Testing the complete workflow with human validation
"""

import os
import sys
import json
import logging
import argparse
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_odoo_code_agent")

# Import the Odoo Code Agent
try:
    from src.odoo_code_agent.main import run_odoo_code_agent, OdooCodeAgentState, AgentPhase
    from src.odoo_code_agent.utils import documentation_helper, odoo_connector
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Get Odoo connection details from environment variables
    ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
    ODOO_DB = os.getenv("ODOO_DB", "llmdb18")
    ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
    ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")
    
    logger.info(f"Using Odoo connection: {ODOO_URL}, database: {ODOO_DB}")
except ImportError as e:
    logger.error(f"Error importing Odoo Code Agent: {str(e)}")
    logger.error("Make sure the odoo_code_agent module is properly installed")
    sys.exit(1)
except Exception as e:
    logger.error(f"Error initializing: {str(e)}")
    sys.exit(1)

def test_basic_functionality():
    """Test the Odoo Code Agent with a basic query."""
    logger.info("Testing Odoo Code Agent with a basic query...")
    
    # Define the query
    query = "Create an Odoo 18 module for customer feedback management with ratings and comments"
    
    # Run the agent
    try:
        result = run_odoo_code_agent(
            query=query,
            odoo_url=ODOO_URL,
            odoo_db=ODOO_DB,
            odoo_username=ODOO_USERNAME,
            odoo_password=ODOO_PASSWORD,
            use_gemini=False,
            use_ollama=False,
            wait_for_validation=True  # Stop at the first validation point
        )
        
        # Check the result
        if not isinstance(result, dict):
            logger.error(f"Invalid result type: {type(result)}")
            return False, None
        
        # Check if the result contains the expected keys
        expected_keys = ["query", "plan", "tasks", "module_name", "current_phase", "requires_validation"]
        missing_keys = [key for key in expected_keys if key not in result]
        
        if missing_keys:
            logger.error(f"Missing keys in result: {missing_keys}")
            return False, None
        
        # Log the result
        logger.info(f"Query: {result['query']}")
        logger.info(f"Module name: {result['module_name']}")
        logger.info(f"Current phase: {result['current_phase']}")
        logger.info(f"Requires validation: {result['requires_validation']}")
        logger.info(f"Plan: {result['plan'][:100]}...")
        logger.info(f"Tasks: {result['tasks']}")
        
        # Save the state for the next test
        state_dict = result.get("state_dict")
        if state_dict:
            data_dir = os.path.join(project_root, "tests", "data")
            os.makedirs(data_dir, exist_ok=True)
            with open(os.path.join(data_dir, "code_agent_state.json"), "w") as f:
                json.dump(state_dict, f, indent=2)
            logger.info("Saved state for the next test")
        
        return True, result
    except Exception as e:
        logger.error(f"Error running Odoo Code Agent: {str(e)}")
        return False, None

def test_with_feedback(state_dict=None):
    """Test the Odoo Code Agent with feedback."""
    logger.info("Testing Odoo Code Agent with feedback...")
    
    # If no state_dict is provided, try to load it from the file
    if state_dict is None:
        state_dict_path = os.path.join(project_root, "tests", "data", "code_agent_state.json")
        if os.path.exists(state_dict_path):
            try:
                with open(state_dict_path, "r") as f:
                    state_dict = json.load(f)
            except Exception as e:
                logger.error(f"Error loading state: {str(e)}")
                return False, None
        else:
            logger.error(f"State file not found: {state_dict_path}")
            return False, None
    
    # Define the query and feedback
    query = "Create an Odoo 18 module for customer feedback management with ratings and comments"
    feedback = "The plan looks good, but please add support for attaching files to feedback"
    
    # Run the agent with feedback
    try:
        result = run_odoo_code_agent(
            query=query,
            odoo_url=ODOO_URL,
            odoo_db=ODOO_DB,
            odoo_username=ODOO_USERNAME,
            odoo_password=ODOO_PASSWORD,
            use_gemini=False,
            use_ollama=False,
            feedback=feedback,
            wait_for_validation=True,  # Stop at the second validation point
            current_phase="human_feedback_1",
            state_dict=state_dict
        )
        
        # Check the result
        if not isinstance(result, dict):
            logger.error(f"Invalid result type: {type(result)}")
            return False, None
        
        # Log the result
        logger.info(f"Query: {result['query']}")
        logger.info(f"Module name: {result['module_name']}")
        logger.info(f"Current phase: {result['current_phase']}")
        logger.info(f"Requires validation: {result['requires_validation']}")
        logger.info(f"Files to create: {len(result.get('files_to_create', []))}")
        
        # Save the state for the next test
        state_dict = result.get("state_dict")
        if state_dict:
            data_dir = os.path.join(project_root, "tests", "data")
            os.makedirs(data_dir, exist_ok=True)
            with open(os.path.join(data_dir, "code_agent_state_2.json"), "w") as f:
                json.dump(state_dict, f, indent=2)
            logger.info("Saved state for the next test")
        
        return True, result
    except Exception as e:
        logger.error(f"Error running Odoo Code Agent with feedback: {str(e)}")
        return False, None

def test_with_gemini():
    """Test the Odoo Code Agent with Google Gemini as a fallback."""
    logger.info("Testing Odoo Code Agent with Google Gemini")

    # Sample query
    query = "Create an Odoo 18 module for inventory management with barcode scanning"

    # Run the agent
    try:
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
        logger.info(f"Plan: {result['plan'][:100]}...")
        logger.info(f"Tasks: {result['tasks']}")
        logger.info(f"Module name: {result['module_name']}")
        logger.info(f"Files to create: {len(result.get('files_to_create', []))}")

        if result.get('error'):
            logger.error(f"Error: {result['error']}")
            return False, None

        return True, result
    except Exception as e:
        logger.error(f"Error running Odoo Code Agent with Gemini: {str(e)}")
        return False, None

def test_with_ollama():
    """Test the Odoo Code Agent with Ollama as a fallback."""
    logger.info("Testing Odoo Code Agent with Ollama")

    # Sample query
    query = "Create an Odoo 18 module for project management with Gantt charts"

    # Run the agent
    try:
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
        logger.info(f"Plan: {result['plan'][:100]}...")
        logger.info(f"Tasks: {result['tasks']}")
        logger.info(f"Module name: {result['module_name']}")
        logger.info(f"Files to create: {len(result.get('files_to_create', []))}")

        if result.get('error'):
            logger.error(f"Error: {result['error']}")
            return False, None

        return True, result
    except Exception as e:
        logger.error(f"Error running Odoo Code Agent with Ollama: {str(e)}")
        return False, None

def test_complete_workflow():
    """Test the complete workflow with human validation."""
    logger.info("Testing complete workflow with human validation...")
    
    # Step 1: Initial analysis
    success1, result1 = test_basic_functionality()
    if not success1 or not result1:
        logger.error("Step 1 failed!")
        return False
    
    # Step 2: Process feedback
    success2, result2 = test_with_feedback(result1.get("state_dict"))
    if not success2 or not result2:
        logger.error("Step 2 failed!")
        return False
    
    # Step 3: Final feedback and code generation
    try:
        query = "Create an Odoo 18 module for customer feedback management with ratings and comments"
        feedback = "The code looks good, but please add validation for the rating field to ensure it's between 1 and 5"
        
        result3 = run_odoo_code_agent(
            query=query,
            odoo_url=ODOO_URL,
            odoo_db=ODOO_DB,
            odoo_username=ODOO_USERNAME,
            odoo_password=ODOO_PASSWORD,
            use_gemini=False,
            use_ollama=False,
            feedback=feedback,
            wait_for_validation=False,  # No need to wait for validation in the final step
            current_phase="human_feedback_2",
            state_dict=result2.get("state_dict")
        )
        
        logger.info(f"Final phase: {result3.get('current_phase')}")
        logger.info(f"Is complete: {result3.get('is_complete', False)}")
        logger.info(f"Files to create: {len(result3.get('files_to_create', []))}")
        
        return result3.get("is_complete", False)
    except Exception as e:
        logger.error(f"Error in step 3: {str(e)}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test the Odoo Code Agent")
    parser.add_argument("--basic", action="store_true", help="Run basic functionality test")
    parser.add_argument("--feedback", action="store_true", help="Run feedback test")
    parser.add_argument("--gemini", action="store_true", help="Run test with Google Gemini")
    parser.add_argument("--ollama", action="store_true", help="Run test with Ollama")
    parser.add_argument("--workflow", action="store_true", help="Run complete workflow test")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    args = parser.parse_args()
    
    # Create the data directory if it doesn't exist
    data_dir = os.path.join(project_root, "tests", "data")
    os.makedirs(data_dir, exist_ok=True)
    
    # Run the tests
    tests = []
    
    if args.all or args.basic:
        tests.append(("Basic Functionality", test_basic_functionality))
    
    if args.all or args.feedback:
        tests.append(("Feedback", test_with_feedback))
    
    if args.all or args.gemini:
        tests.append(("Gemini Fallback", test_with_gemini))
    
    if args.all or args.ollama:
        tests.append(("Ollama Fallback", test_with_ollama))
    
    if args.all or args.workflow:
        tests.append(("Complete Workflow", test_complete_workflow))
    
    # If no tests were specified, run the basic test
    if not tests:
        tests.append(("Basic Functionality", test_basic_functionality))
    
    # Run the tests
    results = []
    for test_name, test_func in tests:
        logger.info(f"Running test: {test_name}")
        try:
            if test_func == test_complete_workflow:
                result = test_func()
                results.append((test_name, result))
            else:
                success, _ = test_func()
                results.append((test_name, success))
        except Exception as e:
            logger.error(f"Error running test {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Print the results
    logger.info("Test results:")
    for test_name, result in results:
        logger.info(f"  {test_name}: {'PASS' if result else 'FAIL'}")
    
    # Return success if all tests passed
    if all(result for _, result in results):
        logger.info("All tests passed")
        return 0
    else:
        logger.error("Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
