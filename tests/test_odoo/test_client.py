#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the Odoo client implementation.
"""

import unittest
from unittest.mock import patch, MagicMock

import pytest

from src.odoo.client import OdooClient, AuthenticationError, OperationError
from src.odoo.schemas import OdooConfig, SearchParams, CreateParams, UpdateParams, DeleteParams


class TestOdooClient(unittest.TestCase):
    """Test the OdooClient class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = OdooConfig(
            url="http://localhost:8069",
            db="test_db",
            username="test_user",
            password="test_password",
        )
        
        # Create a mock for the XML-RPC ServerProxy
        self.common_mock = MagicMock()
        self.models_mock = MagicMock()
        
        # Set up authentication mock
        self.common_mock.authenticate.return_value = 1  # User ID
        
        # Create client with mocked connections
        with patch('xmlrpc.client.ServerProxy') as mock_server_proxy:
            # Configure the mock to return different values for different URLs
            def side_effect(url, *args, **kwargs):
                if 'common' in url:
                    return self.common_mock
                elif 'object' in url:
                    return self.models_mock
            
            mock_server_proxy.side_effect = side_effect
            
            self.client = OdooClient(self.config)
    
    def test_authentication(self):
        """Test authentication."""
        # Authentication should have been called during setup
        self.common_mock.authenticate.assert_called_once_with(
            self.config.db,
            self.config.username,
            self.config.password,
            {}
        )
        self.assertEqual(self.client.uid, 1)
    
    def test_authentication_failure(self):
        """Test authentication failure."""
        # Set up authentication to fail
        self.common_mock.authenticate.return_value = False
        
        # Create a new client
        with patch('xmlrpc.client.ServerProxy') as mock_server_proxy:
            # Configure the mock to return different values for different URLs
            def side_effect(url, *args, **kwargs):
                if 'common' in url:
                    return self.common_mock
                elif 'object' in url:
                    return self.models_mock
            
            mock_server_proxy.side_effect = side_effect
            
            # Authentication should fail
            with self.assertRaises(AuthenticationError):
                client = OdooClient(self.config)
                client.authenticate()
    
    def test_execute(self):
        """Test execute method."""
        # Set up mock for execute_kw
        self.models_mock.execute_kw.return_value = {"id": 1, "name": "Test"}
        
        # Call execute
        result = self.client.execute(
            "res.partner",
            "read",
            [1],
            ["id", "name"]
        )
        
        # Check result
        self.assertEqual(result, {"id": 1, "name": "Test"})
        
        # Check that execute_kw was called correctly
        self.models_mock.execute_kw.assert_called_once_with(
            self.config.db,
            self.client.uid,
            self.config.password,
            "res.partner",
            "read",
            ([1], ["id", "name"]),
            {}
        )
    
    def test_search_read(self):
        """Test search_read method."""
        # Set up mock for execute
        self.models_mock.execute_kw.return_value = [{"id": 1, "name": "Test"}]
        
        # Create search params
        params = SearchParams(
            domain=[["is_company", "=", True]],
            offset=0,
            limit=10,
            order="name asc"
        )
        
        # Call search_read
        result = self.client.search_read(
            "res.partner",
            params,
            ["id", "name"]
        )
        
        # Check result
        self.assertEqual(result, [{"id": 1, "name": "Test"}])
        
        # Check that execute_kw was called correctly
        self.models_mock.execute_kw.assert_called_once_with(
            self.config.db,
            self.client.uid,
            self.config.password,
            "res.partner",
            "search_read",
            ([["is_company", "=", True]],),
            {'fields': ["id", "name"], 'offset': 0, 'limit': 10, 'order': 'name asc'}
        )
    
    def test_create(self):
        """Test create method."""
        # Set up mock for execute
        self.models_mock.execute_kw.return_value = 1  # Record ID
        
        # Create params
        params = CreateParams(
            values={"name": "Test Partner", "is_company": True}
        )
        
        # Call create
        result = self.client.create("res.partner", params)
        
        # Check result
        self.assertEqual(result, 1)
        
        # Check that execute_kw was called correctly
        self.models_mock.execute_kw.assert_called_once_with(
            self.config.db,
            self.client.uid,
            self.config.password,
            "res.partner",
            "create",
            ({"name": "Test Partner", "is_company": True},),
            {}
        )
    
    def test_update(self):
        """Test update method."""
        # Set up mock for execute
        self.models_mock.execute_kw.return_value = True
        
        # Create params
        params = UpdateParams(
            id=1,
            values={"name": "Updated Partner"}
        )
        
        # Call update
        result = self.client.update("res.partner", params)
        
        # Check result
        self.assertTrue(result)
        
        # Check that execute_kw was called correctly
        self.models_mock.execute_kw.assert_called_once_with(
            self.config.db,
            self.client.uid,
            self.config.password,
            "res.partner",
            "write",
            ([[1], {"name": "Updated Partner"}],),
            {}
        )
    
    def test_delete(self):
        """Test delete method."""
        # Set up mock for execute
        self.models_mock.execute_kw.return_value = True
        
        # Create params
        params = DeleteParams(
            ids=[1, 2]
        )
        
        # Call delete
        result = self.client.delete("res.partner", params)
        
        # Check result
        self.assertTrue(result)
        
        # Check that execute_kw was called correctly
        self.models_mock.execute_kw.assert_called_once_with(
            self.config.db,
            self.client.uid,
            self.config.password,
            "res.partner",
            "unlink",
            ([1, 2],),
            {}
        )