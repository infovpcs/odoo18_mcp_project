#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coding nodes for the Odoo Code Agent.

This module provides the coding phase nodes for the Odoo Code Agent workflow.
"""

import logging
import os
import json
from typing import Dict, List, Any, Optional

from ..state import OdooCodeAgentState, AgentPhase
from ..utils.gemini_client import GeminiClient

# Set up logging
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
        # Get the module name from the analysis
        analysis = state.analysis_state.context.get("analysis", {})

        # Use the module name from the analysis if available, otherwise extract from query
        if analysis and "module_name" in analysis:
            module_name = analysis["module_name"]
        else:
            # Fallback: Extract module name from the query
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
            else:
                module_name = "odoo_custom_module"

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
    """Generate code for the module.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    try:
        # Get the module name, analysis, and plan
        module_name = state.coding_state.module_name
        analysis = state.analysis_state.context.get("analysis", {})
        plan_result = state.planning_state.context.get("plan_result", {})

        # Use Gemini to generate code if available
        if state.use_gemini:
            logger.info("Using Gemini to generate code")
            gemini_client = GeminiClient()

            # Get the code from Gemini
            code_result = gemini_client.generate_module_code(analysis, plan_result)

            if "error" in code_result:
                logger.error(f"Gemini code generation error: {code_result['error']}")
                state.coding_state.error = code_result["error"]
                state.current_step = "error"
                return state

            # Update the module name if provided by Gemini
            if "module_name" in code_result:
                state.coding_state.module_name = code_result["module_name"]

            # Store the files to create
            if "files" in code_result:
                state.coding_state.files_to_create = code_result["files"]

            # Add to history
            state.history.append(f"Code generated with {len(state.coding_state.files_to_create)} files")

            # Mark as complete
            state.coding_state.coding_complete = True
            state.current_step = "complete_coding"

            logger.info(f"Code generated successfully with {len(state.coding_state.files_to_create)} files")
        else:
            # Fallback to the code generator utility
            logger.info("Gemini not available, using fallback code generator")

            try:
                # Import the code generator utility
                from ..utils.code_generator import generate_complete_module_from_description

                # Get the query
                query = state.analysis_state.query

                # Generate module files from description
                files = generate_complete_module_from_description(
                    description=query,
                    module_name=module_name,
                    base_path=".",
                    use_fallback=True
                )

                # Update the state with the generated files
                state.coding_state.files_to_create = [
                    {"path": path, "content": content} for path, content in files.items()
                ]

                # Add to history
                state.history.append(f"Code generated (fallback) with {len(state.coding_state.files_to_create)} files")

                # Mark as complete
                state.coding_state.coding_complete = True
                state.current_step = "complete_coding"

                logger.info(f"Code generated with fallback: {len(state.coding_state.files_to_create)} files")
            except ImportError:
                # If the code generator is not available, use a very basic fallback
                logger.warning("Code generator not available, using basic fallback")

                # Get module information from analysis
                analysis = state.analysis_state.context.get("analysis", {})
                module_title = analysis.get("module_title", "Custom Module")
                module_description = analysis.get("description", "Custom Odoo Module")
                models_info = analysis.get("models", [])

                # Create model code based on analysis
                models_code = "from odoo import models, fields, api\n\n"

                if models_info:
                    for model_info in models_info:
                        model_name = model_info.get("name", "custom.model")
                        model_description = model_info.get("description", "Custom Model")
                        fields_info = model_info.get("fields", [])

                        models_code += f"class {model_name.split('.')[-1].replace('.', '_').title()} (models.Model):\n"
                        models_code += f"    _name = '{model_name}'\n"
                        models_code += f"    _description = '{model_description}'\n"
                        models_code += f"    _inherit = ['mail.thread', 'mail.activity.mixin']\n\n"

                        for field_info in fields_info:
                            field_name = field_info.get("name", "name")
                            field_type = field_info.get("type", "char")
                            field_description = field_info.get("description", "")

                            if field_type == "char":
                                models_code += f"    {field_name} = fields.Char(string='{field_description}', required=True, tracking=True)\n"
                            elif field_type == "text":
                                models_code += f"    {field_name} = fields.Text(string='{field_description}', tracking=True)\n"
                            elif field_type == "integer":
                                models_code += f"    {field_name} = fields.Integer(string='{field_description}', tracking=True)\n"
                            elif field_type == "float":
                                models_code += f"    {field_name} = fields.Float(string='{field_description}', tracking=True)\n"
                            elif field_type == "boolean":
                                models_code += f"    {field_name} = fields.Boolean(string='{field_description}', tracking=True)\n"
                            elif field_type == "date":
                                models_code += f"    {field_name} = fields.Date(string='{field_description}', tracking=True)\n"
                            elif field_type == "datetime":
                                models_code += f"    {field_name} = fields.Datetime(string='{field_description}', tracking=True)\n"
                            elif field_type == "selection":
                                selection = field_info.get("selection", [])
                                selection_str = str(selection).replace("[", "[").replace("]", "]")
                                models_code += f"    {field_name} = fields.Selection({selection_str}, string='{field_description}', tracking=True)\n"
                            elif field_type == "many2one":
                                relation = field_info.get("relation", "res.partner")
                                models_code += f"    {field_name} = fields.Many2one('{relation}', string='{field_description}', tracking=True)\n"
                            elif field_type == "one2many":
                                relation = field_info.get("relation", "custom.model")
                                inverse_name = field_info.get("inverse_name", "parent_id")
                                models_code += f"    {field_name} = fields.One2many('{relation}', '{inverse_name}', string='{field_description}')\n"
                            elif field_type == "many2many":
                                relation = field_info.get("relation", "res.partner")
                                models_code += f"    {field_name} = fields.Many2many('{relation}', string='{field_description}')\n"
                            else:
                                models_code += f"    {field_name} = fields.Char(string='{field_description}', tracking=True)\n"

                        models_code += "\n"
                else:
                    # Default model if none provided
                    models_code += "class CustomModel(models.Model):\n"
                    models_code += "    _name = 'custom.model'\n"
                    models_code += "    _description = 'Custom Model'\n\n"
                    models_code += "    name = fields.Char(string='Name', required=True)\n"
                    models_code += "    description = fields.Text(string='Description')\n"

                # Create basic files
                state.coding_state.files_to_create = [
                    {"path": f"{module_name}/__init__.py", "content": "from . import models\n"},
                    {"path": f"{module_name}/__manifest__.py", "content": "{\n" +
                                                                f"    'name': '{module_title}',\n" +
                                                                f"    'version': '1.0',\n" +
                                                                f"    'category': 'Custom',\n" +
                                                                f"    'summary': '{module_title}',\n" +
                                                                f"    'description': \"\"\"\n{module_description}\n\"\"\",\n" +
                                                                f"    'author': 'Your Company',\n" +
                                                                f"    'website': 'https://www.example.com',\n" +
                                                                f"    'depends': ['base', 'mail'],\n" +
                                                                f"    'data': [\n" +
                                                                f"        'security/ir.model.access.csv',\n" +
                                                                f"        'views/views.xml',\n" +
                                                                f"    ],\n" +
                                                                f"    'installable': True,\n" +
                                                                f"    'application': True,\n" +
                                                                f"    'auto_install': False,\n" +
                                                                f"}}"},
                    {"path": f"{module_name}/models/__init__.py", "content": "from . import models\n"},
                    {"path": f"{module_name}/models/models.py", "content": models_code},
                    {"path": f"{module_name}/views/views.xml", "content": "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<odoo>\n    <!-- Views will go here -->\n</odoo>"},
                    {"path": f"{module_name}/security/ir.model.access.csv", "content": "id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink\n"},
                ]

                # Add to history
                state.history.append(f"Code generated (basic fallback) with {len(state.coding_state.files_to_create)} files")

                # Mark as complete
                state.coding_state.coding_complete = True
                state.current_step = "complete_coding"

                logger.info(f"Code generated with basic fallback: {len(state.coding_state.files_to_create)} files")

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
    """Finalize the code based on feedback.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    try:
        # Get the feedback
        feedback = state.feedback_state.feedback

        if not feedback:
            logger.info("No feedback provided, skipping finalization")
            state.current_step = "complete"
            return state

        # Get the current code
        analysis = state.analysis_state.context.get("analysis", {})
        plan_result = state.planning_state.context.get("plan_result", {})

        # Create a code object with the current files
        code = {
            "module_name": state.coding_state.module_name,
            "files": state.coding_state.files_to_create
        }

        # Use Gemini to process feedback if available
        if state.use_gemini:
            logger.info("Using Gemini to process feedback")
            gemini_client = GeminiClient()

            # Process the feedback
            updated_code = gemini_client.process_feedback(analysis, plan_result, code, feedback)

            if "error" in updated_code:
                logger.error(f"Gemini feedback processing error: {updated_code['error']}")
                state.coding_state.error = updated_code["error"]
                state.current_step = "error"
                return state

            # Update the module name if provided
            if "module_name" in updated_code:
                state.coding_state.module_name = updated_code["module_name"]

            # Update the files
            if "files" in updated_code:
                state.coding_state.files_to_create = updated_code["files"]

            # Add changes to history
            if "changes" in updated_code and updated_code["changes"]:
                changes = updated_code["changes"]
                state.history.append(f"Applied {len(changes)} changes based on feedback")
                for change in changes:
                    state.history.append(f"- {change}")
            else:
                state.history.append("Processed feedback (no changes needed)")

            logger.info(f"Feedback processed successfully")
        else:
            # Just add the feedback to history
            logger.info("Gemini not available, skipping feedback processing")
            state.history.append("Feedback received (not processed)")

        # Mark as complete
        state.current_step = "complete"

    except Exception as e:
        logger.error(f"Error finalizing code: {str(e)}")
        state.coding_state.error = f"Error finalizing code: {str(e)}"
        state.current_step = "error"

    return state