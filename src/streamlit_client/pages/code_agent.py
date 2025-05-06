#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Code Agent Page for Streamlit Client

This module provides the code agent page for the Streamlit client.
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Union

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from ..components.chat import render_chat, render_feedback_form
from ..components.file_viewer import render_file_viewer
from ..utils.mcp_connector import MCPConnector
from ..utils.session_state import SessionState, AgentPhase

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("code_agent_page")

def render_code_agent_page(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the code agent page.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.title("Odoo 18 Code Agent")

    # Create tabs for different sections
    tabs = st.tabs(["Requirements", "Planning", "Code Generation", "Generated Files"])

    # Requirements tab
    with tabs[0]:
        render_requirements_tab(session_state, mcp_connector)

    # Planning tab
    with tabs[1]:
        render_planning_tab(session_state, mcp_connector)

    # Code Generation tab
    with tabs[2]:
        render_code_generation_tab(session_state, mcp_connector)

    # Generated Files tab
    with tabs[3]:
        render_generated_files_tab(session_state, mcp_connector)

def render_requirements_tab(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the requirements tab.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.header("Module Requirements")

    # Description of the tab
    st.markdown("""
    Specify your requirements for the Odoo 18 module you want to create.
    The code agent will analyze your requirements and create a plan for implementation.
    """)

    # Input for module requirements
    query = st.text_area(
        "Module Requirements",
        value=session_state.code_agent.query,
        height=200,
        placeholder="Describe the Odoo 18 module you want to create...",
        help="Provide a detailed description of the module you want to create."
    )

    # Options for code generation
    st.subheader("Options")

    col1, col2 = st.columns(2)

    with col1:
        use_gemini = st.checkbox(
            "Use Google Gemini",
            value=session_state.code_agent.use_gemini,
            help="Use Google Gemini as a fallback model for code generation."
        )

        save_to_files = st.checkbox(
            "Save to Files",
            value=session_state.code_agent.save_to_files,
            help="Save the generated files to disk."
        )

    with col2:
        use_ollama = st.checkbox(
            "Use Ollama",
            value=session_state.code_agent.use_ollama,
            help="Use Ollama as a fallback model for code generation."
        )

        output_dir = st.text_input(
            "Output Directory",
            value=session_state.code_agent.output_dir or "./generated_modules",
            help="Directory to save the generated files to."
        )

    # Start button
    if st.button("Start Analysis", type="primary"):
        if not query:
            st.error("Please provide module requirements.")
            return

        # Update session state
        session_state.code_agent.query = query
        session_state.code_agent.use_gemini = use_gemini
        session_state.code_agent.use_ollama = use_ollama
        session_state.code_agent.save_to_files = save_to_files
        session_state.code_agent.output_dir = output_dir

        # Show a spinner and progress bar while processing
        with st.spinner("Analyzing requirements..."):
            # Create a progress bar
            progress_placeholder = st.empty()
            progress_bar = progress_placeholder.progress(0)

            # Show a status message
            status_placeholder = st.empty()
            status_placeholder.info("Phase 1/3: Analyzing requirements and gathering documentation...")

            # Update progress bar to simulate progress
            for i in range(33):
                progress_bar.progress(i)
                time.sleep(0.1)

            status_placeholder.info("Phase 2/3: Planning module implementation...")

            for i in range(33, 66):
                progress_bar.progress(i)
                time.sleep(0.1)

            status_placeholder.info("Phase 3/3: Finalizing analysis...")

            # Call the MCP tool with wait_for_validation=True to stop at the first validation point
            result = mcp_connector.run_odoo_code_agent(
                query=query,
                use_gemini=use_gemini,
                use_ollama=use_ollama,
                save_to_files=save_to_files,
                output_dir=output_dir,
                wait_for_validation=True  # Stop at the first validation point
            )

            # Complete the progress bar
            for i in range(66, 101):
                progress_bar.progress(i)
                time.sleep(0.05)

            # Clear the placeholders
            progress_placeholder.empty()
            status_placeholder.empty()

            if result.get("success", False):
                # Update session state with the result
                data = result.get("data", {})

                session_state.code_agent.plan = data.get("plan", "")
                session_state.code_agent.tasks = data.get("tasks", [])
                session_state.code_agent.module_name = data.get("module_name", "")
                session_state.code_agent.files_to_create = data.get("files_to_create", {})
                session_state.code_agent.history = data.get("history", [])

                # Store the state information for resuming later
                session_state.code_agent.state_dict = data.get("state_dict")
                session_state.code_agent.requires_validation = data.get("requires_validation", False)
                session_state.code_agent.current_step = data.get("current_step")

                # Get the current phase from the result
                current_phase = data.get("current_phase", "planning")
                try:
                    session_state.code_agent.phase = AgentPhase(current_phase)
                except ValueError:
                    session_state.code_agent.phase = AgentPhase.PLANNING

                # Show a success message
                st.success("Analysis completed successfully!")

                # Add a message to the chat based on the validation status
                if session_state.code_agent.requires_validation:
                    session_state.add_chat_message(
                        "assistant",
                        f"I've analyzed your requirements for the '{session_state.code_agent.module_name}' module. "
                        f"Please review the plan in the Planning tab and provide feedback to continue."
                    )
                else:
                    session_state.add_chat_message(
                        "assistant",
                        f"I've analyzed your requirements for the '{session_state.code_agent.module_name}' module. "
                        f"Please review the plan in the Planning tab."
                    )
            else:
                # Show an error message
                error_msg = result.get("error", "Unknown error")
                session_state.code_agent.error = error_msg
                st.error(f"Error analyzing requirements: {error_msg}")

def render_planning_tab(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the planning tab.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.header("Module Planning")

    # Description of the tab
    st.markdown("""
    Review the plan for implementing the module and provide feedback.
    The code agent will use your feedback to refine the plan before generating code.
    """)

    # Display the plan
    if session_state.code_agent.plan:
        st.subheader("Implementation Plan")
        st.markdown(session_state.code_agent.plan)

        # Display the tasks
        if session_state.code_agent.tasks:
            st.subheader("Implementation Tasks")
            for i, task in enumerate(session_state.code_agent.tasks, 1):
                st.markdown(f"{i}. {task}")

        # Feedback form
        st.subheader("Feedback")
        render_feedback_form(
            session_state,
            on_submit=lambda feedback: handle_planning_feedback(session_state, mcp_connector, feedback),
            key_prefix="planning_feedback",
            placeholder="Provide feedback on the plan..."
        )
    else:
        st.info("No plan available yet. Please complete the analysis in the Requirements tab.")

def handle_planning_feedback(session_state: SessionState, mcp_connector: MCPConnector, feedback: str) -> None:
    """Handle feedback on the planning.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
        feedback: Feedback on the planning
    """
    # Update session state
    session_state.code_agent.feedback = feedback

    # Show a spinner and progress bar while processing
    with st.spinner("Processing feedback..."):
        # Create a progress bar
        progress_placeholder = st.empty()
        progress_bar = progress_placeholder.progress(0)

        # Show a status message
        status_placeholder = st.empty()
        status_placeholder.info("Phase 1/3: Analyzing feedback...")

        # Update progress bar to simulate progress
        for i in range(33):
            progress_bar.progress(i)
            time.sleep(0.05)

        status_placeholder.info("Phase 2/3: Updating implementation plan...")

        for i in range(33, 66):
            progress_bar.progress(i)
            time.sleep(0.05)

        status_placeholder.info("Phase 3/3: Generating code...")

        # Call the MCP tool with wait_for_validation=True to stop at the second validation point
        # Also pass the current phase and state_dict if available
        result = mcp_connector.run_odoo_code_agent(
            query=session_state.code_agent.query,
            use_gemini=session_state.code_agent.use_gemini,
            use_ollama=session_state.code_agent.use_ollama,
            feedback=feedback,
            save_to_files=session_state.code_agent.save_to_files,
            output_dir=session_state.code_agent.output_dir,
            wait_for_validation=True,  # Stop at the second validation point
            current_phase=AgentPhase.HUMAN_FEEDBACK_1.value,  # Continue from the first feedback phase
            state_dict=session_state.code_agent.state_dict  # Pass the saved state if available
        )

        # Complete the progress bar
        for i in range(66, 101):
            progress_bar.progress(i)
            time.sleep(0.03)

        # Clear the placeholders
        progress_placeholder.empty()
        status_placeholder.empty()

        if result.get("success", False):
            # Update session state with the result
            data = result.get("data", {})

            session_state.code_agent.files_to_create = data.get("files_to_create", {})
            session_state.code_agent.history = data.get("history", [])

            # Store the state information for resuming later
            session_state.code_agent.state_dict = data.get("state_dict")
            session_state.code_agent.requires_validation = data.get("requires_validation", False)
            session_state.code_agent.current_step = data.get("current_step")

            # Get the current phase from the result
            current_phase = data.get("current_phase", "coding")
            try:
                session_state.code_agent.phase = AgentPhase(current_phase)
            except ValueError:
                session_state.code_agent.phase = AgentPhase.CODING

            # Show a success message
            st.success("Feedback processed successfully!")

            # Add a message to the chat based on the validation status
            if session_state.code_agent.requires_validation:
                session_state.add_chat_message(
                    "assistant",
                    f"I've processed your feedback and generated code for the '{session_state.code_agent.module_name}' module. "
                    f"Please review the code in the Code Generation tab and provide feedback to continue."
                )
            else:
                session_state.add_chat_message(
                    "assistant",
                    f"I've processed your feedback and started generating code for the '{session_state.code_agent.module_name}' module. "
                    f"Please check the Code Generation tab."
                )
        else:
            # Show an error message
            error_msg = result.get("error", "Unknown error")
            session_state.code_agent.error = error_msg
            st.error(f"Error processing feedback: {error_msg}")

def render_code_generation_tab(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the code generation tab.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.header("Code Generation")

    # Description of the tab
    st.markdown("""
    Review the generated code and provide feedback.
    The code agent will use your feedback to refine the code.
    """)

    # Display the generated files
    if session_state.code_agent.files_to_create:
        st.subheader("Generated Files")

        # Display the number of files
        st.info(f"Generated {len(session_state.code_agent.files_to_create)} files for the '{session_state.code_agent.module_name}' module.")

        # Feedback form
        st.subheader("Feedback")
        render_feedback_form(
            session_state,
            on_submit=lambda feedback: handle_code_feedback(session_state, mcp_connector, feedback),
            key_prefix="code_feedback",
            placeholder="Provide feedback on the generated code..."
        )
    else:
        st.info("No code generated yet. Please complete the planning in the Planning tab.")

def handle_code_feedback(session_state: SessionState, mcp_connector: MCPConnector, feedback: str) -> None:
    """Handle feedback on the code.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
        feedback: Feedback on the code
    """
    # Update session state
    session_state.code_agent.feedback = feedback

    # Show a spinner and progress bar while processing
    with st.spinner("Processing feedback..."):
        # Create a progress bar
        progress_placeholder = st.empty()
        progress_bar = progress_placeholder.progress(0)

        # Show a status message
        status_placeholder = st.empty()
        status_placeholder.info("Phase 1/3: Analyzing feedback...")

        # Update progress bar to simulate progress
        for i in range(33):
            progress_bar.progress(i)
            time.sleep(0.05)

        status_placeholder.info("Phase 2/3: Updating implementation plan...")

        for i in range(33, 66):
            progress_bar.progress(i)
            time.sleep(0.05)

        status_placeholder.info("Phase 3/3: Finalizing code...")

        # Call the MCP tool to finalize the code (no need to wait for validation)
        # Also pass the current phase and state_dict if available
        result = mcp_connector.run_odoo_code_agent(
            query=session_state.code_agent.query,
            use_gemini=session_state.code_agent.use_gemini,
            use_ollama=session_state.code_agent.use_ollama,
            feedback=feedback,
            save_to_files=session_state.code_agent.save_to_files,
            output_dir=session_state.code_agent.output_dir,
            wait_for_validation=False,  # No need to wait for validation in the final step
            current_phase=AgentPhase.HUMAN_FEEDBACK_2.value,  # Continue from the second feedback phase
            state_dict=session_state.code_agent.state_dict  # Pass the saved state if available
        )

        # Complete the progress bar
        for i in range(66, 101):
            progress_bar.progress(i)
            time.sleep(0.03)

        # Clear the placeholders
        progress_placeholder.empty()
        status_placeholder.empty()

        if result.get("success", False):
            # Update session state with the result
            data = result.get("data", {})

            session_state.code_agent.files_to_create = data.get("files_to_create", {})
            session_state.code_agent.history = data.get("history", [])

            # Store the state information for resuming later
            session_state.code_agent.state_dict = data.get("state_dict")
            session_state.code_agent.requires_validation = data.get("requires_validation", False)
            session_state.code_agent.current_step = data.get("current_step")

            # Get the current phase from the result
            current_phase = data.get("current_phase", "finalization")
            try:
                session_state.code_agent.phase = AgentPhase(current_phase)
            except ValueError:
                session_state.code_agent.phase = AgentPhase.FINALIZATION

            # Check if the process is complete
            is_complete = data.get("is_complete", False)
            if is_complete:
                session_state.code_agent.phase = AgentPhase.FINALIZATION

            # Show a success message
            st.success("Feedback processed successfully!")

            # Add a message to the chat
            session_state.add_chat_message(
                "assistant",
                f"I've processed your feedback and finalized the code for the '{session_state.code_agent.module_name}' module. "
                f"Please check the Generated Files tab to download the files."
            )
        else:
            # Show an error message
            error_msg = result.get("error", "Unknown error")
            session_state.code_agent.error = error_msg
            st.error(f"Error processing feedback: {error_msg}")

def render_generated_files_tab(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the generated files tab.

    Args:
        session_state: Session state
        mcp_connector: MCP connector (not used in this function but kept for consistency)
    """
    # Note: mcp_connector is not used in this function but kept for consistency with other tab functions
    st.header("Generated Files")

    # Description of the tab
    st.markdown("""
    View and download the generated files for the module.
    """)

    # Display the generated files
    if session_state.code_agent.files_to_create:
        # Render the file viewer
        render_file_viewer(
            session_state.code_agent.files_to_create,
            show_download=True,
            max_height=500
        )

        # Download all files as a zip
        if st.button("Download All Files as ZIP"):
            # Create a zip file
            import io
            import zipfile

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for file_path, file_content in session_state.code_agent.files_to_create.items():
                    zip_file.writestr(file_path, file_content)

            # Create a download link
            import base64

            b64 = base64.b64encode(zip_buffer.getvalue()).decode()
            module_name = session_state.code_agent.module_name or "odoo_module"
            href = f'<a href="data:application/zip;base64,{b64}" download="{module_name}.zip">Download {module_name}.zip</a>'
            st.markdown(href, unsafe_allow_html=True)
    else:
        st.info("No files generated yet. Please complete the code generation in the Code Generation tab.")
