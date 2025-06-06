#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import tempfile

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from src.simple_odoo_code_agent.odoo_code_generator import OdooCodeGenerator
from src.simple_odoo_code_agent.utils.file_saver import save_module_files

def test_template_loading():
    """Test that templates can be loaded correctly."""
    print("Testing template loading...")
    templates = OdooCodeGenerator._load_templates(None)
    print(f"Templates loaded: {list(templates.keys())}")
    
    # Print a sample template
    if 'manifest' in templates:
        print("\nSample manifest template:")
        print(templates['manifest'][:200] + "...")
    
    return True

def test_file_saver():
    """Test that files can be saved correctly."""
    print("\nTesting file saver...")
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    print(f"Created temporary directory: {temp_dir}")
    
    # Define some files to create
    files_to_create = [
        {
            'path': '__init__.py',
            'content': '# Test module'
        },
        {
            'path': '__manifest__.py',
            'content': "{'name': 'Test Module', 'version': '1.0', 'depends': ['base']}"
        }
    ]
    
    # Save the files
    result = save_module_files(
        module_name="test_module",
        files_to_create=files_to_create,
        output_dir=temp_dir
    )
    
    # Check the result
    if result["success"]:
        print(f"Files saved successfully to {result['module_dir']}")
        print(f"Saved {result['saved_count']} files")
        print(f"Saved files: {result['saved_files']}")
        return True
    else:
        print(f"Failed to save files: {result['error']}")
        return False

# Run the tests
if __name__ == "__main__":
    print("Running tests for Odoo Code Generator...\n")
    
    template_test = test_template_loading()
    file_saver_test = test_file_saver()
    
    if template_test and file_saver_test:
        print("\nAll tests passed successfully!")
        sys.exit(0)
    else:
        print("\nSome tests failed.")
        sys.exit(1)