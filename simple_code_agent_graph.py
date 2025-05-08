#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple script to display the Odoo code agent graph flow diagram using NetworkX and Matplotlib.
This is a fallback for when LangGraph's visualization methods are not available.
"""

import os
import sys
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path

# Add the project root to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

# Import the Odoo code agent state
try:
    from src.odoo_code_agent.state import AgentPhase
except ImportError:
    # Create a mock class for demonstration purposes
    class AgentPhase(str, Enum):
        ANALYSIS = "analysis"
        PLANNING = "planning"
        HUMAN_FEEDBACK_1 = "human_feedback_1"
        CODING = "coding"
        HUMAN_FEEDBACK_2 = "human_feedback_2"
        FINALIZATION = "finalization"

def create_code_agent_graph():
    """Create a NetworkX representation of the Odoo code agent workflow."""
    
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add nodes for each phase
    
    # Analysis phase nodes
    analysis_nodes = ["initialize", "gather_documentation", "gather_model_information", 
                     "analyze_requirements", "complete_analysis"]
    G.add_nodes_from(analysis_nodes, color='lightblue', phase='Analysis')
    
    # Planning phase nodes
    planning_nodes = ["create_plan", "create_tasks", "complete_planning"]
    G.add_nodes_from(planning_nodes, color='lightgreen', phase='Planning')
    
    # Human feedback nodes
    feedback_nodes = ["request_feedback", "process_feedback"]
    G.add_nodes_from(feedback_nodes, color='lightyellow', phase='Feedback')
    
    # Coding phase nodes
    coding_nodes = ["setup_module_structure", "generate_code", "complete_coding"]
    G.add_nodes_from(coding_nodes, color='lightpink', phase='Coding')
    
    # Finalization phase nodes
    finalization_nodes = ["finalize_code", "complete"]
    G.add_nodes_from(finalization_nodes, color='lightgrey', phase='Finalization')
    
    # Add error node
    G.add_node("error", color='red', phase='Error')
    
    # Add edges for Analysis phase
    G.add_edge("initialize", "gather_documentation")
    G.add_edge("gather_documentation", "gather_model_information")
    G.add_edge("gather_model_information", "analyze_requirements")
    G.add_edge("analyze_requirements", "complete_analysis")
    G.add_edge("complete_analysis", "create_plan")
    
    # Add edges for Planning phase
    G.add_edge("create_plan", "create_tasks")
    G.add_edge("create_tasks", "complete_planning")
    G.add_edge("complete_planning", "request_feedback")  # First human feedback
    
    # Add edges for first Human Feedback phase
    G.add_edge("request_feedback", "process_feedback")
    
    # Add conditional edges for after feedback
    G.add_edge("process_feedback", "setup_module_structure", style='dashed', label='if HUMAN_FEEDBACK_1')
    G.add_edge("process_feedback", "finalize_code", style='dashed', label='if HUMAN_FEEDBACK_2')
    G.add_edge("process_feedback", "error", style='dashed', label='if error')
    
    # Add edges for Coding phase
    G.add_edge("setup_module_structure", "generate_code")
    G.add_edge("generate_code", "complete_coding")
    G.add_edge("complete_coding", "request_feedback")  # Second human feedback
    
    # Add edges for Finalization phase
    G.add_edge("finalize_code", "complete")
    
    # Add error edges from all nodes to error
    for node in analysis_nodes + planning_nodes + feedback_nodes + coding_nodes + finalization_nodes:
        if node != "error" and node != "complete":
            G.add_edge(node, "error", style='dotted', label='if error')
    
    return G

def draw_graph(G, output_file=None):
    """Draw the graph using Matplotlib."""
    plt.figure(figsize=(12, 8))
    
    # Create a layout for the graph
    pos = nx.spring_layout(G, seed=42)
    
    # Get node colors
    node_colors = [G.nodes[n].get('color', 'lightgrey') for n in G.nodes()]
    
    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=2000, alpha=0.8)
    
    # Draw edges
    solid_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('style', 'solid') == 'solid']
    dashed_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('style', 'solid') == 'dashed']
    dotted_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('style', 'solid') == 'dotted']
    
    nx.draw_networkx_edges(G, pos, edgelist=solid_edges, width=1.5)
    nx.draw_networkx_edges(G, pos, edgelist=dashed_edges, width=1.5, style='dashed')
    nx.draw_networkx_edges(G, pos, edgelist=dotted_edges, width=1.0, style='dotted', alpha=0.5)
    
    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=10, font_family='sans-serif')
    
    # Draw edge labels
    edge_labels = {(u, v): d.get('label', '') for u, v, d in G.edges(data=True) if 'label' in d}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)
    
    # Add a title
    plt.title("Odoo Code Agent Workflow", fontsize=16)
    
    # Remove the axis
    plt.axis('off')
    
    # Adjust the layout
    plt.tight_layout()
    
    # Save the figure if an output file is specified
    if output_file:
        plt.savefig(output_file, format='png', dpi=300, bbox_inches='tight')
        print(f"Graph saved to {output_file}")
    
    # Show the figure
    plt.show()

# Main execution
if __name__ == "__main__":
    # Create the graph
    G = create_code_agent_graph()
    
    try:
        # Draw the graph
        print("Generating Odoo Code Agent graph visualization...")
        draw_graph(G, output_file="odoo_code_agent_graph.png")
        print("Graph visualization complete.")
    except Exception as e:
        print(f"Error generating graph visualization: {str(e)}")
        print("This could be due to missing dependencies or incompatible versions.")
        print("Please make sure you have installed the required dependencies:")
        print("  pip install networkx matplotlib")
        
        # Print text-based representation as fallback
        print("\nText-based Workflow Representation:")
        print("\nAnalysis Phase:")
        print("1. initialize → gather_documentation")
        print("2. gather_documentation → gather_model_information")
        print("3. gather_model_information → analyze_requirements")
        print("4. analyze_requirements → complete_analysis")
        print("5. complete_analysis → create_plan")
        
        print("\nPlanning Phase:")
        print("6. create_plan → create_tasks")
        print("7. create_tasks → complete_planning")
        print("8. complete_planning → request_feedback")
        
        print("\nHuman Feedback 1:")
        print("9. request_feedback → process_feedback")
        print("10. process_feedback → setup_module_structure/finalize_code/error (conditional)")
        
        print("\nCoding Phase:")
        print("11. setup_module_structure → generate_code")
        print("12. generate_code → complete_coding")
        print("13. complete_coding → request_feedback")
        
        print("\nHuman Feedback 2:")
        print("14. request_feedback → process_feedback")
        print("15. process_feedback → finalize_code/error (conditional)")
        
        print("\nFinalization Phase:")
        print("16. finalize_code → complete")
        
        print("\nError Handling:")
        print("Any node can transition to error if an error occurs")
