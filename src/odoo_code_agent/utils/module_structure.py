# src/agents/odoo_code_agent/utils/module_structure.py
import os
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def create_module_structure(module_name: str, base_path: str = ".") -> Dict[str, Any]:
    """
    Create the structure for an Odoo module.

    Args:
        module_name: Name of the module
        base_path: Base path where the module should be created

    Returns:
        Dictionary with the module structure
    """
    module_path = os.path.join(base_path, module_name)
    
    # Define the module structure
    structure = {
        "__init__.py": "from . import models\n",
        "__manifest__.py": generate_manifest(module_name),
        "models": {
            "__init__.py": "from . import models\n",
            "models.py": "from odoo import models, fields, api\n\n# Your models here\n"
        },
        "views": {
            "views.xml": "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<odoo>\n    <!-- Views will go here -->\n</odoo>"
        },
        "security": {
            "ir.model.access.csv": "id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink\n"
        },
        "static": {
            "description": {
                "icon.png": ""
            }
        }
    }
    
    return structure


def generate_manifest(module_name: str) -> str:
    """
    Generate the __manifest__.py content for an Odoo module.

    Args:
        module_name: Name of the module

    Returns:
        Content of the __manifest__.py file
    """
    # Convert module_name to a more readable format
    display_name = module_name.replace("_", " ").title()
    
    manifest = f"""{{
    'name': '{display_name}',
    'version': '1.0',
    'category': 'Custom',
    'summary': 'Custom Odoo Module',
    'description': \"\"\"
{display_name}
=============
This module provides custom functionality for Odoo 18.
\"\"\",
    'author': 'Your Company',
    'website': 'https://www.example.com',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}}"""
    
    return manifest


def create_module_files(module_structure: Dict[str, Any], base_path: str = ".") -> List[Dict[str, Any]]:
    """
    Create a list of files to be created based on the module structure.

    Args:
        module_structure: Dictionary with the module structure
        base_path: Base path where the module should be created

    Returns:
        List of dictionaries with file paths and contents
    """
    files_to_create = []
    
    def process_structure(structure, current_path):
        for key, value in structure.items():
            path = os.path.join(current_path, key)
            if isinstance(value, dict):
                # This is a directory, process its contents
                process_structure(value, path)
            else:
                # This is a file, add it to the list
                files_to_create.append({
                    "path": path,
                    "content": value
                })
    
    process_structure(module_structure, base_path)
    return files_to_create


def create_files_on_disk(files_to_create: List[Dict[str, Any]]) -> List[str]:
    """
    Create the files on disk.

    Args:
        files_to_create: List of dictionaries with file paths and contents

    Returns:
        List of created file paths
    """
    created_files = []
    
    for file_info in files_to_create:
        path = file_info["path"]
        content = file_info["content"]
        
        # Create the directory if it doesn't exist
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        # Write the file
        with open(path, "w") as f:
            f.write(content)
        
        created_files.append(path)
    
    return created_files