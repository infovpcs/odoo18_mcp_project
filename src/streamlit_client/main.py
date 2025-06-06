#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main Module for Streamlit Client

This module provides the main functionality for the Streamlit client.
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional, Union

import streamlit as st

from src.streamlit_client.components.chat import render_chat
from src.streamlit_client.pages.improved_odoo_generator import render_improved_odoo_generator_page
from src.streamlit_client.pages.documentation import render_documentation_page, render_model_documentation, render_field_documentation
from src.streamlit_client.pages.export_import import render_export_import_page
from src.streamlit_client.pages.deepwiki import render_deepwiki_page
from src.streamlit_client.pages.graph_visualization import render_graph_visualization_page
from src.streamlit_client.pages.crud_test import render_crud_test_page
from src.streamlit_client.utils.mcp_connector import MCPConnector
from src.streamlit_client.utils.session_state import SessionState

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("streamlit_client")

def setup_page():
    """Set up the page configuration."""
    st.set_page_config(
        page_title="Odoo 18 MCP Client",
        page_icon="🦉",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Add custom CSS
    st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .stSidebar {
        background-color: #f5f5f5;
    }
    .stButton button {
        width: 100%;
    }
    .stExpander {
        border: 1px solid #ddd;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f5f5f5;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4CAF50;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

def render_sidebar(session_state: SessionState) -> None:
    """Render the sidebar.

    Args:
        session_state: Session state
    """
    st.sidebar.title("Odoo 18 MCP Client")

    # MCP server URL
    mcp_server_url = st.sidebar.text_input(
        "MCP Server URL",
        value=session_state.mcp_server_url,
        help="URL of the MCP server."
    )

    # Update session state
    session_state.mcp_server_url = mcp_server_url

    # Navigation
    st.sidebar.header("Navigation")
        
    # Improved Odoo Module Generator
    if st.sidebar.button("✨ Improved Generator", use_container_width=True, type="primary" if session_state.current_page == "improved_generator" else "secondary"):
        session_state.current_page = "improved_generator"
        st.rerun()

    # Export/Import
    if st.sidebar.button("Export/Import", use_container_width=True, type="primary" if session_state.current_page == "export_import" else "secondary"):
        session_state.current_page = "export_import"
        st.rerun()

    # Documentation
    if st.sidebar.button("Documentation", use_container_width=True, type="primary" if session_state.current_page == "documentation" else "secondary"):
        session_state.current_page = "documentation"
        st.rerun()
        
    # DeepWiki
    if st.sidebar.button("DeepWiki Docs", use_container_width=True, type="primary" if session_state.current_page == "deepwiki" else "secondary"):
        session_state.current_page = "deepwiki"
        st.rerun()
        
    # Graph Visualization
    if st.sidebar.button("Workflow Graphs", use_container_width=True, type="primary" if session_state.current_page == "graph_visualization" else "secondary"):
        session_state.current_page = "graph_visualization"
        st.rerun()

    # Odoo Tool Tester
    if st.sidebar.button("🛠️ Odoo Tool Tester", use_container_width=True, type="primary" if session_state.current_page == "crud_test" else "secondary"):
        session_state.current_page = "crud_test"
        st.rerun()

    # Advanced
    if st.sidebar.button("Advanced", use_container_width=True, type="primary" if session_state.current_page == "advanced" else "secondary"):
        session_state.current_page = "advanced"
        st.rerun()

    # Chat
    if st.sidebar.button("Chat", use_container_width=True, type="primary" if session_state.current_page == "chat" else "secondary"):
        session_state.current_page = "chat"
        st.rerun()

    # Reset
    if st.sidebar.button("Reset All", use_container_width=True):
        # Reset all session state
        session_state.reset_export_import()
        session_state.reset_documentation()
        session_state.reset_deepwiki()
        session_state.reset_graph_visualization()
        session_state.reset_improved_generator()
        session_state.clear_chat()
        session_state.current_page = "improved_generator" # Reset to a default page
        st.rerun()

    # Health check
    st.sidebar.header("MCP Server Status")

    # Create MCP connector
    mcp_connector = MCPConnector(server_url=session_state.mcp_server_url)

    # Check if the MCP server is running
    if mcp_connector.health_check():
        st.sidebar.success("MCP Server is running")
    else:
        st.sidebar.error("MCP Server is not running")

    # About
    st.sidebar.header("About")
    st.sidebar.info("""
    Odoo 18 MCP Client

    This client provides a user interface for interacting with the Odoo 18 MCP server.
    It allows you to:
    - Generate Odoo 18 modules using the code agent
    - Export and import records from Odoo models
    - Search for information in the Odoo 18 documentation
    """)

def render_chat_page(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the chat page.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.title("Chat with Odoo 18 MCP")

    # Description of the page
    st.markdown("""
    Chat with the Odoo 18 MCP server.
    You can ask questions about Odoo 18, request information about models, and more.
    """)

    # Render the chat
    render_chat(
        session_state,
        on_submit=lambda message: handle_chat_message(session_state, mcp_connector, message),
        placeholder="Ask a question about Odoo 18...",
        max_height=500
    )

def handle_chat_message(session_state: SessionState, mcp_connector: MCPConnector, message: str) -> None:
    """Handle a chat message.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
        message: Chat message
    """
    # Show a spinner while processing
    with st.spinner("Processing message..."):
        # First, try to determine if this is a search query or a documentation query
        is_search_query = any(keyword in message.lower() for keyword in
                             ["list", "find", "show", "get", "search", "display", "where", "which"])

        is_doc_query = any(keyword in message.lower() for keyword in
                          ["how to", "what is", "explain", "documentation", "help with", "guide", "tutorial"])

        # Initialize variables to store results
        result = {"success": False, "data": None, "error": None}
        doc_result = {"success": False, "data": None, "error": None}

        # Create a progress bar
        progress_placeholder = st.empty()
        progress_bar = progress_placeholder.progress(0)

        # Create a status message placeholder
        status_placeholder = st.empty()

        # If it looks like a search query, try advanced search first
        if is_search_query and not is_doc_query:
            # Call the advanced search tool
            logger.info(f"Treating as search query: {message}")

            # Show a message that we're processing the query
            status_placeholder.info("Searching for records matching your query... This may take a moment.")

            # Show initial progress
            for i in range(30):
                progress_bar.progress(i)
                time.sleep(0.02)

            # Call the advanced search with polling
            result = mcp_connector.advanced_search(query=message)

            # Continue progress bar while waiting for response
            for i in range(30, 101):
                progress_bar.progress(i)
                time.sleep(0.01)

            # Clear the progress bar and status message
            progress_placeholder.empty()
            status_placeholder.empty()

            if result.get("success", False) and (result.get("data") or result.get("result")):
                # Add the response to the chat - check both data and result fields
                response_content = result.get("data") or result.get("result")
                session_state.add_chat_message("assistant", response_content)
                return

        # If it looks like a documentation query or advanced search failed, try documentation retrieval
        if is_doc_query or not is_search_query or not (result.get("data") or result.get("result")):
            logger.info(f"Treating as documentation query: {message}")

            # Show a message that we're retrieving documentation
            status_placeholder.info("Searching Odoo 18 documentation for relevant information... This may take a moment.")

            # Reset progress bar
            progress_bar = progress_placeholder.progress(0)

            # Show initial progress
            for i in range(30):
                progress_bar.progress(i)
                time.sleep(0.02)

            # Call the documentation retrieval with polling
            doc_result = mcp_connector.retrieve_odoo_documentation(
                query=message,
                max_results=5,
                use_gemini=True,
                use_online_search=True
            )

            # Continue progress bar while waiting for response
            for i in range(30, 101):
                progress_bar.progress(i)
                time.sleep(0.01)

            # Clear the progress bar and status message
            progress_placeholder.empty()
            status_placeholder.empty()

            if doc_result.get("success", False) and (doc_result.get("data") or doc_result.get("result")):
                # Add the response to the chat - check both data and result fields
                response_content = doc_result.get("data") or doc_result.get("result")
                session_state.add_chat_message("assistant", response_content)
                return

        # If we got here, both methods failed or returned no data
        if result.get("success", False) and (result.get("data") or result.get("result")):
            # If advanced search returned something, use that
            response_content = result.get("data") or result.get("result")
            session_state.add_chat_message("assistant", response_content)
        elif doc_result.get("success", False) and (doc_result.get("data") or doc_result.get("result")):
            # If documentation retrieval returned something, use that
            response_content = doc_result.get("data") or doc_result.get("result")
            session_state.add_chat_message("assistant", response_content)
        elif result.get("error") or doc_result.get("error"):
            # If there was an error, report it
            error_msg = result.get("error") or doc_result.get("error") or "Unknown error"
            session_state.add_chat_message(
                "assistant",
                f"I'm sorry, there was an error processing your message: {error_msg}"
            )
        else:
            # No results from either method - try one more time with a longer timeout
            status_placeholder.warning("Initial search didn't return results. Trying again with a longer timeout...")

            # Reset progress bar
            progress_bar = progress_placeholder.progress(0)

            # Try advanced search one more time with a longer timeout
            result = mcp_connector.advanced_search(
                query=message,
                limit=100
            )

            # Update progress bar
            for i in range(101):
                progress_bar.progress(i)
                time.sleep(0.02)

            # Clear the progress bar and status message
            progress_placeholder.empty()
            status_placeholder.empty()

            if result.get("success", False) and (result.get("data") or result.get("result")):
                # Add the response to the chat - check both data and result fields
                response_content = result.get("data") or result.get("result")
                session_state.add_chat_message("assistant", response_content)
            else:
                # Still no results
                session_state.add_chat_message(
                    "assistant",
                    "I'm sorry, I couldn't find any information about that. "
                    "Please try rephrasing your question or use the specific tools in the Export/Import or Documentation pages for more targeted operations."
                )

def render_advanced_page(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the advanced page.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.title("Advanced Odoo 18 Tools")

    # Create tabs for different sections
    tabs = st.tabs(["Model Documentation", "Field Documentation", "Advanced Search"])

    # Model Documentation tab
    with tabs[0]:
        render_model_documentation(session_state, mcp_connector)

    # Field Documentation tab
    with tabs[1]:
        render_field_documentation(session_state, mcp_connector)

    # Advanced Search tab
    with tabs[2]:
        render_advanced_search(session_state, mcp_connector)

def render_advanced_search(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the advanced search section.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.header("Advanced Search")

    # Description of the section
    st.markdown("""
    Perform an advanced search using natural language queries.
    This tool can handle complex queries across multiple Odoo models.
    """)

    # Search form
    col1, col2 = st.columns([4, 1])

    with col1:
        query = st.text_input(
            "Search Query",
            placeholder="e.g., List all customers with more than 5 orders",
            help="Natural language query string."
        )

    with col2:
        limit = st.number_input(
            "Limit",
            value=100,
            min_value=1,
            max_value=1000,
            help="Maximum number of records to return per model."
        )

    # Search button
    if st.button("Search", type="primary", key="advanced_search_button"):
        if not query:
            st.error("Please provide a search query.")
            return

        # Show a spinner while processing
        with st.spinner("Searching..."):
            # Call the MCP tool
            result = mcp_connector.advanced_search(
                query=query,
                limit=limit
            )

            if result.get("success", False):
                # Display the search results - check both data and result fields
                data = result.get("data") or result.get("result") or ""

                if data:
                    st.subheader("Search Results")
                    st.markdown(data)
                else:
                    st.info("No results found.")
            else:
                # Show an error message
                error_msg = result.get("error", "Unknown error")
                st.error(f"Error searching: {error_msg}")

def main():
    """Main function."""
    # Set up the page
    setup_page()

    # Initialize session state
    session_state = SessionState()

    # Create MCP connector
    mcp_connector = MCPConnector(server_url=session_state.mcp_server_url)

    # Render the sidebar
    render_sidebar(session_state)

    # Render the current page
    if session_state.current_page == "improved_generator":
        render_improved_odoo_generator_page(session_state, mcp_connector)
    elif session_state.current_page == "export_import":
        render_export_import_page(session_state, mcp_connector)
    elif session_state.current_page == "documentation":
        render_documentation_page(session_state, mcp_connector)
    elif session_state.current_page == "deepwiki":
        render_deepwiki_page(session_state, mcp_connector)
    elif session_state.current_page == "graph_visualization":
        render_graph_visualization_page(session_state, mcp_connector)
    elif session_state.current_page == "crud_test":
        render_crud_test_page(mcp_connector)
    elif session_state.current_page == "advanced":
        render_advanced_page(session_state, mcp_connector)
    elif session_state.current_page == "chat":
        render_chat_page(session_state, mcp_connector)
    else:
        # Default to improved generator page (make it the new default)
        render_improved_odoo_generator_page(session_state, mcp_connector)

if __name__ == "__main__":
    main()
