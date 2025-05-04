# src/agents/odoo_code_agent/nodes/analysis_nodes.py
import logging
from typing import Dict, List, Optional, Any

from langchain.schema import HumanMessage, AIMessage
from src.agents.odoo_code_agent.state import OdooCodeAgentState, AgentPhase
from src.odoo_docs_rag.docs_retriever import OdooDocsRetriever

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
        # Initialize the Odoo documentation retriever
        docs_dir = "odoo_docs"
        index_dir = "odoo_docs_index"
        
        retriever = OdooDocsRetriever(
            docs_dir=docs_dir,
            index_dir=index_dir,
            force_rebuild=False
        )
        
        # Query the documentation
        query = state.analysis_state.query
        results = retriever.retrieve(query, max_results=5)
        
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