#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analysis nodes for the Odoo Code Agent.

This module provides the analysis phase nodes for the Odoo Code Agent workflow.
"""

import logging
import json
from typing import Dict, List, Optional, Any

from ..state import OdooCodeAgentState, AgentPhase
from ..utils.gemini_client import GeminiClient
from src.odoo_docs_rag.docs_retriever import OdooDocsRetriever

# Set up logging
logger = logging.getLogger(__name__)


def initialize_analysis(state: OdooCodeAgentState, query: Optional[str] = None) -> OdooCodeAgentState:
    """Initialize the analysis phase.

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

    # Add the query to the history
    state.history.append(f"User query: {state.analysis_state.query}")

    logger.info(f"Analysis initialized with query: {state.analysis_state.query}")
    return state


def gather_documentation(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """Gather documentation related to the query.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    try:
        # Initialize the Odoo documentation retriever
        docs_dir = "/Users/vinusoft85/workspace/odoo18_mcp_project/odoo_docs"

        retriever = OdooDocsRetriever(
            docs_dir=docs_dir,
            force_rebuild=False
        )

        # Query the documentation
        query = state.analysis_state.query
        results = retriever.retrieve(query, max_results=5)

        # Store the results in the state
        state.analysis_state.documentation_results = results

        # Format the documentation for context
        formatted_docs = []
        for result in results:
            formatted_docs.append({
                "source": result.get("metadata", {}).get("file_name", "Unknown"),
                "content": result.get("text", "")[:500] + "..." if len(result.get("text", "")) > 500 else result.get("text", ""),
                "score": result.get("score", 0)
            })

        # Add documentation to context
        state.analysis_state.context["documentation"] = formatted_docs

        # Add to history
        state.history.append(f"Retrieved {len(results)} documentation results")

        state.current_step = "analyze_requirements"
        logger.info(f"Documentation gathered: {len(results)} results")

    except Exception as e:
        logger.error(f"Error gathering documentation: {str(e)}")
        state.analysis_state.error = f"Error gathering documentation: {str(e)}"
        state.current_step = "error"

    return state


def analyze_requirements(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """Analyze the requirements based on the query and documentation.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    try:
        # Use Gemini to analyze the requirements if available
        if state.use_gemini:
            logger.info("Using Gemini to analyze requirements")
            gemini_client = GeminiClient()

            # Prepare context for the analysis
            query = state.analysis_state.query

            # Get the analysis from Gemini
            analysis_result = gemini_client.analyze_requirements(query)

            if "error" in analysis_result:
                logger.error(f"Gemini analysis error: {analysis_result['error']}")
                state.analysis_state.error = analysis_result["error"]
                state.current_step = "error"
                return state

            # Store the analysis in the state
            state.analysis_state.context["analysis"] = analysis_result

            # Add to history
            state.history.append(f"Requirements analyzed: {analysis_result.get('module_name', 'Unknown module')}")

            # Mark analysis as complete
            state.analysis_state.analysis_complete = True
            state.current_step = "complete_analysis"

            logger.info(f"Requirements analyzed successfully: {json.dumps(analysis_result, indent=2)[:200]}...")
        else:
            # Fallback to a simpler analysis
            logger.info("Gemini not available, using fallback analysis")

            # Extract module name from query
            query = state.analysis_state.query.lower()

            # Try to find a meaningful module name based on the query
            if "customer feedback" in query:
                module_name = "customer_feedback"
            elif "project" in query:
                module_name = "project_management"
            elif "inventory" in query:
                module_name = "inventory_management"
            elif "sales" in query:
                module_name = "sales_management"
            elif "purchase" in query:
                module_name = "purchase_management"
            elif "hr" in query or "employee" in query:
                module_name = "hr_management"
            else:
                # Default fallback
                words = query.split()
                key_words = [w for w in words if len(w) > 3 and w not in ["odoo", "module", "create", "with", "that", "this", "for", "and", "the"]]
                module_name = "_".join(key_words[:2]) if key_words else "custom_module"

            module_name = module_name.replace(" ", "_").replace("-", "_").lower()

            # Create a basic analysis with fields based on the module type
            models = []

            # Customer feedback module
            if "customer feedback" in query or "feedback" in query:
                models = [
                    {
                        "name": f"{module_name}.feedback",
                        "description": "Customer Feedback",
                        "fields": [
                            {
                                "name": "name",
                                "type": "char",
                                "description": "Feedback Title"
                            },
                            {
                                "name": "partner_id",
                                "type": "many2one",
                                "description": "Customer",
                                "relation": "res.partner"
                            },
                            {
                                "name": "rating",
                                "type": "selection",
                                "description": "Rating",
                                "selection": [
                                    ("1", "Poor"),
                                    ("2", "Fair"),
                                    ("3", "Average"),
                                    ("4", "Good"),
                                    ("5", "Excellent")
                                ]
                            },
                            {
                                "name": "feedback_date",
                                "type": "date",
                                "description": "Feedback Date"
                            },
                            {
                                "name": "comment",
                                "type": "text",
                                "description": "Comment"
                            },
                            {
                                "name": "state",
                                "type": "selection",
                                "description": "Status",
                                "selection": [
                                    ("draft", "Draft"),
                                    ("submitted", "Submitted"),
                                    ("reviewed", "Reviewed"),
                                    ("closed", "Closed")
                                ]
                            }
                        ]
                    }
                ]
            # Project management module
            elif "project" in query:
                models = [
                    {
                        "name": f"{module_name}.project",
                        "description": "Project",
                        "fields": [
                            {
                                "name": "name",
                                "type": "char",
                                "description": "Project Name"
                            },
                            {
                                "name": "description",
                                "type": "text",
                                "description": "Description"
                            },
                            {
                                "name": "start_date",
                                "type": "date",
                                "description": "Start Date"
                            },
                            {
                                "name": "end_date",
                                "type": "date",
                                "description": "End Date"
                            },
                            {
                                "name": "state",
                                "type": "selection",
                                "description": "Status",
                                "selection": [
                                    ("draft", "Draft"),
                                    ("in_progress", "In Progress"),
                                    ("completed", "Completed"),
                                    ("cancelled", "Cancelled")
                                ]
                            }
                        ]
                    }
                ]
            # Default model for other types
            else:
                models = [
                    {
                        "name": f"{module_name}.main",
                        "description": "Main model for the module",
                        "fields": [
                            {
                                "name": "name",
                                "type": "char",
                                "description": "Name"
                            },
                            {
                                "name": "description",
                                "type": "text",
                                "description": "Description"
                            }
                        ]
                    }
                ]

            # Create the analysis result
            analysis_result = {
                "module_name": module_name,
                "module_title": state.analysis_state.query,
                "description": f"Module for {state.analysis_state.query}",
                "models": models,
                "views": ["list", "form", "kanban"],
                "security": ["base.group_user"],
                "dependencies": ["base", "mail"]
            }

            # Store the analysis in the state
            state.analysis_state.context["analysis"] = analysis_result

            # Add to history
            state.history.append(f"Requirements analyzed (fallback): {module_name}")

            # Mark analysis as complete
            state.analysis_state.analysis_complete = True
            state.current_step = "complete_analysis"

            logger.info(f"Requirements analyzed with fallback: {json.dumps(analysis_result, indent=2)}")

    except Exception as e:
        logger.error(f"Error analyzing requirements: {str(e)}")
        state.analysis_state.error = f"Error analyzing requirements: {str(e)}"
        state.current_step = "error"

    return state


def complete_analysis(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """Complete the analysis phase and transition to planning.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    # Transfer relevant information to the planning state
    analysis = state.analysis_state.context.get("analysis", {})

    # Add to history
    state.history.append("Analysis phase completed")

    # Transition to planning phase
    state.phase = AgentPhase.PLANNING
    state.current_step = "create_plan"

    logger.info("Analysis phase completed, transitioning to planning")
    return state