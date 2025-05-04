#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Documentation Helper for Odoo Code Agent

This module provides utilities for retrieving and processing Odoo documentation
to assist with code generation.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

# Import the Odoo documentation retriever if available
try:
    from src.odoo_docs_rag.docs_retriever import OdooDocsRetriever
    odoo_docs_available = True
except ImportError:
    odoo_docs_available = False

logger = logging.getLogger(__name__)


class DocumentationHelper:
    """Helper class for retrieving and processing Odoo documentation."""

    def __init__(
        self,
        docs_dir: Optional[str] = None,
        index_dir: Optional[str] = None,
        force_rebuild: bool = False,
    ):
        """Initialize the documentation helper.

        Args:
            docs_dir: Directory to store the documentation files
            index_dir: Directory to store the index files
            force_rebuild: Whether to force rebuilding the index
        """
        self.docs_dir = docs_dir or "odoo_docs"
        self.index_dir = index_dir or "odoo_docs_index"
        self.force_rebuild = force_rebuild
        self.retriever = None

        # Initialize the retriever if available
        if odoo_docs_available:
            self._initialize_retriever()
        else:
            logger.warning("Odoo documentation retriever not available. "
                          "Install the required dependencies: sentence-transformers, "
                          "faiss-cpu, beautifulsoup4, markdown, gitpython")

    def _initialize_retriever(self) -> bool:
        """Initialize the Odoo documentation retriever.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Create directories if they don't exist
            os.makedirs(self.docs_dir, exist_ok=True)
            os.makedirs(self.index_dir, exist_ok=True)

            # Initialize the retriever
            self.retriever = OdooDocsRetriever(
                docs_dir=self.docs_dir,
                index_dir=self.index_dir,
                force_rebuild=self.force_rebuild
            )

            logger.info("Odoo documentation retriever initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Odoo documentation retriever: {str(e)}")
            self.retriever = None
            return False

    def query_documentation(
        self,
        query: str,
        max_results: int = 5,
        min_score: float = 0.5,
    ) -> Union[str, List[Dict[str, Any]]]:
        """Query the Odoo documentation.

        Args:
            query: Query text
            max_results: Maximum number of results to return
            min_score: Minimum similarity score for results

        Returns:
            Either a formatted string with the results or a list of result dictionaries
        """
        if not self.retriever:
            if odoo_docs_available:
                success = self._initialize_retriever()
                if not success:
                    return "Failed to initialize Odoo documentation retriever"
            else:
                return "Odoo documentation retriever not available"

        try:
            # Query the documentation
            results = self.retriever.retrieve(query, max_results=max_results, min_score=min_score)
            return results
        except Exception as e:
            logger.error(f"Error querying Odoo documentation: {str(e)}")
            return f"Error querying Odoo documentation: {str(e)}"

    def get_formatted_results(
        self,
        query: str,
        max_results: int = 5,
        min_score: float = 0.5,
    ) -> str:
        """Get formatted results from the Odoo documentation.

        Args:
            query: Query text
            max_results: Maximum number of results to return
            min_score: Minimum similarity score for results

        Returns:
            Formatted string with the results
        """
        if not self.retriever:
            if odoo_docs_available:
                success = self._initialize_retriever()
                if not success:
                    return "Failed to initialize Odoo documentation retriever"
            else:
                return "Odoo documentation retriever not available"

        try:
            # Query the documentation
            return self.retriever.query(query, max_results=max_results, min_score=min_score)
        except Exception as e:
            logger.error(f"Error querying Odoo documentation: {str(e)}")
            return f"Error querying Odoo documentation: {str(e)}"

    def get_model_documentation(self, model_name: str) -> str:
        """Get documentation for a specific Odoo model.

        Args:
            model_name: Name of the Odoo model

        Returns:
            Formatted string with the model documentation
        """
        query = f"Odoo 18 model {model_name} fields and methods"
        return self.get_formatted_results(query, max_results=3)

    def get_field_documentation(self, model_name: str, field_name: str) -> str:
        """Get documentation for a specific field in an Odoo model.

        Args:
            model_name: Name of the Odoo model
            field_name: Name of the field

        Returns:
            Formatted string with the field documentation
        """
        query = f"Odoo 18 model {model_name} field {field_name}"
        return self.get_formatted_results(query, max_results=2)

    def get_method_documentation(self, model_name: str, method_name: str) -> str:
        """Get documentation for a specific method in an Odoo model.

        Args:
            model_name: Name of the Odoo model
            method_name: Name of the method

        Returns:
            Formatted string with the method documentation
        """
        query = f"Odoo 18 model {model_name} method {method_name}"
        return self.get_formatted_results(query, max_results=2)

    def get_view_documentation(self, view_type: str) -> str:
        """Get documentation for a specific view type in Odoo.

        Args:
            view_type: Type of the view (form, tree, kanban, etc.)

        Returns:
            Formatted string with the view documentation
        """
        query = f"Odoo 18 {view_type} view definition and attributes"
        return self.get_formatted_results(query, max_results=3)

    def get_inheritance_documentation(self) -> str:
        """Get documentation for Odoo model inheritance.

        Returns:
            Formatted string with the inheritance documentation
        """
        query = "Odoo 18 model inheritance types and implementation"
        return self.get_formatted_results(query, max_results=3)

    def get_security_documentation(self) -> str:
        """Get documentation for Odoo security.

        Returns:
            Formatted string with the security documentation
        """
        query = "Odoo 18 security access rights and rules"
        return self.get_formatted_results(query, max_results=3)

    def get_module_structure_documentation(self) -> str:
        """Get documentation for Odoo module structure.

        Returns:
            Formatted string with the module structure documentation
        """
        query = "Odoo 18 module structure and manifest"
        return self.get_formatted_results(query, max_results=3)


# Create a singleton instance
documentation_helper = DocumentationHelper()