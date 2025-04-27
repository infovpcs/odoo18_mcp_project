"""
Odoo Documentation RAG (Retrieval Augmented Generation) Module

This module provides functionality for retrieving information from the Odoo 18 documentation
using RAG techniques. It includes components for processing documentation, creating embeddings,
and retrieving relevant information based on queries.
"""

from .docs_retriever import OdooDocsRetriever
from .docs_processor import OdooDocsProcessor
from .embedding_engine import EmbeddingEngine

__all__ = ["OdooDocsRetriever", "OdooDocsProcessor", "EmbeddingEngine"]