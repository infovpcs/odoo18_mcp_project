#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Saver utility for the Simple Odoo Code Agent.

This module provides functionality to save generated code files to disk.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)


def save_module_files(
    module_name: str,
    files_to_create: List[Dict[str, Any]],
    output_dir: str = "./generated_modules"
) -> Dict[str, Any]:
    """
    Save generated module files to disk.
    
    Args:
        module_name: The name of the module
        files_to_create: List of file dictionaries with path and content
        output_dir: The directory to save the module in
        
    Returns:
        A dictionary with the results of the save operation
    """
    try:
        # Create the output directory if it doesn't exist
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create the module directory
        module_dir = output_path / module_name
        module_dir.mkdir(exist_ok=True)
        
        # Track saved files
        saved_files = []
        saved_count = 0
        
        # Save each file
        for file_info in files_to_create:
            try:
                # Get the file path
                file_path = file_info.get("path", "")
                
                # Clean up the path to remove any module name prefix if it's already there
                if file_path.startswith(f"{module_name}/"):
                    file_path = file_path[len(module_name) + 1:]
                
                # Get the content
                content = file_info.get("content", "")
                
                # Create the full path
                full_path = module_dir / file_path
                
                # Create parent directories if they don't exist
                full_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write the file
                with open(full_path, "w") as f:
                    f.write(content)
                
                # Track the saved file
                saved_files.append(str(full_path))
                saved_count += 1
                
                logger.info(f"Saved file: {full_path}")
                
            except Exception as e:
                logger.error(f"Error saving file {file_info.get('path', 'unknown')}: {str(e)}")
                # Continue with the next file
        
        return {
            "success": True,
            "module_dir": str(module_dir),
            "saved_count": saved_count,
            "saved_files": saved_files
        }
        
    except Exception as e:
        logger.error(f"Error saving module files: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "saved_files": []
        }