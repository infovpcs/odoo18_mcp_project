"""
Embedding Engine for Odoo Documentation RAG

This module provides functionality for creating embeddings from text chunks
and storing them in a vector database for similarity search.
"""

import os
import pickle
import numpy as np
import logging
import io
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

# Import sentence_transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    print(
        "Warning: sentence_transformers is not installed. Please install it with 'pip install sentence-transformers'"
    )
    SENTENCE_TRANSFORMERS_AVAILABLE = False
except Exception as e:
    print(f"Error importing sentence_transformers: {e}")
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Import FAISS for vector storage
try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    print(
        "Warning: faiss-cpu is not installed. Please install it with 'pip install faiss-cpu'"
    )
    FAISS_AVAILABLE = False
except Exception as e:
    print(f"Error importing faiss: {e}")
    FAISS_AVAILABLE = False

from .utils import logger
from .db_storage import EmbeddingDatabase  # Import the database class


class EmbeddingEngine:
    """Engine for creating and storing embeddings."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        index_path: Optional[str] = None,
        documents_path: Optional[str] = None,
        db: Optional[EmbeddingDatabase] = None,  # Add optional database instance
        db_path: Optional[str] = None,  # Add optional database path
        skip_embedding_if_exists: bool = False,  # Skip embedding creation if they exist
    ):
        """Initialize the embedding engine.

        Args:
            model_name: Name of the sentence-transformers model to use
            index_path: Path to save/load the FAISS index (file-based fallback)
            documents_path: Path to save/load the documents (file-based fallback)
            db: Optional EmbeddingDatabase instance for persistence
            db_path: Optional path to the database file (if db is not provided)
            skip_embedding_if_exists: Skip embedding creation if they already exist
        """
        self.model_name = model_name
        self.index_path = Path(index_path) if index_path else None
        self.documents_path = Path(documents_path) if documents_path else None
        self.skip_embedding_if_exists = skip_embedding_if_exists

        # Initialize database if path is provided but no database instance
        if db is None and db_path:
            logger.info(f"Initializing database from path: {db_path}")
            self.db = EmbeddingDatabase(db_path=db_path, model_name=model_name)
        else:
            self.db = db  # Store the database instance

        # Check if sentence_transformers is available
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error(
                "sentence_transformers is not installed. Please install it with 'pip install sentence-transformers'"
            )
            self.model = None
        else:
            # Load the model
            try:
                logger.info(f"Loading sentence-transformers model: {model_name}")
                self.model = SentenceTransformer(model_name)
                logger.info(f"Model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading model: {e}")
                self.model = None

        # Check if FAISS is available
        if not FAISS_AVAILABLE:
            logger.error(
                "FAISS is not installed. Please install it with 'pip install faiss-cpu' or 'pip install faiss-gpu'"
            )
            self.index = None
        else:
            self.index = None

        # Initialize documents
        self.documents = []
        self.document_ids = []

        # Load index and documents from database or files
        self.load_index_and_documents()

    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """Create embeddings for a list of texts.

        Args:
            texts: List of texts to embed

        Returns:
            Numpy array of embeddings
        """
        if not self.model:
            logger.error("Model not initialized")
            return np.array([])

        try:
            logger.info(f"Creating embeddings for {len(texts)} texts")
            embeddings = self.model.encode(texts, show_progress_bar=True)
            logger.info(f"Created embeddings with shape {embeddings.shape}")

            # If database is available, update model dimension
            if self.db:
                self.db.update_model_dimension(embeddings.shape[1], self.model_name)

            return embeddings
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            return np.array([])

    def create_index(self, embeddings: np.ndarray) -> bool:
        """Create a FAISS index from embeddings.

        Args:
            embeddings: Numpy array of embeddings

        Returns:
            True if the index was created successfully, False otherwise
        """
        if not FAISS_AVAILABLE:
            logger.error("FAISS is not installed")
            return False

        try:
            # Get the dimension of the embeddings
            dimension = embeddings.shape[1]

            # Create the index
            logger.info(f"Creating FAISS index with dimension {dimension}")
            self.index = faiss.IndexFlatL2(dimension)

            # Add the embeddings to the index
            self.index.add(embeddings.astype(np.float32))

            logger.info(f"Created FAISS index with {self.index.ntotal} vectors")
            return True
        except Exception as e:
            logger.error(f"Error creating FAISS index: {e}")
            return False

    def save_index(self, path: Optional[str] = None) -> bool:
        """Save the FAISS index to disk (file-based fallback).

        Args:
            path: Path to save the index (if None, use self.index_path)

        Returns:
            True if the index was saved successfully, False otherwise
        """
        if not self.index:
            logger.error("Index not initialized")
            return False

        # Use the provided path or the default path
        save_path = Path(path) if path else self.index_path

        if not save_path:
            logger.error("No path provided to save the index")
            return False

        try:
            # Create the directory if it doesn't exist
            os.makedirs(save_path.parent, exist_ok=True)

            # Save the index
            logger.info(f"Saving FAISS index to {save_path}")
            faiss.write_index(self.index, str(save_path))

            logger.info(f"FAISS index saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")
            return False

    def load_index(self, path: Optional[str] = None) -> bool:
        """Load the FAISS index from disk (file-based fallback).

        Args:
            path: Path to load the index from (if None, use self.index_path)

        Returns:
            True if the index was loaded successfully, False otherwise
        """
        if not FAISS_AVAILABLE:
            logger.error("FAISS is not installed")
            return False

        # Use the provided path or the default path
        load_path = Path(path) if path else self.index_path

        if not load_path:
            logger.error("No path provided to load the index")
            return False

        if not load_path.exists():
            logger.error(f"Index file does not exist: {load_path}")
            return False

        try:
            # Load the index
            logger.info(f"Loading FAISS index from {load_path}")
            self.index = faiss.read_index(str(load_path))

            logger.info(
                f"FAISS index loaded successfully with {self.index.ntotal} vectors"
            )
            return True
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
            return False

    def save_documents(
        self, documents: List[Dict[str, Any]], path: Optional[str] = None
    ) -> bool:
        """Save the documents to disk (file-based fallback).

        Args:
            documents: List of documents to save
            path: Path to save the documents (if None, use self.documents_path)

        Returns:
            True if the documents were saved successfully, False otherwise
        """
        # Use the provided path or the default path
        save_path = Path(path) if path else self.documents_path

        if not save_path:
            logger.error("No path provided to save the documents")
            return False

        try:
            # Create the directory if it doesn't exist
            os.makedirs(save_path.parent, exist_ok=True)

            # Save the documents
            logger.info(f"Saving {len(documents)} documents to {save_path}")
            with open(save_path, "wb") as f:
                pickle.dump(documents, f)

            logger.info(f"Documents saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving documents: {e}")
            return False

    def load_documents(self, path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Load the documents from disk (file-based fallback).

        Args:
            path: Path to load the documents from (if None, use self.documents_path)

        Returns:
            List of loaded documents
        """
        # Use the provided path or the default path
        load_path = Path(path) if path else self.documents_path

        if not load_path:
            logger.error("No path provided to load the documents")
            return []

        if not load_path.exists():
            logger.error(f"Documents file does not exist: {load_path}")
            return []

        try:
            # Load the documents
            logger.info(f"Loading documents from {load_path}")
            with open(load_path, "rb") as f:
                documents = pickle.load(f)

            logger.info(f"Loaded {len(documents)} documents successfully")
            return documents
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            return []

    def save_index_and_documents(self) -> bool:
        """Save both the index and documents to database or disk.

        Prioritizes saving to the database if available.

        Returns:
            True if both were saved successfully, False otherwise
        """
        if self.db:
            logger.info("Saving index and documents to database")
            # Save documents to database
            docs_saved = self.db.save_documents(self.documents)

            # Save index to database
            index_saved = False
            if self.index:
                try:
                    # Serialize the FAISS index
                    index_buffer = io.BytesIO()
                    faiss.write_index(
                        self.index,
                        faiss.PyCallbackIOWriter(lambda x: index_buffer.write(x)),
                    )
                    index_data = index_buffer.getvalue()
                    index_saved = self.db.save_index(index_data, self.model_name)
                except Exception as e:
                    logger.error(
                        f"Error serializing or saving FAISS index to database: {e}"
                    )
                    index_saved = False
            else:
                logger.warning(
                    "FAISS index not initialized, skipping index save to database."
                )
                index_saved = True  # Consider it saved if there's no index to save

            return docs_saved and index_saved
        elif self.index_path and self.documents_path:
            logger.info("Saving index and documents to files")
            index_saved = self.save_index()
            documents_saved = self.save_documents(self.documents)
            return index_saved and documents_saved
        else:
            logger.warning("No database or file paths configured for saving.")
            return False

    def load_index_and_documents(self) -> bool:
        """Load both the index and documents from database or disk.

        Prioritizes loading from the database if available.

        Returns:
            True if both were loaded successfully, False otherwise
        """
        loaded_from_db = False
        if self.db:
            logger.info("Attempting to load index and documents from database")
            # Load documents from database
            loaded_documents = self.db.load_documents()
            if loaded_documents:
                self.documents = loaded_documents
                self.document_ids = [doc["id"] for doc in self.documents]
                logger.info(f"Loaded {len(self.documents)} documents from database.")

                # Load index from database
                index_data = self.db.load_index(self.model_name)
                if index_data:
                    try:
                        # Deserialize the FAISS index
                        index_buffer = io.BytesIO(index_data)
                        self.index = faiss.read_index(
                            faiss.PyCallbackIOReader(
                                lambda size: index_buffer.read(size)
                            )
                        )
                        logger.info(
                            f"Loaded FAISS index from database with {self.index.ntotal} vectors."
                        )
                        loaded_from_db = True
                    except Exception as e:
                        logger.error(
                            f"Error deserializing or loading FAISS index from database: {e}"
                        )
                        self.index = None  # Ensure index is None if loading fails
                else:
                    logger.warning(
                        "No FAISS index found in database for the current model."
                    )
                    # If documents were loaded but no index, we might need to rebuild
                    if self.documents and self.model:
                        logger.info(
                            "Documents loaded but no index found. Rebuilding index from documents."
                        )
                        self.rebuild_index()
                        loaded_from_db = (
                            True  # Consider it loaded if we rebuilt the index
                        )
                    else:
                        logger.warning(
                            "No documents or model available to rebuild index."
                        )

            else:
                logger.warning("No documents found in database.")

        if not loaded_from_db and self.index_path and self.documents_path:
            logger.info("Attempting to load index and documents from files")
            # Fallback to loading from files if database load failed or not available
            index_loaded = self.load_index()

            loaded_documents = self.load_documents()
            if loaded_documents:
                self.documents = loaded_documents
                self.document_ids = [doc["id"] for doc in self.documents]

            # Check if we need to rebuild the index due to model change (only if loaded from files)
            if index_loaded and self.index and self.model and loaded_documents:
                try:
                    # Create a test embedding to check dimensions
                    test_embedding = self.model.encode(["test"])[0]
                    if test_embedding.shape[0] != self.index.d:
                        logger.warning(
                            f"Model dimension ({test_embedding.shape[0]}) doesn't match index dimension ({self.index.d})"
                        )
                        logger.info("Rebuilding index with current model...")
                        self.rebuild_index()
                except Exception as e:
                    logger.error(
                        f"Error checking model dimension or rebuilding index: {e}"
                    )

            return index_loaded and bool(loaded_documents)
        elif loaded_from_db:
            return True  # Successfully loaded from database
        else:
            logger.info(
                "No database or file paths configured for loading, or no existing data found."
            )
            return False

    def rebuild_index(self) -> bool:
        """Rebuild the index with the current model.

        This is useful when the model has changed and the dimensions don't match.
        Saves the rebuilt index and documents to the database if available.

        Returns:
            True if the index was rebuilt successfully, False otherwise
        """
        if not self.documents:
            logger.error("No documents available to rebuild index")
            return False

        if not self.model:
            logger.error("Model not initialized")
            return False

        try:
            logger.info("Rebuilding index from existing documents...")
            # Extract text from documents
            texts = [doc["text"] for doc in self.documents]

            # Create new embeddings
            new_embeddings = self.create_embeddings(texts)

            if len(new_embeddings) == 0:
                logger.error("Failed to create new embeddings during rebuild")
                return False

            # Create new index
            if not self.create_index(new_embeddings):
                logger.error("Failed to create new index during rebuild")
                return False

            # Save the updated index and documents to database if available
            if self.db:
                logger.info("Saving rebuilt index and documents to database...")
                # Save documents (in case they were modified or loaded from files)
                self.db.save_documents(self.documents)
                # Save the new embeddings
                self.db.save_embeddings(
                    self.document_ids, new_embeddings, self.model_name
                )
                # Save the new index
                index_buffer = io.BytesIO()
                faiss.write_index(
                    self.index,
                    faiss.PyCallbackIOWriter(lambda x: index_buffer.write(x)),
                )
                index_data = index_buffer.getvalue()
                self.db.save_index(index_data, self.model_name)
            elif self.index_path and self.documents_path:
                logger.info("Saving rebuilt index and documents to files...")
                self.save_index()
                self.save_documents(self.documents)

            logger.info("Index rebuilt successfully")
            return True
        except Exception as e:
            logger.error(f"Error rebuilding index: {str(e)}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def index_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Index a list of documents.

        Creates embeddings, builds the index, and stores documents and embeddings.
        Saves to the database if available.

        Args:
            documents: List of documents to index

        Returns:
            True if the documents were indexed successfully, False otherwise
        """
        if not documents:
            logger.error("No documents provided to index")
            return False

        logger.info(f"Indexing {len(documents)} documents...")

        # Store the documents first (before creating embeddings)
        self.documents = documents
        self.document_ids = [doc["id"] for doc in documents]

        # Check if we can skip embedding creation
        embeddings_exist = False

        # Check if embeddings exist in database
        if self.skip_embedding_if_exists and self.db:
            logger.info("Checking if embeddings already exist in database...")
            if self.db.has_embeddings(self.model_name):
                logger.info("Embeddings already exist in database, loading them...")
                doc_ids, embeddings = self.db.load_embeddings(self.model_name)
                if len(doc_ids) > 0 and len(embeddings) > 0:
                    logger.info(f"Loaded {len(embeddings)} embeddings from database")
                    embeddings_exist = True

                    # Create the index from loaded embeddings
                    index_created = self.create_index(embeddings)
                    if not index_created:
                        logger.error("Failed to create index from existing embeddings")
                        embeddings_exist = False

        # Check if embeddings exist in files
        if not embeddings_exist and self.skip_embedding_if_exists and self.index_path and self.index_path.exists():
            logger.info("Embeddings may exist in files, trying to load index...")
            if self.load_index():
                logger.info("Successfully loaded index from file")
                embeddings_exist = True

        # If embeddings don't exist or we're not skipping, create them
        if not embeddings_exist:
            # Create embeddings
            logger.info("Creating new embeddings...")
            embeddings = self.create_embeddings([doc["text"] for doc in documents])

            if len(embeddings) == 0:
                logger.error("Failed to create embeddings during indexing")
                return False

            # Create the index
            index_created = self.create_index(embeddings)

            if not index_created:
                logger.error("Failed to create index during indexing")
                return False

        # Save the documents, embeddings, and index to database if available
        if self.db:
            logger.info(
                "Saving indexed documents, embeddings, and index to database..."
            )
            docs_saved = self.db.save_documents(self.documents)
            embeddings_saved = self.db.save_embeddings(
                self.document_ids, embeddings, self.model_name
            )
            index_saved = False
            if self.index:
                try:
                    index_buffer = io.BytesIO()
                    faiss.write_index(
                        self.index,
                        faiss.PyCallbackIOWriter(lambda x: index_buffer.write(x)),
                    )
                    index_data = index_buffer.getvalue()
                    index_saved = self.db.save_index(index_data, self.model_name)
                except Exception as e:
                    logger.error(
                        f"Error serializing or saving FAISS index to database after indexing: {e}"
                    )
                    index_saved = False
            else:
                logger.warning(
                    "FAISS index not initialized after creation, skipping index save to database."
                )
                index_saved = True  # Consider it saved if there's no index to save

            if not (docs_saved and embeddings_saved and index_saved):
                logger.error(
                    "Failed to save all components to database after indexing."
                )
                return False  # Indicate failure if saving to DB failed

        elif self.index_path and self.documents_path:
            logger.info("Saving indexed documents and index to files...")
            # Fallback to saving to files
            self.save_index()
            self.save_documents(self.documents)

        logger.info("Documents indexed successfully.")
        return True

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents to a query.

        Args:
            query: Query text
            k: Number of results to return

        Returns:
            List of similar documents with scores
        """
        if not self.model or not self.index:
            logger.error("Model or index not initialized. Cannot perform search.")
            # Attempt to load if not initialized
            if self.load_index_and_documents():
                logger.info("Successfully loaded index and documents, retrying search.")
            else:
                logger.error(
                    "Failed to load index and documents. Cannot perform search."
                )
                return []

        try:
            # Create embedding for the query
            logger.info(f"Creating embedding for query: {query}")
            query_embedding = self.model.encode([query])[0]

            # Get the dimension of the index
            index_dimension = self.index.d
            query_dimension = query_embedding.shape[0]

            # Check if dimensions match
            if query_dimension != index_dimension:
                logger.warning(
                    f"Dimension mismatch: query dimension is {query_dimension}, index dimension is {index_dimension}"
                )

                # Rebuild the index if needed (this should ideally be handled during load,
                # but adding a check here as a safeguard)
                logger.info(
                    "Dimension mismatch detected during search. Attempting to rebuild index with current model..."
                )
                if len(self.documents) > 0:
                    if self.rebuild_index():
                        logger.info("Index rebuilt successfully. Retrying search.")
                        # Re-encode the query with the potentially new model
                        query_embedding = self.model.encode([query])[0]
                        # Re-check dimension after rebuild
                        if query_embedding.shape[0] != self.index.d:
                            logger.error(
                                "Dimension mismatch persists after rebuild. Cannot perform search."
                            )
                            return []
                    else:
                        logger.error("Failed to rebuild index. Cannot perform search.")
                        return []
                else:
                    logger.error(
                        "No documents available to rebuild index. Cannot perform search."
                    )
                    return []

            # Reshape and convert to float32
            query_embedding = query_embedding.reshape(1, -1).astype(np.float32)

            # Search the index
            logger.info(f"Searching index with k={k}")
            distances, indices = self.index.search(query_embedding, k)

            # Get the results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.documents) and idx >= 0:
                    doc = self.documents[idx].copy()
                    # Ensure score is a float before adding to dict
                    doc["score"] = float(
                        1.0 / (1.0 + distances[0][i])
                    )  # Convert distance to similarity score
                    results.append(doc)

            logger.info(f"Found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            # Print the full traceback for debugging
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
