#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Documentation Page for Streamlit Client

This module provides the documentation page for the Streamlit client.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Union

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from ..utils.mcp_connector import MCPConnector
from ..utils.session_state import SessionState

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("documentation_page")

def render_documentation_page(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the documentation page.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.title("Odoo 18 Documentation")

    # Description of the page
    st.markdown("""
    Search for information in the Odoo 18 documentation.
    This tool uses semantic search to find the most relevant documentation sections.
    """)

    # Search form
    col1, col2 = st.columns([4, 1])

    with col1:
        query = st.text_input(
            "Search Query",
            value=session_state.documentation.query,
            placeholder="e.g., How to create a custom module in Odoo 18",
            help="The query to search for in the Odoo documentation."
        )

    with col2:
        max_results = st.number_input(
            "Max Results",
            value=session_state.documentation.max_results,
            min_value=1,
            max_value=20,
            help="Maximum number of results to return."
        )

    # Advanced options
    with st.expander("Advanced Options"):
        col1, col2 = st.columns(2)

        with col1:
            use_gemini = st.checkbox(
                "Use Gemini LLM",
                value=session_state.documentation.use_gemini,
                help="Use Google's Gemini LLM to summarize and enhance the search results."
            )

        with col2:
            use_online_search = st.checkbox(
                "Include Online Search",
                value=session_state.documentation.use_online_search,
                help="Include results from online search in addition to local documentation."
            )

    # Search button
    if st.button("Search", type="primary"):
        if not query:
            st.error("Please provide a search query.")
            return

        # Update session state
        session_state.documentation.query = query
        session_state.documentation.max_results = max_results
        session_state.documentation.use_gemini = use_gemini
        session_state.documentation.use_online_search = use_online_search

        # Show a spinner while processing
        with st.spinner("Searching documentation..."):
            # Call the MCP tool
            result = mcp_connector.retrieve_odoo_documentation(
                query=query,
                max_results=max_results,
                use_gemini=use_gemini,
                use_online_search=use_online_search
            )

            if result.get("success", False):
                # Get the documentation results - check both data and result fields
                data = result.get("data", "") or result.get("result", "")

                if data:
                    # Store the raw markdown data in session state
                    session_state.documentation.raw_results = data

                    # Display the markdown results directly
                    st.markdown(data)
                else:
                    st.info("No results found.")
            else:
                # Show an error message
                error_msg = result.get("error", "Unknown error")
                st.error(f"Error searching documentation: {error_msg}")

    # We don't need to display results here as we're now directly displaying
    # the markdown in the search button click handler

def render_model_documentation(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the model documentation section.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.header("Model Documentation")

    # Description of the section
    st.markdown("""
    Get documentation for a specific Odoo model.
    """)

    # Model selection
    model_name = st.text_input(
        "Model Name",
        placeholder="e.g., res.partner",
        help="The technical name of the Odoo model."
    )

    # Get model info button
    if st.button("Get Model Info", key="get_model_info_button"):
        if not model_name:
            st.error("Please provide a model name.")
            return

        # Show a spinner while processing
        with st.spinner(f"Getting information for model {model_name}..."):
            # Call the MCP tool to get field groups
            field_groups_result = mcp_connector.call_tool("get_field_groups", {"model_name": model_name})

            if field_groups_result.get("success", False):
                # Display the field groups - check both data and result fields
                field_groups_data = field_groups_result.get("data", "") or field_groups_result.get("result", "")

                if field_groups_data:
                    st.subheader("Field Groups")
                    st.markdown(field_groups_data)
                else:
                    st.info("No field groups found.")
            else:
                # Show an error message
                error_msg = field_groups_result.get("error", "Unknown error")
                st.error(f"Error getting field groups: {error_msg}")

            # Call the MCP tool to analyze field importance
            field_importance_result = mcp_connector.call_tool("analyze_field_importance", {"model_name": model_name})

            if field_importance_result.get("success", False):
                # Display the field importance - check both data and result fields
                field_importance_data = field_importance_result.get("data", "") or field_importance_result.get("result", "")

                if field_importance_data:
                    st.subheader("Field Importance")
                    st.markdown(field_importance_data)
                else:
                    st.info("No field importance analysis available.")
            else:
                # Show an error message
                error_msg = field_importance_result.get("error", "Unknown error")
                st.error(f"Error analyzing field importance: {error_msg}")

            # Call the MCP tool to get a record template
            record_template_result = mcp_connector.call_tool("get_record_template", {"model_name": model_name})

            if record_template_result.get("success", False):
                # Display the record template - check both data and result fields
                record_template_data = record_template_result.get("data", "") or record_template_result.get("result", "")

                if record_template_data:
                    st.subheader("Record Template")
                    st.code(record_template_data, language="json")
                else:
                    st.info("No record template available.")
            else:
                # Show an error message
                error_msg = record_template_result.get("error", "Unknown error")
                st.error(f"Error getting record template: {error_msg}")

def render_field_documentation(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the field documentation section.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.header("Field Documentation")

    # Description of the section
    st.markdown("""
    Get documentation for a specific field in an Odoo model.
    """)

    # Model selection
    model_name = st.text_input(
        "Model Name",
        placeholder="e.g., res.partner",
        help="The technical name of the Odoo model.",
        key="field_model_name"
    )

    # Field selection
    field_name = st.text_input(
        "Field Name",
        placeholder="e.g., name",
        help="The name of the field."
    )

    # Value for validation
    value = st.text_input(
        "Value",
        placeholder="e.g., Test Partner",
        help="A value to validate against the field."
    )

    # Validate field button
    if st.button("Validate Field", key="validate_field_button"):
        if not model_name:
            st.error("Please provide a model name.")
            return

        if not field_name:
            st.error("Please provide a field name.")
            return

        # Show a spinner while processing
        with st.spinner(f"Validating field {field_name} in model {model_name}..."):
            # Call the MCP tool
            result = mcp_connector.call_tool("validate_field_value", {
                "model_name": model_name,
                "field_name": field_name,
                "value": value
            })

            if result.get("success", False):
                # Display the validation results - check both data and result fields
                data = result.get("data", "") or result.get("result", "")

                if data:
                    st.subheader("Validation Results")
                    st.markdown(data)
                else:
                    st.info("No validation results available.")
            else:
                # Show an error message
                error_msg = result.get("error", "Unknown error")
                st.error(f"Error validating field: {error_msg}")
