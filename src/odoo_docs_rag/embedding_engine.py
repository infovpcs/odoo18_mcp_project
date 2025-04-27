"""
Embedding Engine for Odoo Documentation RAG

This module provides functionality for creating embeddings from text chunks
and storing them in a vector database for similarity search.
"""

import os
import pickle
import numpy as np
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

# Import sentence_transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("Warning: sentence_transformers is not installed. Please install it with 'pip install sentence-transformers'")
    SENTENCE_TRANSFORMERS_AVAILABLE = False
except Exception as e:
    print(f"Error importing sentence_transformers: {e}")
    SENTENCE_TRANSFORMERS_AVAILABLE = False

# Import FAISS for vector storage
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    print("Warning: faiss-cpu is not installed. Please install it with 'pip install faiss-cpu'")
    FAISS_AVAILABLE = False
except Exception as e:
    print(f"Error importing faiss: {e}")
    FAISS_AVAILABLE = False

from .utils import logger

class EmbeddingEngine:
    """Engine for creating and storing embeddings."""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        index_path: Optional[str] = None,
        documents_path: Optional[str] = None,
    ):
        """Initialize the embedding engine.
        
        Args:
            model_name: Name of the sentence-transformers model to use
            index_path: Path to save/load the FAISS index
            documents_path: Path to save/load the documents
        """
        self.model_name = model_name
        self.index_path = Path(index_path) if index_path else None
        self.documents_path = Path(documents_path) if documents_path else None
        
        # Check if sentence_transformers is available
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("sentence_transformers is not installed. Please install it with 'pip install sentence-transformers'")
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
            logger.error("FAISS is not installed. Please install it with 'pip install faiss-cpu' or 'pip install faiss-gpu'")
            self.index = None
        else:
            self.index = None
        
        # Initialize documents
        self.documents = []
        self.document_ids = []
        
        # Load index and documents if paths are provided
        if self.index_path and self.documents_path:
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
        """Save the FAISS index to disk.
        
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
        """Load the FAISS index from disk.
        
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
            
            logger.info(f"FAISS index loaded successfully with {self.index.ntotal} vectors")
            return True
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
            return False
    
    def save_documents(self, documents: List[Dict[str, Any]], path: Optional[str] = None) -> bool:
        """Save the documents to disk.
        
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
        """Load the documents from disk.
        
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
        """Save both the index and documents to disk.
        
        Returns:
            True if both were saved successfully, False otherwise
        """
        if not self.index_path or not self.documents_path:
            logger.error("Index path or documents path not set")
            return False
        
        index_saved = self.save_index()
        documents_saved = self.save_documents(self.documents)
        
        return index_saved and documents_saved
    
    def load_index_and_documents(self) -> bool:
        """Load both the index and documents from disk.
        
        Returns:
            True if both were loaded successfully, False otherwise
        """
        if not self.index_path or not self.documents_path:
            logger.error("Index path or documents path not set")
            return False
        
        index_loaded = self.load_index()
        
        loaded_documents = self.load_documents()
        if loaded_documents:
            self.documents = loaded_documents
            self.document_ids = [doc["id"] for doc in self.documents]
        
        return index_loaded and bool(loaded_documents)
    
    def index_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Index a list of documents.
        
        Args:
            documents: List of documents to index
            
        Returns:
            True if the documents were indexed successfully, False otherwise
        """
        if not documents:
            logger.error("No documents provided")
            return False
        
        # Extract text from documents
        texts = [doc["text"] for doc in documents]
        
        # Create embeddings
        embeddings = self.create_embeddings(texts)
        
        if len(embeddings) == 0:
            logger.error("Failed to create embeddings")
            return False
        
        # Create the index
        index_created = self.create_index(embeddings)
        
        if not index_created:
            logger.error("Failed to create index")
            return False
        
        # Store the documents
        self.documents = documents
        self.document_ids = [doc["id"] for doc in documents]
        
        # Save the index and documents if paths are provided
        if self.index_path and self.documents_path:
            self.save_index_and_documents()
        
        return True
    
    def search(
        self, 
        query: str, 
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar documents to a query.
        
        Args:
            query: Query text
            k: Number of results to return
            
        Returns:
            List of similar documents with scores
        """
        if not self.model or not self.index:
            logger.error("Model or index not initialized")
            return []
        
        try:
            # Create embedding for the query
            query_embedding = self.model.encode([query])[0].reshape(1, -1).astype(np.float32)
            
            # Search the index
            distances, indices = self.index.search(query_embedding, k)
            
            # Get the results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    doc["score"] = float(1.0 / (1.0 + distances[0][i]))  # Convert distance to similarity score
                    results.append(doc)
            
            return results
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []