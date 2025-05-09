#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for GeminiClient class.
"""

import logging
import sys
import os
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Try to import GeminiClient
    logger.info("Attempting to import GeminiClient...")
    try:
        from src.odoo_code_agent.utils.gemini_client import GeminiClient
        logger.info("Successfully imported GeminiClient")
    except ImportError as e:
        logger.error(f"Failed to import GeminiClient: {str(e)}")
        sys.exit(1)

    # Initialize GeminiClient
    logger.info("Initializing GeminiClient...")
    try:
        gemini_client = GeminiClient()
        logger.info("Successfully initialized GeminiClient")
    except Exception as e:
        logger.error(f"Failed to initialize GeminiClient: {str(e)}")
        sys.exit(1)

    # Test analyze_requirements
    logger.info("Testing analyze_requirements...")
    try:
        query = "Create a CRM mass mailing module"
        context = """
        RELEVANT ODOO MODELS:

        Model: crm.lead (CRM Lead)
        Important fields:
          - name (char): Subject
          - partner_id (many2one -> res.partner): Customer
          - email_from (char): Email
          - phone (char): Phone
          - description (text): Notes
          - type (selection): Type
          - stage_id (many2one -> crm.stage): Stage

        Model: mail.template (Email Template)
        Important fields:
          - name (char): Name
          - model_id (many2one -> ir.model): Applies to
          - subject (char): Subject
          - body_html (html): Body
          - email_from (char): From
          - email_to (char): To
          - partner_to (char): To (Partners)
        """
        
        result = gemini_client.analyze_requirements(query, context)
        logger.info(f"Analysis result: {result}")
    except Exception as e:
        logger.error(f"Failed to execute analyze_requirements: {str(e)}")
        sys.exit(1)

    logger.info("Test completed successfully")

except Exception as e:
    logger.error(f"Unexpected error: {str(e)}")
    sys.exit(1)
