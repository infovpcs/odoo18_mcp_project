# src/odoo_code_agent/utils/module_structure.py
import os
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def create_module_structure(module_name: str, base_path: str = ".") -> Dict[str, Any]:
    """
    Create the structure for an Odoo module following Odoo 18 standards.

    Args:
        module_name: Name of the module
        base_path: Base path where the module should be created

    Returns:
        Dictionary with the module structure
    """
    # Add _vpcs_ext suffix to prevent conflicts with existing Odoo apps
    if not module_name.endswith("_vpcs_ext"):
        module_name = f"{module_name}_vpcs_ext"

    module_path = os.path.join(base_path, module_name)

    # Define the module structure
    structure = {
        "__init__.py": "from . import models\nfrom . import controllers\nfrom . import wizard\n",
        "__manifest__.py": generate_manifest(module_name),
        "README.md": generate_readme(module_name),
        "models": {
            "__init__.py": "# -*- coding: utf-8 -*-\n# Register your models here\n",
            "models.py": "# -*- coding: utf-8 -*-\n\nfrom odoo import models, fields, api, _\n\n# Your models here\n"
        },
        "controllers": {
            "__init__.py": "# -*- coding: utf-8 -*-\n# Register your controllers here\n",
            "main.py": "# -*- coding: utf-8 -*-\n\nfrom odoo import http\nfrom odoo.http import request\n\n# Your controllers here\n"
        },
        "wizard": {
            "__init__.py": "# -*- coding: utf-8 -*-\n# Register your wizards here\n"
        },
        "views": {
            "templates.xml": "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<odoo>\n    <!-- Templates will go here -->\n</odoo>",
            "views.xml": "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<odoo>\n    <!-- Views will go here -->\n</odoo>",
            "menus.xml": "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<odoo>\n    <!-- Menu items will go here -->\n</odoo>"
        },
        "data": {
            "data.xml": "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<odoo>\n    <!-- Data records will go here -->\n</odoo>"
        },
        "security": {
            "ir.model.access.csv": "id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink\n",
            "security_groups.xml": "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<odoo>\n    <!-- Security groups will go here -->\n</odoo>"
        },
        "static": {
            "description": {
                "icon.png": "",
                "index.html": "<!-- Module description HTML -->"
            },
            "src": {
                "js": {
                    "module_name.js": "/** JavaScript code for the module */\n"
                },
                "scss": {
                    "module_name.scss": "/* SCSS styles for the module */\n"
                },
                "xml": {
                    "templates.xml": "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<!-- QWeb templates will go here -->\n"
                }
            }
        },
        "tests": {
            "__init__.py": "# -*- coding: utf-8 -*-\n# Register your tests here\n",
            "test_module.py": "# -*- coding: utf-8 -*-\n\nfrom odoo.tests import common\n\nclass Test{}(common.TransactionCase):\n    def setUp(self):\n        super().setUp()\n        # Setup test data\n\n    def test_feature(self):\n        # Test implementation\n        pass\n".format(module_name.replace('_', ' ').title().replace(' ', ''))
        }
    }

    return structure


def generate_readme(module_name: str) -> str:
    """
    Generate the README.md content for an Odoo module.

    Args:
        module_name: Name of the module

    Returns:
        Content of the README.md file
    """
    # Ensure module_name has the _vpcs_ext suffix
    if not module_name.endswith("_vpcs_ext"):
        module_name = f"{module_name}_vpcs_ext"

    # Convert module_name to a more readable format for display
    # Remove the _vpcs_ext suffix for display purposes
    display_name = module_name.replace("_vpcs_ext", "").replace("_", " ").title()

    readme = f"""# {display_name}

This module provides custom functionality for Odoo 18.

## Features

- Feature 1
- Feature 2
- Feature 3

## Usage

Describe how to use the module here.

## Technical Information

Technical details about the implementation.

## Contributors

- Your Name <your.email@example.com>
"""

    return readme


def generate_manifest(module_name: str) -> str:
    """
    Generate the __manifest__.py content for an Odoo module following Odoo 18 standards.

    Args:
        module_name: Name of the module

    Returns:
        Content of the __manifest__.py file
    """
    # Ensure module_name has the _vpcs_ext suffix
    if not module_name.endswith("_vpcs_ext"):
        module_name = f"{module_name}_vpcs_ext"

    # Convert module_name to a more readable format for display
    # Remove the _vpcs_ext suffix for display purposes
    display_name = module_name.replace("_vpcs_ext", "").replace("_", " ").title()

    manifest = f"""# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{{
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
    'depends': ['base', 'mail'],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/menus.xml',
        'data/data.xml',
    ],
    'assets': {{
        'web.assets_backend': [
            '{module_name}/static/src/js/{module_name}.js',
            '{module_name}/static/src/scss/{module_name}.scss',
            '{module_name}/static/src/xml/templates.xml',
        ],
    }},
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
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