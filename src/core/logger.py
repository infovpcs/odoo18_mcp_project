#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Logging Configuration for Odoo 18 MCP Integration

This module provides a centralized logging configuration system.
"""

import logging
import sys
from typing import Optional

from .config import get_settings


def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Get a configured logger.

    Args:
        name: Logger name
        level: Logging level (overrides config)

    Returns:
        logging.Logger: Configured logger
    """
    settings = get_settings()
    
    # Get log level from settings or parameter
    log_level = level or settings.mcp.log_level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(numeric_level)
    
    # Create console handler if no handlers exist
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(numeric_level)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
    
    return logger