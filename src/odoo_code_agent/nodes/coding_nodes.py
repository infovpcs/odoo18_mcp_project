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
            elif "project" in query and "management" in query:
                module_name = "project_management"
            elif "inventory" in query:
                module_name = "inventory_management"
            elif "sales" in query:
                module_name = "sales_management"
            elif "purchase" in query:
                module_name = "purchase_management"
            elif "point of sale" in query or "pos" in query:
                if "multi-currency" in query or "currency" in query:
                    module_name = "pos_multi_currency"
                else:
                    module_name = "pos_custom"
            elif "website" in query:
                module_name = "website_custom"
            elif "ecommerce" in query or "e-commerce" in query:
                module_name = "website_sale_custom"
            elif "crm" in query:
                module_name = "crm_custom"
            else:
                # Default fallback: extract key words from the query
                words = query.split()
                key_words = [w for w in words if len(w) > 3 and w not in ["odoo", "module", "create", "with", "that", "this", "for", "and", "the"]]
                module_name = "_".join(key_words[:2]) if key_words else "custom_module"

        # Add _vpcs_ext suffix to prevent conflicts with existing Odoo apps
        if not module_name.endswith("_vpcs_ext"):
            module_name = f"{module_name}_vpcs_ext"

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

        # Get the full analysis context
        analysis = state.analysis_state.context.get("analysis", {})
        if not analysis:
            logger.warning("Analysis context is empty, attempting to extract from analysis_state")
            # Try to get analysis directly from the analysis state
            analysis = getattr(state.analysis_state, "analysis", {})

        # Get the full plan context
        plan_result = state.planning_state.context.get("plan_result", {})
        if not plan_result:
            logger.warning("Plan context is empty, attempting to extract from planning_state")
            # Try to get plan directly from the planning state
            plan_result = {
                "plan": state.planning_state.plan,
                "tasks": state.planning_state.tasks
            }

        # Log the analysis and plan for debugging
        logger.info(f"Analysis for code generation: {str(analysis)[:200]}...")
        logger.info(f"Plan for code generation: {str(plan_result)[:200]}...")

        # Use Gemini to generate code if available and enabled
        if state.use_gemini:
            logger.info("Using Gemini to generate code")
            gemini_client = GeminiClient()

            # Get the code from Gemini
            code_result = gemini_client.generate_module_code(analysis, plan_result)

            if "error" in code_result:
                logger.error(f"Gemini code generation error: {code_result['error']}")

                # Check if we have a raw response that we can try to parse manually
                if "raw_response" in code_result:
                    logger.info("Attempting to manually extract code from raw response")
                    raw_response = code_result["raw_response"]

                    # Try to extract module name and files from the raw response
                    try:
                        import re

                        # Extract module name
                        module_name_match = re.search(r'"module_name"\s*:\s*"([^"]+)"', raw_response)
                        extracted_module_name = module_name_match.group(1) if module_name_match else state.coding_state.module_name

                        # Extract file blocks
                        files = []

                        # Try to find file blocks in JSON format
                        file_blocks = re.finditer(r'"path"\s*:\s*"([^"]+)"[^}]*"content"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', raw_response, re.DOTALL)
                        for match in file_blocks:
                            path = match.group(1)
                            content = match.group(2)
                            # Unescape content
                            content = content.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                            files.append({"path": path, "content": content})

                        # If no files found, try to find code blocks with filenames
                        if not files:
                            file_blocks = re.finditer(r'```(?:python|xml|csv)?\s*(?:(\S+))\s*\n(.*?)```', raw_response, re.DOTALL)
                            for match in file_blocks:
                                path = match.group(1)
                                content = match.group(2)
                                if path and content:
                                    files.append({"path": f"{extracted_module_name}/{path}", "content": content})

                        if files:
                            logger.info(f"Successfully extracted {len(files)} files from raw response")

                            # Update the module name
                            state.coding_state.module_name = extracted_module_name

                            # Update the files
                            state.coding_state.files_to_create = files

                            # Add to history
                            state.history.append(f"Code extracted from raw response with {len(files)} files")

                            # Mark as complete
                            state.coding_state.coding_complete = True
                            state.current_step = "complete_coding"

                            logger.info(f"Code extracted successfully with {len(files)} files")
                            return state
                        else:
                            logger.error("Failed to extract files from raw response")
                    except Exception as e:
                        logger.error(f"Error extracting code from raw response: {str(e)}")

                # If we couldn't extract code from the raw response, set error and return
                state.coding_state.error = code_result["error"]
                state.current_step = "error"
                return state

            # Update the module name if provided by Gemini
            if "module_name" in code_result:
                state.coding_state.module_name = code_result["module_name"]
                logger.info(f"Using module name from Gemini: {code_result['module_name']}")

            # Store the files to create
            if "files" in code_result:
                state.coding_state.files_to_create = code_result["files"]
                logger.info(f"Generated {len(code_result['files'])} files")

                # Log the first few files for debugging
                for i, file in enumerate(code_result["files"][:3]):
                    logger.info(f"File {i+1}: {file.get('path', 'unknown')} - {len(file.get('content', ''))} bytes")

            # Add to history
            state.history.append(f"Code generated with {len(state.coding_state.files_to_create)} files")

            # Mark as complete
            state.coding_state.coding_complete = True
            state.current_step = "complete_coding"

            logger.info(f"Code generated successfully with {len(state.coding_state.files_to_create)} files")
            return state

        # Use Ollama to generate code if available and enabled
        elif state.use_ollama:
            logger.info("Using Ollama to generate code")

            try:
                # Import the fallback models utility
                from ..utils.fallback_models import generate_with_ollama

                # Create a simpler prompt for Ollama
                query = state.analysis_state.query
                prompt = f"""
                Create a simple Odoo 18 module named 'customer_feedback' for collecting customer feedback.

                The module should have:
                1. A model for storing feedback with fields for customer, rating (1-5), comment, and status
                2. Form, list, and kanban views
                3. Security access rights
                4. Basic demo data

                Provide the code for all necessary files.
                """

                # Get the code from Ollama
                result = generate_with_ollama(prompt)

                if not result:
                    logger.error("Failed to generate code with Ollama")
                    # Continue to fallback code generator
                else:
                    # Parse the result to extract files
                    # This is a simple approach - in a real implementation, you'd want more robust parsing
                    files_to_create = []

                    # Try to extract file blocks from the Ollama response
                    import re

                    # Log the result for debugging
                    logger.info(f"Ollama response length: {len(result)}")
                    logger.info(f"Ollama response first 200 chars: {result[:200]}")

                    # Try different regex patterns to extract code blocks
                    # Pattern 1: Standard markdown code blocks with filename
                    file_blocks = re.findall(r'```(?:python|xml|csv|ini)?\s*(?:(\S+))\s*\n(.*?)```', result, re.DOTALL)

                    # If that doesn't work, try a more lenient pattern
                    if not file_blocks:
                        logger.info("First pattern didn't match, trying alternative pattern")
                        file_blocks = re.findall(r'(?:File|Filename|Path):\s*(\S+)\s*```(?:python|xml|csv|ini)?\s*\n(.*?)```', result, re.DOTALL)

                    # If that still doesn't work, try an even more lenient pattern
                    if not file_blocks:
                        logger.info("Second pattern didn't match, trying another pattern")
                        file_blocks = re.findall(r'(?:File|Filename|Path):\s*(\S+)\s*\n```(?:python|xml|csv|ini)?\s*(.*?)```', result, re.DOTALL)

                    # If we found file blocks, process them
                    if file_blocks:
                        logger.info(f"Found {len(file_blocks)} file blocks")
                        for file_path, content in file_blocks:
                            # Clean up the file path
                            clean_path = file_path.strip()
                            if not clean_path.startswith(module_name):
                                clean_path = f"{module_name}/{clean_path}"

                            # Clean up the content (remove leading/trailing whitespace)
                            clean_content = content.strip()

                            logger.info(f"Extracted file: {clean_path} (content length: {len(clean_content)})")

                            files_to_create.append({
                                "path": clean_path,
                                "content": clean_content
                            })

                        # Update the state with the generated files
                        state.coding_state.files_to_create = files_to_create

                        # Add to history
                        state.history.append(f"Code generated with Ollama: {len(files_to_create)} files")

                        # Mark as complete
                        state.coding_state.coding_complete = True
                        state.current_step = "complete_coding"

                        logger.info(f"Code generated with Ollama: {len(files_to_create)} files")
                        return state
            except Exception as e:
                logger.error(f"Error using Ollama for code generation: {str(e)}")
                # Continue to fallback code generator

            # Fallback to the code generator utility
            logger.info("Ollama generation failed or not available, using fallback code generator")

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

                # Check if we have a raw response that we can try to parse manually
                if "raw_response" in updated_code:
                    logger.info("Attempting to manually extract code from raw feedback response")
                    raw_response = updated_code["raw_response"]

                    # Try to extract module name, files, and changes from the raw response
                    try:
                        import re

                        # Extract module name
                        module_name_match = re.search(r'"module_name"\s*:\s*"([^"]+)"', raw_response)
                        extracted_module_name = module_name_match.group(1) if module_name_match else state.coding_state.module_name

                        # Extract file blocks
                        files = []

                        # Try to find file blocks in JSON format
                        file_blocks = re.finditer(r'"path"\s*:\s*"([^"]+)"[^}]*"content"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', raw_response, re.DOTALL)
                        for match in file_blocks:
                            path = match.group(1)
                            content = match.group(2)
                            # Unescape content
                            content = content.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                            files.append({"path": path, "content": content})

                        # If no files found, try to find code blocks with filenames
                        if not files:
                            file_blocks = re.finditer(r'```(?:python|xml|csv)?\s*(?:(\S+))\s*\n(.*?)```', raw_response, re.DOTALL)
                            for match in file_blocks:
                                path = match.group(1)
                                content = match.group(2)
                                if path and content:
                                    files.append({"path": f"{extracted_module_name}/{path}", "content": content})

                        # Extract changes
                        changes = []
                        changes_match = re.search(r'"changes"\s*:\s*\[(.*?)\]', raw_response, re.DOTALL)
                        if changes_match:
                            changes_text = changes_match.group(1)
                            change_items = re.finditer(r'"([^"]*(?:\\.[^"]*)*)"', changes_text)
                            for match in change_items:
                                changes.append(match.group(1))

                        # If no changes found in JSON format, try to extract from text
                        if not changes:
                            changes_section = re.search(r'Changes:(.*?)(?:Files:|$)', raw_response, re.DOTALL)
                            if changes_section:
                                changes_text = changes_section.group(1)
                                changes = [line.strip() for line in changes_text.split('\n') if line.strip()]

                        if files:
                            logger.info(f"Successfully extracted {len(files)} files from raw feedback response")

                            # Update the module name
                            state.coding_state.module_name = extracted_module_name

                            # Update the files
                            state.coding_state.files_to_create = files

                            # Add changes to history
                            if changes:
                                state.history.append(f"Applied {len(changes)} changes based on feedback (extracted from raw response)")
                                for change in changes:
                                    state.history.append(f"- {change}")
                            else:
                                state.history.append("Processed feedback (extracted from raw response)")

                            logger.info(f"Feedback processed successfully (extracted from raw response)")
                            return state
                        else:
                            logger.error("Failed to extract files from raw feedback response")
                    except Exception as e:
                        logger.error(f"Error extracting code from raw feedback response: {str(e)}")

                # If we couldn't extract code from the raw response, continue with the current code
                logger.warning("Using existing code due to feedback processing error")
                state.history.append("Feedback processing failed, using existing code")
                state.current_step = "complete"
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