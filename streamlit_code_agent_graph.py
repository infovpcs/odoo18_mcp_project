#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Streamlit app to display the Odoo code agent graph flow diagram.
"""

import streamlit as st
import os
import sys
import tempfile
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import LangGraph
try:
    from langgraph.graph import StateGraph, END
except ImportError:
    st.error("LangGraph is not installed. Please install it with `pip install langgraph`")
    st.stop()

# Import the Odoo code agent state
from src.odoo_code_agent.state import OdooCodeAgentState, AgentPhase

# Set page config
st.set_page_config(
    page_title="Odoo Code Agent Graph Flow",
    page_icon="🧩",
    layout="wide"
)

# Title
st.title("Odoo Code Agent Graph Flow Diagram")

# Create a function to build the graph
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

# Conditional edge function for after feedback
def conditional_edge_after_feedback(state):
    """Determine the next step after processing feedback."""
    if state.phase == AgentPhase.HUMAN_FEEDBACK_1:
        return "setup_module_structure"  # Move to coding phase
    elif state.phase == AgentPhase.HUMAN_FEEDBACK_2:
        return "finalize_code"  # Move to finalization phase
    else:
        return "error"  # Unexpected state

# Create the graph
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
    st.error(f"Error generating graph: {str(e)}")
    
    # Display text-based representation as fallback
    st.subheader("Text-based Workflow Representation")
    
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

# Display additional information
with st.expander("Odoo Code Agent State Structure"):
    st.code("""
class OdooCodeAgentState(BaseModel):
    phase: AgentPhase = AgentPhase.ANALYSIS
    analysis_state: AnalysisState
    planning_state: PlanningState
    coding_state: CodingState
    feedback_state: FeedbackState
    current_step: str = "initialize"
    history: List[str]
    odoo_url: str = "http://localhost:8069"
    odoo_db: str = "llmdb18"
    odoo_username: str = "admin"
    odoo_password: str = "admin"
    use_gemini: bool = False
    use_ollama: bool = False
    """, language="python")

with st.expander("Agent Phases"):
    st.code("""
class AgentPhase(str, Enum):
    ANALYSIS = "analysis"
    PLANNING = "planning"
    HUMAN_FEEDBACK_1 = "human_feedback_1"
    CODING = "coding"
    HUMAN_FEEDBACK_2 = "human_feedback_2"
    FINALIZATION = "finalization"
    """, language="python")
