"""
Odoo Documentation Retriever

This module provides the main class for retrieving information from Odoo documentation
using RAG (Retrieval Augmented Generation) techniques.
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from pathlib import Path

from .docs_processor import OdooDocsProcessor
from .embedding_engine import EmbeddingEngine
from .db_storage import EmbeddingDatabase
from .utils import logger


class OdooDocsRetriever:
    """Main class for retrieving information from Odoo documentation."""

    def __init__(
        self,
        docs_dir: Optional[str] = None,
        index_dir: Optional[str] = None,
        model_name: str = "all-mpnet-base-v2",  # Using a more powerful model
        chunk_size: int = 1500,  # Larger chunks for more context
        chunk_overlap: int = 300,  # More overlap to avoid missing context
        force_rebuild: bool = False,
        db: Optional[EmbeddingDatabase] = None,  # Add database parameter
        db_path: Optional[str] = None,  # Add database path parameter
        update_repo: bool = False,  # Whether to update the repository
        skip_embedding_if_exists: bool = False,  # Skip embedding creation if they exist
    ):
        """Initialize the Odoo documentation retriever.

        Args:
            docs_dir: Directory to store the documentation files (if None, a temporary directory will be used)
            index_dir: Directory to store the index and documents (if None, a default directory will be used)
            model_name: Name of the sentence-transformers model to use
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
            force_rebuild: If True, force rebuilding the index even if it already exists
            db: Optional EmbeddingDatabase instance for persistence
            db_path: Optional path to the database file (if db is not provided)
            update_repo: Whether to update the repository even if it exists
            skip_embedding_if_exists: Skip embedding creation if database already exists
        """
        # Set up directories
        self.docs_dir = Path(docs_dir) if docs_dir else None

        if index_dir:
            self.index_dir = Path(index_dir)
        else:
            # Use a default directory in the user's home directory
            self.index_dir = Path.home() / "odoo_docs_rag"

        # Create the index directory if it doesn't exist
        os.makedirs(self.index_dir, exist_ok=True)

        # Set up paths for index and documents
        self.index_path = self.index_dir / "faiss_index.bin"
        self.documents_path = self.index_dir / "documents.pkl"

        # Initialize the database if provided or create from path
        self.db = db
        if self.db is None and db_path:
            logger.info(f"Initializing database from path: {db_path}")
            self.db = EmbeddingDatabase(db_path=db_path, model_name=model_name)

        # Initialize the processor and engine
        self.processor = OdooDocsProcessor(
            docs_dir=str(self.docs_dir) if self.docs_dir else None,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        # Initialize the engine with database if available
        self.engine = EmbeddingEngine(
            model_name=model_name,
            index_path=str(self.index_path),
            documents_path=str(self.documents_path),
            db=self.db,
        )

        # Initialize the index
        self.initialized = False

        # Store the update_repo and skip_embedding_if_exists parameters
        self.update_repo = update_repo
        self.skip_embedding_if_exists = skip_embedding_if_exists

        # Check if we can skip embedding creation
        if skip_embedding_if_exists and self.db and self.db.has_embeddings():
            logger.info("Using existing embeddings from database, skipping initialization")
            self.initialized = True
            return

        # Initialize the index if it doesn't exist or force_rebuild is True
        if (
            force_rebuild
            or not self.index_path.exists()
            or not self.documents_path.exists()
        ):
            self.initialize_index()
        else:
            # Try to load the existing index
            if self.engine.load_index_and_documents():
                logger.info("Loaded existing index and documents")
                # Verify the index dimensions match the model
                if self.engine.model and self.engine.index:
                    test_embedding = self.engine.model.encode(["test"])[0]
                    if test_embedding.shape[0] != self.engine.index.d:
                        logger.warning(
                            f"Model dimension ({test_embedding.shape[0]}) doesn't match index dimension ({self.engine.index.d})"
                        )
                        logger.info("Forcing index rebuild due to dimension mismatch")
                        self.initialize_index()
                    else:
                        self.initialized = True
                else:
                    self.initialized = True
            else:
                logger.warning(
                    "Failed to load existing index and documents, initializing new index"
                )
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
            # Only update if update_repo is True
            if self.update_repo:
                logger.info("Updating repository as requested")
                if not self.processor.update_repository():
                    logger.warning("Failed to update repository, using existing files")
            else:
                logger.info("Using existing repository without updating")

        # Check if we can skip embedding creation
        if self.skip_embedding_if_exists and self.db and self.db.has_embeddings():
            logger.info("Using existing embeddings from database, skipping document processing")
            self.initialized = True
            return True

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

    def preprocess_query(self, query: str) -> str:
        """Preprocess the query to improve retrieval.

        Args:
            query: Original query

        Returns:
            Preprocessed query
        """
        # Convert to lowercase
        query = query.lower()

        # Remove unnecessary words and characters
        query = re.sub(r"[^\w\s]", " ", query)

        # Replace specific terms with more general ones for better matching
        replacements = {
            "taxes": "tax",
            "taxation": "tax",
            "configure": "configuration",
            "setup": "configuration",
            "set up": "configuration",
            "indian": "india",
            "gst": "goods and services tax",
            "localization": "fiscal localization",
            "localisation": "fiscal localization",
        }

        for old, new in replacements.items():
            query = re.sub(r"\b" + old + r"\b", new, query)

        # Add context for version-specific queries
        if "18.0" in query or "18" in query:
            query = query.replace("18.0", "").replace("18", "")
            query = f"odoo 18 {query}"

        # Clean up extra spaces
        query = re.sub(r"\s+", " ", query).strip()

        return query

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
        try:
            if not self.initialized:
                logger.warning("Index not initialized, initializing now")
                if not self.initialize_index():
                    logger.error("Failed to initialize index")
                    return []

            # Preprocess the query
            processed_query = self.preprocess_query(query)
            logger.info(
                f"Original query: '{query}', Processed query: '{processed_query}'"
            )

            # Search for similar documents
            try:
                results = self.engine.search(
                    processed_query, k=max_results * 3
                )  # Get more results for filtering
            except Exception as e:
                logger.error(f"Error during search: {str(e)}")
                import traceback

                logger.error(f"Search traceback: {traceback.format_exc()}")
                return []

            # Filter results by score
            filtered_results = [r for r in results if r["score"] >= min_score]

            # If we have specific keywords in the query, boost documents that contain them
            boost_keywords = []

            # Extract potential keywords from the query
            if "tax" in query.lower():
                boost_keywords.extend(["tax", "taxation", "taxes"])

            if "india" in query.lower() or "indian" in query.lower():
                boost_keywords.extend(["india", "indian", "gst"])

            if "localization" in query.lower() or "localisation" in query.lower():
                boost_keywords.extend(["localization", "localisation", "fiscal"])

            # Add more domain-specific keywords for module development
            if "module" in query.lower() or "addon" in query.lower():
                boost_keywords.extend(["module", "addon", "development", "manifest"])

            if "crm" in query.lower():
                boost_keywords.extend(["crm", "customer", "lead", "opportunity"])

            if (
                "mail" in query.lower()
                or "email" in query.lower()
                or "mailing" in query.lower()
            ):
                boost_keywords.extend(
                    ["mail", "email", "mailing", "message", "notification"]
                )

            # Apply boosting if we have keywords
            if boost_keywords:
                # Check if any of the boost keywords are in the document text
                for result in filtered_results:
                    boost_score = 0
                    text_lower = result["text"].lower()

                    for keyword in boost_keywords:
                        if keyword in text_lower:
                            # Count occurrences and boost based on that
                            occurrences = text_lower.count(keyword)
                            boost_score += 0.05 * min(
                                occurrences, 5
                            )  # Cap at 5 occurrences

                    # Apply the boost
                    result["score"] += boost_score

                # Re-sort by score
                filtered_results.sort(key=lambda x: x["score"], reverse=True)

            # Limit to max_results
            limited_results = filtered_results[:max_results]

            # Log the results for debugging
            logger.info(
                f"Retrieved {len(limited_results)} results for query: '{query}'"
            )
            for i, result in enumerate(limited_results):
                logger.info(
                    f"Result {i+1}: Score={result['score']:.2f}, Source={result['metadata'].get('file_name', 'Unknown')}"
                )

            return limited_results

        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}")
            import traceback

            logger.error(f"Retrieval traceback: {traceback.format_exc()}")
            return []

    def format_results(self, results: List[Dict[str, Any]], query: str) -> str:
        """Format the retrieval results as a string.

        Args:
            results: List of retrieval results
            query: Original query

        Returns:
            Formatted string with the results
        """
        if not results:
            return f"# No relevant information found for: {query}\n\nThe Odoo 18 documentation does not contain information directly relevant to your query. Please try rephrasing your question or check the official Odoo website.\n\nSuggested alternatives:\n- Try using more general terms\n- Check for typos in technical terms\n- Search for related concepts instead"

        # Format the results
        output = f"# Odoo 18 Documentation Results for: {query}\n\n"

        for i, result in enumerate(results):
            # Extract metadata
            file_path = result["metadata"]["file_path"]
            file_name = result["metadata"]["file_name"]

            # Make the file path relative to the repository
            repo_path = str(self.processor.repo_path)
            if file_path.startswith(repo_path):
                relative_path = file_path[len(repo_path) :].lstrip("/\\")
            else:
                relative_path = file_path

            # Extract additional metadata if available
            section = result["metadata"].get("section", "")
            subsection = result["metadata"].get("subsection", "")
            country = result["metadata"].get("country", "")
            title = result["metadata"].get("title", "")

            # Create a more descriptive source line
            source_parts = []
            if section:
                source_parts.append(f"Section: {section.title()}")
            if subsection:
                source_parts.append(f"Category: {subsection.title()}")
            if country:
                source_parts.append(f"Country: {country.title()}")

            source_info = ", ".join(source_parts)
            if source_info:
                source_info = f" ({source_info})"

            # Format the result with a more descriptive header
            output += f"## Result {i+1} (Score: {result['score']:.2f})\n\n"

            # Use the title if available, otherwise use the filename
            if title:
                output += f"**Topic**: {title}\n\n"

            output += f"**Source**: {file_name}{source_info}\n"
            output += f"**Path**: {relative_path}\n\n"

            # Add the content
            output += result["text"] + "\n\n"
            output += "---\n\n"

        # Add suggestions for related searches
        output += "## Related Searches\n\n"

        # Generate related search suggestions based on the query
        related_searches = []

        if "tax" in query.lower():
            related_searches.extend(
                [
                    "Odoo 18 tax configuration",
                    "Odoo 18 tax reports",
                    "Odoo 18 fiscal positions",
                ]
            )

        if "india" in query.lower() or "indian" in query.lower():
            related_searches.extend(
                [
                    "Odoo 18 Indian GST",
                    "Odoo 18 TDS TCS configuration",
                    "Odoo 18 e-invoicing India",
                ]
            )

        if "localization" in query.lower():
            related_searches.extend(
                [
                    "Odoo 18 fiscal localization packages",
                    "Odoo 18 accounting localization",
                    "Odoo 18 country-specific features",
                ]
            )

        # If no specific related searches, add general ones
        if not related_searches:
            related_searches = [
                "Odoo 18 accounting setup",
                "Odoo 18 developer guide",
                "Odoo 18 module development",
                "Odoo 18 technical documentation",
            ]

        # Add the related searches to the output
        for search in related_searches[:3]:  # Limit to 3 suggestions
            output += f"- {search}\n"

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
