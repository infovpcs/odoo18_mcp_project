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

        use_ollama = st.checkbox(
            "Use Ollama",
            value=session_state.code_agent.use_ollama,
            help="Use Ollama as a fallback model for code generation."
        )

        no_llm = st.checkbox(
            "No LLM (Fallback Only)",
            value=session_state.code_agent.no_llm,
            help="Don't use any LLM models, use fallback analysis only. This is useful if you're having issues with the LLM models."
        )

    with col2:
        save_to_files = st.checkbox(
            "Save to Files",
            value=session_state.code_agent.save_to_files,
            help="Save the generated files to disk."
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
        session_state.code_agent.no_llm = no_llm
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
                no_llm=no_llm,
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

            # Log the result for debugging
            logger.info(f"Result from run_odoo_code_agent: {json.dumps(result, indent=2)}")

            if result.get("success", False):
                # Update session state with the result
                data = result.get("data", {})

                # Log the data for debugging
                logger.info(f"Data from result: {json.dumps(data, indent=2)}")

                # Check if the result contains a 'result' field that might be a JSON string
                if not data and "result" in result:
                    try:
                        # Try to parse the result as JSON
                        result_data = json.loads(result["result"]) if isinstance(result["result"], str) else result["result"]
                        if isinstance(result_data, dict) and "data" in result_data:
                            # Extract the data from the result
                            data = result_data["data"]
                            logger.info(f"Extracted data from result: {json.dumps(data, indent=2)}")
                    except (json.JSONDecodeError, TypeError, KeyError) as e:
                        # If the result is not a valid JSON object or doesn't have the expected structure
                        logger.info(f"Could not extract structured data from result: {str(e)}")

                # Update session state with the data
                session_state.code_agent.plan = data.get("plan", "")
                session_state.code_agent.tasks = data.get("tasks", [])
                session_state.code_agent.module_name = data.get("module_name", "")
                session_state.code_agent.files_to_create = data.get("files_to_create", {})
                session_state.code_agent.history = data.get("history", [])

                # Store the raw planning and analysis states if available
                if "state_dict" in data and isinstance(data["state_dict"], dict):
                    # Store planning state
                    session_state.code_agent.planning_state = data["state_dict"].get("planning_state", {})

                    # Store analysis state
                    session_state.code_agent.analysis_state = data["state_dict"].get("analysis_state", {})

                    # Extract technical considerations and estimated time from planning state
                    if session_state.code_agent.planning_state and "context" in session_state.code_agent.planning_state:
                        plan_context = session_state.code_agent.planning_state.get("context", {})
                        plan_result = plan_context.get("plan_result", {})

                        # Extract technical considerations
                        if "technical_considerations" in plan_result:
                            session_state.code_agent.technical_considerations = plan_result.get("technical_considerations", [])

                        # Extract estimated time
                        if "estimated_time" in plan_result:
                            session_state.code_agent.estimated_time = plan_result.get("estimated_time", "")

                    # Extract model information from analysis state
                    if session_state.code_agent.analysis_state and "context" in session_state.code_agent.analysis_state:
                        analysis_context = session_state.code_agent.analysis_state.get("context", {})

                        # Extract model information
                        if "model_info" in analysis_context:
                            session_state.code_agent.model_info = analysis_context.get("model_info", {})

                        # Extract detailed model information
                        if "detailed_model_info" in analysis_context:
                            session_state.code_agent.detailed_model_info = analysis_context.get("detailed_model_info", {})

                        # Extract analysis result
                        if "analysis" in analysis_context:
                            session_state.code_agent.analysis_result = analysis_context.get("analysis", {})

                            # Extract proposed models from analysis result
                            if "models" in session_state.code_agent.analysis_result:
                                proposed_models = session_state.code_agent.analysis_result.get("models", [])

                                # Module name is now managed by the MCP server
                                # No need to derive module name here as it's handled by the server

                                # Enhance model information with default values if missing
                                enhanced_models = []
                                for i, model in enumerate(proposed_models):
                                    # Ensure model has a name
                                    if not model.get('name') or model.get('name') == 'unknown.model':
                                        # Use a default model name if none is provided
                                        model['name'] = f"{session_state.code_agent.module_name}.model{i+1}"

                                    # Ensure model has a description
                                    if not model.get('description') or model.get('description') == '':
                                        model['description'] = f"Model for {model['name']}"

                                    # Ensure model has fields array
                                    if 'fields' not in model:
                                        model['fields'] = []

                                    # Enhance field information
                                    enhanced_fields = []
                                    for field in model.get('fields', []):
                                        # Ensure field has a name
                                        if not field.get('name'):
                                            field['name'] = 'unknown_field'

                                        # Ensure field has a type
                                        if not field.get('type'):
                                            field['type'] = 'char'

                                        # Ensure field has a description
                                        if not field.get('description'):
                                            field['description'] = 'No description available'

                                        enhanced_fields.append(field)

                                    model['fields'] = enhanced_fields
                                    enhanced_models.append(model)

                                session_state.code_agent.proposed_models = enhanced_models

                # Store the state information for resuming later
                session_state.code_agent.state_dict = data.get("state_dict")
                session_state.code_agent.requires_validation = data.get("requires_validation", False)
                session_state.code_agent.current_step = data.get("current_step")

                # Log the session state for debugging
                logger.info(f"Updated session state: plan={bool(session_state.code_agent.plan)}, tasks={len(session_state.code_agent.tasks)}, technical_considerations={len(session_state.code_agent.technical_considerations)}, estimated_time={session_state.code_agent.estimated_time}, module_name={session_state.code_agent.module_name}, model_info={len(session_state.code_agent.model_info)}, detailed_model_info={len(session_state.code_agent.detailed_model_info)}, proposed_models={len(session_state.code_agent.proposed_models)}")

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

        # Display estimated time if available
        if session_state.code_agent.estimated_time:
            st.subheader("Estimated Time")
            st.markdown(f"**{session_state.code_agent.estimated_time}**")

        # Display the tasks
        if session_state.code_agent.tasks:
            st.subheader("Implementation Tasks")
            for i, task in enumerate(session_state.code_agent.tasks, 1):
                if isinstance(task, dict):
                    # If task is a dictionary, format it nicely
                    task_name = task.get('task_name', f"Task {i}")
                    task_desc = task.get('description', '')
                    st.markdown(f"**{i}. {task_name}**")
                    if task_desc:
                        st.markdown(f"   *{task_desc}*")

                    # Display steps if available
                    if 'steps' in task and task['steps']:
                        for step in task['steps']:
                            st.markdown(f"   - {step}")
                else:
                    # If task is a string, display it directly
                    st.markdown(f"{i}. {task}")

        # Display technical considerations if available
        if session_state.code_agent.technical_considerations:
            st.subheader("Technical Considerations")
            for consideration in session_state.code_agent.technical_considerations:
                st.markdown(f"- {consideration}")

        # Display model information if available
        if session_state.code_agent.model_info:
            with st.expander("Existing Odoo Models Analysis"):
                st.subheader("Relevant Odoo Models")
                for model_name, info in session_state.code_agent.model_info.items():
                    st.markdown(f"**Model: {model_name}** ({info.get('name', '')})")
                    st.markdown("Important fields:")

                    fields = info.get("fields", {})
                    for field_name, field_info in fields.items():
                        field_type = field_info.get("type", "char")
                        field_string = field_info.get("string", field_name)
                        relation = field_info.get("relation", "")
                        relation_info = f" -> {relation}" if relation else ""

                        st.markdown(f"- {field_name} ({field_type}{relation_info}): {field_string}")

                    st.markdown("---")

        # Display proposed models if available
        if session_state.code_agent.proposed_models:
            with st.expander("Proposed Models for the Module", expanded=True):
                st.subheader("Models to be Created")
                for model in session_state.code_agent.proposed_models:
                    model_name = model.get('name', '')
                    model_desc = model.get('description', '')

                    # Display model name with better formatting
                    st.markdown(f"### Model: {model_name}")

                    # Display model description if available
                    if model_desc:
                        st.markdown(f"**Description**: {model_desc}")

                    # Display fields with better formatting
                    st.markdown("#### Fields:")

                    # Check if fields exist and are not empty
                    if 'fields' in model and model.get('fields') and len(model.get('fields', [])) > 0:
                        # Create columns for field information
                        field_data = []
                        for field in model.get('fields', []):
                            field_name = field.get('name', '')
                            field_type = field.get('type', 'char')
                            field_desc = field.get('description', '')
                            relation = field.get('relation', '')
                            required = field.get('required', False)
                            readonly = field.get('readonly', False)

                            # Format field type with relation if applicable
                            field_type_display = field_type
                            if relation:
                                field_type_display = f"{field_type} → {relation}"

                            # Add attributes like required, readonly
                            attributes = []
                            if required:
                                attributes.append("required")
                            if readonly:
                                attributes.append("readonly")

                            attributes_str = f" ({', '.join(attributes)})" if attributes else ""

                            field_data.append({
                                "Field": field_name,
                                "Type": field_type_display,
                                "Attributes": attributes_str,
                                "Description": field_desc
                            })

                        if field_data:
                            # Convert to DataFrame for better display
                            import pandas as pd
                            df = pd.DataFrame(field_data)
                            st.table(df)
                    else:
                        # Dynamic field suggestion based on model name and query
                        st.info("No fields have been defined for this model yet. Based on your requirements, the following fields might be included:")

                        # Import pandas for table display
                        import pandas as pd
                        import re

                        # Extract key concepts from the query
                        query = session_state.code_agent.query.lower()

                        # Common fields for all models
                        common_fields = [
                            {"Field": "name", "Type": "char", "Attributes": "(required)", "Description": "Name/Description of the record"},
                            {"Field": "active", "Type": "boolean", "Attributes": "", "Description": "Whether this record is active"},
                            {"Field": "sequence", "Type": "integer", "Attributes": "", "Description": "Sequence for ordering"},
                        ]

                        # Initialize suggested fields with common fields
                        suggested_fields = common_fields.copy()

                        # Detect model type from model name
                        model_type = "unknown"

                        # Check for configuration model
                        if "config" in model_name or ".config" in model_name:
                            model_type = "configuration"

                        # Check for wizard model
                        elif "wizard" in model_name or ".wizard" in model_name:
                            model_type = "wizard"

                        # Check for report model
                        elif "report" in model_name or ".report" in model_name:
                            model_type = "report"

                        # Check for settings model
                        elif "settings" in model_name or ".settings" in model_name:
                            model_type = "settings"

                        # Check for line items model
                        elif "line" in model_name or ".line" in model_name:
                            model_type = "line_item"

                        # Add fields based on model type
                        if model_type == "configuration":
                            suggested_fields.extend([
                                {"Field": "company_id", "Type": "many2one → res.company", "Attributes": "", "Description": "Company this configuration belongs to"},
                                {"Field": "user_id", "Type": "many2one → res.users", "Attributes": "", "Description": "User who created this configuration"}
                            ])
                        elif model_type == "wizard":
                            suggested_fields.extend([
                                {"Field": "user_id", "Type": "many2one → res.users", "Attributes": "", "Description": "User running the wizard"},
                                {"Field": "state", "Type": "selection", "Attributes": "", "Description": "Current state of the wizard"}
                            ])
                        elif model_type == "report":
                            suggested_fields.extend([
                                {"Field": "date_from", "Type": "date", "Attributes": "", "Description": "Start date for the report"},
                                {"Field": "date_to", "Type": "date", "Attributes": "", "Description": "End date for the report"},
                                {"Field": "company_id", "Type": "many2one → res.company", "Attributes": "", "Description": "Company for the report"}
                            ])
                        elif model_type == "settings":
                            suggested_fields.extend([
                                {"Field": "company_id", "Type": "many2one → res.company", "Attributes": "(required)", "Description": "Company these settings apply to"},
                                {"Field": "group_id", "Type": "many2one → res.groups", "Attributes": "", "Description": "User group these settings apply to"}
                            ])
                        elif model_type == "line_item":
                            # Find the parent model from the model name
                            parent_model = re.sub(r'\.line$', '', model_name)
                            if parent_model == model_name:
                                parent_model = model_name.replace("line", "")

                            suggested_fields.extend([
                                {"Field": f"{parent_model}_id", "Type": f"many2one → {parent_model}", "Attributes": "(required)", "Description": "Parent record this line belongs to"},
                                {"Field": "product_id", "Type": "many2one → product.product", "Attributes": "", "Description": "Product for this line"},
                                {"Field": "quantity", "Type": "float", "Attributes": "", "Description": "Quantity"},
                                {"Field": "price_unit", "Type": "float", "Attributes": "", "Description": "Unit price"}
                            ])

                        # Add fields based on keywords in the query
                        if "currency" in query or "multi-currency" in query:
                            suggested_fields.extend([
                                {"Field": "currency_id", "Type": "many2one → res.currency", "Attributes": "", "Description": "Currency"},
                                {"Field": "rate", "Type": "float", "Attributes": "", "Description": "Exchange rate"}
                            ])

                        if "point of sale" in query or "pos" in query:
                            suggested_fields.extend([
                                {"Field": "pos_config_id", "Type": "many2one → pos.config", "Attributes": "", "Description": "POS configuration"},
                                {"Field": "pos_session_id", "Type": "many2one → pos.session", "Attributes": "", "Description": "POS session"}
                            ])

                        if "accounting" in query or "invoice" in query or "account" in query:
                            suggested_fields.extend([
                                {"Field": "journal_id", "Type": "many2one → account.journal", "Attributes": "", "Description": "Accounting journal"},
                                {"Field": "account_id", "Type": "many2one → account.account", "Attributes": "", "Description": "Account"}
                            ])

                        if "partner" in query or "customer" in query or "vendor" in query:
                            suggested_fields.extend([
                                {"Field": "partner_id", "Type": "many2one → res.partner", "Attributes": "", "Description": "Partner/Customer/Vendor"}
                            ])

                        if "product" in query or "inventory" in query:
                            suggested_fields.extend([
                                {"Field": "product_id", "Type": "many2one → product.product", "Attributes": "", "Description": "Product"},
                                {"Field": "product_tmpl_id", "Type": "many2one → product.template", "Attributes": "", "Description": "Product template"}
                            ])

                        if "sale" in query or "order" in query:
                            suggested_fields.extend([
                                {"Field": "order_id", "Type": "many2one → sale.order", "Attributes": "", "Description": "Sales order"},
                                {"Field": "state", "Type": "selection", "Attributes": "", "Description": "State of the order"}
                            ])

                        if "purchase" in query:
                            suggested_fields.extend([
                                {"Field": "purchase_id", "Type": "many2one → purchase.order", "Attributes": "", "Description": "Purchase order"}
                            ])

                        if "date" in query or "time" in query:
                            suggested_fields.extend([
                                {"Field": "date", "Type": "date", "Attributes": "", "Description": "Date"},
                                {"Field": "datetime", "Type": "datetime", "Attributes": "", "Description": "Date and time"}
                            ])

                        if "user" in query or "employee" in query:
                            suggested_fields.extend([
                                {"Field": "user_id", "Type": "many2one → res.users", "Attributes": "", "Description": "User"},
                                {"Field": "employee_id", "Type": "many2one → hr.employee", "Attributes": "", "Description": "Employee"}
                            ])

                        if "company" in query:
                            suggested_fields.extend([
                                {"Field": "company_id", "Type": "many2one → res.company", "Attributes": "", "Description": "Company"}
                            ])

                        # Remove duplicate fields based on Field name
                        unique_fields = []
                        field_names = set()
                        for field in suggested_fields:
                            if field["Field"] not in field_names:
                                unique_fields.append(field)
                                field_names.add(field["Field"])

                        # Display the suggested fields
                        if unique_fields:
                            df = pd.DataFrame(unique_fields)
                            st.table(df)

                            st.markdown("""
                            **Note**: These are suggested fields based on the model name and your requirements.
                            The code agent will define the actual fields during the coding phase, which may include additional fields or modify these suggestions.
                            """)
                        else:
                            # Fallback message if no fields could be suggested
                            st.markdown("""
                            The code agent will define appropriate fields during the coding phase based on:
                            1. The requirements in your query
                            2. Standard Odoo field conventions
                            3. Relationships with other models
                            4. Best practices for the specific use case
                            """)

                        st.markdown("You can provide feedback about specific fields you want to include in the feedback section below.")

                    st.markdown("---")

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
            no_llm=session_state.code_agent.no_llm,
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

        # Log the result for debugging
        logger.info(f"Result from run_odoo_code_agent (feedback): {json.dumps(result, indent=2)}")

        if result.get("success", False):
            # Update session state with the result
            data = result.get("data", {})

            # Log the data for debugging
            logger.info(f"Data from result (feedback): {json.dumps(data, indent=2)}")

            # Check if the result contains a 'result' field that might be a JSON string
            if not data and "result" in result:
                try:
                    # Try to parse the result as JSON
                    result_data = json.loads(result["result"]) if isinstance(result["result"], str) else result["result"]
                    if isinstance(result_data, dict) and "data" in result_data:
                        # Extract the data from the result
                        data = result_data["data"]
                        logger.info(f"Extracted data from result (feedback): {json.dumps(data, indent=2)}")
                except (json.JSONDecodeError, TypeError, KeyError) as e:
                    # If the result is not a valid JSON object or doesn't have the expected structure
                    logger.info(f"Could not extract structured data from result (feedback): {str(e)}")

            # Update session state with the data
            session_state.code_agent.files_to_create = data.get("files_to_create", {})
            session_state.code_agent.history = data.get("history", [])

            # Store the raw planning and analysis states if available
            if "state_dict" in data and isinstance(data["state_dict"], dict):
                # Store planning state
                session_state.code_agent.planning_state = data["state_dict"].get("planning_state", {})

                # Store analysis state
                session_state.code_agent.analysis_state = data["state_dict"].get("analysis_state", {})

                # Extract technical considerations and estimated time from planning state
                if session_state.code_agent.planning_state and "context" in session_state.code_agent.planning_state:
                    plan_context = session_state.code_agent.planning_state.get("context", {})
                    plan_result = plan_context.get("plan_result", {})

                    # Extract technical considerations
                    if "technical_considerations" in plan_result:
                        session_state.code_agent.technical_considerations = plan_result.get("technical_considerations", [])

                    # Extract estimated time
                    if "estimated_time" in plan_result:
                        session_state.code_agent.estimated_time = plan_result.get("estimated_time", "")

                # Extract model information from analysis state
                if session_state.code_agent.analysis_state and "context" in session_state.code_agent.analysis_state:
                    analysis_context = session_state.code_agent.analysis_state.get("context", {})

                    # Extract model information
                    if "model_info" in analysis_context:
                        session_state.code_agent.model_info = analysis_context.get("model_info", {})

                    # Extract detailed model information
                    if "detailed_model_info" in analysis_context:
                        session_state.code_agent.detailed_model_info = analysis_context.get("detailed_model_info", {})

                    # Extract analysis result
                    if "analysis" in analysis_context:
                        session_state.code_agent.analysis_result = analysis_context.get("analysis", {})

                        # Extract proposed models from analysis result
                        if "models" in session_state.code_agent.analysis_result:
                            proposed_models = session_state.code_agent.analysis_result.get("models", [])

                            # Enhance model information with default values if missing
                            enhanced_models = []
                            for model in proposed_models:
                                # Ensure model has a name
                                if not model.get('name'):
                                    model['name'] = 'unknown.model'

                                # Ensure model has a description
                                if not model.get('description'):
                                    model['description'] = 'No description available'

                                # Ensure model has fields array
                                if 'fields' not in model:
                                    model['fields'] = []

                                # Enhance field information
                                enhanced_fields = []
                                for field in model.get('fields', []):
                                    # Ensure field has a name
                                    if not field.get('name'):
                                        field['name'] = 'unknown_field'

                                    # Ensure field has a type
                                    if not field.get('type'):
                                        field['type'] = 'char'

                                    # Ensure field has a description
                                    if not field.get('description'):
                                        field['description'] = 'No description available'

                                    enhanced_fields.append(field)

                                model['fields'] = enhanced_fields
                                enhanced_models.append(model)

                            session_state.code_agent.proposed_models = enhanced_models

            # Store the state information for resuming later
            session_state.code_agent.state_dict = data.get("state_dict")
            session_state.code_agent.requires_validation = data.get("requires_validation", False)
            session_state.code_agent.current_step = data.get("current_step")

            # Log the session state for debugging
            logger.info(f"Updated session state (feedback): files_to_create={len(session_state.code_agent.files_to_create)}, technical_considerations={len(session_state.code_agent.technical_considerations)}, estimated_time={session_state.code_agent.estimated_time}, model_info={len(session_state.code_agent.model_info)}, detailed_model_info={len(session_state.code_agent.detailed_model_info)}, proposed_models={len(session_state.code_agent.proposed_models)}, requires_validation={session_state.code_agent.requires_validation}")

            # Get the current phase from the result
            current_phase = data.get("current_phase", "coding")
            try:
                session_state.code_agent.phase = AgentPhase(current_phase)
            except ValueError:
                # Default to CODE_REVIEW phase after processing planning feedback
                session_state.code_agent.phase = AgentPhase.CODE_REVIEW

            # Show a success message
            st.success("Feedback processed successfully!")

            # Add a message to the chat based on the phase and validation status
            if session_state.code_agent.phase == AgentPhase.CODE_REVIEW:
                session_state.add_chat_message(
                    "assistant",
                    f"I've processed your feedback and generated code for the '{session_state.code_agent.module_name}' module. "
                    f"I'm now reviewing the code for completeness and will automatically regenerate any incomplete files. "
                    f"Please check the Code Generation tab to monitor the review progress."
                )

                # Automatically continue with code review
                st.info("Starting code review process...")
                handle_code_review(session_state, mcp_connector)
            elif session_state.code_agent.requires_validation:
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

        # Display code review status if in CODE_REVIEW phase
        if session_state.code_agent.phase == AgentPhase.CODE_REVIEW:
            st.subheader("Code Review in Progress")
            st.markdown("""
            The code agent is currently reviewing the generated code for completeness.
            This process will automatically regenerate any incomplete files before presenting them for your feedback.
            """)

            # Show progress indicator
            st.spinner("Reviewing code for completeness...")

        # Display incomplete files if any
        if session_state.code_agent.incomplete_files:
            with st.expander("Incomplete Files Detected", expanded=True):
                st.warning(f"Found {len(session_state.code_agent.incomplete_files)} incomplete files that need to be regenerated.")

                for i, file in enumerate(session_state.code_agent.incomplete_files):
                    file_path = file.get("path", "unknown")
                    file_type = file.get("file_type", "unknown")
                    reason = file.get("reason", "Unknown reason")

                    st.markdown(f"**{i+1}. {file_path}** ({file_type})")
                    st.markdown(f"   - Reason: {reason}")

        # Display regenerated files if any
        if session_state.code_agent.regenerated_files:
            with st.expander("Regenerated Files", expanded=True):
                st.success(f"Successfully regenerated {len(session_state.code_agent.regenerated_files)} files.")

                for i, file in enumerate(session_state.code_agent.regenerated_files):
                    file_path = file.get("path", "unknown")
                    reason = file.get("reason", "Unknown reason")

                    st.markdown(f"**{i+1}. {file_path}**")
                    st.markdown(f"   - Original issue: {reason}")

        # Only show feedback form if not in CODE_REVIEW phase or if review is complete
        if session_state.code_agent.phase != AgentPhase.CODE_REVIEW or session_state.code_agent.review_complete:
            # Feedback form
            st.subheader("Feedback")
            render_feedback_form(
                session_state,
                on_submit=lambda feedback: handle_code_feedback(session_state, mcp_connector, feedback),
                key_prefix="code_feedback",
                placeholder="Provide feedback on the generated code..."
            )
        elif session_state.code_agent.phase == AgentPhase.CODE_REVIEW and not session_state.code_agent.review_complete:
            st.info("Code review is in progress. Please wait for the review to complete before providing feedback.")
    else:
        st.info("No code generated yet. Please complete the planning in the Planning tab.")

def handle_code_review(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Handle the code review phase.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    # Show a spinner and progress bar while processing
    with st.spinner("Reviewing code for completeness..."):
        # Create a progress bar
        progress_placeholder = st.empty()
        progress_bar = progress_placeholder.progress(0)

        # Show a status message
        status_placeholder = st.empty()
        status_placeholder.info("Phase 1/3: Analyzing code completeness...")

        # Update progress bar to simulate progress
        for i in range(33):
            progress_bar.progress(i)
            time.sleep(0.05)

        status_placeholder.info("Phase 2/3: Identifying incomplete files...")

        for i in range(33, 66):
            progress_bar.progress(i)
            time.sleep(0.05)

        status_placeholder.info("Phase 3/3: Regenerating incomplete files...")

        # Call the MCP tool to continue the code review process
        result = mcp_connector.run_odoo_code_agent(
            query=session_state.code_agent.query,
            use_gemini=session_state.code_agent.use_gemini,
            use_ollama=session_state.code_agent.use_ollama,
            no_llm=session_state.code_agent.no_llm,
            feedback=None,  # No feedback needed for code review
            save_to_files=session_state.code_agent.save_to_files,
            output_dir=session_state.code_agent.output_dir,
            wait_for_validation=True,  # Stop at the second validation point
            current_phase=AgentPhase.CODE_REVIEW.value,  # Continue from the code review phase
            state_dict=session_state.code_agent.state_dict  # Pass the saved state
        )

        # Complete the progress bar
        for i in range(66, 101):
            progress_bar.progress(i)
            time.sleep(0.03)

        # Clear the placeholders
        progress_placeholder.empty()
        status_placeholder.empty()

        # Log the result for debugging
        logger.info(f"Result from run_odoo_code_agent (code review): {json.dumps(result, indent=2)}")

        if result.get("success", False):
            # Update session state with the result
            data = result.get("data", {})

            # Log the data for debugging
            logger.info(f"Data from result (code review): {json.dumps(data, indent=2)}")

            # Check if the result contains a 'result' field that might be a JSON string
            if not data and "result" in result:
                try:
                    # Try to parse the result as JSON
                    result_data = json.loads(result["result"]) if isinstance(result["result"], str) else result["result"]
                    if isinstance(result_data, dict) and "data" in result_data:
                        # Extract the data from the result
                        data = result_data["data"]
                        logger.info(f"Extracted data from result (code review): {json.dumps(data, indent=2)}")
                except (json.JSONDecodeError, TypeError, KeyError) as e:
                    # If the result is not a valid JSON object or doesn't have the expected structure
                    logger.info(f"Could not extract structured data from result (code review): {str(e)}")

            # Update session state with the data
            session_state.code_agent.files_to_create = data.get("files_to_create", {})
            session_state.code_agent.history = data.get("history", [])

            # Extract incomplete and regenerated files if available
            if "state_dict" in data and isinstance(data["state_dict"], dict):
                coding_state = data["state_dict"].get("coding_state", {})
                session_state.code_agent.incomplete_files = coding_state.get("incomplete_files", [])
                session_state.code_agent.regenerated_files = coding_state.get("regenerated_files", [])
                session_state.code_agent.review_complete = coding_state.get("review_complete", False)

            # Store the state information for resuming later
            session_state.code_agent.state_dict = data.get("state_dict")
            session_state.code_agent.requires_validation = data.get("requires_validation", False)
            session_state.code_agent.current_step = data.get("current_step")

            # Get the current phase from the result
            current_phase = data.get("current_phase", "human_feedback_2")
            try:
                session_state.code_agent.phase = AgentPhase(current_phase)
            except ValueError:
                session_state.code_agent.phase = AgentPhase.HUMAN_FEEDBACK_2

            # Show a success message
            st.success("Code review completed successfully!")

            # Add a message to the chat
            if session_state.code_agent.incomplete_files:
                session_state.add_chat_message(
                    "assistant",
                    f"I've reviewed the code and found {len(session_state.code_agent.incomplete_files)} incomplete files. "
                    f"I've regenerated these files to ensure the module is complete. "
                    f"Please review the updated code in the Code Generation tab and provide feedback to continue."
                )
            else:
                session_state.add_chat_message(
                    "assistant",
                    f"I've reviewed the code and found no incomplete files. "
                    f"The module is ready for your review. "
                    f"Please check the Code Generation tab and provide feedback to continue."
                )
        else:
            # Show an error message
            error_msg = result.get("error", "Unknown error")
            session_state.code_agent.error = error_msg
            st.error(f"Error during code review: {error_msg}")


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
            no_llm=session_state.code_agent.no_llm,
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

        # Log the result for debugging
        logger.info(f"Result from run_odoo_code_agent (code feedback): {json.dumps(result, indent=2)}")

        if result.get("success", False):
            # Update session state with the result
            data = result.get("data", {})

            # Log the data for debugging
            logger.info(f"Data from result (code feedback): {json.dumps(data, indent=2)}")

            # Check if the result contains a 'result' field that might be a JSON string
            if not data and "result" in result:
                try:
                    # Try to parse the result as JSON
                    result_data = json.loads(result["result"]) if isinstance(result["result"], str) else result["result"]
                    if isinstance(result_data, dict) and "data" in result_data:
                        # Extract the data from the result
                        data = result_data["data"]
                        logger.info(f"Extracted data from result (code feedback): {json.dumps(data, indent=2)}")
                except (json.JSONDecodeError, TypeError, KeyError) as e:
                    # If the result is not a valid JSON object or doesn't have the expected structure
                    logger.info(f"Could not extract structured data from result (code feedback): {str(e)}")

            # Update session state with the data
            session_state.code_agent.files_to_create = data.get("files_to_create", {})
            session_state.code_agent.history = data.get("history", [])

            # Store the raw planning and analysis states if available
            if "state_dict" in data and isinstance(data["state_dict"], dict):
                # Store planning state
                session_state.code_agent.planning_state = data["state_dict"].get("planning_state", {})

                # Store analysis state
                session_state.code_agent.analysis_state = data["state_dict"].get("analysis_state", {})

                # Extract technical considerations and estimated time from planning state
                if session_state.code_agent.planning_state and "context" in session_state.code_agent.planning_state:
                    plan_context = session_state.code_agent.planning_state.get("context", {})
                    plan_result = plan_context.get("plan_result", {})

                    # Extract technical considerations
                    if "technical_considerations" in plan_result:
                        session_state.code_agent.technical_considerations = plan_result.get("technical_considerations", [])

                    # Extract estimated time
                    if "estimated_time" in plan_result:
                        session_state.code_agent.estimated_time = plan_result.get("estimated_time", "")

                # Extract model information from analysis state
                if session_state.code_agent.analysis_state and "context" in session_state.code_agent.analysis_state:
                    analysis_context = session_state.code_agent.analysis_state.get("context", {})

                    # Extract model information
                    if "model_info" in analysis_context:
                        session_state.code_agent.model_info = analysis_context.get("model_info", {})

                    # Extract detailed model information
                    if "detailed_model_info" in analysis_context:
                        session_state.code_agent.detailed_model_info = analysis_context.get("detailed_model_info", {})

                    # Extract analysis result
                    if "analysis" in analysis_context:
                        session_state.code_agent.analysis_result = analysis_context.get("analysis", {})

                        # Extract proposed models from analysis result
                        if "models" in session_state.code_agent.analysis_result:
                            proposed_models = session_state.code_agent.analysis_result.get("models", [])

                            # Enhance model information with default values if missing
                            enhanced_models = []
                            for model in proposed_models:
                                # Ensure model has a name
                                if not model.get('name'):
                                    model['name'] = 'unknown.model'

                                # Ensure model has a description
                                if not model.get('description'):
                                    model['description'] = 'No description available'

                                # Ensure model has fields array
                                if 'fields' not in model:
                                    model['fields'] = []

                                # Enhance field information
                                enhanced_fields = []
                                for field in model.get('fields', []):
                                    # Ensure field has a name
                                    if not field.get('name'):
                                        field['name'] = 'unknown_field'

                                    # Ensure field has a type
                                    if not field.get('type'):
                                        field['type'] = 'char'

                                    # Ensure field has a description
                                    if not field.get('description'):
                                        field['description'] = 'No description available'

                                    enhanced_fields.append(field)

                                model['fields'] = enhanced_fields
                                enhanced_models.append(model)

                            session_state.code_agent.proposed_models = enhanced_models

            # Store the state information for resuming later
            session_state.code_agent.state_dict = data.get("state_dict")
            session_state.code_agent.requires_validation = data.get("requires_validation", False)
            session_state.code_agent.current_step = data.get("current_step")

            # Log the session state for debugging
            logger.info(f"Updated session state (code feedback): files_to_create={len(session_state.code_agent.files_to_create)}, technical_considerations={len(session_state.code_agent.technical_considerations)}, estimated_time={session_state.code_agent.estimated_time}, model_info={len(session_state.code_agent.model_info)}, detailed_model_info={len(session_state.code_agent.detailed_model_info)}, proposed_models={len(session_state.code_agent.proposed_models)}, requires_validation={session_state.code_agent.requires_validation}")

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
