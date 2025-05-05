#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import unittest
import tempfile
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.odoo_code_agent.utils.module_structure import (
    create_module_structure,
    generate_manifest,
    generate_readme,
    create_module_files,
    create_files_on_disk
)


class TestModuleStructure(unittest.TestCase):
    """Test the module structure implementation."""

    def setUp(self):
        """Set up the test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.module_name = "test_module"
        self.module_path = os.path.join(self.temp_dir, self.module_name)

    def tearDown(self):
        """Clean up the test environment."""
        shutil.rmtree(self.temp_dir)

    def test_create_module_structure(self):
        """Test the create_module_structure function."""
        structure = create_module_structure(self.module_name, self.temp_dir)

        # Check that the structure contains the expected keys
        self.assertIn("__init__.py", structure)
        self.assertIn("__manifest__.py", structure)
        self.assertIn("README.md", structure)
        self.assertIn("models", structure)
        self.assertIn("controllers", structure)
        self.assertIn("wizard", structure)
        self.assertIn("views", structure)
        self.assertIn("data", structure)
        self.assertIn("security", structure)
        self.assertIn("static", structure)
        self.assertIn("tests", structure)

        # Check that the models directory contains the expected files
        self.assertIn("__init__.py", structure["models"])
        self.assertIn("models.py", structure["models"])

        # Check that the controllers directory contains the expected files
        self.assertIn("__init__.py", structure["controllers"])
        self.assertIn("main.py", structure["controllers"])

        # Check that the views directory contains the expected files
        self.assertIn("templates.xml", structure["views"])
        self.assertIn("views.xml", structure["views"])
        self.assertIn("menus.xml", structure["views"])

        # Check that the security directory contains the expected files
        self.assertIn("ir.model.access.csv", structure["security"])
        self.assertIn("security_groups.xml", structure["security"])

        # Check that the static directory contains the expected directories
        self.assertIn("description", structure["static"])
        self.assertIn("src", structure["static"])

        # Check that the static/src directory contains the expected directories
        self.assertIn("js", structure["static"]["src"])
        self.assertIn("scss", structure["static"]["src"])
        self.assertIn("xml", structure["static"]["src"])

    def test_generate_manifest(self):
        """Test the generate_manifest function."""
        manifest = generate_manifest(self.module_name)

        # Check that the manifest contains the expected content
        self.assertIn("# -*- coding: utf-8", manifest)
        self.assertIn("'name': 'Test Module'", manifest)
        self.assertIn("'version': '1.0'", manifest)
        self.assertIn("'category': 'Custom'", manifest)
        self.assertIn("'depends': ['base', 'mail']", manifest)
        self.assertIn("'data': [", manifest)
        self.assertIn("'security/security_groups.xml'", manifest)
        self.assertIn("'security/ir.model.access.csv'", manifest)
        self.assertIn("'views/views.xml'", manifest)
        self.assertIn("'views/templates.xml'", manifest)
        self.assertIn("'views/menus.xml'", manifest)
        self.assertIn("'data/data.xml'", manifest)
        self.assertIn("'assets': {", manifest)
        self.assertIn("'web.assets_backend': [", manifest)
        self.assertIn(f"'{self.module_name}/static/src/js/{self.module_name}.js'", manifest)
        self.assertIn(f"'{self.module_name}/static/src/scss/{self.module_name}.scss'", manifest)
        self.assertIn(f"'{self.module_name}/static/src/xml/templates.xml'", manifest)
        self.assertIn("'license': 'LGPL-3'", manifest)

    def test_generate_readme(self):
        """Test the generate_readme function."""
        readme = generate_readme(self.module_name)

        # Check that the readme contains the expected content
        self.assertIn("# Test Module", readme)
        self.assertIn("This module provides custom functionality for Odoo 18.", readme)
        self.assertIn("## Features", readme)
        self.assertIn("## Usage", readme)
        self.assertIn("## Technical Information", readme)
        self.assertIn("## Contributors", readme)

    def test_create_module_files(self):
        """Test the create_module_files function."""
        structure = create_module_structure(self.module_name, self.temp_dir)
        files = create_module_files(structure, self.temp_dir)

        # Check that the files list contains the expected number of files
        self.assertGreater(len(files), 10)

        # Check that each file has a path and content
        for file_info in files:
            self.assertIn("path", file_info)
            self.assertIn("content", file_info)
            self.assertTrue(file_info["path"].startswith(self.temp_dir))

    def test_create_files_on_disk(self):
        """Test the create_files_on_disk function."""
        # Create the module structure directly in the temp_dir
        structure = create_module_structure(self.module_name)
        files = create_module_files(structure, self.temp_dir)
        created_files = create_files_on_disk(files)

        # Check that the created_files list contains the expected number of files
        self.assertGreater(len(created_files), 10)

        # Check that each file exists on disk
        for file_path in created_files:
            self.assertTrue(os.path.exists(file_path))

        # The module path is now directly in the temp_dir
        module_path = self.temp_dir

        # Check that the key files exist
        self.assertTrue(os.path.isfile(os.path.join(module_path, "__init__.py")))
        self.assertTrue(os.path.isfile(os.path.join(module_path, "__manifest__.py")))
        self.assertTrue(os.path.isfile(os.path.join(module_path, "README.md")))

        # Check that the module directory structure is correct
        self.assertTrue(os.path.isdir(os.path.join(module_path, "models")))
        self.assertTrue(os.path.isdir(os.path.join(module_path, "controllers")))
        self.assertTrue(os.path.isdir(os.path.join(module_path, "wizard")))
        self.assertTrue(os.path.isdir(os.path.join(module_path, "views")))
        self.assertTrue(os.path.isdir(os.path.join(module_path, "data")))
        self.assertTrue(os.path.isdir(os.path.join(module_path, "security")))
        self.assertTrue(os.path.isdir(os.path.join(module_path, "static")))
        self.assertTrue(os.path.isdir(os.path.join(module_path, "tests")))

        # Check that the key files exist in subdirectories
        self.assertTrue(os.path.isfile(os.path.join(module_path, "models", "__init__.py")))
        self.assertTrue(os.path.isfile(os.path.join(module_path, "models", "models.py")))
        self.assertTrue(os.path.isfile(os.path.join(module_path, "controllers", "__init__.py")))
        self.assertTrue(os.path.isfile(os.path.join(module_path, "controllers", "main.py")))
        self.assertTrue(os.path.isfile(os.path.join(module_path, "views", "views.xml")))
        self.assertTrue(os.path.isfile(os.path.join(module_path, "security", "ir.model.access.csv")))


if __name__ == "__main__":
    unittest.main()