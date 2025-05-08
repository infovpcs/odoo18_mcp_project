#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Agent Graph Page for Streamlit Client

This module provides the code agent graph visualization page for the Streamlit client.
"""

import logging
import os
import tempfile
from typing import Any, Dict, List, Optional, Union

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from ..utils.mcp_connector import MCPConnector
from ..utils.session_state import SessionState, AgentPhase

# Import LangGraph
try:
    from langgraph.graph import StateGraph, END
except ImportError:
    st.error("LangGraph is not installed. Please install it with `pip install langgraph`")
    st.stop()

# Import the Odoo code agent state
try:
    from src.odoo_code_agent.state import OdooCodeAgentState, AgentPhase as OdooAgentPhase
except ImportError:
    # Create a mock class for demonstration purposes
    class OdooCodeAgentState:
        pass
    
    class OdooAgentPhase(str, Enum):
        ANALYSIS = "analysis"
        PLANNING = "planning"
        HUMAN_FEEDBACK_1 = "human_feedback_1"
        CODING = "coding"
        HUMAN_FEEDBACK_2 = "human_feedback_2"
        FINALIZATION = "finalization"

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("code_agent_graph_page")

def render_code_agent_graph_page(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the code agent graph page.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.title("Odoo 18 Code Agent Graph Flow")

    # Description of the page
    st.markdown("""
    This page visualizes the workflow of the Odoo 18 Code Agent using LangGraph.
    The graph shows the different phases and steps in the code generation process.
    """)

    # Create tabs for different views
    tabs = st.tabs(["Graph Visualization", "Workflow Explanation", "Current State"])

    # Graph Visualization tab
    with tabs[0]:
        render_graph_visualization()

    # Workflow Explanation tab
    with tabs[1]:
        render_workflow_explanation()

    # Current State tab
    with tabs[2]:
        render_current_state(session_state)

def conditional_edge_after_feedback(state):
    """Determine the next step after processing feedback."""
    if state.phase == OdooAgentPhase.HUMAN_FEEDBACK_1:
        return "setup_module_structure"  # Move to coding phase
    elif state.phase == OdooAgentPhase.HUMAN_FEEDBACK_2:
        return "finalize_code"  # Move to finalization phase
    else:
        return "error"  # Unexpected state

def create_code_agent_graph():
    """Create a LangGraph representation of the Odoo code agent workflow."""
    
    # Create the graph
    graph = StateGraph(OdooCodeAgentState)
    
    # Add nodes for each phase
    
    # Analysis phase nodes
    graph.add_node("initialize", lambda state: state)
    graph.add_node("gather_documentation", lambda state: state)
    graph.add_node("gather_model_information", lambda state: state)
    graph.add_node("analyze_requirements", lambda state: state)
    graph.add_node("complete_analysis", lambda state: state)
    
    # Planning phase nodes
    graph.add_node("create_plan", lambda state: state)
    graph.add_node("create_tasks", lambda state: state)
    graph.add_node("complete_planning", lambda state: state)
    
    # Human feedback nodes
    graph.add_node("request_feedback", lambda state: state)
    graph.add_node("process_feedback", lambda state: state)
    
    # Coding phase nodes
    graph.add_node("setup_module_structure", lambda state: state)
    graph.add_node("generate_code", lambda state: state)
    graph.add_node("complete_coding", lambda state: state)
    
    # Finalization phase
    graph.add_node("finalize_code", lambda state: state)
    
    # Add end node
    graph.add_node("complete", lambda state: state)
    
    # Add error node
    graph.add_node("error", lambda state: state)
    
    # Add edges for Analysis phase
    graph.add_edge("initialize", "gather_documentation")
    graph.add_edge("gather_documentation", "gather_model_information")
    graph.add_edge("gather_model_information", "analyze_requirements")
    graph.add_edge("analyze_requirements", "complete_analysis")
    graph.add_edge("complete_analysis", "create_plan")
    
    # Add edges for Planning phase
    graph.add_edge("create_plan", "create_tasks")
    graph.add_edge("create_tasks", "complete_planning")
    graph.add_edge("complete_planning", "request_feedback")  # First human feedback
    
    # Add edges for first Human Feedback phase
    graph.add_edge("request_feedback", "process_feedback")
    graph.add_edge("process_feedback", conditional_edge_after_feedback)
    
    # Add edges for Coding phase
    graph.add_edge("setup_module_structure", "generate_code")
    graph.add_edge("generate_code", "complete_coding")
    graph.add_edge("complete_coding", "request_feedback")  # Second human feedback
    
    # Add edges for Finalization phase
    graph.add_edge("finalize_code", "complete")
    
    # Add error edges from all nodes to error
    for node in ["initialize", "gather_documentation", "gather_model_information", 
                "analyze_requirements", "complete_analysis", "create_plan", 
                "create_tasks", "complete_planning", "request_feedback", 
                "process_feedback", "setup_module_structure", "generate_code", 
                "complete_coding", "finalize_code"]:
        graph.add_edge(node, "error", condition=lambda state: state.analysis_state.error or 
                                                            state.planning_state.error or 
                                                            state.coding_state.error or 
                                                            state.feedback_state.error)
    
    return graph

def render_graph_visualization():
    """Render the graph visualization."""
    st.header("Graph Visualization")

    # Create the graph
    try:
        graph = create_code_agent_graph()
        
        # Generate the Mermaid diagram
        try:
            # Create a temporary file to save the image
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                tmp_path = tmp.name
            
            # Generate the Mermaid diagram
            mermaid_png = graph.get_graph().draw_mermaid_png()
            
            # Save the image to the temporary file
            with open(tmp_path, 'wb') as f:
                f.write(mermaid_png)
            
            # Display the image
            st.image(tmp_path, caption="Odoo Code Agent Workflow", use_column_width=True)
            
            # Clean up the temporary file
            os.unlink(tmp_path)
        except Exception as e:
            st.error(f"Error generating graph visualization: {str(e)}")
            st.info("Displaying text-based representation instead.")
            render_text_based_graph()
    except Exception as e:
        st.error(f"Error creating graph: {str(e)}")
        st.info("Displaying text-based representation instead.")
        render_text_based_graph()

def render_text_based_graph():
    """Render a text-based representation of the graph."""
    # Analysis phase
    st.markdown("### Analysis Phase")
    st.markdown("1. **initialize** → gather_documentation")
    st.markdown("2. **gather_documentation** → gather_model_information")
    st.markdown("3. **gather_model_information** → analyze_requirements")
    st.markdown("4. **analyze_requirements** → complete_analysis")
    st.markdown("5. **complete_analysis** → create_plan (Planning Phase)")
    
    # Planning phase
    st.markdown("### Planning Phase")
    st.markdown("6. **create_plan** → create_tasks")
    st.markdown("7. **create_tasks** → complete_planning")
    st.markdown("8. **complete_planning** → request_feedback (Human Feedback 1)")
    
    # Human Feedback 1
    st.markdown("### Human Feedback 1")
    st.markdown("9. **request_feedback** → process_feedback")
    st.markdown("10. **process_feedback** → setup_module_structure (Coding Phase)")
    
    # Coding phase
    st.markdown("### Coding Phase")
    st.markdown("11. **setup_module_structure** → generate_code")
    st.markdown("12. **generate_code** → complete_coding")
    st.markdown("13. **complete_coding** → request_feedback (Human Feedback 2)")
    
    # Human Feedback 2
    st.markdown("### Human Feedback 2")
    st.markdown("14. **request_feedback** → process_feedback")
    st.markdown("15. **process_feedback** → finalize_code (Finalization Phase)")
    
    # Finalization phase
    st.markdown("### Finalization Phase")
    st.markdown("16. **finalize_code** → complete")
    
    # Error handling
    st.markdown("### Error Handling")
    st.markdown("Any node can transition to **error** if an error occurs")

def render_workflow_explanation():
    """Render the workflow explanation."""
    st.header("Workflow Explanation")

    st.markdown("""
    The Odoo 18 Code Agent follows a structured workflow with multiple phases:

    ### 1. Analysis Phase
    - **Initialize**: Set up the agent state and prepare for analysis
    - **Gather Documentation**: Retrieve relevant Odoo documentation
    - **Gather Model Information**: Collect information about Odoo models
    - **Analyze Requirements**: Analyze the user's requirements
    - **Complete Analysis**: Finalize the analysis and transition to planning

    ### 2. Planning Phase
    - **Create Plan**: Create a high-level implementation plan
    - **Create Tasks**: Break down the plan into specific tasks
    - **Complete Planning**: Finalize the planning and transition to human feedback

    ### 3. Human Feedback 1
    - **Request Feedback**: Ask the user for feedback on the plan
    - **Process Feedback**: Incorporate the user's feedback into the plan

    ### 4. Coding Phase
    - **Setup Module Structure**: Create the basic module structure
    - **Generate Code**: Generate the code for the module
    - **Complete Coding**: Finalize the code generation and transition to human feedback

    ### 5. Human Feedback 2
    - **Request Feedback**: Ask the user for feedback on the generated code
    - **Process Feedback**: Incorporate the user's feedback into the code

    ### 6. Finalization Phase
    - **Finalize Code**: Make final adjustments to the code
    - **Complete**: Mark the process as complete

    ### Error Handling
    - At any point, if an error occurs, the workflow transitions to the error state
    """)

def render_current_state(session_state: SessionState):
    """Render the current state of the code agent.

    Args:
        session_state: Session state
    """
    st.header("Current State")

    # Display the current phase
    st.subheader("Current Phase")
    st.info(f"Current Phase: {session_state.code_agent.phase.value}")

    # Display the current step
    st.subheader("Current Step")
    if session_state.code_agent.current_step:
        st.info(f"Current Step: {session_state.code_agent.current_step}")
    else:
        st.info("No current step available.")

    # Display whether validation is required
    st.subheader("Validation Status")
    if session_state.code_agent.requires_validation:
        st.warning("Requires Validation: Yes - Please provide feedback to continue.")
    else:
        st.success("Requires Validation: No - The agent is processing or has completed.")

    # Display the module name
    st.subheader("Module Information")
    if session_state.code_agent.module_name:
        st.info(f"Module Name: {session_state.code_agent.module_name}")
        st.info(f"Files to Create: {len(session_state.code_agent.files_to_create)}")
    else:
        st.info("No module information available.")

    # Display any errors
    if session_state.code_agent.error:
        st.subheader("Error")
        st.error(session_state.code_agent.error)
