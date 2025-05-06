#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export/Import Page for Streamlit Client

This module provides the export/import page for the Streamlit client.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Union

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from ..components.file_viewer import render_csv_viewer
from ..utils.mcp_connector import MCPConnector
from ..utils.session_state import SessionState

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("export_import_page")

def render_export_import_page(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the export/import page.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.title("Odoo 18 Export/Import")

    # Create tabs for different sections
    tabs = st.tabs(["Export", "Import", "Related Export/Import"])

    # Export tab
    with tabs[0]:
        render_export_tab(session_state, mcp_connector)

    # Import tab
    with tabs[1]:
        render_import_tab(session_state, mcp_connector)

    # Related Export/Import tab
    with tabs[2]:
        render_related_export_import_tab(session_state, mcp_connector)

def render_export_tab(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the export tab.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.header("Export Records")

    # Description of the tab
    st.markdown("""
    Export records from an Odoo model to a CSV file.
    """)

    # Model selection
    model_name = st.text_input(
        "Model Name",
        value=session_state.export_import.model_name,
        placeholder="e.g., res.partner",
        help="The technical name of the Odoo model to export."
    )

    # Fields selection
    fields_input = st.text_area(
        "Fields",
        placeholder="Enter field names separated by commas (leave empty for all fields)",
        help="List of field names to export. Leave empty to export all fields."
    )

    # Parse fields
    fields = [field.strip() for field in fields_input.split(",")] if fields_input else None

    # Filter domain
    filter_domain = st.text_input(
        "Filter Domain",
        value=session_state.export_import.filter_domain,
        placeholder="e.g., [('customer_rank', '>', 0)]",
        help="Domain filter in string format."
    )

    # Limit
    limit = st.number_input(
        "Limit",
        value=session_state.export_import.limit,
        min_value=1,
        max_value=10000,
        help="Maximum number of records to export."
    )

    # Export path
    export_path = st.text_input(
        "Export Path",
        value=session_state.export_import.export_path,
        placeholder="e.g., /tmp/export.csv",
        help="Path to export the CSV file."
    )

    # Export button
    if st.button("Export", type="primary", key="export_button"):
        if not model_name:
            st.error("Please provide a model name.")
            return

        if not export_path:
            st.error("Please provide an export path.")
            return

        # Update session state
        session_state.export_import.model_name = model_name
        session_state.export_import.fields = fields or []
        session_state.export_import.filter_domain = filter_domain
        session_state.export_import.limit = limit
        session_state.export_import.export_path = export_path

        # Show a spinner while processing
        with st.spinner("Exporting records..."):
            # Call the MCP tool
            result = mcp_connector.export_records_to_csv(
                model_name=model_name,
                fields=fields,
                filter_domain=filter_domain,
                limit=limit,
                export_path=export_path
            )

            if result.get("success", False):
                # Show a success message
                st.success(f"Records exported successfully to {export_path}!")

                # Display the exported data if available
                data = result.get("data", "")
                if data:
                    st.subheader("Exported Data")
                    render_csv_viewer(
                        data,
                        file_name=os.path.basename(export_path)
                    )
            else:
                # Show an error message
                error_msg = result.get("error", "Unknown error")
                st.error(f"Error exporting records: {error_msg}")

def render_import_tab(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the import tab.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.header("Import Records")

    # Description of the tab
    st.markdown("""
    Import records from a CSV file into an Odoo model.
    """)

    # Model selection
    model_name = st.text_input(
        "Model Name",
        value=session_state.export_import.model_name,
        placeholder="e.g., res.partner",
        help="The technical name of the Odoo model to import into.",
        key="import_model_name"
    )

    # Input path
    input_path = st.text_input(
        "Input Path",
        value=session_state.export_import.input_path,
        placeholder="e.g., /tmp/import.csv",
        help="Path to the CSV file to import."
    )

    # Field mapping
    field_mapping = st.text_area(
        "Field Mapping",
        value=session_state.export_import.field_mapping,
        placeholder='{"csv_field": "odoo_field"}',
        help="JSON string with mapping from CSV field names to Odoo field names."
    )

    # Options
    col1, col2 = st.columns(2)

    with col1:
        create_if_not_exists = st.checkbox(
            "Create If Not Exists",
            value=session_state.export_import.create_if_not_exists,
            help="Whether to create new records if they don't exist."
        )

    with col2:
        update_if_exists = st.checkbox(
            "Update If Exists",
            value=session_state.export_import.update_if_exists,
            help="Whether to update existing records."
        )

    # Import button
    if st.button("Import", type="primary", key="import_button"):
        if not model_name:
            st.error("Please provide a model name.")
            return

        if not input_path:
            st.error("Please provide an input path.")
            return

        # Update session state
        session_state.export_import.model_name = model_name
        session_state.export_import.input_path = input_path
        session_state.export_import.field_mapping = field_mapping
        session_state.export_import.create_if_not_exists = create_if_not_exists
        session_state.export_import.update_if_exists = update_if_exists

        # Show a spinner while processing
        with st.spinner("Importing records..."):
            # Call the MCP tool
            result = mcp_connector.import_records_from_csv(
                input_path=input_path,
                model_name=model_name,
                field_mapping=field_mapping,
                create_if_not_exists=create_if_not_exists,
                update_if_exists=update_if_exists
            )

            if result.get("success", False):
                # Show a success message
                st.success("Records imported successfully!")

                # Display the import results if available
                data = result.get("data", "") or result.get("result", "")
                if data:
                    st.subheader("Import Results")
                    st.markdown(data)
                else:
                    # Even if no data is returned, show a more detailed success message
                    st.success(f"Successfully imported records from {input_path} to {model_name}. Check the Odoo interface to verify the imported records.")
            else:
                # Show an error message
                error_msg = result.get("error", "Unknown error")
                st.error(f"Error importing records: {error_msg}")

def render_related_export_import_tab(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the related export/import tab.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.header("Related Export/Import")

    # Description of the tab
    st.markdown("""
    Export and import related records (parent-child relationships) between Odoo models.
    """)

    # Create tabs for export and import
    subtabs = st.tabs(["Related Export", "Related Import"])

    # Related Export tab
    with subtabs[0]:
        render_related_export_tab(session_state, mcp_connector)

    # Related Import tab
    with subtabs[1]:
        render_related_import_tab(session_state, mcp_connector)

def render_related_export_tab(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the related export tab.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.subheader("Export Related Records")

    # Parent model selection
    parent_model = st.text_input(
        "Parent Model",
        value=session_state.export_import.parent_model,
        placeholder="e.g., account.move",
        help="The technical name of the parent Odoo model."
    )

    # Child model selection
    child_model = st.text_input(
        "Child Model",
        value=session_state.export_import.child_model,
        placeholder="e.g., account.move.line",
        help="The technical name of the child Odoo model."
    )

    # Relation field
    relation_field = st.text_input(
        "Relation Field",
        value=session_state.export_import.relation_field,
        placeholder="e.g., move_id",
        help="The field in the child model that relates to the parent."
    )

    # Parent fields
    parent_fields_input = st.text_area(
        "Parent Fields",
        placeholder="Enter field names separated by commas (leave empty for all fields)",
        help="List of field names to export from the parent model."
    )

    # Parse parent fields
    parent_fields = [field.strip() for field in parent_fields_input.split(",")] if parent_fields_input else None

    # Child fields
    child_fields_input = st.text_area(
        "Child Fields",
        placeholder="Enter field names separated by commas (leave empty for all fields)",
        help="List of field names to export from the child model."
    )

    # Parse child fields
    child_fields = [field.strip() for field in child_fields_input.split(",")] if child_fields_input else None

    # Filter domain
    filter_domain = st.text_input(
        "Filter Domain",
        value=session_state.export_import.filter_domain,
        placeholder="e.g., [('move_type', '=', 'out_invoice')]",
        help="Domain filter for the parent model in string format.",
        key="related_filter_domain"
    )

    # Move type (for account.move)
    move_type = st.text_input(
        "Move Type",
        value=session_state.export_import.move_type or "",
        placeholder="e.g., out_invoice",
        help="For account.move model, specify the move_type to filter by."
    )

    # Limit
    limit = st.number_input(
        "Limit",
        value=session_state.export_import.limit,
        min_value=1,
        max_value=10000,
        help="Maximum number of parent records to export.",
        key="related_limit"
    )

    # Export path
    export_path = st.text_input(
        "Export Path",
        value=session_state.export_import.export_path,
        placeholder="e.g., /tmp/related_export.csv",
        help="Path to export the CSV file.",
        key="related_export_path"
    )

    # Export button
    if st.button("Export Related Records", type="primary", key="related_export_button"):
        if not parent_model:
            st.error("Please provide a parent model name.")
            return

        if not child_model:
            st.error("Please provide a child model name.")
            return

        if not relation_field:
            st.error("Please provide a relation field.")
            return

        if not export_path:
            st.error("Please provide an export path.")
            return

        # Update session state
        session_state.export_import.parent_model = parent_model
        session_state.export_import.child_model = child_model
        session_state.export_import.relation_field = relation_field
        session_state.export_import.parent_fields = parent_fields or []
        session_state.export_import.child_fields = child_fields or []
        session_state.export_import.filter_domain = filter_domain
        session_state.export_import.move_type = move_type if move_type else None
        session_state.export_import.limit = limit
        session_state.export_import.export_path = export_path

        # Show a spinner while processing
        with st.spinner("Exporting related records..."):
            # Call the MCP tool
            params = {
                "parent_model": parent_model,
                "child_model": child_model,
                "relation_field": relation_field,
                "limit": limit,
                "export_path": export_path
            }

            if parent_fields:
                params["parent_fields"] = parent_fields

            if child_fields:
                params["child_fields"] = child_fields

            if filter_domain:
                params["filter_domain"] = filter_domain

            if move_type:
                params["move_type"] = move_type

            result = mcp_connector.call_tool("export_related_records_to_csv", params)

            if result.get("success", False):
                # Show a success message
                st.success(f"Related records exported successfully to {export_path}!")

                # Display the exported data if available
                data = result.get("data", "")
                if data:
                    st.subheader("Exported Data")
                    render_csv_viewer(
                        data,
                        file_name=os.path.basename(export_path)
                    )
            else:
                # Show an error message
                error_msg = result.get("error", "Unknown error")
                st.error(f"Error exporting related records: {error_msg}")

def render_related_import_tab(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the related import tab.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.subheader("Import Related Records")

    # Parent model selection
    parent_model = st.text_input(
        "Parent Model",
        value=session_state.export_import.parent_model,
        placeholder="e.g., account.move",
        help="The technical name of the parent Odoo model.",
        key="related_import_parent_model"
    )

    # Child model selection
    child_model = st.text_input(
        "Child Model",
        value=session_state.export_import.child_model,
        placeholder="e.g., account.move.line",
        help="The technical name of the child Odoo model.",
        key="related_import_child_model"
    )

    # Relation field
    relation_field = st.text_input(
        "Relation Field",
        value=session_state.export_import.relation_field,
        placeholder="e.g., move_id",
        help="The field in the child model that relates to the parent.",
        key="related_import_relation_field"
    )

    # Input path
    input_path = st.text_input(
        "Input Path",
        value=session_state.export_import.input_path,
        placeholder="e.g., /tmp/related_import.csv",
        help="Path to the CSV file to import.",
        key="related_import_path"
    )

    # Options
    col1, col2 = st.columns(2)

    with col1:
        create_if_not_exists = st.checkbox(
            "Create If Not Exists",
            value=session_state.export_import.create_if_not_exists,
            help="Whether to create new records if they don't exist.",
            key="related_create_if_not_exists"
        )

        draft_only = st.checkbox(
            "Draft Only",
            value=False,
            help="Whether to only update records in draft state (important for account.move)."
        )

    with col2:
        update_if_exists = st.checkbox(
            "Update If Exists",
            value=session_state.export_import.update_if_exists,
            help="Whether to update existing records.",
            key="related_update_if_exists"
        )

        reset_to_draft = st.checkbox(
            "Reset To Draft",
            value=False,
            help="Whether to reset records to draft before updating (use with caution)."
        )

    # Import button
    if st.button("Import Related Records", type="primary", key="related_import_button"):
        if not parent_model:
            st.error("Please provide a parent model name.")
            return

        if not child_model:
            st.error("Please provide a child model name.")
            return

        if not relation_field:
            st.error("Please provide a relation field.")
            return

        if not input_path:
            st.error("Please provide an input path.")
            return

        # Update session state
        session_state.export_import.parent_model = parent_model
        session_state.export_import.child_model = child_model
        session_state.export_import.relation_field = relation_field
        session_state.export_import.input_path = input_path
        session_state.export_import.create_if_not_exists = create_if_not_exists
        session_state.export_import.update_if_exists = update_if_exists

        # Show a spinner while processing
        with st.spinner("Importing related records..."):
            # Call the MCP tool
            params = {
                "parent_model": parent_model,
                "child_model": child_model,
                "relation_field": relation_field,
                "input_path": input_path,
                "create_if_not_exists": create_if_not_exists,
                "update_if_exists": update_if_exists,
                "draft_only": draft_only,
                "reset_to_draft": reset_to_draft
            }

            result = mcp_connector.call_tool("import_related_records_from_csv", params)

            if result.get("success", False):
                # Show a success message
                st.success("Related records imported successfully!")

                # Display the import results if available
                data = result.get("data", "") or result.get("result", "")
                if data:
                    st.subheader("Import Results")
                    st.markdown(data)
                else:
                    # Even if no data is returned, show a more detailed success message
                    st.success(f"Successfully imported related records from {input_path} to {parent_model}/{child_model}. Check the Odoo interface to verify the imported records.")
            else:
                # Show an error message
                error_msg = result.get("error", "Unknown error")
                st.error(f"Error importing related records: {error_msg}")
