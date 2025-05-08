#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolidated test script for the Odoo Code Agent utilities.

This script provides comprehensive testing for the Odoo Code Agent utilities:
1. Documentation helper
2. Odoo connector
3. Gemini client
4. Fallback models
5. Human validation workflow
"""

import os
import sys
import logging
import argparse
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_odoo_code_agent_utils")

# Load environment variables
load_dotenv()

# Import the utilities
try:
    from src.odoo_code_agent.utils import documentation_helper, odoo_connector, gemini_client, fallback_models
    from src.odoo_code_agent.utils import file_saver, module_structure
    from src.odoo_code_agent.main import OdooCodeAgentState, AgentPhase
except ImportError as e:
    logger.error(f"Failed to import Odoo Code Agent utilities: {str(e)}")
    logger.error("Make sure the package is installed.")
    sys.exit(1)


def test_documentation_helper():
    """Test the documentation helper."""
    logger.info("Testing documentation helper...")

    try:
        # Test querying documentation
        query = "Odoo 18 module structure"
        result = documentation_helper.get_formatted_results(query, max_results=2)

        logger.info(f"Query: {query}")
        logger.info(f"Result: {result[:200]}...")  # Show first 200 chars

        # Test getting model documentation
        model_name = "res.partner"
        result = documentation_helper.get_model_documentation(model_name)

        logger.info(f"Model documentation for {model_name}")
        logger.info(f"Result: {result[:200]}...")  # Show first 200 chars

        logger.info("Documentation helper test completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error testing documentation helper: {str(e)}")
        return False


def test_odoo_connector():
    """Test the Odoo connector."""
    logger.info("Testing Odoo connector...")

    try:
        # Test getting models list - fix the fields to match Odoo 18
        models = odoo_connector.search_read(
            'ir.model',
            [('state', '=', 'base')],
            ['name', 'model', 'modules']
        )
        logger.info(f"Found {len(models)} models")

        if models:
            # Show first 5 models
            for i, model in enumerate(models[:5]):
                logger.info(f"Model {i+1}: {model['model']} - {model['name']}")

        # Test getting model fields
        model_name = "res.partner"
        fields = odoo_connector.get_model_fields(model_name)
        logger.info(f"Found {len(fields)} fields for model {model_name}")

        if fields:
            # Show first 5 fields
            for i, (field_name, field_info) in enumerate(list(fields.items())[:5]):
                logger.info(f"Field {i+1}: {field_name} - {field_info.get('type')} - {field_info.get('string')}")

        # Test getting field groups
        field_groups = odoo_connector.get_field_groups(model_name)
        logger.info(f"Field groups for model {model_name}:")

        for field_type, field_names in field_groups.items():
            logger.info(f"  {field_type}: {len(field_names)} fields")

        # Test getting record template
        template = odoo_connector.get_record_template(model_name)
        logger.info(f"Record template for model {model_name} has {len(template)} fields")

        logger.info("Odoo connector test completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error testing Odoo connector: {str(e)}")
        return False


def test_human_validation_workflow():
    """Test the human validation workflow."""
    logger.info("Testing human validation workflow...")

    try:
        # Create a new agent state
        state = OdooCodeAgentState()

        # Set the initial query
        state.analysis_state.query = "Create a simple CRM module with mass mailing feature"

        # Test phase transitions
        logger.info(f"Initial phase: {state.phase}")

        # Simulate completing analysis
        state.phase = AgentPhase.PLANNING
        logger.info(f"After analysis phase: {state.phase}")

        # Simulate completing planning
        state.phase = AgentPhase.HUMAN_FEEDBACK_1
        logger.info(f"First human validation point: {state.phase}")

        # Simulate processing feedback
        state.feedback_state.feedback = "Please add a dashboard with key metrics"
        state.phase = AgentPhase.CODING
        logger.info(f"After processing feedback: {state.phase}")

        # Simulate completing coding
        state.phase = AgentPhase.HUMAN_FEEDBACK_2
        logger.info(f"Second human validation point: {state.phase}")

        # Simulate processing feedback
        state.feedback_state.feedback = "Please add more comments to the code"
        state.phase = AgentPhase.FINALIZATION
        logger.info(f"After processing feedback: {state.phase}")

        # Test serialization and deserialization
        state_dict = state.model_dump()
        logger.info(f"Serialized state has {len(state_dict)} keys")

        # Deserialize the state
        restored_state = OdooCodeAgentState.model_validate(state_dict)
        logger.info(f"Deserialized state phase: {restored_state.phase}")
        logger.info(f"Deserialized state feedback: {restored_state.feedback_state.feedback}")

        logger.info("Human validation workflow test completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error testing human validation workflow: {str(e)}")
        return False


def test_gemini_client():
    """Test the Gemini client."""
    logger.info("Testing Gemini client...")

    try:
        # Initialize the Gemini client
        client = gemini_client.GeminiClient()

        # Check if the client is available
        if not client.is_available:
            logger.warning("Gemini client is not available, skipping test")
            return False

        # Test generating text
        prompt = "Write a short description of Odoo 18"
        result = client.generate_text(prompt, temperature=0.2)

        if result:
            logger.info(f"Generated text (first 100 chars): {result[:100]}...")
            logger.info("Gemini client test completed successfully")
            return True
        else:
            logger.error("Failed to generate text with Gemini client")
            return False
    except Exception as e:
        logger.error(f"Error testing Gemini client: {str(e)}")
        return False


def test_fallback_models():
    """Test the fallback models."""
    logger.info("Testing fallback models...")

    try:
        # Test Gemini fallback
        prompt = "Write a short description of Odoo 18"
        result = fallback_models.generate_with_fallback(prompt, use_gemini=True, use_ollama=False)

        if result:
            logger.info(f"Generated text with Gemini (first 100 chars): {result[:100]}...")
        else:
            logger.warning("Failed to generate text with Gemini fallback")

        # Test Ollama fallback
        result = fallback_models.generate_with_fallback(prompt, use_gemini=False, use_ollama=True)

        if result:
            logger.info(f"Generated text with Ollama (first 100 chars): {result[:100]}...")
        else:
            logger.warning("Failed to generate text with Ollama fallback")

        logger.info("Fallback models test completed")
        return True
    except Exception as e:
        logger.error(f"Error testing fallback models: {str(e)}")
        return False


def test_file_saver():
    """Test the file saver."""
    logger.info("Testing file saver...")

    try:
        # Create a temporary directory for testing
        import tempfile
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory: {temp_dir}")

        # Create some test files
        files_to_create = [
            {
                "path": "__init__.py",
                "content": "# -*- coding: utf-8 -*-\n\nfrom . import models\n"
            },
            {
                "path": "models/__init__.py",
                "content": "# -*- coding: utf-8 -*-\n\nfrom . import test_model\n"
            },
            {
                "path": "models/test_model.py",
                "content": "# -*- coding: utf-8 -*-\n\nfrom odoo import models, fields, api\n\nclass TestModel(models.Model):\n    _name = 'test.model'\n    _description = 'Test Model'\n\n    name = fields.Char(string='Name', required=True)\n    description = fields.Text(string='Description')\n"
            }
        ]

        # Save the files
        result = file_saver.save_module_files(
            module_name="test_module",
            files_to_create=files_to_create,
            output_dir=temp_dir
        )

        # Check the result
        if result["success"]:
            logger.info(f"Files saved successfully to {result['module_dir']}")
            logger.info(f"Saved {result['saved_count']} files")
            logger.info(f"Saved files: {result['saved_files']}")

            # Verify that the files exist
            for file_path in result["saved_files"]:
                if os.path.exists(file_path):
                    logger.info(f"File exists: {file_path}")
                else:
                    logger.error(f"File does not exist: {file_path}")
                    return False

            logger.info("File saver test completed successfully")
            return True
        else:
            logger.error(f"Failed to save files: {result['error']}")
            return False
    except Exception as e:
        logger.error(f"Error testing file saver: {str(e)}")
        return False
    finally:
        # Clean up the temporary directory
        import shutil
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"Removed temporary directory: {temp_dir}")
        except Exception as e:
            logger.warning(f"Error removing temporary directory: {str(e)}")


def test_module_structure():
    """Test the module structure utilities."""
    logger.info("Testing module structure utilities...")

    try:
        # Test creating a module structure
        module_name = "test_module"
        structure = module_structure.create_module_structure(module_name)

        logger.info(f"Created module structure for {module_name}")
        logger.info(f"Structure has {len(structure)} entries")

        # Check that the structure contains the expected directories
        expected_dirs = ["models", "views", "security", "static"]
        for dir_name in expected_dirs:
            if dir_name in structure:
                logger.info(f"Structure contains directory: {dir_name}")
            else:
                logger.warning(f"Structure does not contain directory: {dir_name}")

        # Test creating a model file
        model_name = "test.model"
        model_content = module_structure.create_model_file(
            model_name=model_name,
            fields={
                "name": {"type": "char", "string": "Name", "required": True},
                "description": {"type": "text", "string": "Description"}
            }
        )

        logger.info(f"Created model file for {model_name}")
        logger.info(f"Model file content (first 100 chars): {model_content[:100]}...")

        logger.info("Module structure test completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error testing module structure: {str(e)}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test the Odoo Code Agent utilities")
    parser.add_argument("--docs", action="store_true", help="Test documentation helper")
    parser.add_argument("--connector", action="store_true", help="Test Odoo connector")
    parser.add_argument("--workflow", action="store_true", help="Test human validation workflow")
    parser.add_argument("--gemini", action="store_true", help="Test Gemini client")
    parser.add_argument("--fallback", action="store_true", help="Test fallback models")
    parser.add_argument("--files", action="store_true", help="Test file saver")
    parser.add_argument("--structure", action="store_true", help="Test module structure")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    args = parser.parse_args()

    logger.info("Testing Odoo Code Agent utilities")

    # Run the tests
    tests = []
    
    if args.all or args.docs:
        tests.append(("Documentation Helper", test_documentation_helper))
    
    if args.all or args.connector:
        tests.append(("Odoo Connector", test_odoo_connector))
    
    if args.all or args.workflow:
        tests.append(("Human Validation Workflow", test_human_validation_workflow))
    
    if args.all or args.gemini:
        tests.append(("Gemini Client", test_gemini_client))
    
    if args.all or args.fallback:
        tests.append(("Fallback Models", test_fallback_models))
    
    if args.all or args.files:
        tests.append(("File Saver", test_file_saver))
    
    if args.all or args.structure:
        tests.append(("Module Structure", test_module_structure))
    
    # If no tests were specified, run all tests
    if not tests:
        tests = [
            ("Documentation Helper", test_documentation_helper),
            ("Odoo Connector", test_odoo_connector),
            ("Human Validation Workflow", test_human_validation_workflow),
            ("Module Structure", test_module_structure)
        ]
    
    # Run the tests
    results = []
    for test_name, test_func in tests:
        logger.info(f"Running test: {test_name}")
        try:
            result = test_func()
            results.append((test_name, result))
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
    main()
