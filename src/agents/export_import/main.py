#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main agent flow for Export/Import operations.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union, Tuple, Annotated, TypedDict

from langchain.schema import HumanMessage, AIMessage
# StrOutputParser removed (unavailable in this langchain version)
from dotenv import load_dotenv
load_dotenv()
import os
try:
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolNode
except ImportError:
    # langgraph not installed: disable graph-based agent
    StateGraph = END = None
    ToolNode = None

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

# Delegate to direct implementation for stability
import export_import_tools
from export_import_tools import run_export_flow as run_export_flow_direct, run_import_flow as run_import_flow_direct

def create_export_import_agent(
    odoo_url: str = os.getenv("ODOO_URL", "http://localhost:8069"),
    odoo_db: str = os.getenv("ODOO_DB", "llmdb18"),
    odoo_username: str = os.getenv("ODOO_USERNAME", "admin"),
    odoo_password: str = os.getenv("ODOO_PASSWORD", "admin")
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

run_export_flow = run_export_flow_direct
run_import_flow = run_import_flow_direct