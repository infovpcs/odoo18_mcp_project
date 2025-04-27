"""
Odoo Documentation Retriever

This module provides the main class for retrieving information from Odoo documentation
using RAG (Retrieval Augmented Generation) techniques.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

from .docs_processor import OdooDocsProcessor
from .embedding_engine import EmbeddingEngine
from .utils import logger

class OdooDocsRetriever:
    """Main class for retrieving information from Odoo documentation."""
    
    def __init__(
        self,
        docs_dir: Optional[str] = None,
        index_dir: Optional[str] = None,
        model_name: str = "all-MiniLM-L6-v2",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        force_rebuild: bool = False,
    ):
        """Initialize the Odoo documentation retriever.
        
        Args:
            docs_dir: Directory to store the documentation files (if None, a temporary directory will be used)
            index_dir: Directory to store the index and documents (if None, a default directory will be used)
            model_name: Name of the sentence-transformers model to use
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
            force_rebuild: If True, force rebuilding the index even if it already exists
        """
        # Set up directories
        self.docs_dir = Path(docs_dir) if docs_dir else None
        
        if index_dir:
            self.index_dir = Path(index_dir)
        else:
            # Use a default directory in the user's home directory
            self.index_dir = Path.home() / ".odoo_docs_rag"
        
        # Create the index directory if it doesn't exist
        os.makedirs(self.index_dir, exist_ok=True)
        
        # Set up paths for index and documents
        self.index_path = self.index_dir / "faiss_index.bin"
        self.documents_path = self.index_dir / "documents.pkl"
        
        # Initialize the processor and engine
        self.processor = OdooDocsProcessor(
            docs_dir=str(self.docs_dir) if self.docs_dir else None,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        
        self.engine = EmbeddingEngine(
            model_name=model_name,
            index_path=str(self.index_path),
            documents_path=str(self.documents_path),
        )
        
        # Initialize the index
        self.initialized = False
        
        # Initialize the index if it doesn't exist or force_rebuild is True
        if force_rebuild or not self.index_path.exists() or not self.documents_path.exists():
            self.initialize_index()
        else:
            # Try to load the existing index
            if self.engine.load_index_and_documents():
                logger.info("Loaded existing index and documents")
                self.initialized = True
            else:
                logger.warning("Failed to load existing index and documents, initializing new index")
                self.initialize_index()
    
    def initialize_index(self) -> bool:
        """Initialize the index by processing the documentation and creating embeddings.
        
        Returns:
            True if the index was initialized successfully, False otherwise
        """
        # Clone or update the repository
        if not self.processor.repo_path.exists():
            if not self.processor.clone_repository():
                logger.error("Failed to clone repository")
                return False
        else:
            if not self.processor.update_repository():
                logger.warning("Failed to update repository, using existing files")
        
        # Process all files
        documents = self.processor.process_all_files()
        
        if not documents:
            logger.error("No documents processed")
            return False
        
        # Index the documents
        if not self.engine.index_documents(documents):
            logger.error("Failed to index documents")
            return False
        
        logger.info("Index initialized successfully")
        self.initialized = True
        return True
    
    def retrieve(
        self, 
        query: str, 
        max_results: int = 5,
        min_score: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Retrieve information from Odoo documentation based on a query.
        
        Args:
            query: Query text
            max_results: Maximum number of results to return
            min_score: Minimum similarity score for results
            
        Returns:
            List of relevant documents with metadata and scores
        """
        if not self.initialized:
            logger.warning("Index not initialized, initializing now")
            if not self.initialize_index():
                logger.error("Failed to initialize index")
                return []
        
        # Search for similar documents
        results = self.engine.search(query, k=max_results * 2)  # Get more results than needed for filtering
        
        # Filter results by score
        filtered_results = [r for r in results if r["score"] >= min_score]
        
        # Limit to max_results
        limited_results = filtered_results[:max_results]
        
        return limited_results
    
    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """Format the retrieval results as a string.
        
        Args:
            results: List of retrieval results
            query: Original query
            
        Returns:
            Formatted string with the results
        """
        if not results:
            return f"# No relevant information found for: {query}\n\nThe Odoo 18 documentation does not contain information directly relevant to your query. Please try rephrasing your question or check the official Odoo website."
        
        # Format the results
        output = f"# Odoo 18 Documentation Results for: {query}\n\n"
        
        for i, result in enumerate(results):
            # Extract metadata
            file_path = result["metadata"]["file_path"]
            file_name = result["metadata"]["file_name"]
            
            # Make the file path relative to the repository
            repo_path = str(self.processor.repo_path)
            if file_path.startswith(repo_path):
                relative_path = file_path[len(repo_path):].lstrip("/\\")
            else:
                relative_path = file_path
            
            # Format the result
            output += f"## Result {i+1} (Score: {result['score']:.2f})\n\n"
            output += f"**Source**: {file_name} ({relative_path})\n\n"
            output += result["text"] + "\n\n"
            output += "---\n\n"
        
        return output
    
    def query(
        self, 
        query: str, 
        max_results: int = 5,
        min_score: float = 0.5,
    ) -> str:
        """Query the Odoo documentation and return formatted results.
        
        Args:
            query: Query text
            max_results: Maximum number of results to return
            min_score: Minimum similarity score for results
            
        Returns:
            Formatted string with the results
        """
        # Retrieve relevant documents
        results = self.retrieve(query, max_results=max_results, min_score=min_score)
        
        # Format the results
        return self.format_results(results, query)