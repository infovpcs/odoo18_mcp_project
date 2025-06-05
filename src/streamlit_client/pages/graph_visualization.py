#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Graph Visualization Page for Streamlit Client

This module provides the graph visualization page for the Streamlit client.
"""

import logging
import os
import streamlit as st
import base64
from typing import Dict, Any, List, Optional

from ..utils.mcp_connector import MCPConnector
from ..utils.session_state import SessionState
from ..utils.diagram_utils import display_diagram, find_diagram_file

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("graph_visualization_page")

def render_graph_visualization_page(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the graph visualization page.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.title("Workflow Visualization")

    # Description of the page
    st.markdown("""
    This page provides visualizations of the Odoo 18 Code Agent workflow and other processes.
    Visualizations are generated using Mermaid diagrams rendered through the MCP server.
    """)

    # Create tabs for different sections
    tabs = st.tabs(["Code Agent Workflow", "Custom Diagram"])

    # Code Agent Workflow tab
    with tabs[0]:
        render_code_agent_workflow(session_state, mcp_connector)

    # Custom Diagram tab
    with tabs[1]:
        render_custom_diagram(session_state, mcp_connector)

def render_code_agent_workflow(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the code agent workflow visualization.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.header("Odoo Code Agent Workflow")

    # Description of the section
    st.markdown("""
    Visualize the workflow of the Simple Odoo Code Agent used for generating Odoo 18 modules.
    """)

    # Options for visualization
    col1, col2 = st.columns(2)
    
    with col1:
        theme = st.selectbox(
            "Theme",
            options=["default", "forest", "dark", "neutral"],
            index=0,
            help="Visual theme for the diagram.",
            key="workflow_theme_select"
        )
    
    with col2:
        background_color = st.color_picker(
            "Background Color",
            value="#ffffff",
            help="Background color for the diagram.",
            key="workflow_bg_color_picker"
        )

    # Use simplified workflow diagram from simple_code_agent_graph.py
    # This is a basic Mermaid flowchart representation of the code agent workflow
    mermaid_code = """
    flowchart TB
        design[Design Phase]
        plan[Planning Phase]
        code[Code Generation Phase]
        respond[Response Phase]
        complete[Complete]
        error[Error]
        
        design --> plan
        plan --> code
        code --> respond
        respond --> complete
        
        design -.-> error
        plan -.-> error
        code -.-> error
        respond -.-> error
        
        plan -.-> design
        code -.-> plan
        respond -.-> code
        
        classDef default fill:#f9f9f9,stroke:#333,stroke-width:1px;
        classDef success fill:#d4edda,stroke:#28a745,stroke-width:1px;
        classDef error fill:#f8d7da,stroke:#dc3545,stroke-width:1px;
        classDef active fill:#cce5ff,stroke:#007bff,stroke-width:2px;
        
        class complete success;
        class error error;
    """

    # Generate button
    if st.button("Generate Workflow Diagram", type="primary", key="generate_workflow_button"):
        # Show a spinner while generating
        with st.spinner("Generating diagram..."):
            # Call the generate_graph tool
            result = mcp_connector.generate_graph(
                mermaid_code=mermaid_code,
                name="odoo_code_agent_workflow",
                theme=theme,
                background_color=background_color.replace("#", "")
            )

            if result.get("success", False):
                # Get the path to the generated image
                image_path = result.get("result", "")
                
                # Use the diagram_utils module to display the workflow diagram
                display_diagram(image_path, session_state, title="Workflow Diagram")
            else:
                # Show an error message
                error_msg = result.get("error", "Unknown error")
                st.error(f"Error generating diagram: {error_msg}")

def render_custom_diagram(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the custom diagram section.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.header("Custom Mermaid Diagram")

    # Description of the section
    st.markdown("""
    Create and visualize custom diagrams using Mermaid syntax.
    [Mermaid Documentation](https://mermaid-js.github.io/mermaid/#/)
    """)

    # Custom diagram input
    mermaid_code = st.text_area(
        "Mermaid Code",
        value="""flowchart LR
    A[Start] --> B{Is it working?}
    B -->|Yes| C[Great!]
    B -->|No| D[Debug]
    D --> B
    C --> E[Deploy]""",
        height=200,
        help="Enter your Mermaid diagram code.",
        key="custom_diagram_input"
    )

    # Options for visualization
    col1, col2, col3 = st.columns(3)
    
    with col1:
        name = st.text_input(
            "Diagram Name",
            value="custom_diagram",
            help="Name for the diagram file.",
            key="custom_diagram_name_1"
        )
    
    with col2:
        theme = st.selectbox(
            "Theme",
            options=["default", "forest", "dark", "neutral"],
            index=0,
            help="Visual theme for the diagram.",
            key="custom_theme_select_1"
        )
    
    with col3:
        background_color = st.color_picker(
            "Background Color",
            value="#ffffff",
            help="Background color for the diagram.",
            key="custom_bg_color_picker_1"
        )

    # Generate button
    if st.button("Generate Custom Diagram", type="primary", key="generate_custom_button_1"):
        if not mermaid_code:
            st.error("Please provide Mermaid code.")
            return

        # Show a spinner while generating
        with st.spinner("Generating diagram..."):
            # Call the generate_graph tool
            result = mcp_connector.generate_graph(
                mermaid_code=mermaid_code,
                name=name,
                theme=theme,
                background_color=background_color.replace("#", "")
            )

            if result.get("success", False):
                # Get the path to the generated image
                image_path = result.get("result", "")
                
                # Use the diagram_utils module to display the custom diagram
                if display_diagram(image_path, session_state, title="Generated Diagram"):
                    # Also store the mermaid code in session state for future reference
                    session_state.last_mermaid_code = mermaid_code
            else:
                # Show an error message
                error_msg = result.get("error", "Unknown error")
                st.error(f"Error generating diagram: {error_msg}")
