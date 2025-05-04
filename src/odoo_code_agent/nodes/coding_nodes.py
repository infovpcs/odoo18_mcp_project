# src/agents/odoo_code_agent/nodes/coding_nodes.py
import logging
import os
from typing import Dict, List, Optional, Any

from langchain.schema import HumanMessage, AIMessage
from src.agents.odoo_code_agent.state import OdooCodeAgentState, AgentPhase

logger = logging.getLogger(__name__)


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