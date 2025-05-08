#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script for the Embedding Database functionality.

This script tests the functionality of the Embedding Database by creating a database,
adding documents and embeddings, and verifying that they can be retrieved.
"""

import os
import sys
import logging
import tempfile
import shutil
import numpy as np
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("test_embedding_db")

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the Embedding Database module
    from src.odoo_docs_rag.db_storage import EmbeddingDatabase
    from src.odoo_docs_rag.embedding_engine import EmbeddingEngine

    def test_embedding_database():
        """Test the Embedding Database functionality."""
        logger.info("Testing Embedding Database functionality...")

        # Create a temporary directory for the database
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_embeddings.db")

        logger.info(f"Using database path: {db_path}")

        # Initialize the database
        db = EmbeddingDatabase(db_path=db_path, model_name="all-MiniLM-L6-v2")

        # Check if the database file was created
        assert os.path.exists(db_path), f"Database file was not created at {db_path}"
        logger.info(f"Database file created successfully at {db_path}")

        # Create some sample documents
        documents = [
            {
                "id": "doc1",
                "text": "This is the first test document.",
                "metadata": {"source": "test_data"},
            },
            {
                "id": "doc2",
                "text": "This is the second test document.",
                "metadata": {"source": "test_data"},
            },
            {
                "id": "doc3",
                "text": "A third document for testing.",
                "metadata": {"source": "test_data"},
            },
        ]

        # Save documents to the database
        result = db.save_documents(documents)
        assert result, "Failed to save documents to the database"
        logger.info("Documents saved to the database successfully")

        # Load documents from the database
        loaded_documents = db.load_documents()
        assert len(loaded_documents) == len(
            documents
        ), "Number of loaded documents doesn't match"
        logger.info(f"Loaded {len(loaded_documents)} documents from the database")

        # Create some sample embeddings
        document_ids = [doc["id"] for doc in documents]
        embeddings = np.random.rand(
            len(document_ids), 384
        )  # 384 is the dimension for all-MiniLM-L6-v2

        # Save embeddings to the database
        result = db.save_embeddings(document_ids, embeddings)
        assert result, "Failed to save embeddings to the database"
        logger.info("Embeddings saved to the database successfully")

        # Load embeddings from the database
        loaded_ids, loaded_embeddings = db.load_embeddings()
        assert len(loaded_ids) == len(
            document_ids
        ), "Number of loaded embeddings doesn't match"
        assert (
            loaded_embeddings.shape == embeddings.shape
        ), "Shape of loaded embeddings doesn't match"
        logger.info(f"Loaded {len(loaded_ids)} embeddings from the database")

        # Create a FAISS index
        import faiss

        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)

        # Serialize the index
        import io

        index_buffer = io.BytesIO()
        faiss.write_index(
            index, faiss.PyCallbackIOWriter(lambda x: index_buffer.write(x))
        )
        index_data = index_buffer.getvalue()

        # Save the index to the database
        result = db.save_index(index_data)
        assert result, "Failed to save index to the database"
        logger.info("Index saved to the database successfully")

        # Load the index from the database
        loaded_index_data = db.load_index()
        assert loaded_index_data is not None, "Failed to load index from the database"
        logger.info("Index loaded from the database successfully")

        # Deserialize the index
        index_buffer = io.BytesIO(loaded_index_data)
        loaded_index = faiss.read_index(
            faiss.PyCallbackIOReader(lambda size: index_buffer.read(size))
        )
        assert (
            loaded_index.ntotal == index.ntotal
        ), "Number of vectors in loaded index doesn't match"
        logger.info(f"Loaded index has {loaded_index.ntotal} vectors")

        # Close the database connection
        db.close()

        # Clean up the temporary directory
        shutil.rmtree(temp_dir)
        logger.info("Temporary directory cleaned up")

        logger.info("Embedding Database tests completed successfully!")

    def test_embedding_engine_with_db():
        """Test the Embedding Engine with the Embedding Database."""
        logger.info("Testing Embedding Engine with Embedding Database...")

        # Create a temporary directory for the database
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_engine_embeddings.db")

        logger.info(f"Using database path: {db_path}")

        # Initialize the database
        db = EmbeddingDatabase(db_path=db_path, model_name="all-MiniLM-L6-v2")

        # Initialize the embedding engine with the database
        engine = EmbeddingEngine(model_name="all-MiniLM-L6-v2", db=db)

        # Create some sample documents
        documents = [
            {
                "id": "doc1",
                "text": "This is the first test document about Odoo modules.",
                "metadata": {"source": "test_data"},
            },
            {
                "id": "doc2",
                "text": "This is the second test document about Odoo views.",
                "metadata": {"source": "test_data"},
            },
            {
                "id": "doc3",
                "text": "A third document discussing Odoo reports.",
                "metadata": {"source": "test_data"},
            },
        ]

        # Index the documents
        result = engine.index_documents(documents)
        assert result, "Failed to index documents"
        logger.info("Documents indexed successfully")

        # Check if the database file was created and has content
        assert os.path.exists(db_path), f"Database file was not created at {db_path}"
        assert os.path.getsize(db_path) > 0, "Database file is empty"
        logger.info(
            f"Database file created successfully at {db_path} with size {os.path.getsize(db_path)} bytes"
        )

        # Close the database connection
        db.close()

        # Initialize a new database instance and engine to test loading
        db2 = EmbeddingDatabase(db_path=db_path, model_name="all-MiniLM-L6-v2")
        engine2 = EmbeddingEngine(model_name="all-MiniLM-L6-v2", db=db2)

        # Check if the documents were loaded
        assert len(engine2.documents) == len(
            documents
        ), "Number of loaded documents doesn't match"
        logger.info(f"Loaded {len(engine2.documents)} documents from the database")

        # Check if the index was loaded
        assert engine2.index is not None, "Index was not loaded"
        assert engine2.index.ntotal == len(
            documents
        ), "Number of vectors in loaded index doesn't match"
        logger.info(f"Loaded index has {engine2.index.ntotal} vectors")

        # Test search functionality
        results = engine2.search("Odoo modules", k=1)
        assert len(results) > 0, "Search returned no results"
        logger.info(f"Search results: {results[0].get('text', 'N/A')[:50]}...")

        # Close the second database connection
        db2.close()

        # Clean up the temporary directory
        shutil.rmtree(temp_dir)
        logger.info("Temporary directory cleaned up")

        logger.info(
            "Embedding Engine with Embedding Database tests completed successfully!"
        )

    def test_with_env_paths():
        """Test the Embedding Database with paths from environment variables."""
        logger.info(
            "Testing Embedding Database with paths from environment variables..."
        )

        # Save original environment variables
        original_db_path = os.environ.get("ODOO_DB_PATH")
        original_index_dir = os.environ.get("ODOO_INDEX_DIR")

        # Create a temporary directory for the database
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "embeddings.db")
        index_dir = temp_dir

        # Set environment variables
        os.environ["ODOO_DB_PATH"] = db_path
        os.environ["ODOO_INDEX_DIR"] = index_dir

        logger.info(f"Set ODOO_DB_PATH to {db_path}")
        logger.info(f"Set ODOO_INDEX_DIR to {index_dir}")

        try:
            # Initialize the database using the path from the environment variable
            from mcp_server import odoo_docs_retriever_instance

            # Check if the database file was created
            assert os.path.exists(
                db_path
            ), f"Database file was not created at {db_path}"
            logger.info(f"Database file created successfully at {db_path}")

            # Test a query to ensure the database is working
            if odoo_docs_retriever_instance:
                result = odoo_docs_retriever_instance.query(
                    "How to create a custom module in Odoo"
                )
                logger.info(f"Query result: {result[:100]}...")
            else:
                logger.warning("Odoo docs retriever instance not available")

        finally:
            # Restore original environment variables
            if original_db_path:
                os.environ["ODOO_DB_PATH"] = original_db_path
            else:
                os.environ.pop("ODOO_DB_PATH", None)

            if original_index_dir:
                os.environ["ODOO_INDEX_DIR"] = original_index_dir
            else:
                os.environ.pop("ODOO_INDEX_DIR", None)

            # Clean up the temporary directory
            shutil.rmtree(temp_dir)
            logger.info("Temporary directory cleaned up")

        logger.info(
            "Embedding Database with paths from environment variables tests completed!"
        )

    if __name__ == "__main__":
        test_embedding_database()
        test_embedding_engine_with_db()
        test_with_env_paths()

except ImportError as e:
    logger.error(f"Error importing required modules: {e}")
    logger.error("Make sure you have installed the required dependencies")
    sys.exit(1)
except Exception as e:
    logger.error(f"Error testing Embedding Database: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)
