#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Planning nodes for the Odoo Code Agent.

This module provides the planning phase nodes for the Odoo Code Agent workflow.
"""

import logging
import json
from typing import Dict, List, Optional, Any

from ..state import OdooCodeAgentState, AgentPhase
from ..utils.gemini_client import GeminiClient

# Set up logging
logger = logging.getLogger(__name__)


def create_plan(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """Create a plan based on the analysis.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    try:
        # Get the analysis from the previous phase
        analysis = state.analysis_state.context.get("analysis", {})

        if not analysis:
            logger.error("No analysis available for planning")
            state.planning_state.error = "No analysis available for planning"
            state.current_step = "error"
            return state

        # Use Gemini to create a plan if available
        if state.use_gemini:
            logger.info("Using Gemini to create plan")
            gemini_client = GeminiClient()

            # Get the plan from Gemini
            plan_result = gemini_client.create_plan(analysis)

            if "error" in plan_result:
                logger.error(f"Gemini planning error: {plan_result['error']}")
                state.planning_state.error = plan_result["error"]
                state.current_step = "error"
                return state

            # Store the plan in the state
            state.planning_state.plan = plan_result.get("plan", "")

            # Store tasks if available
            if "tasks" in plan_result:
                state.planning_state.tasks = plan_result["tasks"]

            # Store the full plan result in the context
            state.planning_state.context = {"plan_result": plan_result}

            # Add to history
            state.history.append(f"Plan created with {len(state.planning_state.tasks)} tasks")

            # If tasks are already available, skip the create_tasks step
            if state.planning_state.tasks:
                state.current_step = "complete_planning"
            else:
                state.current_step = "create_tasks"

            logger.info(f"Plan created successfully: {state.planning_state.plan[:200]}...")
        else:
            # Fallback to a simpler plan
            logger.info("Gemini not available, using fallback planning")

            # Create a basic plan based on the analysis
            module_name = analysis.get("module_name", "custom_module")

            # Create a basic plan
            state.planning_state.plan = f"""
            Plan for implementing the {module_name} module:

            1. Set up the basic module structure
            2. Implement the models defined in the analysis
            3. Create views for the models
            4. Set up security and access rights
            5. Add demo data for testing
            """

            # Add to history
            state.history.append("Plan created (fallback)")

            state.current_step = "create_tasks"

            logger.info(f"Plan created with fallback: {state.planning_state.plan}")

    except Exception as e:
        logger.error(f"Error creating plan: {str(e)}")
        state.planning_state.error = f"Error creating plan: {str(e)}"
        state.current_step = "error"

    return state


def create_tasks(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """Create tasks based on the plan.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    try:
        # If tasks are already available from the plan, skip this step
        if state.planning_state.tasks:
            state.current_step = "complete_planning"
            return state

        # Get the analysis and plan
        analysis = state.analysis_state.context.get("analysis", {})
        plan = state.planning_state.plan

        # Create tasks based on the plan
        module_name = analysis.get("module_name", "custom_module")
        models = analysis.get("models", [])

        # Create basic tasks
        state.planning_state.tasks = [
            f"Task 1: Set up {module_name} module structure",
            f"Task 2: Implement {len(models)} models",
            "Task 3: Create views for the models",
            "Task 4: Set up security and access rights",
            "Task 5: Add demo data for testing"
        ]

        # Add to history
        state.history.append(f"Created {len(state.planning_state.tasks)} tasks")

        state.current_step = "complete_planning"

        logger.info(f"Tasks created: {json.dumps(state.planning_state.tasks, indent=2)}")

    except Exception as e:
        logger.error(f"Error creating tasks: {str(e)}")
        state.planning_state.error = f"Error creating tasks: {str(e)}"
        state.current_step = "error"

    return state


def complete_planning(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """Complete the planning phase and transition to human feedback.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    # Mark planning as complete
    state.planning_state.planning_complete = True

    # Add to history
    state.history.append("Planning phase completed")

    # Transition to human feedback phase
    state.phase = AgentPhase.HUMAN_FEEDBACK_1
    state.current_step = "request_feedback"

    logger.info("Planning phase completed, transitioning to human feedback")
    return state