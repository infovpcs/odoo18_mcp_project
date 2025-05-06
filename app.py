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

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

# Import the Streamlit client
from src.streamlit_client import main

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("app")

if __name__ == "__main__":
    # Run the Streamlit client
    main()
