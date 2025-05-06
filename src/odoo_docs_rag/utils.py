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
    """Check if a file is a documentation file (Markdown, HTML, or RST).

    Args:
        file_path: Path to the file

    Returns:
        True if the file is a documentation file, False otherwise
    """
    # Check file extension
    extension = get_file_extension(file_path)

    # Skip certain directories and files
    path_lower = file_path.lower()
    if any(excluded in path_lower for excluded in [
        "/.git/",
        "/__pycache__/",
        "/node_modules/",
        "/static/lib/",
        "/tests/",
        "requirements.txt",
        "setup.py",
        "package.json",
        ".gitignore"
    ]):
        return False

    # Include only documentation file types
    return extension in ["md", "markdown", "html", "htm", "rst"]

def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace, etc.

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Replace multiple newlines with a single newline
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Replace multiple spaces with a single space
    text = re.sub(r" {2,}", " ", text)

    # Remove special characters that don't add meaning
    text = re.sub(r"[^\w\s.,;:!?()[\]{}\"'`~@#$%^&*+=<>/\\|-]", " ", text)

    # Replace tabs with spaces
    text = text.replace("\t", " ")

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

    # First, try to split by section headers (# or ## in markdown, or === and --- in RST)
    section_splits = []

    # Find markdown headers
    for match in re.finditer(r'^#{1,3}\s+.+$', text, re.MULTILINE):
        section_splits.append(match.start())

    # Find RST headers (=== or --- underlines)
    for match in re.finditer(r'^[=\-]{3,}\s*$', text, re.MULTILINE):
        # Get the line before the === or --- line
        prev_line_end = text.rfind('\n', 0, match.start())
        if prev_line_end != -1:
            prev_line_start = text.rfind('\n', 0, prev_line_end - 1) + 1
            if prev_line_start < prev_line_end:
                section_splits.append(prev_line_start)

    # Sort and deduplicate section splits
    section_splits = sorted(set(section_splits))

    # If we have section splits, use them to create chunks
    if section_splits:
        current_chunk = ""
        last_split = 0

        for split_point in section_splits:
            # Skip the first split point (beginning of text)
            if split_point == 0:
                continue

            # Get the text from the last split to this one
            section_text = text[last_split:split_point]

            # If adding this section would exceed chunk size, start a new chunk
            if len(current_chunk) + len(section_text) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = section_text
            else:
                current_chunk += section_text

            last_split = split_point

        # Add the last chunk
        if last_split < len(text):
            final_section = text[last_split:]
            if len(current_chunk) + len(final_section) > chunk_size:
                chunks.append(current_chunk.strip())
                chunks.append(final_section.strip())
            else:
                current_chunk += final_section
                chunks.append(current_chunk.strip())

    # If we don't have section splits or the chunks are too large, fall back to character-based chunking
    if not chunks or any(len(chunk) > chunk_size * 1.5 for chunk in chunks):
        chunks = []
        start = 0

        while start < len(text):
            # Get the chunk
            end = start + chunk_size

            # If we're at the end of the text, just take the rest
            if end >= len(text):
                chunks.append(text[start:].strip())
                break

            # Try to find a good breaking point (paragraph, sentence, or word boundary)
            # Look for a paragraph break first (double newline)
            break_point = text.rfind("\n\n", start + chunk_size - chunk_overlap, end)

            # If no paragraph break, look for a single newline
            if break_point == -1:
                break_point = text.rfind("\n", start + chunk_size - chunk_overlap, end)

            # If no newline, look for a sentence end (period followed by space or newline)
            if break_point == -1:
                sentence_end = re.search(r'\.(?:\s|$)', text[start + chunk_size - chunk_overlap:end])
                if sentence_end:
                    break_point = start + chunk_size - chunk_overlap + sentence_end.end() - 1

            # If still no good breaking point, look for a word boundary
            if break_point == -1:
                word_boundary = re.search(r'\s', text[start + chunk_size - chunk_overlap:end])
                if word_boundary:
                    break_point = start + chunk_size - chunk_overlap + word_boundary.start()

            # If still no good breaking point, just break at the chunk size
            if break_point == -1:
                break_point = end

            # Add the chunk
            chunks.append(text[start:break_point].strip())

            # Move to the next chunk with overlap
            start = max(start + chunk_size - chunk_overlap, break_point - chunk_overlap)

    # Filter out empty chunks and ensure minimum content
    chunks = [chunk for chunk in chunks if chunk and len(chunk) > 50]

    return chunks

def extract_metadata_from_path(file_path: str) -> Dict[str, Any]:
    """Extract metadata from a file path.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with metadata (file_path, file_name, directory, etc.)
    """
    path = Path(file_path)

    # Basic metadata
    metadata = {
        "file_path": str(path),
        "file_name": path.name,
        "directory": str(path.parent),
        "extension": path.suffix.lstrip(".").lower(),
    }

    # Extract additional context from the path
    path_parts = str(path).split(os.sep)

    # Try to identify document type and category from path
    if "content" in path_parts:
        content_index = path_parts.index("content")
        if content_index + 1 < len(path_parts):
            metadata["section"] = path_parts[content_index + 1]

            # If there's a subsection, add it
            if content_index + 2 < len(path_parts):
                metadata["subsection"] = path_parts[content_index + 2]

                # For fiscal localizations, add the country
                if metadata.get("subsection") == "fiscal_localizations" and content_index + 3 < len(path_parts):
                    metadata["country"] = path_parts[content_index + 3]

    # Extract title from filename (remove extension and replace underscores/hyphens with spaces)
    base_name = path.stem
    title = base_name.replace('_', ' ').replace('-', ' ').title()
    metadata["title"] = title

    return metadata

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