#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for the Odoo Code Agent utilities.
"""

import os
import sys
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_odoo_code_agent_utils")

# Load environment variables
load_dotenv()

# Import the utilities
try:
    from src.odoo_code_agent.utils import documentation_helper, odoo_connector, gemini_client, fallback_models
    from src.odoo_code_agent.main import OdooCodeAgentState, AgentPhase
except ImportError:
    logger.error("Failed to import Odoo Code Agent utilities. Make sure the package is installed.")
    sys.exit(1)


def test_documentation_helper():
    """Test the documentation helper."""
    logger.info("Testing documentation helper...")

    # Force rebuild the index to ensure dimensions match
    logger.info("Forcing rebuild of documentation index...")
    documentation_helper.force_rebuild_index()

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

    logger.info("Documentation helper test completed")


def test_odoo_connector():
    """Test the Odoo connector."""
    logger.info("Testing Odoo connector...")

    try:
        # Test getting models list - fix the fields to match Odoo 18
        models = odoo_connector.search_read(
            'ir.model',
            [('state', '=', 'base')],
            ['name', 'model', 'info', 'modules']
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


def main():
    """Main function."""
    logger.info("Testing Odoo Code Agent utilities")

    # Test documentation helper
    test_documentation_helper()

    # Test Odoo connector
    test_odoo_connector()

    # Test human validation workflow
    test_human_validation_workflow()

    # Test Gemini client (if available)
    test_gemini_client()

    # Test fallback models (if available)
    test_fallback_models()

    logger.info("All tests completed")


if __name__ == "__main__":
    main()
