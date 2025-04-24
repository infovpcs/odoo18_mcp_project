#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the configuration management system.
"""

import os
import unittest
from unittest.mock import patch

import pytest

from src.core.config import Settings, get_settings


class TestConfig(unittest.TestCase):
    """Test the configuration management system."""

    def test_default_settings(self):
        """Test default settings."""
        settings = Settings()
        
        # Check default values
        self.assertEqual(settings.app_name, "odoo18-mcp-project")
        self.assertEqual(settings.environment, "development")
        self.assertEqual(settings.odoo.url, "http://localhost:8069")
        self.assertEqual(settings.mcp.host, "0.0.0.0")
        self.assertEqual(settings.mcp.port, 8000)
    
    def test_environment_variables(self):
        """Test loading settings from environment variables."""
        # Set environment variables
        env_vars = {
            "APP_NAME": "test-app",
            "ENVIRONMENT": "testing",
            "ODOO_URL": "https://test-odoo.example.com",
            "ODOO_DB": "test_db",
            "ODOO_USERNAME": "test_user",
            "ODOO_PASSWORD": "test_password",
            "MCP_HOST": "127.0.0.1",
            "MCP_PORT": "9000",
            "MCP_DEBUG": "true",
        }
        
        with patch.dict(os.environ, env_vars):
            # Load settings
            settings = Settings()
            
            # Check values
            self.assertEqual(settings.app_name, "test-app")
            self.assertEqual(settings.environment, "testing")
            self.assertEqual(settings.odoo.url, "https://test-odoo.example.com")
            self.assertEqual(settings.odoo.db, "test_db")
            self.assertEqual(settings.odoo.username, "test_user")
            self.assertEqual(settings.odoo.password, "test_password")
            self.assertEqual(settings.mcp.host, "127.0.0.1")
            self.assertEqual(settings.mcp.port, 9000)
            self.assertTrue(settings.mcp.debug)
    
    def test_url_validation(self):
        """Test URL validation."""
        # Test with valid URL
        with patch.dict(os.environ, {"ODOO_URL": "https://odoo.example.com"}):
            settings = Settings()
            self.assertEqual(settings.odoo.url, "https://odoo.example.com")
        
        # Test with URL without scheme
        with patch.dict(os.environ, {"ODOO_URL": "odoo.example.com"}):
            settings = Settings()
            self.assertEqual(settings.odoo.url, "http://odoo.example.com")
        
        # Test with URL with trailing slash
        with patch.dict(os.environ, {"ODOO_URL": "https://odoo.example.com/"}):
            settings = Settings()
            self.assertEqual(settings.odoo.url, "https://odoo.example.com")
    
    def test_dict_for_odoo_client(self):
        """Test dict_for_odoo_client method."""
        # Set environment variables
        env_vars = {
            "ODOO_URL": "https://test-odoo.example.com",
            "ODOO_DB": "test_db",
            "ODOO_USERNAME": "test_user",
            "ODOO_PASSWORD": "test_password",
            "ODOO_API_KEY": "test_api_key",
            "ODOO_TIMEOUT": "600",
        }
        
        with patch.dict(os.environ, env_vars):
            # Load settings
            settings = Settings()
            
            # Get dict for OdooClient
            odoo_dict = settings.dict_for_odoo_client()
            
            # Check values
            self.assertEqual(odoo_dict["url"], "https://test-odoo.example.com")
            self.assertEqual(odoo_dict["db"], "test_db")
            self.assertEqual(odoo_dict["username"], "test_user")
            self.assertEqual(odoo_dict["password"], "test_password")
            self.assertEqual(odoo_dict["api_key"], "test_api_key")
            self.assertEqual(odoo_dict["timeout"], 600)
    
    def test_get_settings_cache(self):
        """Test get_settings caching."""
        # Get settings twice
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Check that they are the same object
        self.assertIs(settings1, settings2)