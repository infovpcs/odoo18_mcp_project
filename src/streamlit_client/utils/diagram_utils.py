#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagram Utilities for Streamlit Client

This module provides utility functions for handling diagram generation and display
across different pages of the Streamlit client.
"""

import os
import logging
import base64
import re
import time
import hashlib
import streamlit as st
from typing import Optional, List, Tuple, Any

# Set up logging
logger = logging.getLogger("diagram_utils")

def find_diagram_file(image_path: str) -> Tuple[bool, Optional[str]]:
    """Find a diagram file in multiple possible locations.
    
    Args:
        image_path: The reported path of the image file
        
    Returns:
        Tuple of (success, file_path) where success is True if a file was found,
        and file_path is the path to the found file or None if not found
    """
    # First check if the provided path exists directly
    if os.path.exists(image_path):
        logger.info(f"Found diagram at original path: {image_path}")
        return True, image_path
    
    # Extract just the filename from the path
    filename = os.path.basename(image_path)
    
    # Determine various directory paths that might contain the file
    # Get the current file's location
    current_file = os.path.abspath(__file__)
    
    # Derive project directories
    # From: /Users/vinusoft85/workspace/odoo18_mcp_project/src/streamlit_client/utils/diagram_utils.py
    # Go up three directories to get to src: utils -> streamlit_client -> src
    src_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    
    # Go up four directories to get to project root: utils -> streamlit_client -> src -> project_root
    project_root = os.path.dirname(src_dir)
    
    # Streamlit client directory
    streamlit_client_dir = os.path.dirname(os.path.dirname(current_file))
    
    # List of possible locations to check in priority order
    possible_locations = [
        # Check in exports/diagrams first (our designated folder)
        os.path.join(project_root, "exports", "diagrams", filename),
        
        # Check in streamlit_client directory
        os.path.join(streamlit_client_dir, filename),
        
        # Check in streamlit_client/static directory if it exists
        os.path.join(streamlit_client_dir, "static", filename),
        
        # Check in current working directory
        os.path.join(os.getcwd(), filename),
        
        # Check in /tmp directory (where some tools save files by default)
        os.path.join("/tmp", filename)
    ]
    
    # Try each location
    for loc in possible_locations:
        if os.path.exists(loc):
            logger.info(f"Found diagram at alternate location: {loc}")
            return True, loc
    
    # If we get here, no file was found
    logger.error(f"Diagram not found at any location. Original path: {image_path}")
    return False, None

def display_diagram(image_path: str, session_state: Optional[Any] = None, title: str = "Generated Diagram") -> bool:
    """Display a diagram in the Streamlit UI with proper error handling.
    
    Args:
        image_path: The reported path to the diagram image
        session_state: Optional session state to store the image path
        title: Title to display above the diagram
        
    Returns:
        True if the diagram was successfully displayed, False otherwise
    """
    # Parse path from message if needed
    if isinstance(image_path, str) and image_path.startswith("# Mermaid Diagram Generated Successfully"):
        path_match = re.search(r'saved to: (.+\.png)', image_path)
        if path_match:
            image_path = path_match.group(1)
    
    # Try to find the file
    found, file_path = find_diagram_file(image_path)
    
    if found:
        try:
            # Read the image file
            with open(file_path, "rb") as image_file:
                image_data = image_file.read()
                encoded_image = base64.b64encode(image_data).decode()
            
            # Display the diagram
            st.subheader(title)
            st.markdown(f"<img src='data:image/png;base64,{encoded_image}' style='width:100%;'>", unsafe_allow_html=True)
            
            # Store in session state if provided
            if session_state:
                session_state.last_generated_graph = file_path
            
            # Create download button with a guaranteed unique key
            filename = os.path.basename(file_path)
            
            # Generate a unique key based on the filename, title, and current timestamp
            timestamp = int(time.time() * 1000)  # millisecond precision
            unique_str = f"{filename}_{title}_{timestamp}"
            hash_key = hashlib.md5(unique_str.encode()).hexdigest()[:10]
            
            st.download_button(
                label="Download Diagram",
                data=image_data,
                file_name=filename,
                mime="image/png",
                key=f"download_{hash_key}"
            )
            
            return True
            
        except Exception as e:
            st.error(f"Error displaying diagram: {str(e)}")
            logger.error(f"Error displaying diagram: {str(e)}", exc_info=True)
            return False
    else:
        st.error(f"Diagram not found at {image_path} or any fallback locations")
        return False
