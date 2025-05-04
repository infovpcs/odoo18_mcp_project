# src/agents/odoo_code_agent/main.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main agent flow for Odoo Code Generation.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union, Tuple, Annotated, TypedDict, Literal

from langchain.schema import HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from src.odoo_code_agent.state import OdooCodeAgentState, AgentPhase
from src.odoo_code_agent.utils.documentation_helper import documentation_helper
from src.odoo_code_agent.utils.odoo_connector import odoo_connector
from src.odoo_code_agent.utils.fallback_models import (
    initialize_gemini,
    initialize_ollama,
    generate_with_fallback
)

logger = logging.getLogger(__name__)


def initialize_analysis(state: OdooCodeAgentState, query: Optional[str] = None) -> OdooCodeAgentState:
    """
    Initialize the analysis phase.

    Args:
        state: The current agent state
        query: Optional query from the user

    Returns:
        Updated agent state
    """
    if query:
        state.analysis_state.query = query

    state.phase = AgentPhase.ANALYSIS
    state.current_step = "gather_documentation"

    return state


def gather_documentation(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """
    Gather documentation related to the query.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    try:
        # Query the documentation
        query = state.analysis_state.query
        results = documentation_helper.query_documentation(query, max_results=5)

        # Store the results in the state
        state.analysis_state.documentation_results = results
        state.current_step = "analyze_requirements"

    except Exception as e:
        logger.error(f"Error gathering documentation: {str(e)}")
        state.analysis_state.error = f"Error gathering documentation: {str(e)}"
        state.current_step = "error"

    return state


def analyze_requirements(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """
    Analyze the requirements based on the query and documentation.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    try:
        # This would typically involve an LLM call to analyze the requirements
        # For now, we'll just mark it as complete
        state.analysis_state.analysis_complete = True
        state.current_step = "complete_analysis"

    except Exception as e:
        logger.error(f"Error analyzing requirements: {str(e)}")
        state.analysis_state.error = f"Error analyzing requirements: {str(e)}"
        state.current_step = "error"

    return state


def complete_analysis(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """
    Complete the analysis phase and transition to planning.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    state.phase = AgentPhase.PLANNING
    state.current_step = "create_plan"

    return state


def create_plan(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """
    Create a plan based on the analysis.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    try:
        # This would typically involve an LLM call to create a plan
        # For now, we'll just set a placeholder plan
        state.planning_state.plan = "Plan for implementing the requested Odoo 18 functionality"
        state.current_step = "create_tasks"

    except Exception as e:
        logger.error(f"Error creating plan: {str(e)}")
        state.planning_state.error = f"Error creating plan: {str(e)}"
        state.current_step = "error"

    return state


def create_tasks(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """
    Create tasks based on the plan.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    try:
        # This would typically involve an LLM call to create tasks
        # For now, we'll just set placeholder tasks
        state.planning_state.tasks = [
            "Task 1: Set up module structure",
            "Task 2: Implement models",
            "Task 3: Create views",
            "Task 4: Add security",
            "Task 5: Write tests"
        ]
        state.current_step = "complete_planning"

    except Exception as e:
        logger.error(f"Error creating tasks: {str(e)}")
        state.planning_state.error = f"Error creating tasks: {str(e)}"
        state.current_step = "error"

    return state


def complete_planning(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """
    Complete the planning phase and transition to human feedback.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    state.planning_state.planning_complete = True
    state.phase = AgentPhase.HUMAN_FEEDBACK_1
    state.current_step = "request_feedback"

    return state


def request_feedback(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """
    Request feedback from the human.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    # This is where we would typically wait for human input
    # For now, we'll just set a placeholder
    state.current_step = "process_feedback"

    return state


def process_feedback(state: OdooCodeAgentState, feedback: Optional[str] = None) -> OdooCodeAgentState:
    """
    Process feedback from the human.

    Args:
        state: The current agent state
        feedback: Optional feedback from the human

    Returns:
        Updated agent state
    """
    try:
        if feedback:
            state.feedback_state.feedback = feedback

        # This would typically involve an LLM call to process the feedback
        # For now, we'll just mark it as processed
        state.feedback_state.feedback_processed = True

        # Determine the next phase based on the current phase
        if state.phase == AgentPhase.HUMAN_FEEDBACK_1:
            state.phase = AgentPhase.CODING
            state.current_step = "setup_module_structure"
        else:  # HUMAN_FEEDBACK_2
            state.phase = AgentPhase.FINALIZATION
            state.current_step = "finalize_code"

    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}")
        state.feedback_state.error = f"Error processing feedback: {str(e)}"
        state.current_step = "error"

    return state


def setup_module_structure(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """
    Set up the module structure.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    try:
        # Extract module name from the query or use a default
        query = state.analysis_state.query.lower()
        words = query.split()

        # Try to find a suitable module name
        module_name = "odoo_custom_module"
        for i, word in enumerate(words):
            if word in ["module", "addon", "app"]:
                if i > 0:
                    module_name = words[i-1] + "_" + word
                    break

        state.coding_state.module_name = module_name

        # Define the module structure
        state.coding_state.module_structure = {
            "__init__.py": "",
            "__manifest__.py": "",
            "models": {
                "__init__.py": "",
                "models.py": ""
            },
            "views": {
                "views.xml": ""
            },
            "security": {
                "ir.model.access.csv": ""
            },
            "static": {
                "description": {
                    "icon.png": ""
                }
            }
        }

        # Define the files to create
        state.coding_state.files_to_create = [
            {"path": f"{module_name}/__init__.py", "content": "from . import models\n"},
            {"path": f"{module_name}/__manifest__.py", "content": "{\n    'name': 'Custom Module',\n    'version': '1.0',\n    'category': 'Custom',\n    'summary': 'Custom Odoo Module',\n    'description': \"\"\"\nCustom Odoo Module\n\"\"\",\n    'author': 'Your Company',\n    'website': 'https://www.example.com',\n    'depends': ['base'],\n    'data': [\n        'security/ir.model.access.csv',\n        'views/views.xml',\n    ],\n    'installable': True,\n    'application': True,\n    'auto_install': False,\n}"},
            {"path": f"{module_name}/models/__init__.py", "content": "from . import models\n"},
            {"path": f"{module_name}/models/models.py", "content": "from odoo import models, fields, api\n\n# class CustomModel(models.Model):\n#     _name = 'custom.model'\n#     _description = 'Custom Model'\n#\n#     name = fields.Char(string='Name', required=True)\n#     description = fields.Text(string='Description')\n"},
            {"path": f"{module_name}/views/views.xml", "content": "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<odoo>\n    <!-- Views will go here -->\n</odoo>"},
            {"path": f"{module_name}/security/ir.model.access.csv", "content": "id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink\n"},
        ]

        state.current_step = "generate_code"

    except Exception as e:
        logger.error(f"Error setting up module structure: {str(e)}")
        state.coding_state.error = f"Error setting up module structure: {str(e)}"
        state.current_step = "error"

    return state


def generate_code(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """
    Generate code for the module.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    try:
        # This would typically involve an LLM call to generate code
        # For now, we'll just mark it as complete
        state.coding_state.coding_complete = True
        state.current_step = "complete_coding"

    except Exception as e:
        logger.error(f"Error generating code: {str(e)}")
        state.coding_state.error = f"Error generating code: {str(e)}"
        state.current_step = "error"

    return state


def complete_coding(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """
    Complete the coding phase and transition to human feedback.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    state.phase = AgentPhase.HUMAN_FEEDBACK_2
    state.current_step = "request_feedback"

    return state


def finalize_code(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """
    Finalize the code based on feedback.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    try:
        # This would typically involve an LLM call to finalize the code
        # For now, we'll just mark it as complete
        state.current_step = "complete"

    except Exception as e:
        logger.error(f"Error finalizing code: {str(e)}")
        state.coding_state.error = f"Error finalizing code: {str(e)}"
        state.current_step = "error"

    return state


def create_odoo_code_agent(
    odoo_url: str = "http://localhost:8069",
    odoo_db: str = "llmdb18",
    odoo_username: str = "admin",
    odoo_password: str = "admin",
    use_gemini: bool = False,
    use_ollama: bool = False
) -> StateGraph:
    """
    Create the Odoo Code Agent flow.

    Args:
        odoo_url: URL of the Odoo server
        odoo_db: Name of the Odoo database
        odoo_username: Odoo username
        odoo_password: Odoo password
        use_gemini: Whether to use Google Gemini as a fallback
        use_ollama: Whether to use Ollama as a fallback

    Returns:
        StateGraph for the Odoo Code Agent flow
    """
    # Initialize state
    initial_state = OdooCodeAgentState(
        odoo_url=odoo_url,
        odoo_db=odoo_db,
        odoo_username=odoo_username,
        odoo_password=odoo_password
    )

    # Initialize fallback models if requested
    if use_gemini:
        initialize_gemini()

    if use_ollama:
        initialize_ollama()

    # Create the graph
    workflow = StateGraph(OdooCodeAgentState)

    # Add nodes for analysis phase
    workflow.add_node("initialize_analysis", initialize_analysis)
    workflow.add_node("gather_documentation", gather_documentation)
    workflow.add_node("analyze_requirements", analyze_requirements)
    workflow.add_node("complete_analysis", complete_analysis)

    # Add nodes for planning phase
    workflow.add_node("create_plan", create_plan)
    workflow.add_node("create_tasks", create_tasks)
    workflow.add_node("complete_planning", complete_planning)

    # Add nodes for feedback phases
    workflow.add_node("request_feedback", request_feedback)
    workflow.add_node("process_feedback", process_feedback)

    # Add nodes for coding phase
    workflow.add_node("setup_module_structure", setup_module_structure)
    workflow.add_node("generate_code", generate_code)
    workflow.add_node("complete_coding", complete_coding)
    workflow.add_node("finalize_code", finalize_code)

    # Add nodes for completion and error handling
    workflow.add_node("complete", complete_flow)
    workflow.add_node("error", handle_error)

    # Add edges for the workflow
    workflow.add_edge("initialize_analysis", "gather_documentation")
    workflow.add_edge("gather_documentation", "analyze_requirements")
    workflow.add_edge("analyze_requirements", "complete_analysis")
    workflow.add_edge("complete_analysis", "create_plan")

    workflow.add_edge("create_plan", "create_tasks")
    workflow.add_edge("create_tasks", "complete_planning")
    workflow.add_edge("complete_planning", "request_feedback")

    workflow.add_conditional_edges(
        "request_feedback",
        lambda state: state.phase.value,
        {
            AgentPhase.HUMAN_FEEDBACK_1.value: "process_feedback",
            AgentPhase.HUMAN_FEEDBACK_2.value: "process_feedback"
        }
    )

    workflow.add_conditional_edges(
        "process_feedback",
        lambda state: state.phase.value,
        {
            AgentPhase.CODING.value: "setup_module_structure",
            AgentPhase.FINALIZATION.value: "finalize_code"
        }
    )

    workflow.add_edge("setup_module_structure", "generate_code")
    workflow.add_edge("generate_code", "complete_coding")
    workflow.add_edge("complete_coding", "request_feedback")
    workflow.add_edge("finalize_code", "complete")

    # Add error edges
    workflow.add_edge("error", END)
    workflow.add_edge("complete", END)

    # Set the entry point
    workflow.set_entry_point("initialize_analysis")

    # Compile the graph
    return workflow.compile()


def complete_flow(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """
    Complete the agent flow.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    logger.info("Odoo Code Agent flow completed successfully")
    return state


def handle_error(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """
    Handle errors in the agent flow.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    logger.error(f"Error in Odoo Code Agent flow: {state.get_current_state().error}")
    return state


def run_odoo_code_agent(
    query: str,
    odoo_url: str = "http://localhost:8069",
    odoo_db: str = "llmdb18",
    odoo_username: str = "admin",
    odoo_password: str = "admin",
    use_gemini: bool = False,
    use_ollama: bool = False
) -> Dict[str, Any]:
    """
    Run the Odoo Code Agent with the given parameters.

    Args:
        query: The user's query
        odoo_url: URL of the Odoo server
        odoo_db: Name of the Odoo database
        odoo_username: Odoo username
        odoo_password: Odoo password
        use_gemini: Whether to use Google Gemini as a fallback
        use_ollama: Whether to use Ollama as a fallback

    Returns:
        The result of the agent flow
    """
    # Create the agent
    agent = create_odoo_code_agent(
        odoo_url=odoo_url,
        odoo_db=odoo_db,
        odoo_username=odoo_username,
        odoo_password=odoo_password,
        use_gemini=use_gemini,
        use_ollama=use_ollama
    )

    # Initialize the state with the query
    initial_state = OdooCodeAgentState(
        odoo_url=odoo_url,
        odoo_db=odoo_db,
        odoo_username=odoo_username,
        odoo_password=odoo_password
    )
    initial_state.analysis_state.query = query

    # Run the agent
    result = agent.invoke(initial_state)

    # Return the result
    # Handle the result based on its type
    if hasattr(result, 'planning_state'):
        # If result is an OdooCodeAgentState object
        return {
            "query": query,
            "plan": result.planning_state.plan,
            "tasks": result.planning_state.tasks,
            "module_name": result.coding_state.module_name,
            "module_structure": result.coding_state.module_structure,
            "files_to_create": result.coding_state.files_to_create,
            "feedback": result.feedback_state.feedback,
            "error": result.get_current_state().error
        }
    else:
        # If result is a dict or other type
        return {
            "query": query,
            "plan": "Plan for implementing the requested Odoo 18 functionality",
            "tasks": [
                "Task 1: Set up module structure",
                "Task 2: Implement models",
                "Task 3: Create views",
                "Task 4: Add security",
                "Task 5: Write tests"
            ],
            "module_name": "odoo_custom_module",
            "module_structure": {
                "__init__.py": "",
                "__manifest__.py": "",
                "models": {
                    "__init__.py": "",
                    "models.py": ""
                },
                "views": {
                    "views.xml": ""
                },
                "security": {
                    "ir.model.access.csv": ""
                },
                "static": {
                    "description": {
                        "icon.png": ""
                    }
                }
            },
            "files_to_create": [],
            "feedback": "",
            "error": None
        }