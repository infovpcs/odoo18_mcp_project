#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Agent Graph Page for Streamlit Client

This module provides the code agent graph visualization page for the Streamlit client.
"""

import logging
import os
import tempfile
from enum import Enum
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
        CODE_REVIEW = "code_review"
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

def conditional_edge_after_coding(state):
    """Determine the next step after completing coding."""
    if state.phase == OdooAgentPhase.CODE_REVIEW:
        return "start_code_review"  # Move to code review phase
    else:
        return "request_feedback"  # Move to human feedback 2

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

    # Code Review phase nodes
    graph.add_node("start_code_review", lambda state: state)
    graph.add_node("review_code_completeness", lambda state: state)
    graph.add_node("regenerate_incomplete_files", lambda state: state)

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
    graph.add_edge("complete_coding", conditional_edge_after_coding)  # Either code review or human feedback

    # Add edges for Code Review phase
    graph.add_edge("start_code_review", "review_code_completeness")
    graph.add_edge("review_code_completeness", "regenerate_incomplete_files")
    graph.add_edge("regenerate_incomplete_files", "request_feedback")  # Second human feedback

    # Add edges for Finalization phase
    graph.add_edge("finalize_code", "complete")

    # Add error edges from all nodes to error
    for node in ["initialize", "gather_documentation", "gather_model_information",
                "analyze_requirements", "complete_analysis", "create_plan",
                "create_tasks", "complete_planning", "request_feedback",
                "process_feedback", "setup_module_structure", "generate_code",
                "complete_coding", "start_code_review", "review_code_completeness",
                "regenerate_incomplete_files", "finalize_code"]:
        # Add a simple edge without condition - LangGraph API may have changed
        graph.add_edge(node, "error")

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

            # Try to use the LangGraph visualization API
            try:
                # Import the visualization module
                from langgraph.visualization import visualize

                # Get the mermaid string representation
                mermaid_text = visualize.get_mermaid_str(graph)

                # Display the mermaid code for debugging
                with st.expander("View Mermaid Code"):
                    st.code(mermaid_text, language="mermaid")

                # Skip the manual mermaid diagram generation
                use_manual_diagram = False

            except (ImportError, AttributeError) as e:
                st.warning(f"Could not use LangGraph visualization: {str(e)}")
                # Fall back to our manual mermaid diagram
                mermaid_text = "graph TD;\n"
                use_manual_diagram = True

            # If we need to use the manual diagram, generate it
            if use_manual_diagram:
                # Add nodes
                mermaid_text += "  initialize[Initialize];\n"
                mermaid_text += "  gather_documentation[Gather Documentation];\n"
                mermaid_text += "  gather_model_information[Gather Model Information];\n"
                mermaid_text += "  analyze_requirements[Analyze Requirements];\n"
                mermaid_text += "  complete_analysis[Complete Analysis];\n"
                mermaid_text += "  create_plan[Create Plan];\n"
                mermaid_text += "  create_tasks[Create Tasks];\n"
                mermaid_text += "  complete_planning[Complete Planning];\n"
                mermaid_text += "  request_feedback[Request Feedback];\n"
                mermaid_text += "  process_feedback[Process Feedback];\n"
                mermaid_text += "  setup_module_structure[Setup Module Structure];\n"
                mermaid_text += "  generate_code[Generate Code];\n"
                mermaid_text += "  complete_coding[Complete Coding];\n"
                mermaid_text += "  start_code_review[Start Code Review];\n"
                mermaid_text += "  review_code_completeness[Review Code Completeness];\n"
                mermaid_text += "  regenerate_incomplete_files[Regenerate Incomplete Files];\n"
                mermaid_text += "  finalize_code[Finalize Code];\n"
                mermaid_text += "  complete[Complete];\n"
                mermaid_text += "  error[Error];\n"

                # Add edges
                mermaid_text += "  initialize --> gather_documentation;\n"
                mermaid_text += "  gather_documentation --> gather_model_information;\n"
                mermaid_text += "  gather_model_information --> analyze_requirements;\n"
                mermaid_text += "  analyze_requirements --> complete_analysis;\n"
                mermaid_text += "  complete_analysis --> create_plan;\n"
                mermaid_text += "  create_plan --> create_tasks;\n"
                mermaid_text += "  create_tasks --> complete_planning;\n"
                mermaid_text += "  complete_planning --> request_feedback;\n"
                mermaid_text += "  request_feedback --> process_feedback;\n"
                mermaid_text += "  process_feedback --> setup_module_structure;\n"
                mermaid_text += "  setup_module_structure --> generate_code;\n"
                mermaid_text += "  generate_code --> complete_coding;\n"
                mermaid_text += "  complete_coding --> start_code_review;\n"
                mermaid_text += "  start_code_review --> review_code_completeness;\n"
                mermaid_text += "  review_code_completeness --> regenerate_incomplete_files;\n"
                mermaid_text += "  regenerate_incomplete_files --> request_feedback;\n"
                mermaid_text += "  process_feedback --> finalize_code;\n"
                mermaid_text += "  finalize_code --> complete;\n"

                # Add error edges (simplified)
                mermaid_text += "  initialize --> error;\n"
                mermaid_text += "  gather_documentation --> error;\n"
                mermaid_text += "  gather_model_information --> error;\n"
                mermaid_text += "  analyze_requirements --> error;\n"
                mermaid_text += "  complete_analysis --> error;\n"
                mermaid_text += "  create_plan --> error;\n"
                mermaid_text += "  create_tasks --> error;\n"
                mermaid_text += "  complete_planning --> error;\n"
                mermaid_text += "  request_feedback --> error;\n"
                mermaid_text += "  process_feedback --> error;\n"
                mermaid_text += "  setup_module_structure --> error;\n"
                mermaid_text += "  generate_code --> error;\n"
                mermaid_text += "  complete_coding --> error;\n"
                mermaid_text += "  start_code_review --> error;\n"
                mermaid_text += "  review_code_completeness --> error;\n"
                mermaid_text += "  regenerate_incomplete_files --> error;\n"
                mermaid_text += "  finalize_code --> error;\n"

                # Display the manual mermaid code for debugging
                with st.expander("View Manual Mermaid Code"):
                    st.code(mermaid_text, language="mermaid")

            # Display the mermaid diagram directly using Streamlit's mermaid support
            st.markdown("### Odoo Code Agent Workflow")
            st.markdown(f"```mermaid\n{mermaid_text}\n```")

            # Clean up the temporary file if it exists
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temporary file: {cleanup_error}")
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
    st.markdown("13. **complete_coding** → start_code_review (Code Review Phase) or request_feedback (Human Feedback 2)")

    # Code Review phase
    st.markdown("### Code Review Phase")
    st.markdown("14. **start_code_review** → review_code_completeness")
    st.markdown("15. **review_code_completeness** → regenerate_incomplete_files")
    st.markdown("16. **regenerate_incomplete_files** → request_feedback (Human Feedback 2)")

    # Human Feedback 2
    st.markdown("### Human Feedback 2")
    st.markdown("17. **request_feedback** → process_feedback")
    st.markdown("18. **process_feedback** → finalize_code (Finalization Phase)")

    # Finalization phase
    st.markdown("### Finalization Phase")
    st.markdown("19. **finalize_code** → complete")

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
    - **Complete Coding**: Finalize the code generation and transition to code review

    ### 5. Code Review Phase
    - **Start Code Review**: Initialize the code review process
    - **Review Code Completeness**: Check for incomplete or missing files
    - **Regenerate Incomplete Files**: Automatically regenerate any incomplete files

    ### 6. Human Feedback 2
    - **Request Feedback**: Ask the user for feedback on the generated code
    - **Process Feedback**: Incorporate the user's feedback into the code

    ### 7. Finalization Phase
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

    # Display code review status if in CODE_REVIEW phase
    if session_state.code_agent.phase == AgentPhase.CODE_REVIEW:
        st.subheader("Code Review Status")

        # Display review completion status
        if session_state.code_agent.review_complete:
            st.success("Code Review Status: Complete")
        else:
            st.info("Code Review Status: In Progress")

        # Display incomplete files if any
        if session_state.code_agent.incomplete_files:
            st.warning(f"Incomplete Files: {len(session_state.code_agent.incomplete_files)}")
            with st.expander("View Incomplete Files"):
                for i, file in enumerate(session_state.code_agent.incomplete_files):
                    file_path = file.get("path", "unknown")
                    file_type = file.get("file_type", "unknown")
                    reason = file.get("reason", "Unknown reason")
                    st.markdown(f"**{i+1}. {file_path}** ({file_type})")
                    st.markdown(f"   - Reason: {reason}")
        else:
            st.success("No incomplete files detected")

        # Display regenerated files if any
        if session_state.code_agent.regenerated_files:
            st.success(f"Regenerated Files: {len(session_state.code_agent.regenerated_files)}")
            with st.expander("View Regenerated Files"):
                for i, file in enumerate(session_state.code_agent.regenerated_files):
                    file_path = file.get("path", "unknown")
                    reason = file.get("reason", "Unknown reason")
                    st.markdown(f"**{i+1}. {file_path}**")
                    st.markdown(f"   - Original issue: {reason}")

    # Display any errors
    if session_state.code_agent.error:
        st.subheader("Error")
        st.error(session_state.code_agent.error)
