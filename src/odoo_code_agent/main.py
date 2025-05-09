#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Main module for the Odoo Code Agent.

This module provides the main entry point for running the Odoo Code Agent.
"""

import os
import logging
import time
from typing import Dict, Any, Optional, List, Callable

from .state import OdooCodeAgentState, AgentPhase
from .utils import documentation_helper, odoo_connector
from .utils.file_saver import save_module_files
from .nodes import analysis_nodes, planning_nodes, coding_nodes, feedback_nodes, review_nodes

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Define the node mapping
NODE_MAPPING = {
    # Analysis phase
    "initialize": analysis_nodes.initialize_analysis,
    "gather_documentation": analysis_nodes.gather_documentation,
    "gather_model_information": analysis_nodes.gather_model_information,
    "analyze_requirements": analysis_nodes.analyze_requirements,
    "complete_analysis": analysis_nodes.complete_analysis,

    # Planning phase
    "create_plan": planning_nodes.create_plan,
    "create_tasks": planning_nodes.create_tasks,
    "complete_planning": planning_nodes.complete_planning,

    # Feedback phases
    "request_feedback": feedback_nodes.request_feedback,
    "process_feedback": feedback_nodes.process_feedback,

    # Coding phase
    "setup_module_structure": coding_nodes.setup_module_structure,
    "generate_code": coding_nodes.generate_code,
    "complete_coding": coding_nodes.complete_coding,

    # Code Review phase
    "start_code_review": review_nodes.start_code_review,
    "review_code_completeness": review_nodes.review_code_completeness,
    "regenerate_incomplete_files": review_nodes.regenerate_incomplete_files,

    # Finalization phase
    "finalize_code": coding_nodes.finalize_code,
}


def run_odoo_code_agent(
    query: str,
    odoo_url: str = "http://localhost:8069",
    odoo_db: str = "llmdb18",
    odoo_username: str = "admin",
    odoo_password: str = "admin",
    use_gemini: bool = False,
    use_ollama: bool = False,
    feedback: Optional[str] = None,
    max_steps: int = 20,
    save_to_files: bool = False,
    output_dir: Optional[str] = None,
    wait_for_validation: bool = False,
    current_phase: Optional[str] = None,
    state_dict: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Run the Odoo Code Agent with the given query.

    Args:
        query: The user query
        odoo_url: Odoo server URL
        odoo_db: Odoo database name
        odoo_username: Odoo username
        odoo_password: Odoo password
        use_gemini: Whether to use Google Gemini as a fallback
        use_ollama: Whether to use Ollama as a fallback
        feedback: Optional feedback for the agent
        max_steps: Maximum number of steps to run
        save_to_files: Whether to save the generated files to disk
        output_dir: Directory to save the generated files to (defaults to ./generated_modules)
        wait_for_validation: Whether to wait for human validation at validation points
        current_phase: The current phase to resume from (if continuing execution)
        state_dict: Serialized state to resume from (if continuing execution)

    Returns:
        Dict containing the agent's response
    """
    logger.info(f"Running Odoo Code Agent with query: {query}")

    # Initialize or restore the agent state
    if state_dict:
        # Restore from serialized state
        logger.info(f"Restoring agent state from serialized state")
        state = OdooCodeAgentState.model_validate(state_dict)

        # Update with any new parameters
        state.use_gemini = use_gemini
        state.use_ollama = use_ollama

        # If feedback is provided, update it
        if feedback:
            state.feedback_state.feedback = feedback

        logger.info(f"Restored agent state with phase: {state.phase}, step: {state.current_step}")
    else:
        # Initialize a new agent state
        state = OdooCodeAgentState()

        # Set the Odoo connection details
        state.odoo_url = odoo_url
        state.odoo_db = odoo_db
        state.odoo_username = odoo_username
        state.odoo_password = odoo_password

        # Set the model preferences
        state.use_gemini = use_gemini
        state.use_ollama = use_ollama

        # Initialize the analysis state with the query
        state.analysis_state.query = query

        # Set the initial step
        state.current_step = "initialize"

        # If a specific phase is requested, set it
        if current_phase:
            try:
                state.phase = AgentPhase(current_phase)
                logger.info(f"Setting initial phase to: {state.phase}")

                # Set appropriate initial step based on the phase
                if state.phase == AgentPhase.PLANNING:
                    state.current_step = "create_plan"
                elif state.phase == AgentPhase.HUMAN_FEEDBACK_1:
                    state.current_step = "request_feedback"
                elif state.phase == AgentPhase.CODING:
                    state.current_step = "setup_module_structure"
                elif state.phase == AgentPhase.CODE_REVIEW:
                    state.current_step = "start_code_review"
                elif state.phase == AgentPhase.HUMAN_FEEDBACK_2:
                    state.current_step = "request_feedback"
                elif state.phase == AgentPhase.FINALIZATION:
                    state.current_step = "finalize_code"
            except ValueError:
                logger.warning(f"Invalid phase: {current_phase}, using default")

    logger.info(f"Agent state initialized with phase: {state.phase}, step: {state.current_step}")

    # Run the agent workflow
    step_count = 0
    while state.current_step != "complete" and state.current_step != "error" and step_count < max_steps:
        step_count += 1
        logger.info(f"Step {step_count}: {state.current_step} (Phase: {state.phase})")

        # Get the current node function
        node_func = NODE_MAPPING.get(state.current_step)

        if not node_func:
            logger.error(f"Unknown step: {state.current_step}")
            state.current_step = "error"
            break

        # Execute the node function
        logger.info(f"Executing node function: {node_func.__name__}")
        try:
            if state.current_step == "process_feedback" and feedback:
                # Pass the feedback to the process_feedback node
                state = node_func(state, feedback)
                # Clear the feedback after processing
                feedback = None
            else:
                state = node_func(state)
            logger.info(f"Node function {node_func.__name__} completed successfully")
            logger.info(f"Next step: {state.current_step}, Phase: {state.phase}")
        except Exception as e:
            logger.error(f"Error executing node function {node_func.__name__}: {str(e)}")
            # Continue to the next step even if there's an error
            state.current_step = "error"

        # Add a small delay to avoid overwhelming the system
        time.sleep(0.1)

        # Check if we need to wait for human validation
        if wait_for_validation:
            # If we just completed planning and are at the first human feedback point
            if state.phase == AgentPhase.HUMAN_FEEDBACK_1 and state.current_step == "request_feedback":
                logger.info("Stopping at first human validation point (after planning)")
                break

            # If we just completed coding and are at the code review point
            if state.phase == AgentPhase.CODE_REVIEW and state.current_step == "start_code_review":
                logger.info("Stopping at code review point (after coding)")
                break

            # If we just completed code review and are at the second human feedback point
            if state.phase == AgentPhase.HUMAN_FEEDBACK_2 and state.current_step == "request_feedback":
                logger.info("Stopping at second human validation point (after code review)")
                break

    # Check if we reached the maximum number of steps
    if step_count >= max_steps:
        logger.warning(f"Reached maximum number of steps ({max_steps})")
        state.current_step = "error"

    # Prepare the response
    response = {
        "query": query,
        "plan": state.planning_state.plan,
        "tasks": state.planning_state.tasks,
        "module_name": state.coding_state.module_name,
        "module_structure": state.coding_state.module_structure,
        "files_to_create": state.coding_state.files_to_create,
        "feedback": state.feedback_state.feedback,
        "history": state.history,
        "error": state.analysis_state.error or state.planning_state.error or state.coding_state.error or state.feedback_state.error,
        "current_phase": state.phase.value,
        "current_step": state.current_step,
        "requires_validation": state.phase in [AgentPhase.HUMAN_FEEDBACK_1, AgentPhase.HUMAN_FEEDBACK_2] and state.current_step == "request_feedback",
        "is_complete": state.current_step == "complete",
        "state_dict": state.model_dump()  # Serialize the state for resuming later
    }

    # Save files to disk if requested
    if save_to_files and state.coding_state.module_name and state.coding_state.files_to_create:
        try:
            logger.info(f"Saving generated files to disk (module: {state.coding_state.module_name})")
            save_result = save_module_files(
                module_name=state.coding_state.module_name,
                files_to_create=state.coding_state.files_to_create,
                output_dir=output_dir
            )

            # Add save result to the response
            response["save_result"] = save_result

            if save_result["success"]:
                logger.info(f"Successfully saved {save_result['saved_count']} files to {save_result['module_dir']}")
            else:
                logger.error(f"Error saving files: {save_result.get('error', 'Unknown error')}")

        except Exception as e:
            logger.error(f"Error saving files to disk: {str(e)}")
            response["save_result"] = {
                "success": False,
                "error": str(e),
                "saved_files": []
            }

    return response