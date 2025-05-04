#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feedback nodes for the Odoo Code Agent.

This module provides the feedback phase nodes for the Odoo Code Agent workflow.
"""

import logging
from typing import Dict, List, Optional, Any

from ..state import OdooCodeAgentState, AgentPhase

# Set up logging
logger = logging.getLogger(__name__)


def request_feedback(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """Request feedback from the human.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    # Prepare the feedback request based on the current phase
    if state.phase == AgentPhase.HUMAN_FEEDBACK_1:
        # After planning phase
        analysis = state.analysis_state.context.get("analysis", {})
        module_name = analysis.get("module_name", "custom_module")

        # Add to history
        state.history.append("Requesting feedback on analysis and plan")

        logger.info(f"Requesting feedback after planning for module: {module_name}")
    else:  # HUMAN_FEEDBACK_2
        # After coding phase
        module_name = state.coding_state.module_name
        files_count = len(state.coding_state.files_to_create)

        # Add to history
        state.history.append(f"Requesting feedback on generated code ({files_count} files)")

        logger.info(f"Requesting feedback after coding for module: {module_name} with {files_count} files")

    # Set the next step
    state.current_step = "process_feedback"

    return state


def process_feedback(state: OdooCodeAgentState, feedback: Optional[str] = None) -> OdooCodeAgentState:
    """Process feedback from the human.

    Args:
        state: The current agent state
        feedback: Optional feedback from the human

    Returns:
        Updated agent state
    """
    try:
        # Store the feedback if provided
        if feedback:
            state.feedback_state.feedback = feedback

            # Add to history
            state.history.append(f"Received feedback: {feedback[:100]}..." if len(feedback) > 100 else f"Received feedback: {feedback}")
        else:
            # Add to history
            state.history.append("No feedback provided, proceeding with default plan")

        # Mark feedback as processed
        state.feedback_state.feedback_processed = True

        # Extract any specific changes required from the feedback
        if feedback:
            # Simple parsing of feedback for changes
            # In a real implementation, this would use an LLM to extract structured changes
            lines = feedback.split('\n')
            changes = []

            for line in lines:
                line = line.strip()
                if line.startswith('- ') or line.startswith('* '):
                    changes.append(line[2:])
                elif line.startswith('Change:') or line.startswith('Fix:'):
                    changes.append(line)

            if changes:
                state.feedback_state.changes_required = changes

                # Add to history
                state.history.append(f"Extracted {len(changes)} change requests from feedback")

        # Determine the next phase based on the current phase
        if state.phase == AgentPhase.HUMAN_FEEDBACK_1:
            # After planning, move to coding
            state.phase = AgentPhase.CODING
            state.current_step = "setup_module_structure"

            logger.info("Processed feedback after planning, moving to coding phase")
        else:  # HUMAN_FEEDBACK_2
            # After coding, move to finalization
            state.phase = AgentPhase.FINALIZATION
            state.current_step = "finalize_code"

            logger.info("Processed feedback after coding, moving to finalization phase")

    except Exception as e:
        logger.error(f"Error processing feedback: {str(e)}")
        state.feedback_state.error = f"Error processing feedback: {str(e)}"
        state.current_step = "error"

    return state