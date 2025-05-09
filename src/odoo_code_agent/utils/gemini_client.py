#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gemini Client for the Odoo Code Agent.

This module provides a client for interacting with Google's Gemini API.
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional, Union
import google.generativeai as genai
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Gemini API key and model from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Configure the Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info(f"Gemini API configured with model: {GEMINI_MODEL}")
else:
    logger.warning("Gemini API key not found in environment variables")


class GeminiClient:
    """Client for interacting with Google's Gemini API."""

    def __init__(self, model_name: str = None):
        """Initialize the Gemini client.

        Args:
            model_name: Name of the Gemini model to use (defaults to environment variable)
        """
        self.model_name = model_name or GEMINI_MODEL
        self.is_available = bool(GEMINI_API_KEY)

        if not self.is_available:
            logger.warning("Gemini client initialized but API key is not available")
        else:
            try:
                # Initialize the model
                self.model = genai.GenerativeModel(self.model_name)
                logger.info(f"Gemini client initialized with model: {self.model_name}")
            except Exception as e:
                logger.error(f"Error initializing Gemini model: {str(e)}")
                self.is_available = False

    def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: int = 8192,
        top_p: float = 0.95,
        top_k: int = 40,
        max_retries: int = 3
    ) -> Optional[str]:
        """Generate text using the Gemini model.

        Args:
            prompt: The prompt to send to the model
            temperature: Controls randomness (0.0 to 1.0)
            max_output_tokens: Maximum number of tokens to generate
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            max_retries: Maximum number of retry attempts if API call fails or times out

        Returns:
            Generated text or None if an error occurs
        """
        if not self.is_available:
            logger.warning("Gemini API is not available")
            return None

        # Initialize retry counter
        retry_count = 0
        last_error = None

        # Retry loop
        while retry_count < max_retries:
            try:
                # If this is a retry, log it
                if retry_count > 0:
                    logger.info(f"Retry attempt {retry_count}/{max_retries} for Gemini API call")

                generation_config = {
                    "temperature": temperature,
                    "top_p": top_p,
                    "top_k": top_k,
                    "max_output_tokens": max_output_tokens,
                }

                # Add a timeout to prevent hanging
                import threading
                import time

                response = None
                error = None

                def generate_with_timeout():
                    nonlocal response, error
                    try:
                        response = self.model.generate_content(
                            prompt,
                            generation_config=generation_config
                        )
                    except Exception as e:
                        error = e

                # Start generation in a separate thread
                thread = threading.Thread(target=generate_with_timeout)
                thread.start()

                # Wait for the thread to complete with a timeout
                # Increase timeout slightly on each retry
                timeout_seconds = 30 + (retry_count * 10)  # 30s, 40s, 50s
                thread.join(timeout=timeout_seconds)

                # Check if the thread is still running (timed out)
                if thread.is_alive():
                    logger.warning(f"Gemini API call timed out after {timeout_seconds} seconds (attempt {retry_count+1}/{max_retries})")
                    # Don't wait for the thread to complete, just move on to the next retry
                    retry_count += 1
                    last_error = TimeoutError(f"API call timed out after {timeout_seconds} seconds")
                    # Add a small delay before retrying
                    time.sleep(2)
                    continue

                # Check if there was an error
                if error:
                    last_error = error
                    logger.warning(f"Gemini API call failed with error: {str(error)} (attempt {retry_count+1}/{max_retries})")
                    retry_count += 1
                    # Add a small delay before retrying
                    time.sleep(2)
                    continue

                # Check if we got a response
                if not response:
                    last_error = ValueError("No response from Gemini API")
                    logger.warning(f"No response from Gemini API (attempt {retry_count+1}/{max_retries})")
                    retry_count += 1
                    # Add a small delay before retrying
                    time.sleep(2)
                    continue

                # If we got here, the call was successful
                logger.info(f"Gemini API call successful{' after ' + str(retry_count) + ' retries' if retry_count > 0 else ''}")
                return response.text

            except Exception as e:
                last_error = e
                logger.warning(f"Error generating text with Gemini: {str(e)} (attempt {retry_count+1}/{max_retries})")
                retry_count += 1
                # Add a small delay before retrying
                time.sleep(2)

        # If we get here, all retries failed
        logger.error(f"All {max_retries} attempts to call Gemini API failed. Last error: {str(last_error)}")
        return None

    def analyze_requirements(self, query: str, context: str = "") -> Dict[str, Any]:
        """Analyze the requirements from a user query.

        Args:
            query: The user query
            context: Additional context information to help with analysis

        Returns:
            Dictionary with analysis results
        """
        # Add context to the prompt if provided
        context_section = f"\nCONTEXT INFORMATION:\n{context}\n\n" if context else ""

        prompt = f"""
        You are an expert Odoo developer specializing in Odoo 18. Analyze the following request for creating an Odoo module:

        REQUEST: {query}{context_section}

        Based on the request and any provided context information, provide a detailed analysis in JSON format with the following structure:
        {{
            "module_name": "suggested technical name for the module",
            "module_title": "Human-readable title for the module",
            "description": "Brief description of what the module will do",
            "models": [
                {{
                    "name": "model.technical.name",
                    "description": "What this model represents",
                    "fields": [
                        {{
                            "name": "field_name",
                            "type": "field type (char, text, integer, float, boolean, date, datetime, many2one, one2many, many2many)",
                            "description": "What this field represents",
                            "relation": "related model for relational fields (optional)"
                        }}
                    ]
                }}
            ],
            "views": ["list", "form", "kanban", "calendar", "graph"],
            "security": ["access rules needed"],
            "dependencies": ["other modules this depends on"]
        }}

        IMPORTANT GUIDELINES:
        1. Use the context information to identify appropriate models, fields, and dependencies
        2. Follow Odoo naming conventions (lowercase with underscores for technical names)
        3. Include appropriate relational fields when relevant
        4. Consider standard Odoo patterns for the requested functionality
        5. Include mail.thread and mail.activity.mixin inheritance if appropriate
        6. Ensure field types are valid Odoo field types

        Ensure the module name follows Odoo conventions (lowercase with underscores).

        IMPORTANT: Return your response as a valid JSON object without any markdown formatting or code blocks. Do not use single quotes for JSON keys or values, use double quotes only. Do not include any explanations or text outside the JSON object.
        """

        try:
            response = self.generate_text(prompt, temperature=0.2)
            if not response:
                return {"error": "Failed to generate analysis"}

            # Extract JSON from the response
            try:
                # Try to parse the entire response as JSON
                result = json.loads(response)
                logger.info("Successfully parsed entire analysis response as JSON")
                return result
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the text using multiple patterns
                import re

                logger.info(f"JSON parsing failed for analysis, trying pattern matching. Response starts with: {response[:100]}...")

                # Try different patterns to extract JSON
                patterns = [
                    r'```json\n([\s\S]*?)\n```',  # Standard markdown JSON block
                    r'```\n([\s\S]*?)\n```',  # Generic code block
                    r'```([\s\S]*?)```',  # Code block without language
                    r'({[\s\S]*"module_name"[\s\S]*"models"[\s\S]*})',  # Look for specific JSON structure
                    r'({[\s\S]*})'  # Any JSON-like structure as a last resort
                ]

                for i, pattern in enumerate(patterns):
                    logger.info(f"Trying pattern {i+1} for analysis")
                    json_match = re.search(pattern, response, re.DOTALL)
                    if json_match:
                        try:
                            json_str = json_match.group(1).strip()
                            logger.info(f"Found match with pattern {i+1}, extracted text starts with: {json_str[:100]}...")

                            # Clean up the JSON string
                            # Remove trailing commas in objects
                            json_str = re.sub(r',\s*}', '}', json_str)
                            # Remove trailing commas in arrays
                            json_str = re.sub(r',\s*]', ']', json_str)
                            # Fix any unescaped quotes in strings
                            json_str = re.sub(r'(?<!\\)"(?=(.*?"[^:,{\[]*?[:,{\[]))', r'\"', json_str)

                            # Try to parse the cleaned JSON
                            try:
                                result = json.loads(json_str)
                                logger.info(f"Successfully parsed analysis JSON after cleanup with pattern {i+1}")
                                return result
                            except json.JSONDecodeError as e:
                                logger.warning(f"JSON parsing still failed after cleanup: {str(e)}")

                                # Try a more aggressive approach for the last pattern
                                if i == len(patterns) - 1:
                                    # Try to manually construct a valid JSON
                                    logger.info("Trying manual JSON construction for analysis...")

                                    # Extract module name from the query
                                    query_lower = query.lower()

                                    # Try to find a meaningful module name based on the query
                                    if "customer feedback" in query_lower:
                                        derived_module_name = "customer_feedback"
                                    elif "project" in query_lower and "management" in query_lower:
                                        derived_module_name = "project_management"
                                    elif "inventory" in query_lower:
                                        derived_module_name = "inventory_management"
                                    elif "sales" in query_lower:
                                        derived_module_name = "sales_management"
                                    elif "purchase" in query_lower:
                                        derived_module_name = "purchase_management"
                                    elif "hr" in query_lower or "employee" in query_lower:
                                        derived_module_name = "hr_management"
                                    elif "point of sale" in query_lower or "pos" in query_lower:
                                        if "multi-currency" in query_lower or "currency" in query_lower:
                                            derived_module_name = "pos_multi_currency"
                                        else:
                                            derived_module_name = "pos_custom"
                                    elif "website" in query_lower:
                                        derived_module_name = "website_custom"
                                    elif "ecommerce" in query_lower or "e-commerce" in query_lower:
                                        derived_module_name = "website_sale_custom"
                                    elif "crm" in query_lower:
                                        derived_module_name = "crm_custom"
                                    else:
                                        # Default fallback: extract key words from the query
                                        words = query_lower.split()
                                        key_words = [w for w in words if len(w) > 3 and w not in ["odoo", "module", "create", "with", "that", "this", "for", "and", "the"]]
                                        derived_module_name = "_".join(key_words[:2]) if key_words else "custom_module"

                                    # Try to extract module name from JSON, fall back to derived name
                                    module_name_match = re.search(r'"module_name"\s*:\s*"([^"]+)"', json_str)
                                    module_name = module_name_match.group(1) if module_name_match and module_name_match.group(1) != "unknown_module" else derived_module_name

                                    # Add _vpcs_ext suffix to prevent conflicts with existing Odoo apps
                                    if not module_name.endswith("_vpcs_ext"):
                                        module_name = f"{module_name}_vpcs_ext"

                                    # Extract module title
                                    module_title_match = re.search(r'"module_title"\s*:\s*"([^"]+)"', json_str)
                                    module_title = module_title_match.group(1) if module_title_match else query

                                    # Extract description
                                    description_match = re.search(r'"description"\s*:\s*"([^"]+)"', json_str)
                                    description = description_match.group(1) if description_match else f"Module for {query}"

                                    # Try to extract models
                                    models = []
                                    models_section = re.search(r'"models"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
                                    if models_section:
                                        # This is a simplified approach - in a real implementation, you'd want more robust parsing
                                        model_blocks = re.finditer(r'{([^{}]*(?:{[^{}]*}[^{}]*)*)}', models_section.group(1))
                                        for i, model_block in enumerate(model_blocks):
                                            model_text = model_block.group(0)

                                            # Extract model name from JSON
                                            model_name_match = re.search(r'"name"\s*:\s*"([^"]+)"', model_text)

                                            # If no model name or it's the default unknown, derive a better one
                                            if not model_name_match or model_name_match.group(1) == "unknown.model":
                                                # Derive model name based on module name and query
                                                if "point of sale" in query_lower or "pos" in query_lower:
                                                    if "currency" in query_lower and i == 0:
                                                        derived_model_name = f"{module_name}.currency"
                                                    elif "config" in query_lower:
                                                        derived_model_name = f"{module_name}.config"
                                                    else:
                                                        derived_model_name = f"{module_name}.{i+1}"
                                                else:
                                                    # Default model name based on module
                                                    derived_model_name = f"{module_name.replace('_', '.')}.{i+1}"

                                                model_name = derived_model_name
                                            else:
                                                model_name = model_name_match.group(1)

                                            # Extract model description
                                            model_desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', model_text)
                                            model_desc = model_desc_match.group(1) if model_desc_match else f"Model for {module_name.replace('_', ' ')}"

                                            # Extract fields
                                            fields = []
                                            fields_section = re.search(r'"fields"\s*:\s*\[(.*?)\]', model_text, re.DOTALL)
                                            if fields_section:
                                                field_blocks = re.finditer(r'{([^{}]*(?:{[^{}]*}[^{}]*)*)}', fields_section.group(1))
                                                for field_block in field_blocks:
                                                    field_text = field_block.group(0)

                                                    # Extract field properties
                                                    field_name_match = re.search(r'"name"\s*:\s*"([^"]+)"', field_text)
                                                    field_type_match = re.search(r'"type"\s*:\s*"([^"]+)"', field_text)
                                                    field_desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', field_text)
                                                    field_relation_match = re.search(r'"relation"\s*:\s*"([^"]+)"', field_text)

                                                    field = {
                                                        "name": field_name_match.group(1) if field_name_match else "unknown_field",
                                                        "type": field_type_match.group(1) if field_type_match else "char",
                                                        "description": field_desc_match.group(1) if field_desc_match else ""
                                                    }

                                                    if field_relation_match:
                                                        field["relation"] = field_relation_match.group(1)

                                                    fields.append(field)

                                            models.append({
                                                "name": model_name,
                                                "description": model_desc,
                                                "fields": fields
                                            })

                                    # Extract views
                                    views_match = re.search(r'"views"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
                                    views = []
                                    if views_match:
                                        views_text = views_match.group(1)
                                        view_items = re.finditer(r'"([^"]*(?:\\.[^"]*)*)"', views_text)
                                        for match in view_items:
                                            views.append(match.group(1))

                                    # Extract security
                                    security_match = re.search(r'"security"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
                                    security = []
                                    if security_match:
                                        security_text = security_match.group(1)
                                        security_items = re.finditer(r'"([^"]*(?:\\.[^"]*)*)"', security_text)
                                        for match in security_items:
                                            security.append(match.group(1))

                                    # Extract dependencies
                                    dependencies_match = re.search(r'"dependencies"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
                                    dependencies = []
                                    if dependencies_match:
                                        dependencies_text = dependencies_match.group(1)
                                        dependency_items = re.finditer(r'"([^"]*(?:\\.[^"]*)*)"', dependencies_text)
                                        for match in dependency_items:
                                            dependencies.append(match.group(1))

                                    result = {
                                        "module_name": module_name,
                                        "module_title": module_title,
                                        "description": description,
                                        "models": models,
                                        "views": views,
                                        "security": security,
                                        "dependencies": dependencies
                                    }

                                    logger.info(f"Manually constructed analysis JSON with {len(models)} models")
                                    return result
                        except Exception as e:
                            logger.warning(f"Error processing analysis match with pattern {i+1}: {str(e)}")
                            continue

                # If we get here, all patterns failed
                logger.error(f"All JSON extraction patterns failed for analysis. Response: {response[:500]}...")
                return {"error": "Failed to extract JSON from analysis response", "raw_response": response}
        except Exception as e:
            logger.error(f"Error analyzing requirements: {str(e)}")
            return {"error": f"Error analyzing requirements: {str(e)}"}

    def create_plan(self, analysis: Dict[str, Any], context: str = "") -> Dict[str, Any]:
        """Create a plan based on the analysis.

        Args:
            analysis: The analysis results
            context: Additional context information to help with planning

        Returns:
            Dictionary with the plan
        """
        # Add context to the prompt if provided
        context_section = f"\nCONTEXT INFORMATION:\n{context}\n\n" if context else ""

        prompt = f"""
        You are an expert Odoo developer specializing in Odoo 18. Create a detailed plan for implementing an Odoo module based on the following analysis:

        ANALYSIS: {json.dumps(analysis, indent=2)}{context_section}

        Provide a detailed plan in JSON format with the following structure:
        {{
            "plan": "Detailed step-by-step plan for implementing the module",
            "tasks": [
                "Task 1: Create module structure",
                "Task 2: Implement models",
                "Task 3: Create views",
                "Task 4: Set up security",
                "Task 5: Add demo data"
            ],
            "estimated_time": "Estimated time to implement the module",
            "technical_considerations": [
                "Important technical considerations for implementation"
            ]
        }}

        IMPORTANT GUIDELINES:
        1. Break down the implementation into clear, manageable tasks
        2. Consider dependencies between tasks
        3. Include specific Odoo 18 technical considerations
        4. Mention any potential challenges and how to address them
        5. Consider testing and quality assurance steps

        IMPORTANT: Return your response as a valid JSON object without any markdown formatting or code blocks. Do not use single quotes for JSON keys or values, use double quotes only. Do not include any explanations or text outside the JSON object.
        """

        try:
            response = self.generate_text(prompt, temperature=0.2)
            if not response:
                return {"error": "Failed to generate plan"}

            # Extract JSON from the response
            try:
                # Try to parse the entire response as JSON
                result = json.loads(response)
                logger.info("Successfully parsed entire plan response as JSON")
                return result
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the text using multiple patterns
                import re

                logger.info(f"JSON parsing failed for plan, trying pattern matching. Response starts with: {response[:100]}...")

                # Try different patterns to extract JSON
                patterns = [
                    r'```json\n([\s\S]*?)\n```',  # Standard markdown JSON block
                    r'```\n([\s\S]*?)\n```',  # Generic code block
                    r'```([\s\S]*?)```',  # Code block without language
                    r'({[\s\S]*"plan"[\s\S]*"tasks"[\s\S]*})',  # Look for specific JSON structure
                    r'({[\s\S]*})'  # Any JSON-like structure as a last resort
                ]

                for i, pattern in enumerate(patterns):
                    logger.info(f"Trying pattern {i+1} for plan")
                    json_match = re.search(pattern, response, re.DOTALL)
                    if json_match:
                        try:
                            json_str = json_match.group(1).strip()
                            logger.info(f"Found match with pattern {i+1}, extracted text starts with: {json_str[:100]}...")

                            # Clean up the JSON string
                            # Remove trailing commas in objects
                            json_str = re.sub(r',\s*}', '}', json_str)
                            # Remove trailing commas in arrays
                            json_str = re.sub(r',\s*]', ']', json_str)
                            # Fix any unescaped quotes in strings
                            json_str = re.sub(r'(?<!\\)"(?=(.*?"[^:,{\[]*?[:,{\[]))', r'\"', json_str)

                            # Try to parse the cleaned JSON
                            try:
                                result = json.loads(json_str)
                                logger.info(f"Successfully parsed plan JSON after cleanup with pattern {i+1}")
                                return result
                            except json.JSONDecodeError as e:
                                logger.warning(f"JSON parsing still failed after cleanup: {str(e)}")

                                # Try a more aggressive approach for the last pattern
                                if i == len(patterns) - 1:
                                    # Try to manually construct a valid JSON
                                    logger.info("Trying manual JSON construction for plan...")

                                    # Extract plan
                                    plan_match = re.search(r'"plan"\s*:\s*"([^"]+(?:\\.[^"]*)*)"', json_str)
                                    plan_text = plan_match.group(1) if plan_match else "No plan available"

                                    # Extract tasks
                                    tasks = []
                                    tasks_section = re.search(r'"tasks"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
                                    if tasks_section:
                                        tasks_text = tasks_section.group(1)
                                        task_items = re.finditer(r'"([^"]*(?:\\.[^"]*)*)"', tasks_text)
                                        for match in task_items:
                                            tasks.append(match.group(1))

                                    # Extract estimated time
                                    time_match = re.search(r'"estimated_time"\s*:\s*"([^"]+)"', json_str)
                                    estimated_time = time_match.group(1) if time_match else "Unknown"

                                    # Extract technical considerations
                                    considerations = []
                                    considerations_section = re.search(r'"technical_considerations"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
                                    if considerations_section:
                                        considerations_text = considerations_section.group(1)
                                        consideration_items = re.finditer(r'"([^"]*(?:\\.[^"]*)*)"', considerations_text)
                                        for match in consideration_items:
                                            considerations.append(match.group(1))

                                    result = {
                                        "plan": plan_text,
                                        "tasks": tasks,
                                        "estimated_time": estimated_time,
                                        "technical_considerations": considerations
                                    }

                                    logger.info(f"Manually constructed plan JSON with {len(tasks)} tasks")
                                    return result
                        except Exception as e:
                            logger.warning(f"Error processing plan match with pattern {i+1}: {str(e)}")
                            continue

                # If we get here, all patterns failed
                logger.error(f"All JSON extraction patterns failed for plan. Response: {response[:500]}...")
                return {"error": "Failed to extract JSON from plan response", "raw_response": response}
        except Exception as e:
            logger.error(f"Error creating plan: {str(e)}")
            return {"error": f"Error creating plan: {str(e)}"}

    def generate_module_code(self, analysis: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code for the Odoo module.

        Args:
            analysis: The analysis results
            plan: The implementation plan

        Returns:
            Dictionary with the generated code
        """
        prompt = f"""
        You are an expert Odoo developer specializing in Odoo 18. Generate code for an Odoo module based on the following analysis and plan:

        ANALYSIS: {json.dumps(analysis, indent=2)}

        PLAN: {json.dumps(plan, indent=2)}

        Generate the complete module code in JSON format with the following structure:
        {{
            "module_name": "technical_name",
            "files": [
                {{
                    "path": "relative path within the module",
                    "content": "file content"
                }}
            ]
        }}

        Include all necessary files for a complete Odoo module:
        1. __init__.py files (both at module root and in subdirectories)
        2. __manifest__.py with proper dependencies, data files, and security files
        3. Model definitions with all fields specified in the analysis
        4. View definitions (form, list, kanban, etc.) as specified in the analysis
        5. Security files (ir.model.access.csv and security rules if needed)
        6. Demo data if applicable

        IMPORTANT REQUIREMENTS:
        1. Follow the plan EXACTLY as outlined above
        2. Implement ALL models and fields from the analysis
        3. Create ALL views mentioned in the analysis
        4. Include proper security settings
        5. Use Odoo 18 best practices and coding standards
        6. Ensure all files are properly referenced in __manifest__.py
        7. Use proper inheritance patterns if extending existing models
        8. Include docstrings and comments for clarity
        9. Implement constraints, computed fields, and methods as needed
        10. Follow proper naming conventions for technical names

        Your code must be complete and functional, ready to be installed in an Odoo 18 instance.

        IMPORTANT: Return your response as a valid JSON object without any markdown formatting or code blocks.
        """

        try:
            response = self.generate_text(prompt, temperature=0.2, max_output_tokens=8192)
            if not response:
                return {"error": "Failed to generate module code"}

            # Extract JSON from the response
            try:
                # Try to parse the entire response as JSON
                result = json.loads(response)
                logger.info("Successfully parsed entire response as JSON")
                return result
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the text using multiple patterns
                import re

                logger.info(f"JSON parsing failed, trying pattern matching. Response starts with: {response[:100]}...")

                # Try different patterns to extract JSON
                patterns = [
                    r'```json\n([\s\S]*?)\n```',  # Standard markdown JSON block
                    r'```\n([\s\S]*?)\n```',  # Generic code block
                    r'```([\s\S]*?)```',  # Code block without language
                    r'({[\s\S]*"module_name"[\s\S]*"files"[\s\S]*})',  # Look for specific JSON structure
                    r'({[\s\S]*})'  # Any JSON-like structure as a last resort
                ]

                for i, pattern in enumerate(patterns):
                    logger.info(f"Trying pattern {i+1}")
                    json_match = re.search(pattern, response, re.DOTALL)
                    if json_match:
                        try:
                            json_str = json_match.group(1).strip()
                            logger.info(f"Found match with pattern {i+1}, extracted text starts with: {json_str[:100]}...")

                            # Clean up the JSON string
                            # Remove trailing commas in objects
                            json_str = re.sub(r',\s*}', '}', json_str)
                            # Remove trailing commas in arrays
                            json_str = re.sub(r',\s*]', ']', json_str)
                            # Fix any unescaped quotes in strings
                            json_str = re.sub(r'(?<!\\)"(?=(.*?"[^:,{\[]*?[:,{\[]))', r'\"', json_str)

                            # Try to parse the cleaned JSON
                            try:
                                result = json.loads(json_str)
                                logger.info(f"Successfully parsed JSON after cleanup with pattern {i+1}")
                                return result
                            except json.JSONDecodeError as e:
                                logger.warning(f"JSON parsing still failed after cleanup: {str(e)}")

                                # Try a more aggressive approach for the last pattern
                                if i == len(patterns) - 1:
                                    # Try to manually construct a valid JSON
                                    logger.info("Trying manual JSON construction...")

                                    # Extract module name
                                    module_name_match = re.search(r'"module_name"\s*:\s*"([^"]+)"', json_str)
                                    module_name = module_name_match.group(1) if module_name_match else "unknown_module"

                                    # Extract files
                                    files = []
                                    file_matches = re.finditer(r'"path"\s*:\s*"([^"]+)"[^}]*"content"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', json_str, re.DOTALL)

                                    for match in file_matches:
                                        path = match.group(1)
                                        content = match.group(2)
                                        # Unescape content
                                        content = content.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                                        files.append({"path": path, "content": content})

                                    if files:
                                        result = {
                                            "module_name": module_name,
                                            "files": files
                                        }
                                        logger.info(f"Manually constructed JSON with {len(files)} files")
                                        return result
                        except Exception as e:
                            logger.warning(f"Error processing match with pattern {i+1}: {str(e)}")
                            continue

                # If we get here, all patterns failed
                logger.error(f"All JSON extraction patterns failed. Response: {response[:500]}...")

                # Last resort: try to manually extract module_name and files
                try:
                    logger.info("Attempting last resort manual extraction...")

                    # Extract module name
                    module_name_match = re.search(r'"module_name"\s*:\s*"([^"]+)"', response)
                    module_name = module_name_match.group(1) if module_name_match else "extracted_module"

                    # Extract file paths and contents
                    files = []

                    # Find all path/content pairs
                    path_content_pairs = re.finditer(r'"path"\s*:\s*"([^"]+)"[^}]*"content"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', response, re.DOTALL)

                    for match in path_content_pairs:
                        path = match.group(1)
                        content = match.group(2)
                        # Unescape content
                        content = content.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                        files.append({"path": path, "content": content})

                    if not files:
                        # Try another approach - look for file blocks
                        file_blocks = re.finditer(r'```(?:python|xml|csv)?\s*(?:(\S+))\s*\n(.*?)```', response, re.DOTALL)
                        for match in file_blocks:
                            path = match.group(1)
                            content = match.group(2)
                            if path and content:
                                files.append({"path": f"{module_name}/{path}", "content": content})

                    if files:
                        result = {
                            "module_name": module_name,
                            "files": files
                        }
                        logger.info(f"Last resort extraction successful: found {len(files)} files")
                        return result
                    else:
                        # If we still couldn't extract files, return the error
                        return {"error": "Failed to extract JSON from response", "raw_response": response}
                except Exception as e:
                    logger.error(f"Last resort extraction failed: {str(e)}")
                    return {"error": "Failed to extract JSON from response", "raw_response": response}

        except Exception as e:
            logger.error(f"Error generating module code: {str(e)}")
            return {"error": f"Error generating module code: {str(e)}"}

    def process_feedback(self, analysis: Dict[str, Any], plan: Dict[str, Any], code: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """Process user feedback and update the module code.

        Args:
            analysis: The analysis results
            plan: The implementation plan
            code: The generated code
            feedback: User feedback

        Returns:
            Dictionary with the updated code
        """
        prompt = f"""
        You are an expert Odoo developer specializing in Odoo 18. Update the module code based on the following feedback:

        ANALYSIS: {json.dumps(analysis, indent=2)}

        PLAN: {json.dumps(plan, indent=2)}

        CURRENT CODE: {json.dumps(code, indent=2)}

        USER FEEDBACK: {feedback}

        First, determine if the feedback indicates that the code needs to be completely regenerated or just modified.
        If the feedback suggests a complete regeneration is needed, create entirely new code following the analysis and plan.
        If the feedback suggests modifications, update the existing code to address the specific issues.

        Generate the updated module code in JSON format with the following structure:
        {{
            "module_name": "technical_name",
            "files": [
                {{
                    "path": "relative path within the module",
                    "content": "file content"
                }}
            ],
            "changes": [
                "Description of change 1",
                "Description of change 2"
            ],
            "regenerated": true/false
        }}

        IMPORTANT REQUIREMENTS:
        1. If regenerating, follow the plan EXACTLY as outlined above
        2. Implement ALL models and fields from the analysis
        3. Create ALL views mentioned in the analysis
        4. Include proper security settings
        5. Use Odoo 18 best practices and coding standards
        6. Ensure all files are properly referenced in __manifest__.py
        7. Use proper inheritance patterns if extending existing models
        8. Include docstrings and comments for clarity
        9. Implement constraints, computed fields, and methods as needed
        10. Follow proper naming conventions for technical names

        Your code must be complete and functional, ready to be installed in an Odoo 18 instance.

        IMPORTANT: Return your response as a valid JSON object without any markdown formatting or code blocks.
        """

        try:
            response = self.generate_text(prompt, temperature=0.2, max_output_tokens=8192)
            if not response:
                return {"error": "Failed to process feedback"}

            # Extract JSON from the response
            try:
                # Try to parse the entire response as JSON
                result = json.loads(response)
                logger.info("Successfully parsed entire feedback response as JSON")
                return result
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the text using multiple patterns
                import re

                logger.info(f"JSON parsing failed for feedback, trying pattern matching. Response starts with: {response[:100]}...")

                # Try different patterns to extract JSON
                patterns = [
                    r'```json\n([\s\S]*?)\n```',  # Standard markdown JSON block
                    r'```\n([\s\S]*?)\n```',  # Generic code block
                    r'```([\s\S]*?)```',  # Code block without language
                    r'({[\s\S]*"module_name"[\s\S]*"files"[\s\S]*})',  # Look for specific JSON structure
                    r'({[\s\S]*"changes"[\s\S]*})',  # Look for changes structure
                    r'({[\s\S]*})'  # Any JSON-like structure as a last resort
                ]

                for i, pattern in enumerate(patterns):
                    logger.info(f"Trying pattern {i+1} for feedback")
                    json_match = re.search(pattern, response, re.DOTALL)
                    if json_match:
                        try:
                            json_str = json_match.group(1).strip()
                            logger.info(f"Found match with pattern {i+1}, extracted text starts with: {json_str[:100]}...")

                            # Clean up the JSON string
                            # Remove trailing commas in objects
                            json_str = re.sub(r',\s*}', '}', json_str)
                            # Remove trailing commas in arrays
                            json_str = re.sub(r',\s*]', ']', json_str)
                            # Fix any unescaped quotes in strings
                            json_str = re.sub(r'(?<!\\)"(?=(.*?"[^:,{\[]*?[:,{\[]))', r'\"', json_str)

                            # Try to parse the cleaned JSON
                            try:
                                result = json.loads(json_str)
                                logger.info(f"Successfully parsed feedback JSON after cleanup with pattern {i+1}")
                                return result
                            except json.JSONDecodeError as e:
                                logger.warning(f"JSON parsing still failed after cleanup: {str(e)}")

                                # Try a more aggressive approach for the last pattern
                                if i == len(patterns) - 1:
                                    # Try to manually construct a valid JSON
                                    logger.info("Trying manual JSON construction for feedback...")

                                    # Extract module name
                                    module_name_match = re.search(r'"module_name"\s*:\s*"([^"]+)"', json_str)
                                    module_name = module_name_match.group(1) if module_name_match else code.get("module_name", "unknown_module")

                                    # Extract files
                                    files = []
                                    file_matches = re.finditer(r'"path"\s*:\s*"([^"]+)"[^}]*"content"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', json_str, re.DOTALL)

                                    for match in file_matches:
                                        path = match.group(1)
                                        content = match.group(2)
                                        # Unescape content
                                        content = content.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                                        files.append({"path": path, "content": content})

                                    # Extract changes
                                    changes = []
                                    changes_match = re.search(r'"changes"\s*:\s*\[(.*?)\]', json_str, re.DOTALL)
                                    if changes_match:
                                        changes_str = changes_match.group(1)
                                        change_items = re.finditer(r'"([^"]*(?:\\.[^"]*)*)"', changes_str)
                                        for match in change_items:
                                            changes.append(match.group(1))

                                    # Determine if regenerated
                                    regenerated = False
                                    regenerated_match = re.search(r'"regenerated"\s*:\s*(true|false)', json_str)
                                    if regenerated_match:
                                        regenerated = regenerated_match.group(1) == "true"

                                    if files:
                                        result = {
                                            "module_name": module_name,
                                            "files": files,
                                            "changes": changes,
                                            "regenerated": regenerated
                                        }
                                        logger.info(f"Manually constructed feedback JSON with {len(files)} files and {len(changes)} changes")
                                        return result
                        except Exception as e:
                            logger.warning(f"Error processing feedback match with pattern {i+1}: {str(e)}")
                            continue

                # If we get here, all patterns failed
                logger.error(f"All JSON extraction patterns failed for feedback. Response: {response[:500]}...")

                # Last resort: try to manually extract module_name and files
                try:
                    logger.info("Attempting last resort manual extraction for feedback...")

                    # Extract module name
                    module_name_match = re.search(r'"module_name"\s*:\s*"([^"]+)"', response)
                    module_name = module_name_match.group(1) if module_name_match else code.get("module_name", "extracted_module")

                    # Extract file paths and contents
                    files = []

                    # Find all path/content pairs
                    path_content_pairs = re.finditer(r'"path"\s*:\s*"([^"]+)"[^}]*"content"\s*:\s*"([^"]*(?:\\.[^"]*)*)"', response, re.DOTALL)

                    for match in path_content_pairs:
                        path = match.group(1)
                        content = match.group(2)
                        # Unescape content
                        content = content.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t')
                        files.append({"path": path, "content": content})

                    if not files:
                        # Try another approach - look for file blocks
                        file_blocks = re.finditer(r'```(?:python|xml|csv)?\s*(?:(\S+))\s*\n(.*?)```', response, re.DOTALL)
                        for match in file_blocks:
                            path = match.group(1)
                            content = match.group(2)
                            if path and content:
                                files.append({"path": f"{module_name}/{path}", "content": content})

                    # Extract changes
                    changes = []
                    changes_match = re.search(r'"changes"\s*:\s*\[(.*?)\]', response, re.DOTALL)
                    if changes_match:
                        changes_str = changes_match.group(1)
                        change_items = re.finditer(r'"([^"]*(?:\\.[^"]*)*)"', changes_str)
                        for match in change_items:
                            changes.append(match.group(1))

                    # If no changes found, try to extract from text
                    if not changes:
                        changes_section = re.search(r'Changes:(.*?)(?:Files:|$)', response, re.DOTALL)
                        if changes_section:
                            changes_text = changes_section.group(1)
                            changes = [line.strip() for line in changes_text.split('\n') if line.strip()]

                    if files:
                        result = {
                            "module_name": module_name,
                            "files": files,
                            "changes": changes,
                            "regenerated": len(files) > 0
                        }
                        logger.info(f"Last resort extraction successful for feedback: found {len(files)} files and {len(changes)} changes")
                        return result
                    else:
                        # If we still couldn't extract files, return the error
                        return {"error": "Failed to extract JSON from feedback response", "raw_response": response}
                except Exception as e:
                    logger.error(f"Last resort extraction failed for feedback: {str(e)}")
                    return {"error": "Failed to extract JSON from feedback response", "raw_response": response}
        except Exception as e:
            logger.error(f"Error processing feedback: {str(e)}")
            return {"error": f"Error processing feedback: {str(e)}"}