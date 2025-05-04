"""
Utilities for the Odoo Code Agent.

This package provides utility modules for the Odoo Code Agent, including:
- documentation_helper: Utilities for retrieving and processing Odoo documentation
- odoo_connector: Utilities for connecting to and interacting with Odoo
- code_generator: Utilities for generating Odoo code
- module_structure: Utilities for creating proper module structure
- fallback_models: Integration with Gemini and Ollama models
"""

from .documentation_helper import DocumentationHelper, documentation_helper
from .odoo_connector import OdooConnector, odoo_connector

__all__ = [
    "DocumentationHelper",
    "documentation_helper",
    "OdooConnector",
    "odoo_connector",
]