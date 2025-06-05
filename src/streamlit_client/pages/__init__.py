#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pages Package

This package provides pages for the Streamlit client.
"""

from .documentation import render_documentation_page, render_model_documentation, render_field_documentation
from .export_import import render_export_import_page
from .improved_odoo_generator import render_improved_odoo_generator_page
from .deepwiki import render_deepwiki_page
from .graph_visualization import render_graph_visualization_page

# Note: The following modules are commented out as they don't exist yet
# from .advanced import render_advanced_page
# from .chat import render_chat_page
