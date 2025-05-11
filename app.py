#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit App for Odoo 18 MCP Client

This is the main entry point for the Streamlit app.
"""

import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Import the Streamlit client
from src.streamlit_client import main

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("app")

# Log environment variables for debugging (without showing sensitive values)
logger.info("Environment variables loaded:")
brave_api_key = os.getenv('BRAVE_API_KEY')
gemini_api_key = os.getenv('GEMINI_API_KEY')
gemini_model = os.getenv('GEMINI_MODEL')

logger.info(f"BRAVE_API_KEY set: {'Yes' if brave_api_key else 'No'}")
logger.info(f"GEMINI_API_KEY set: {'Yes' if gemini_api_key else 'No'}")
logger.info(f"GEMINI_MODEL set: {'Yes' if gemini_model else 'No'}")

# Print the first few characters of the keys for verification (if they exist)
if brave_api_key:
    logger.info(f"BRAVE_API_KEY first 4 chars: {brave_api_key[:4]}...")
if gemini_api_key:
    logger.info(f"GEMINI_API_KEY first 4 chars: {gemini_api_key[:4]}...")
if gemini_model:
    logger.info(f"GEMINI_MODEL value: {gemini_model}")

if __name__ == "__main__":
    # Run the Streamlit client
    main()
