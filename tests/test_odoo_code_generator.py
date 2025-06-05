#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test for OdooCodeGenerator

This module tests the OdooCodeGenerator class from the simple_odoo_code_agent package.
It verifies that the generator can properly create Odoo module code with the expected
structure and content.
"""

import os
import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any

from src.simple_odoo_code_agent.odoo_code_generator import OdooCodeGenerator, OdooCodeFile

# Configure test constants
TEST_MODULE_NAME = "test_library"
TEST_REQUIREMENTS = """
Create a simple Odoo module for managing a library. The module should have:
1. A 'library.book' model with fields for title, author, ISBN, publication date, and genre
2. A 'library.member' model for library members with name, email, and membership status
3. A 'library.checkout' model to track book borrowing with relations to books and members
4. Views for all models (form, list)
5. Basic security access rights
6. A simple dashboard for librarians
"""

@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for test output files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after the test
    shutil.rmtree(temp_dir)

@pytest.mark.asyncio
async def test_odoo_code_generator_initialization():
    """Test that the OdooCodeGenerator initializes correctly."""
    # Test with default parameters
    api_key = os.environ.get("GEMINI_API_KEY", "test_api_key")
    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")
    generator = OdooCodeGenerator(api_key=api_key, model=model)
    assert generator.model == model
    assert generator.api_key is not None
    assert "manifest" in generator.templates
    assert "init" in generator.templates
    assert "models_init" in generator.templates

@pytest.mark.asyncio
async def test_extract_files_from_response():
    """Test the file extraction from LLM response."""
    api_key = os.environ.get("GEMINI_API_KEY", "test_api_key")
    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")
    generator = OdooCodeGenerator(api_key=api_key, model=model)
    
    # Mock LLM response with file definitions
    mock_response = """
    # /test_module/__manifest__.py
    ```python
    # -*- coding: utf-8 -*-
    {
        "name": "Test Module",
        "version": "1.0",
        "depends": ["base"],
    }
    ```
    
    # /test_module/models/test_model.py
    ```python
    from odoo import models, fields
    
    class TestModel(models.Model):
        _name = 'test.model'
        name = fields.Char()
    ```
    """
    
    files = generator._extract_files_from_response(mock_response, "test_module")
    
    # Verify extraction results
    assert len(files) == 2
    assert any(f.path == "test_module/__manifest__.py" for f in files)
    assert any(f.path == "test_module/models/test_model.py" for f in files)
    
    # Check content extraction
    manifest_file = next(f for f in files if f.path == "test_module/__manifest__.py")
    assert '"name": "Test Module"' in manifest_file.content
    assert '"version": "1.0"' in manifest_file.content
    assert '"depends": ["base"]' in manifest_file.content

@pytest.mark.asyncio
async def test_merge_files():
    """Test merging original and updated files."""
    api_key = os.environ.get("GEMINI_API_KEY", "test_api_key")
    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")
    generator = OdooCodeGenerator(api_key=api_key, model=model)
    
    # Create original files
    original_files = [
        OdooCodeFile("test_module/__manifest__.py", "# Original manifest", "python"),
        OdooCodeFile("test_module/models/model1.py", "# Original model1", "python")
    ]
    
    # Create updated files (one updated, one new)
    updated_files = [
        OdooCodeFile("test_module/__manifest__.py", "# Updated manifest", "python"),
        OdooCodeFile("test_module/models/model2.py", "# New model2", "python")
    ]
    
    # Merge the files
    merged_files = generator._merge_files(original_files, updated_files)
    
    # Verify merge results
    assert len(merged_files) == 3  # Should have all three files
    
    # Check that the manifest was updated
    manifest_file = next(f for f in merged_files if f.get_full_path() == "test_module/__manifest__.py")
    assert manifest_file.content == "# Updated manifest"
    
    # Check that both model files are present
    assert any(f.get_full_path() == "test_module/models/model1.py" for f in merged_files)
    assert any(f.get_full_path() == "test_module/models/model2.py" for f in merged_files)

@pytest.mark.asyncio
async def test_generate_odoo_module(temp_output_dir, monkeypatch):
    """Test the full module generation process."""
    api_key = os.environ.get("GEMINI_API_KEY", "test_api_key")
    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")
    generator = OdooCodeGenerator(api_key=api_key, model=model)
    
    # Mock the _generate_initial_code method to avoid actual API calls
    async def mock_generate_initial_code(module_name, requirements, documentation):
        # Return a mock response and files
        mock_files = [
            OdooCodeFile(f"{module_name}/__manifest__.py", "# Mock manifest", "python"),
            OdooCodeFile(f"{module_name}/__init__.py", "# Mock init", "python"),
            OdooCodeFile(f"{module_name}/models/__init__.py", "# Mock models init", "python"),
            OdooCodeFile(f"{module_name}/models/library_book.py", "# Mock book model", "python")
        ]
        return "Mock response", mock_files
    
    # Mock the _validate_and_enhance_code method
    async def mock_validate_and_enhance_code(module_name, requirements, files, documentation):
        # Just return the same files for testing
        return files
    
    # Apply the monkeypatches
    monkeypatch.setattr(generator, "_generate_initial_code", mock_generate_initial_code)
    monkeypatch.setattr(generator, "_validate_and_enhance_code", mock_validate_and_enhance_code)
    
    # Run the generate_odoo_module method
    result = await generator.generate_odoo_module(
        module_name=TEST_MODULE_NAME,
        requirements=TEST_REQUIREMENTS,
        save_to_disk=True,
        output_dir=temp_output_dir,
        validation_iterations=1
    )
    
    # Verify the result
    assert result["module_name"] == TEST_MODULE_NAME
    assert result["requirements"] == TEST_REQUIREMENTS
    assert result["file_count"] == 4
    
    # Check that files were saved to disk
    assert os.path.exists(os.path.join(temp_output_dir, TEST_MODULE_NAME, "__manifest__.py"))
    assert os.path.exists(os.path.join(temp_output_dir, TEST_MODULE_NAME, "__init__.py"))
    assert os.path.exists(os.path.join(temp_output_dir, TEST_MODULE_NAME, "models", "__init__.py"))
    assert os.path.exists(os.path.join(temp_output_dir, TEST_MODULE_NAME, "models", "library_book.py"))

@pytest.mark.asyncio
async def test_odoo_code_file_class():
    """Test the OdooCodeFile class functionality."""
    # Test with explicit extension
    file1 = OdooCodeFile("test_module/models/test_model.py", "# Test content", "python")
    assert file1.get_full_path() == "test_module/models/test_model.py"
    assert file1.language == "python"
    assert file1.content == "# Test content"
    
    # Test with extension determined from language
    file2 = OdooCodeFile("test_module/models/test_model", "# Test content", "python")
    assert file2.get_full_path() == "test_module/models/test_model.py"
    
    # Test with different language
    file3 = OdooCodeFile("test_module/views/test_view", "<record id='test'></record>", "xml")
    assert file3.get_full_path() == "test_module/views/test_view.xml"
    
    # Test string representation
    assert str(file1).startswith("OdooCodeFile(path='test_module/models/test_model.py'")

@pytest.mark.asyncio
async def test_format_manifest():
    """Test the manifest formatting function."""
    api_key = os.environ.get("GEMINI_API_KEY", "test_api_key")
    model = os.environ.get("GEMINI_MODEL", "gemini-1.5-pro")
    generator = OdooCodeGenerator(api_key=api_key, model=model)
    
    manifest = generator._format_manifest(
        module_name="test_module",
        module_title="Test Module",
        summary="A test module",
        description="This is a test module\nwith multiple lines",
        depends=["base", "mail"],
        data_files=["views/test_view.xml"],
        is_app=True
    )
    
    # Verify manifest content
    assert "'name': 'Test Module'" in manifest
    assert "'summary': 'A test module'" in manifest
    assert "'description': '''" in manifest
    assert "This is a test module" in manifest
    assert "'depends':" in manifest
    assert '"base"' in manifest
    assert '"mail"' in manifest
    assert "'data':" in manifest
    assert '"views/test_view.xml"' in manifest
    assert "'application': true" in manifest

if __name__ == "__main__":
    pytest.main(['-xvs', __file__])