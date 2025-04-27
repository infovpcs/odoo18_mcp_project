"""
Utility functions for the Odoo Documentation RAG module.
"""

import os
import re
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

# Set up logging
logger = logging.getLogger("odoo_docs_rag")

def setup_logging(level: int = logging.INFO) -> None:
    """Set up logging for the Odoo Documentation RAG module.
    
    Args:
        level: The logging level (default: logging.INFO)
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger.setLevel(level)

def get_file_hash(file_path: str) -> str:
    """Get the MD5 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MD5 hash of the file
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_file_extension(file_path: str) -> str:
    """Get the extension of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        File extension (lowercase, without the dot)
    """
    return os.path.splitext(file_path)[1].lower().lstrip(".")

def is_documentation_file(file_path: str) -> bool:
    """Check if a file is a documentation file (Markdown or HTML).
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if the file is a documentation file, False otherwise
    """
    extension = get_file_extension(file_path)
    return extension in ["md", "markdown", "html", "htm", "rst"]

def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace, etc.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text
    """
    # Replace multiple newlines with a single newline
    text = re.sub(r"\n{3,}", "\n\n", text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r" {2,}", " ", text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text

def split_text_into_chunks(
    text: str, 
    chunk_size: int = 1000, 
    chunk_overlap: int = 200
) -> List[str]:
    """Split text into chunks of a specified size with overlap.
    
    Args:
        text: Text to split
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Overlap between chunks in characters
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    # Clean the text first
    text = clean_text(text)
    
    # If the text is shorter than the chunk size, return it as is
    if len(text) <= chunk_size:
        return [text]
    
    # Split the text into chunks
    chunks = []
    start = 0
    
    while start < len(text):
        # Get the chunk
        end = start + chunk_size
        
        # If we're at the end of the text, just take the rest
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # Try to find a good breaking point (newline or period)
        # Look for a newline first
        break_point = text.rfind("\n", start + chunk_size - chunk_overlap, end)
        
        # If no newline, look for a period
        if break_point == -1:
            break_point = text.rfind(". ", start + chunk_size - chunk_overlap, end)
            if break_point != -1:
                break_point += 1  # Include the period
        
        # If still no good breaking point, just break at the chunk size
        if break_point == -1:
            break_point = end
        
        # Add the chunk
        chunks.append(text[start:break_point].strip())
        
        # Move to the next chunk
        start = break_point
    
    return chunks

def extract_metadata_from_path(file_path: str) -> Dict[str, Any]:
    """Extract metadata from a file path.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with metadata (file_path, file_name, directory, etc.)
    """
    path = Path(file_path)
    return {
        "file_path": str(path),
        "file_name": path.name,
        "directory": str(path.parent),
        "extension": path.suffix.lstrip(".").lower(),
    }

def create_document_id(metadata: Dict[str, Any], chunk_index: int) -> str:
    """Create a unique ID for a document chunk.
    
    Args:
        metadata: Document metadata
        chunk_index: Index of the chunk
        
    Returns:
        Unique ID for the document chunk
    """
    file_path = metadata.get("file_path", "")
    return f"{file_path}_{chunk_index}"