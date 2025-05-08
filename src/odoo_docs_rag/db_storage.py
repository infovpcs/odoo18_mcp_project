"""
Database Storage for Odoo Documentation RAG

This module provides functionality for storing and retrieving embeddings and documents
in a SQLite database, improving performance by avoiding repeated embedding generation.
"""

import os
import sqlite3
import pickle
import numpy as np
import json
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path
import time

from .utils import logger


class EmbeddingDatabase:
    """Database for storing and retrieving embeddings and documents."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        model_name: str = "all-MiniLM-L6-v2",
    ):
        """Initialize the embedding database.

        Args:
            db_path: Path to the SQLite database file
            model_name: Name of the sentence-transformers model used for embeddings
        """
        self.db_path = Path(db_path) if db_path else None
        self.model_name = model_name
        self.conn = None
        self.cursor = None

        # Initialize the database if a path is provided
        if self.db_path:
            self._initialize_db()

    def _initialize_db(self) -> bool:
        """Initialize the database connection and create tables if they don't exist.

        Returns:
            True if the database was initialized successfully, False otherwise
        """
        try:
            # Create the directory if it doesn't exist
            if self.db_path:
                # Ensure we have an absolute path
                if not os.path.isabs(self.db_path):
                    self.db_path = Path(os.path.abspath(self.db_path))

                # Create parent directory
                os.makedirs(self.db_path.parent, exist_ok=True)

                logger.info(f"Initializing database at {self.db_path}")
            else:
                logger.error("No database path provided")
                return False

            # Connect to the database
            self.conn = sqlite3.connect(str(self.db_path))
            self.cursor = self.conn.cursor()

            # Enable foreign keys
            self.cursor.execute("PRAGMA foreign_keys = ON")

            # Create the model table
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    dimension INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create the documents table
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create the embeddings table
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT NOT NULL,
                    model_id INTEGER NOT NULL,
                    embedding BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
                    UNIQUE(document_id, model_id)
                )
            """
            )

            # Create the index table
            self.cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS indices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_id INTEGER NOT NULL,
                    index_data BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE
                )
            """
            )

            # Commit the changes
            self.conn.commit()

            # Check if the model exists, if not insert it
            self.cursor.execute(
                "SELECT id, dimension FROM models WHERE name = ?", (self.model_name,)
            )
            result = self.cursor.fetchone()

            if not result:
                # We'll add the model with a placeholder dimension, which will be updated
                # when embeddings are actually created
                self.cursor.execute(
                    "INSERT INTO models (name, dimension) VALUES (?, ?)",
                    (self.model_name, 384),  # Default dimension for all-MiniLM-L6-v2
                )
                self.conn.commit()

            logger.info(f"Database initialized successfully at {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def get_model_id(self, model_name: Optional[str] = None) -> Optional[int]:
        """Get the ID of a model from the database.

        Args:
            model_name: Name of the model (if None, use self.model_name)

        Returns:
            Model ID if found, None otherwise
        """
        if not self.conn:
            logger.error("Database not initialized")
            return None

        model_name = model_name or self.model_name

        try:
            self.cursor.execute("SELECT id FROM models WHERE name = ?", (model_name,))
            result = self.cursor.fetchone()

            if result:
                return result[0]
            else:
                logger.warning(f"Model {model_name} not found in database")
                return None
        except Exception as e:
            logger.error(f"Error getting model ID: {e}")
            return None

    def update_model_dimension(
        self, dimension: int, model_name: Optional[str] = None
    ) -> bool:
        """Update the dimension of a model in the database.

        Args:
            dimension: New dimension value
            model_name: Name of the model (if None, use self.model_name)

        Returns:
            True if the model was updated successfully, False otherwise
        """
        if not self.conn:
            logger.error("Database not initialized")
            return False

        model_name = model_name or self.model_name

        try:
            self.cursor.execute(
                "UPDATE models SET dimension = ? WHERE name = ?",
                (dimension, model_name),
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating model dimension: {e}")
            return False

    def save_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Save documents to the database.

        Args:
            documents: List of documents to save

        Returns:
            True if the documents were saved successfully, False otherwise
        """
        if not self.conn:
            logger.error("Database not initialized")
            return False

        if not documents:
            logger.warning("No documents to save")
            return False

        try:
            # Start a transaction
            self.conn.execute("BEGIN TRANSACTION")

            # Insert or replace documents
            for doc in documents:
                doc_id = doc.get("id")
                text = doc.get("text", "")

                # Extract metadata (everything except id and text)
                metadata = {k: v for k, v in doc.items() if k not in ["id", "text"]}

                self.cursor.execute(
                    "INSERT OR REPLACE INTO documents (id, text, metadata) VALUES (?, ?, ?)",
                    (doc_id, text, json.dumps(metadata)),
                )

            # Commit the transaction
            self.conn.commit()

            logger.info(f"Saved {len(documents)} documents to database")
            return True
        except Exception as e:
            # Rollback in case of error
            self.conn.rollback()
            logger.error(f"Error saving documents to database: {e}")
            return False

    def load_documents(self) -> List[Dict[str, Any]]:
        """Load all documents from the database.

        Returns:
            List of documents
        """
        if not self.conn:
            logger.error("Database not initialized")
            return []

        try:
            self.cursor.execute("SELECT id, text, metadata FROM documents")
            rows = self.cursor.fetchall()

            documents = []
            for row in rows:
                doc_id, text, metadata_json = row

                # Parse metadata
                try:
                    metadata = json.loads(metadata_json)
                except:
                    metadata = {}

                # Create document
                doc = {"id": doc_id, "text": text, **metadata}
                documents.append(doc)

            logger.info(f"Loaded {len(documents)} documents from database")
            return documents
        except Exception as e:
            logger.error(f"Error loading documents from database: {e}")
            return []

    def save_embeddings(
        self,
        document_ids: List[str],
        embeddings: np.ndarray,
        model_name: Optional[str] = None,
    ) -> bool:
        """Save embeddings to the database.

        Args:
            document_ids: List of document IDs
            embeddings: Numpy array of embeddings
            model_name: Name of the model (if None, use self.model_name)

        Returns:
            True if the embeddings were saved successfully, False otherwise
        """
        if not self.conn:
            logger.error("Database not initialized")
            return False

        if len(document_ids) != embeddings.shape[0]:
            logger.error(
                f"Number of document IDs ({len(document_ids)}) doesn't match number of embeddings ({embeddings.shape[0]})"
            )
            return False

        model_name = model_name or self.model_name
        model_id = self.get_model_id(model_name)

        if not model_id:
            logger.error(f"Model {model_name} not found in database")
            return False

        # Update model dimension if needed
        dimension = embeddings.shape[1]
        self.update_model_dimension(dimension, model_name)

        try:
            # Start a transaction
            self.conn.execute("BEGIN TRANSACTION")

            # Insert or replace embeddings
            for i, doc_id in enumerate(document_ids):
                # Serialize the embedding
                embedding_bytes = pickle.dumps(embeddings[i])

                self.cursor.execute(
                    "INSERT OR REPLACE INTO embeddings (document_id, model_id, embedding) VALUES (?, ?, ?)",
                    (doc_id, model_id, embedding_bytes),
                )

            # Commit the transaction
            self.conn.commit()

            logger.info(f"Saved {len(document_ids)} embeddings to database")
            return True
        except Exception as e:
            # Rollback in case of error
            self.conn.rollback()
            logger.error(f"Error saving embeddings to database: {e}")
            return False

    def load_embeddings(
        self, model_name: Optional[str] = None
    ) -> Tuple[List[str], np.ndarray]:
        """Load all embeddings for a model from the database.

        Args:
            model_name: Name of the model (if None, use self.model_name)

        Returns:
            Tuple of (document_ids, embeddings)
        """
        if not self.conn:
            logger.error("Database not initialized")
            return [], np.array([])

        model_name = model_name or self.model_name
        model_id = self.get_model_id(model_name)

        if not model_id:
            logger.error(f"Model {model_name} not found in database")
            return [], np.array([])

        try:
            self.cursor.execute(
                """
                SELECT d.id, e.embedding
                FROM embeddings e
                JOIN documents d ON e.document_id = d.id
                WHERE e.model_id = ?
                """,
                (model_id,),
            )
            rows = self.cursor.fetchall()

            if not rows:
                logger.warning(f"No embeddings found for model {model_name}")
                return [], np.array([])

            document_ids = []
            embeddings_list = []

            for row in rows:
                doc_id, embedding_bytes = row

                # Deserialize the embedding
                embedding = pickle.loads(embedding_bytes)

                document_ids.append(doc_id)
                embeddings_list.append(embedding)

            # Convert to numpy array
            embeddings = np.array(embeddings_list)

            logger.info(f"Loaded {len(document_ids)} embeddings from database")
            return document_ids, embeddings
        except Exception as e:
            logger.error(f"Error loading embeddings from database: {e}")
            return [], np.array([])

    def save_index(self, index_data: bytes, model_name: Optional[str] = None) -> bool:
        """Save a FAISS index to the database.

        Args:
            index_data: Serialized FAISS index
            model_name: Name of the model (if None, use self.model_name)

        Returns:
            True if the index was saved successfully, False otherwise
        """
        if not self.conn:
            logger.error("Database not initialized")
            return False

        model_name = model_name or self.model_name
        model_id = self.get_model_id(model_name)

        if not model_id:
            logger.error(f"Model {model_name} not found in database")
            return False

        try:
            # Check if an index already exists for this model
            self.cursor.execute(
                "SELECT id FROM indices WHERE model_id = ?", (model_id,)
            )
            result = self.cursor.fetchone()

            if result:
                # Update existing index
                self.cursor.execute(
                    "UPDATE indices SET index_data = ?, created_at = CURRENT_TIMESTAMP WHERE model_id = ?",
                    (index_data, model_id),
                )
            else:
                # Insert new index
                self.cursor.execute(
                    "INSERT INTO indices (model_id, index_data) VALUES (?, ?)",
                    (model_id, index_data),
                )

            self.conn.commit()

            logger.info(f"Saved index for model {model_name} to database")
            return True
        except Exception as e:
            logger.error(f"Error saving index to database: {e}")
            return False

    def load_index(self, model_name: Optional[str] = None) -> Optional[bytes]:
        """Load a FAISS index from the database.

        Args:
            model_name: Name of the model (if None, use self.model_name)

        Returns:
            Serialized FAISS index if found, None otherwise
        """
        if not self.conn:
            logger.error("Database not initialized")
            return None

        model_name = model_name or self.model_name
        model_id = self.get_model_id(model_name)

        if not model_id:
            logger.error(f"Model {model_name} not found in database")
            return None

        try:
            self.cursor.execute(
                "SELECT index_data FROM indices WHERE model_id = ?", (model_id,)
            )
            result = self.cursor.fetchone()

            if result:
                logger.info(f"Loaded index for model {model_name} from database")
                return result[0]
            else:
                logger.warning(f"No index found for model {model_name}")
                return None
        except Exception as e:
            logger.error(f"Error loading index from database: {e}")
            return None

    def has_embeddings(self, model_name: Optional[str] = None) -> bool:
        """Check if the database has embeddings for a model.

        Args:
            model_name: Name of the model (if None, use self.model_name)

        Returns:
            True if embeddings exist, False otherwise
        """
        if not self.conn:
            logger.error("Database not initialized")
            return False

        model_name = model_name or self.model_name
        model_id = self.get_model_id(model_name)

        if not model_id:
            logger.warning(f"Model {model_name} not found in database")
            return False

        try:
            self.cursor.execute(
                "SELECT COUNT(*) FROM embeddings WHERE model_id = ?", (model_id,)
            )
            result = self.cursor.fetchone()

            if result and result[0] > 0:
                logger.info(f"Found {result[0]} embeddings for model {model_name}")
                return True
            else:
                logger.info(f"No embeddings found for model {model_name}")
                return False
        except Exception as e:
            logger.error(f"Error checking for embeddings: {e}")
            return False

    def migrate_from_files(self, documents_path: str, index_path: str) -> bool:
        """Migrate data from file storage to database storage.

        Args:
            documents_path: Path to the documents file
            index_path: Path to the index file

        Returns:
            True if the migration was successful, False otherwise
        """
        try:
            start_time = time.time()
            logger.info(f"Starting migration from files to database")

            # Load documents from file
            if os.path.exists(documents_path):
                with open(documents_path, "rb") as f:
                    documents = pickle.load(f)

                # Save documents to database
                if not self.save_documents(documents):
                    logger.error("Failed to save documents to database")
                    return False
            else:
                logger.warning(f"Documents file not found: {documents_path}")
                return False

            # Load index from file
            if os.path.exists(index_path):
                # We don't load the index directly, as we'll rebuild it from the embeddings
                # Instead, we just check that it exists
                pass
            else:
                logger.warning(f"Index file not found: {index_path}")
                return False

            elapsed_time = time.time() - start_time
            logger.info(f"Migration completed in {elapsed_time:.2f} seconds")
            return True
        except Exception as e:
            logger.error(f"Error migrating from files to database: {e}")
            return False
