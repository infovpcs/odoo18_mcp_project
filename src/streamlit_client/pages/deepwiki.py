#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepWiki Documentation Page for Streamlit Client

This module provides the DeepWiki documentation page for the Streamlit client.
"""

import logging
import streamlit as st
from typing import Dict, Any, List, Optional

from ..utils.mcp_connector import MCPConnector
from ..utils.session_state import SessionState

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("deepwiki_page")

def render_deepwiki_page(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the DeepWiki documentation page.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.title("Odoo Documentation (DeepWiki)")

    # Description of the page
    st.markdown("""
    This page allows you to search and browse Odoo documentation from DeepWiki.
    DeepWiki provides enhanced documentation with context and relationships.
    """)

    # Create tabs for different sections
    tabs = st.tabs(["Browse Documentation", "Search Documentation"])

    # Browse Documentation tab
    with tabs[0]:
        render_browse_documentation(session_state, mcp_connector)

    # Search Documentation tab
    with tabs[1]:
        render_search_documentation(session_state, mcp_connector)

def render_browse_documentation(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the browse documentation section.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.header("Browse Documentation")

    # Description of the section
    st.markdown("""
    Browse Odoo documentation by selecting a documentation URL from DeepWiki.
    """)

    # Common DeepWiki URLs for Odoo documentation
    deepwiki_urls = {
        "Odoo 18 Documentation": "https://deepwiki.com/odoo/odoo",
        "Odoo OWL Framework": "https://deepwiki.com/odoo/owl",
        "Odoo JavaScript Framework": "https://deepwiki.com/odoo/javascript",
        "Odoo Models & Fields": "https://deepwiki.com/odoo/models",
        "Odoo Views": "https://deepwiki.com/odoo/views",
        "Odoo Controllers": "https://deepwiki.com/odoo/controllers",
        "Odoo Security": "https://deepwiki.com/odoo/security"
    }

    # URL selection
    selected_url_key = st.selectbox(
        "Select Documentation Source",
        options=list(deepwiki_urls.keys())
    )

    # Custom URL option
    use_custom_url = st.checkbox("Use custom URL", value=False)
    if use_custom_url:
        custom_url = st.text_input(
            "Custom DeepWiki URL",
            value="https://deepwiki.com/odoo/",
            help="Must start with https://deepwiki.com/"
        )
        if not custom_url.startswith("https://deepwiki.com/"):
            st.error("URL must start with https://deepwiki.com/")
            return
        target_url = custom_url
    else:
        target_url = deepwiki_urls[selected_url_key]

    # Fetch button
    if st.button("Fetch Documentation", type="primary", key="fetch_docs_button"):
        if not target_url:
            st.error("Please provide a valid DeepWiki URL.")
            return

        # Show a spinner while fetching
        with st.spinner("Fetching documentation..."):
            # Call the DeepWiki query tool
            result = mcp_connector.query_deepwiki(
                target_url=target_url
            )

            if result.get("success", False):
                # Display the documentation
                documentation = result.get("result", "")
                
                # Store in session state for future reference
                session_state.deepwiki_documentation = documentation
                
                # Display the documentation
                st.subheader(f"Documentation from {target_url}")
                st.markdown(documentation)
            else:
                # Show an error message
                error_msg = result.get("error", "Unknown error")
                st.error(f"Error fetching documentation: {error_msg}")
    
    # Display previously fetched documentation if available
    elif hasattr(session_state, 'deepwiki_documentation') and session_state.deepwiki_documentation:
        st.subheader(f"Previously Fetched Documentation")
        st.markdown(session_state.deepwiki_documentation)

def render_search_documentation(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the search documentation section.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.header("Search Documentation")

    # Description of the section
    st.markdown("""
    Search Odoo documentation by providing a query and DeepWiki URL.
    """)

    # Search form
    col1, col2 = st.columns([3, 1])

    with col1:
        query = st.text_input(
            "Search Query",
            placeholder="e.g., How to create a custom field in Odoo?",
            help="Enter your question or search terms."
        )

    with col2:
        target_domain = st.selectbox(
            "Domain",
            options=["odoo", "owl", "javascript", "models", "views", "controllers", "security"],
            index=0
        )

    # Construct the target URL
    target_url = f"https://deepwiki.com/odoo/{target_domain}"

    # Search button
    if st.button("Search", type="primary", key="search_docs_button"):
        if not query:
            st.error("Please provide a search query.")
            return

        # Show a spinner while searching
        with st.spinner("Searching documentation..."):
            # Call the DeepWiki query tool
            result = mcp_connector.query_deepwiki(
                target_url=target_url,
                query=query
            )

            if result.get("success", False):
                # Display the search results
                documentation = result.get("result", "")
                
                # Store in session state for future reference
                session_state.deepwiki_documentation = documentation
                
                # Display the documentation
                st.subheader("Search Results")
                st.markdown(documentation)
            else:
                # Show an error message
                error_msg = result.get("error", "Unknown error")
                st.error(f"Error searching documentation: {error_msg}")
