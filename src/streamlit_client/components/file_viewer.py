#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File Viewer Component for Streamlit Client

This module provides a reusable file viewer component for the Streamlit client.
"""

import base64
import logging
import os
from typing import Any, Dict, List, Optional, Union

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("file_viewer")

def get_file_extension(file_path: str) -> str:
    """Get the file extension from a file path.
    
    Args:
        file_path: File path
        
    Returns:
        File extension
    """
    _, ext = os.path.splitext(file_path)
    return ext.lower().lstrip(".")

def get_language_for_extension(ext: str) -> str:
    """Get the programming language for a file extension.
    
    Args:
        ext: File extension
        
    Returns:
        Programming language
    """
    language_map = {
        "py": "python",
        "js": "javascript",
        "html": "html",
        "css": "css",
        "xml": "xml",
        "json": "json",
        "md": "markdown",
        "csv": "csv",
        "txt": "text",
        "sh": "bash",
        "yml": "yaml",
        "yaml": "yaml",
    }
    
    return language_map.get(ext, "text")

def create_download_link(file_content: str, file_name: str) -> str:
    """Create a download link for a file.
    
    Args:
        file_content: Content of the file
        file_name: Name of the file
        
    Returns:
        Download link
    """
    b64 = base64.b64encode(file_content.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{file_name}">Download {file_name}</a>'
    return href

def render_file_viewer(
    files: Dict[str, str],
    container: Optional[DeltaGenerator] = None,
    key_prefix: str = "file_viewer",
    show_download: bool = True,
    max_height: int = 400
) -> None:
    """Render a file viewer component.
    
    Args:
        files: Dictionary of file paths and contents
        container: Container to render the file viewer in (if None, uses st)
        key_prefix: Prefix for the component keys
        show_download: Whether to show the download button
        max_height: Maximum height of the code container
    """
    # Use the provided container or st directly
    cont = container if container is not None else st
    
    # Create a container for the file viewer
    viewer_container = cont.container()
    
    with viewer_container:
        if not files:
            st.info("No files to display.")
            return
        
        # Create a selectbox for file selection
        file_paths = list(files.keys())
        selected_file = st.selectbox(
            "Select a file",
            file_paths,
            key=f"{key_prefix}_file_selector"
        )
        
        # Get the file content
        file_content = files[selected_file]
        
        # Get the file extension and language
        ext = get_file_extension(selected_file)
        language = get_language_for_extension(ext)
        
        # Create a container for the code with a fixed height
        code_container = st.container(height=max_height)
        
        with code_container:
            # Display the file content
            st.code(file_content, language=language)
        
        # Show download button if requested
        if show_download:
            st.markdown(
                create_download_link(file_content, os.path.basename(selected_file)),
                unsafe_allow_html=True
            )

def render_file_tree(
    files: Dict[str, str],
    container: Optional[DeltaGenerator] = None,
    key_prefix: str = "file_tree",
    on_select: Optional[callable] = None
) -> None:
    """Render a file tree component.
    
    Args:
        files: Dictionary of file paths and contents
        container: Container to render the file tree in (if None, uses st)
        key_prefix: Prefix for the component keys
        on_select: Callback function to call when a file is selected
    """
    # Use the provided container or st directly
    cont = container if container is not None else st
    
    # Create a container for the file tree
    tree_container = cont.container()
    
    with tree_container:
        if not files:
            st.info("No files to display.")
            return
        
        # Group files by directory
        file_tree = {}
        for file_path in files.keys():
            parts = file_path.split("/")
            current = file_tree
            
            # Create the directory structure
            for i, part in enumerate(parts[:-1]):
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Add the file
            current[parts[-1]] = file_path
        
        # Render the file tree
        st.markdown("### File Tree")
        
        # Recursively render the file tree
        def render_tree(tree, level=0):
            for key, value in sorted(tree.items()):
                if isinstance(value, dict):
                    # Directory
                    st.markdown(f"{'&nbsp;' * (level * 4)}📁 {key}")
                    render_tree(value, level + 1)
                else:
                    # File
                    if on_select:
                        if st.button(f"{'&nbsp;' * (level * 4)}📄 {key}", key=f"{key_prefix}_{value}"):
                            on_select(value)
                    else:
                        st.markdown(f"{'&nbsp;' * (level * 4)}📄 {key}")
        
        render_tree(file_tree)

def render_csv_viewer(
    csv_content: str,
    container: Optional[DeltaGenerator] = None,
    key_prefix: str = "csv_viewer",
    show_download: bool = True,
    file_name: str = "data.csv"
) -> None:
    """Render a CSV viewer component.
    
    Args:
        csv_content: Content of the CSV file
        container: Container to render the CSV viewer in (if None, uses st)
        key_prefix: Prefix for the component keys
        show_download: Whether to show the download button
        file_name: Name of the CSV file for download
    """
    import io
    import pandas as pd
    
    # Use the provided container or st directly
    cont = container if container is not None else st
    
    # Create a container for the CSV viewer
    viewer_container = cont.container()
    
    with viewer_container:
        try:
            # Convert the CSV content to a pandas DataFrame
            df = pd.read_csv(io.StringIO(csv_content))
            
            # Display the DataFrame
            st.dataframe(df)
            
            # Show download button if requested
            if show_download:
                st.markdown(
                    create_download_link(csv_content, file_name),
                    unsafe_allow_html=True
                )
        except Exception as e:
            st.error(f"Error parsing CSV: {str(e)}")
            st.text(csv_content)
