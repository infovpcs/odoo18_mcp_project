"""
Core module for the Odoo 18 MCP Integration project.

This module provides core functionality such as configuration management,
logging, and security utilities.
"""

from .config import get_settings, Settings
from .logger import get_logger

__all__ = ["get_settings", "Settings", "get_logger"]