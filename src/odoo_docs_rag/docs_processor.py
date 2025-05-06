"""
Odoo Documentation Processor

This module provides functionality for processing Odoo documentation files,
including cloning the documentation repository, extracting text from Markdown
and HTML files, and chunking the text for embedding.
"""

import os
import re
import git
import logging
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
import markdown
from bs4 import BeautifulSoup

from .utils import (
    logger,
    is_documentation_file,
    clean_text,
    split_text_into_chunks,
    extract_metadata_from_path,
    create_document_id,
)

class OdooDocsProcessor:
    """Processor for Odoo documentation files."""

    def __init__(
        self,
        docs_dir: Optional[str] = None,
        repo_url: str = "https://github.com/odoo/documentation.git",
        branch: str = "18.0",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        """Initialize the Odoo documentation processor.

        Args:
            docs_dir: Directory to store the documentation files (if None, a temporary directory will be used)
            repo_url: URL of the Odoo documentation repository
            branch: Branch of the repository to use
            chunk_size: Maximum size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
        """
        self.repo_url = repo_url
        self.branch = branch
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Set up the documentation directory
        if docs_dir:
            self.docs_dir = Path(docs_dir)
            self.temp_dir = None
        else:
            self.temp_dir = tempfile.mkdtemp(prefix="odoo_docs_")
            self.docs_dir = Path(self.temp_dir)

        # Create the directory if it doesn't exist
        os.makedirs(self.docs_dir, exist_ok=True)

        # Initialize repository path
        self.repo_path = self.docs_dir / "odoo_documentation"

        logger.info(f"Initialized Odoo documentation processor with docs_dir={self.docs_dir}")

    def __del__(self):
        """Clean up temporary directory if it was created."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            logger.info(f"Cleaning up temporary directory: {self.temp_dir}")
            shutil.rmtree(self.temp_dir)

    def clone_repository(self, force: bool = False) -> bool:
        """Clone the Odoo documentation repository.

        Args:
            force: If True, delete the existing repository and clone again

        Returns:
            True if the repository was cloned successfully, False otherwise
        """
        # Check if the repository already exists
        if self.repo_path.exists() and not force:
            logger.info(f"Repository already exists at {self.repo_path}")
            return True

        # Delete the existing repository if force is True
        if self.repo_path.exists() and force:
            logger.info(f"Deleting existing repository at {self.repo_path}")
            shutil.rmtree(self.repo_path)

        # Clone the repository
        try:
            logger.info(f"Cloning repository {self.repo_url} (branch {self.branch}) to {self.repo_path}")
            git.Repo.clone_from(self.repo_url, self.repo_path, branch=self.branch)
            logger.info("Repository cloned successfully")
            return True
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            return False

    def update_repository(self) -> bool:
        """Update the Odoo documentation repository.

        Returns:
            True if the repository was updated successfully, False otherwise
        """
        # Check if the repository exists
        if not self.repo_path.exists():
            logger.warning(f"Repository does not exist at {self.repo_path}")
            return self.clone_repository()

        # Update the repository
        try:
            logger.info(f"Updating repository at {self.repo_path}")
            repo = git.Repo(self.repo_path)
            repo.git.checkout(self.branch)
            repo.git.pull()
            logger.info("Repository updated successfully")
            return True
        except Exception as e:
            logger.error(f"Error updating repository: {e}")
            return False

    def get_documentation_files(self) -> List[str]:
        """Get a list of documentation files in the repository.

        Returns:
            List of file paths
        """
        # Check if the repository exists
        if not self.repo_path.exists():
            logger.warning(f"Repository does not exist at {self.repo_path}")
            return []

        # Get all files in the repository
        files = []
        for root, _, filenames in os.walk(self.repo_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                if is_documentation_file(file_path):
                    files.append(file_path)

        logger.info(f"Found {len(files)} documentation files")
        return files

    def extract_text_from_markdown(self, file_path: str) -> str:
        """Extract text from a Markdown file.

        Args:
            file_path: Path to the Markdown file

        Returns:
            Extracted text
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Convert Markdown to HTML
            html = markdown.markdown(content)

            # Extract text from HTML
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text()

            # Clean the text
            text = clean_text(text)

            return text
        except Exception as e:
            logger.error(f"Error extracting text from Markdown file {file_path}: {e}")
            return ""

    def extract_text_from_html(self, file_path: str) -> str:
        """Extract text from an HTML file.

        Args:
            file_path: Path to the HTML file

        Returns:
            Extracted text
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract text from HTML
            soup = BeautifulSoup(content, "html.parser")

            # Remove script and style elements
            for element in soup(["script", "style"]):
                element.extract()

            # Get text
            text = soup.get_text()

            # Clean the text
            text = clean_text(text)

            return text
        except Exception as e:
            logger.error(f"Error extracting text from HTML file {file_path}: {e}")
            return ""

    def extract_text_from_rst(self, file_path: str) -> str:
        """Extract text from a reStructuredText file.

        Args:
            file_path: Path to the file

        Returns:
            Extracted text
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # For RST files, we'll do some basic processing
            # Remove directive blocks like .. code-block:: python
            content = re.sub(r'^\.\.\s+.*?::\s*.*?$', '', content, flags=re.MULTILINE)

            # Remove directive options (indented blocks after directives)
            content = re.sub(r'^\s+:.*?:.*?$', '', content, flags=re.MULTILINE)

            # Replace section headers (=== and ---) with actual headers
            lines = content.split('\n')
            processed_lines = []

            i = 0
            while i < len(lines):
                if i + 1 < len(lines) and re.match(r'^[=]+$', lines[i+1]):
                    # This is a top-level header
                    processed_lines.append(f"# {lines[i]}")
                    i += 2  # Skip the === line
                elif i + 1 < len(lines) and re.match(r'^[-]+$', lines[i+1]):
                    # This is a second-level header
                    processed_lines.append(f"## {lines[i]}")
                    i += 2  # Skip the --- line
                else:
                    processed_lines.append(lines[i])
                    i += 1

            content = '\n'.join(processed_lines)

            # Clean the text
            text = clean_text(content)

            return text
        except Exception as e:
            logger.error(f"Error extracting text from RST file {file_path}: {e}")
            return ""

    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from a file based on its extension.

        Args:
            file_path: Path to the file

        Returns:
            Extracted text
        """
        extension = os.path.splitext(file_path)[1].lower()

        if extension in [".md", ".markdown"]:
            return self.extract_text_from_markdown(file_path)
        elif extension in [".html", ".htm"]:
            return self.extract_text_from_html(file_path)
        elif extension == ".rst":
            return self.extract_text_from_rst(file_path)
        else:
            logger.warning(f"Unsupported file extension: {extension}")
            return ""

    def process_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Process a documentation file and split it into chunks.

        Args:
            file_path: Path to the file

        Returns:
            List of document chunks with metadata
        """
        # Extract text from the file
        text = self.extract_text_from_file(file_path)

        if not text:
            logger.warning(f"No text extracted from {file_path}")
            return []

        # Split the text into chunks
        chunks = split_text_into_chunks(
            text,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

        # Extract metadata from the file path
        metadata = extract_metadata_from_path(file_path)

        # Create document chunks with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            doc_id = create_document_id(metadata, i)
            documents.append({
                "id": doc_id,
                "text": chunk,
                "metadata": {
                    **metadata,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                }
            })

        logger.debug(f"Processed {file_path}: {len(chunks)} chunks")
        return documents

    def process_all_files(self) -> List[Dict[str, Any]]:
        """Process all documentation files in the repository.

        Returns:
            List of document chunks with metadata
        """
        # Get all documentation files
        files = self.get_documentation_files()

        if not files:
            logger.warning("No documentation files found")
            return []

        # Process each file
        all_documents = []
        for file_path in files:
            documents = self.process_file(file_path)
            all_documents.extend(documents)

        logger.info(f"Processed {len(files)} files, created {len(all_documents)} document chunks")
        return all_documents