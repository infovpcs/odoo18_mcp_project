#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main agent flow for Export/Import operations.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union, Tuple, Annotated, TypedDict

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.agents.export_import.state import AgentState, FlowMode
from src.agents.export_import.nodes.export_nodes import (
    select_model,
    select_fields,
    set_filter,
    execute_export
)
from src.agents.export_import.nodes.import_nodes import (
    select_import_file,
    select_import_model,
    map_fields,
    validate_mapping,
    execute_import
)

logger = logging.getLogger(__name__)


def create_export_import_agent(
    odoo_url: str = "http://localhost:8069",
    odoo_db: str = "llmdb18",
    odoo_username: str = "admin",
    odoo_password: str = "admin"
) -> StateGraph:
    """
    Create the Export/Import agent flow.

    Args:
        odoo_url: URL of the Odoo server
        odoo_db: Name of the Odoo database
        odoo_username: Odoo username
        odoo_password: Odoo password

    Returns:
        StateGraph for the Export/Import agent flow
    """
    # Initialize state
    initial_state = AgentState(
        odoo_url=odoo_url,
        odoo_db=odoo_db,
        odoo_username=odoo_username,
        odoo_password=odoo_password
    )

    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("initialize", initialize_flow)
    workflow.add_node("select_model", select_model)
    workflow.add_node("select_fields", select_fields)
    workflow.add_node("set_filter", set_filter)
    workflow.add_node("execute_export", execute_export)
    workflow.add_node("select_import_file", select_import_file)
    workflow.add_node("select_import_model", select_import_model)
    workflow.add_node("map_fields", map_fields)
    workflow.add_node("validate_mapping", validate_mapping)
    workflow.add_node("execute_import", execute_import)
    workflow.add_node("complete", complete_flow)
    workflow.add_node("error", handle_error)

    # Add edges
    workflow.add_edge("initialize", "select_model")
    workflow.add_conditional_edges(
        "initialize",
        lambda state: state.mode.value,
        {
            FlowMode.EXPORT.value: "select_model",
            FlowMode.IMPORT.value: "select_import_file"
        }
    )

    # Export flow
    workflow.add_conditional_edges(
        "select_model",
        lambda state: state.current_step,
        {
            "select_model": "select_model",
            "select_fields": "select_fields",
            "error": "error"
        }
    )

    workflow.add_conditional_edges(
        "select_fields",
        lambda state: state.current_step,
        {
            "select_model": "select_model",
            "select_fields": "select_fields",
            "set_filter": "set_filter",
            "error": "error"
        }
    )

    workflow.add_conditional_edges(
        "set_filter",
        lambda state: state.current_step,
        {
            "select_model": "select_model",
            "select_fields": "select_fields",
            "set_filter": "set_filter",
            "execute_export": "execute_export",
            "error": "error"
        }
    )

    workflow.add_conditional_edges(
        "execute_export",
        lambda state: state.current_step,
        {
            "select_model": "select_model",
            "select_fields": "select_fields",
            "set_filter": "set_filter",
            "execute_export": "execute_export",
            "complete": "complete",
            "error": "error"
        }
    )

    # Import flow
    workflow.add_conditional_edges(
        "select_import_file",
        lambda state: state.current_step,
        {
            "select_import_file": "select_import_file",
            "select_import_model": "select_import_model",
            "error": "error"
        }
    )

    workflow.add_conditional_edges(
        "select_import_model",
        lambda state: state.current_step,
        {
            "select_import_file": "select_import_file",
            "select_import_model": "select_import_model",
            "map_fields": "map_fields",
            "error": "error"
        }
    )

    workflow.add_conditional_edges(
        "map_fields",
        lambda state: state.current_step,
        {
            "select_import_file": "select_import_file",
            "select_import_model": "select_import_model",
            "map_fields": "map_fields",
            "validate_mapping": "validate_mapping",
            "error": "error"
        }
    )

    workflow.add_conditional_edges(
        "validate_mapping",
        lambda state: state.current_step,
        {
            "select_import_file": "select_import_file",
            "select_import_model": "select_import_model",
            "map_fields": "map_fields",
            "validate_mapping": "validate_mapping",
            "execute_import": "execute_import",
            "error": "error"
        }
    )

    workflow.add_conditional_edges(
        "execute_import",
        lambda state: state.current_step,
        {
            "select_import_file": "select_import_file",
            "select_import_model": "select_import_model",
            "map_fields": "map_fields",
            "validate_mapping": "validate_mapping",
            "execute_import": "execute_import",
            "complete": "complete",
            "error": "error"
        }
    )

    # Final nodes
    workflow.add_edge("complete", END)
    workflow.add_edge("error", END)

    # Set the entry point
    workflow.set_entry_point("initialize")

    # Compile the graph
    return workflow.compile()


def initialize_flow(state: AgentState, message: Optional[str] = None) -> AgentState:
    """
    Initialize the agent flow.

    Args:
        state: The current agent state
        message: Optional message from the user

    Returns:
        Updated agent state
    """
    # Determine the mode based on the message
    if message:
        message_lower = message.lower()

        if "import" in message_lower:
            state.mode = FlowMode.IMPORT
            state.current_step = "select_import_file"
        else:
            # Default to export
            state.mode = FlowMode.EXPORT
            state.current_step = "select_model"

        # Try to extract model name if present
        if state.mode == FlowMode.EXPORT and "model" in message_lower:
            import re
            model_match = re.search(r"model[:\s]\s*['\"]?([a-zA-Z0-9_.]+)['\"]?", message)

            if model_match:
                state.export_state.model_name = model_match.group(1)
                state.current_step = "select_fields"

        # Try to extract import file if present
        if state.mode == FlowMode.IMPORT and ("file" in message_lower or "csv" in message_lower):
            import re
            file_match = re.search(r"(?:file|csv)[:\s]\s*['\"]?([^'\"]+\.csv)['\"]?", message)

            if file_match:
                file_path = file_match.group(1)

                if os.path.exists(file_path):
                    state.import_state.import_path = file_path
                    state.current_step = "select_import_model"

    return state


def complete_flow(state: AgentState, message: Optional[str] = None) -> AgentState:
    """
    Complete the agent flow.

    Args:
        state: The current agent state
        message: Optional message from the user

    Returns:
        Updated agent state
    """
    if state.mode == FlowMode.EXPORT:
        state.export_state.status = "completed"
    else:
        state.import_state.status = "completed"

    return state


def handle_error(state: AgentState, message: Optional[str] = None) -> AgentState:
    """
    Handle errors in the agent flow.

    Args:
        state: The current agent state
        message: Optional message from the user

    Returns:
        Updated agent state
    """
    if state.mode == FlowMode.EXPORT:
        state.export_state.status = "error"
    else:
        state.import_state.status = "error"

    return state


def run_export_flow(
    model_name: str,
    fields: Optional[List[str]] = None,
    filter_domain: Optional[List[Any]] = None,
    limit: int = 1000,
    export_path: Optional[str] = None,
    odoo_url: str = "http://localhost:8069",
    odoo_db: str = "llmdb18",
    odoo_username: str = "admin",
    odoo_password: str = "admin"
) -> Dict[str, Any]:
    """
    Run the export flow with the given parameters.

    Args:
        model_name: Name of the Odoo model to export
        fields: List of fields to export (if None, all fields are exported)
        filter_domain: Domain filter for the export
        limit: Maximum number of records to export
        export_path: Path to export the CSV file
        odoo_url: URL of the Odoo server
        odoo_db: Name of the Odoo database
        odoo_username: Odoo username
        odoo_password: Odoo password

    Returns:
        Dictionary with the export results
    """
    # Create initial state
    state = AgentState(
        mode=FlowMode.EXPORT,
        odoo_url=odoo_url,
        odoo_db=odoo_db,
        odoo_username=odoo_username,
        odoo_password=odoo_password
    )

    # Set export parameters
    state.export_state.model_name = model_name

    if fields:
        state.export_state.selected_fields = fields

    if filter_domain:
        state.export_state.filter_domain = filter_domain

    state.export_state.limit = limit

    if export_path:
        state.export_state.export_path = export_path
    else:
        model_name_safe = model_name.replace('.', '_')
        state.export_state.export_path = f"exports/{model_name_safe}_export.csv"

    # Create the graph
    graph = create_export_import_agent(odoo_url, odoo_db, odoo_username, odoo_password)

    # Run the flow with a higher recursion limit
    try:
        # Create a message to help the flow proceed without user input
        initial_message = f"Export records from {model_name} with fields {fields}"

        # Run the flow with a higher recursion limit
        outputs = []
        for output in graph.stream(state, config={"recursion_limit": 100}):
            outputs.append(output)
            if "error" in output:
                logger.error(f"Error in export flow: {output['error']}")
                return {
                    "success": False,
                    "error": output["error"]
                }

        # Get the final state from the last output
        if outputs:
            final_state = outputs[-1]["state"]
        else:
            logger.error("No outputs from graph.stream")
            return {
                "success": False,
                "error": "No outputs from graph.stream"
            }
    except Exception as e:
        logger.error(f"Error running export flow: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

    # Return the results
    return {
        "success": final_state.export_state.status == "completed",
        "model_name": final_state.export_state.model_name,
        "selected_fields": final_state.export_state.selected_fields,
        "filter_domain": final_state.export_state.filter_domain,
        "total_records": final_state.export_state.total_records,
        "exported_records": final_state.export_state.exported_records,
        "export_path": final_state.export_state.export_path,
        "error": final_state.export_state.error
    }


def run_import_flow(
    import_path: str,
    model_name: str,
    field_mapping: Optional[Dict[str, str]] = None,
    create_if_not_exists: bool = True,
    update_if_exists: bool = True,
    odoo_url: str = "http://localhost:8069",
    odoo_db: str = "llmdb18",
    odoo_username: str = "admin",
    odoo_password: str = "admin"
) -> Dict[str, Any]:
    """
    Run the import flow with the given parameters.

    Args:
        import_path: Path to the CSV file to import
        model_name: Name of the Odoo model to import into
        field_mapping: Mapping from CSV field names to Odoo field names
        create_if_not_exists: Whether to create new records if they don't exist
        update_if_exists: Whether to update existing records
        odoo_url: URL of the Odoo server
        odoo_db: Name of the Odoo database
        odoo_username: Odoo username
        odoo_password: Odoo password

    Returns:
        Dictionary with the import results
    """
    # Create initial state
    state = AgentState(
        mode=FlowMode.IMPORT,
        odoo_url=odoo_url,
        odoo_db=odoo_db,
        odoo_username=odoo_username,
        odoo_password=odoo_password
    )

    # Set import parameters
    state.import_state.import_path = import_path
    state.import_state.model_name = model_name

    if field_mapping:
        state.import_state.field_mapping = field_mapping

    state.import_state.create_if_not_exists = create_if_not_exists
    state.import_state.update_if_exists = update_if_exists

    # Create the graph
    graph = create_export_import_agent(odoo_url, odoo_db, odoo_username, odoo_password)

    # Run the flow with a higher recursion limit
    try:
        # Create a message to help the flow proceed without user input
        initial_message = f"Import records into {model_name} from {import_path}"

        # Run the flow with a higher recursion limit
        outputs = []
        for output in graph.stream(state, config={"recursion_limit": 100}):
            outputs.append(output)
            if "error" in output:
                logger.error(f"Error in import flow: {output['error']}")
                return {
                    "success": False,
                    "error": output["error"]
                }

        # Get the final state from the last output
        if outputs:
            final_state = outputs[-1]["state"]
        else:
            logger.error("No outputs from graph.stream")
            return {
                "success": False,
                "error": "No outputs from graph.stream"
            }
    except Exception as e:
        logger.error(f"Error running import flow: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

    # Return the results
    return {
        "success": final_state.import_state.status == "completed",
        "model_name": final_state.import_state.model_name,
        "import_path": final_state.import_state.import_path,
        "field_mapping": final_state.import_state.field_mapping,
        "total_records": final_state.import_state.total_records,
        "imported_records": final_state.import_state.imported_records,
        "updated_records": final_state.import_state.updated_records,
        "failed_records": final_state.import_state.failed_records,
        "error": final_state.import_state.error
    }