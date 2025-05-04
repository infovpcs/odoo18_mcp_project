#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utility for saving generated Odoo module files to disk.
"""

import os
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("odoo_code_agent.file_saver")

def save_module_files(module_name: str, files_to_create: List[Dict[str, str]], output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Save generated module files to disk.
    
    Args:
        module_name: The name of the module
        files_to_create: List of dictionaries with 'path' and 'content' keys
        output_dir: Optional directory to save the files to (defaults to ./generated_modules)
        
    Returns:
        Dictionary with results of the save operation
    """
    if not output_dir:
        output_dir = os.path.join(os.getcwd(), "generated_modules")
    
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            logger.info(f"Created output directory: {output_dir}")
        except Exception as e:
            logger.error(f"Error creating output directory: {str(e)}")
            return {
                "success": False,
                "error": f"Error creating output directory: {str(e)}",
                "saved_files": []
            }
    
    # Create the module directory
    module_dir = os.path.join(output_dir, module_name)
    if not os.path.exists(module_dir):
        try:
            os.makedirs(module_dir)
            logger.info(f"Created module directory: {module_dir}")
        except Exception as e:
            logger.error(f"Error creating module directory: {str(e)}")
            return {
                "success": False,
                "error": f"Error creating module directory: {str(e)}",
                "saved_files": []
            }
    
    # Save each file
    saved_files = []
    errors = []
    
    for file_info in files_to_create:
        if not isinstance(file_info, dict):
            logger.warning(f"Invalid file info: {file_info}")
            continue
            
        file_path = file_info.get('path', '')
        file_content = file_info.get('content', '')
        
        if not file_path:
            logger.warning("File path is empty, skipping")
            continue
        
        # Handle paths with or without module name prefix
        if file_path.startswith(f"{module_name}/"):
            # Path already includes module name, use as is
            relative_path = file_path
        else:
            # Add module name prefix
            relative_path = os.path.join(module_name, file_path)
        
        # Get the full path
        full_path = os.path.join(output_dir, relative_path)
        
        # Create parent directories if they don't exist
        parent_dir = os.path.dirname(full_path)
        if not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir)
                logger.info(f"Created directory: {parent_dir}")
            except Exception as e:
                error_msg = f"Error creating directory {parent_dir}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
        
        # Save the file
        try:
            with open(full_path, 'w') as f:
                f.write(file_content)
            logger.info(f"Saved file: {full_path}")
            saved_files.append(full_path)
        except Exception as e:
            error_msg = f"Error saving file {full_path}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
    
    # Return the results
    return {
        "success": len(saved_files) > 0,
        "module_dir": module_dir,
        "saved_files": saved_files,
        "errors": errors,
        "total_files": len(files_to_create),
        "saved_count": len(saved_files),
        "error_count": len(errors)
    }
