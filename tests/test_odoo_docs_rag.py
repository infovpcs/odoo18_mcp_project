#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the Odoo Documentation RAG module.

This script tests the functionality of the Odoo Documentation RAG module
by initializing the retriever and performing a few test queries.
"""

import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_odoo_docs_rag")

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the Odoo Documentation RAG module
    from src.odoo_docs_rag import OdooDocsRetriever

    def test_odoo_docs_retriever():
        """Test the Odoo Documentation RAG module."""
        logger.info("Testing Odoo Documentation RAG module...")

        # Set up directories
        docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "odoo_docs")
        index_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "odoo_docs_index")

        # Create directories if they don't exist
        os.makedirs(docs_dir, exist_ok=True)
        os.makedirs(index_dir, exist_ok=True)

        # Check if the required dependencies are available
        try:
            import sentence_transformers
            import faiss
            import bs4
            import markdown
            import git
            logger.info("All required dependencies for Odoo documentation retriever are available")
        except ImportError as e:
            logger.error(f"Missing dependency: {e}")
            logger.error("Please install the required dependencies: sentence-transformers, faiss-cpu, beautifulsoup4, markdown, gitpython")
            return

        # Initialize the retriever
        logger.info("Initializing Odoo Documentation Retriever...")
        try:
            retriever = OdooDocsRetriever(
                docs_dir=docs_dir,
                index_dir=index_dir,
                force_rebuild=True  # Force rebuilding the index with our improved implementation
            )
        except Exception as e:
            logger.error(f"Error initializing Odoo Documentation Retriever: {e}")
            return

        # Test queries
        test_queries = [
            "How to create a custom module in Odoo 18",
            "Odoo 18 ORM API reference",
            "Odoo 18 view inheritance",
            "How to implement a wizard in Odoo 18",
            "Odoo 18 security and access rights",
            # Add our specific test cases
            "How to configure Odoo taxes with 18.0",
            "How to configure taxes with indian localization part",
            "Indian GST configuration in Odoo 18",
            "E-invoicing setup for India in Odoo"
        ]

        for query in test_queries:
            logger.info(f"Testing query: {query}")
            try:
                result = retriever.query(query, max_results=3)

                # Print the first 200 characters of the result
                logger.info(f"Result: {result[:200]}...")
            except Exception as e:
                logger.error(f"Error querying: {e}")
            logger.info("-" * 80)

        logger.info("Odoo Documentation RAG module tests completed successfully!")

    def test_embedding_storage():
        """Test the embedding storage functionality using the database."""
        logger.info("Testing embedding storage using database...")

        # Import necessary modules
        from src.odoo_docs_rag.db_storage import EmbeddingDatabase
        from src.odoo_docs_rag.embedding_engine import EmbeddingEngine
        import numpy as np
        import os
        import tempfile
        import shutil

        # Create a temporary directory for the database
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_embeddings.db") # Use a distinct name

        # --- Test Indexing and Saving to Database ---

        logger.info("Initializing database and engine for indexing...")
        # Initialize the database
        db_write = EmbeddingDatabase(db_path=db_path, model_name="all-MiniLM-L6-v2") # Specify model_name

        # Initialize the embedding engine, passing the database instance
        # File paths are not needed when using the database for persistence
        engine_write = EmbeddingEngine(model_name="all-MiniLM-L6-v2", db=db_write)

        # Create some sample documents
        documents_to_index = [
            {"id": "doc1", "text": "This is the first test document about Odoo modules.", "metadata": {"source": "test_data"}},
            {"id": "doc2", "text": "This is the second test document about Odoo views.", "metadata": {"source": "test_data"}},
            {"id": "doc3", "text": "A third document discussing Odoo reports.", "metadata": {"source": "test_data"}},
        ]

        # Index the documents using the engine
        # This should automatically save documents, embeddings, and index to the database
        logger.info("Indexing documents...")
        indexing_successful = engine_write.index_documents(documents_to_index)

        assert indexing_successful, "Indexing documents failed"
        assert engine_write.index is not None, "FAISS index was not created by the engine"
        assert len(engine_write.documents) == len(documents_to_index), "Engine did not store documents correctly"

        logger.info("Indexing and saving to database successful.")
        db_write.close() # Close the connection after writing

        # --- Test Loading from Database ---

        logger.info("Initializing a new engine to load from the database...")
        # Initialize a new database instance (simulating a new server start)
        db_read = EmbeddingDatabase(db_path=db_path, model_name="all-MiniLM-L6-v2") # Use the same db_path and model_name

        # Initialize a new embedding engine, passing the same database instance
        # The engine should automatically load data from the database on init
        engine_read = EmbeddingEngine(model_name="all-MiniLM-L6-v2", db=db_read)

        # Verify that the engine loaded the data from the database
        assert engine_read.index is not None, "FAISS index was not loaded from the database"
        assert engine_read.index.ntotal == len(documents_to_index), "Loaded index has incorrect number of vectors"
        assert len(engine_read.documents) == len(documents_to_index), "Documents were not loaded from the database"

        # Verify the content of loaded documents (optional, but good practice)
        loaded_docs = sorted(engine_read.documents, key=lambda x: x['id'])
        original_docs = sorted(documents_to_index, key=lambda x: x['id'])
        assert loaded_docs == original_docs, "Loaded documents do not match original documents"


        logger.info("Loading from database successful.")

        # --- Test Search with Loaded Data ---

        logger.info("Testing search with loaded data...")
        test_query = "How to create Odoo modules?"
        search_results = engine_read.search(test_query, k=1)

        assert len(search_results) > 0, "Search returned no results from loaded data"
        logger.info(f"Search results (first result): {search_results[0].get('text', 'N/A')[:100]}...")

        logger.info("Search with loaded data successful.")

        # Clean up the temporary directory
        db_read.close() # Close the connection before removing the directory
        shutil.rmtree(temp_dir)

        logger.info("Embedding storage tests using database completed successfully!")


    if __name__ == "__main__":
        test_odoo_docs_retriever()
        test_embedding_storage()

except ImportError as e:
    logger.error(f"Error importing Odoo Documentation RAG module: {e}")
    logger.error("Make sure you have installed the required dependencies:")
    logger.error("  - sentence-transformers")
    logger.error("  - faiss-cpu")
    logger.error("  - beautifulsoup4")
    logger.error("  - markdown")
    logger.error("  - gitpython")
    sys.exit(1)
except Exception as e:
    logger.error(f"Error testing Odoo Documentation RAG module: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
