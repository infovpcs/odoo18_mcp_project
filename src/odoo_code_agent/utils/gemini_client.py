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
        top_k: int = 40
    ) -> Optional[str]:
        """Generate text using the Gemini model.
        
        Args:
            prompt: The prompt to send to the model
            temperature: Controls randomness (0.0 to 1.0)
            max_output_tokens: Maximum number of tokens to generate
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            
        Returns:
            Generated text or None if an error occurs
        """
        if not self.is_available:
            logger.warning("Gemini API is not available")
            return None
        
        try:
            generation_config = {
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "max_output_tokens": max_output_tokens,
            }
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return response.text
        except Exception as e:
            logger.error(f"Error generating text with Gemini: {str(e)}")
            return None
    
    def analyze_requirements(self, query: str) -> Dict[str, Any]:
        """Analyze the requirements from a user query.
        
        Args:
            query: The user query
            
        Returns:
            Dictionary with analysis results
        """
        prompt = f"""
        You are an expert Odoo developer specializing in Odoo 18. Analyze the following request for creating an Odoo module:
        
        REQUEST: {query}
        
        Provide a detailed analysis in JSON format with the following structure:
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
                            "description": "What this field represents"
                        }}
                    ]
                }}
            ],
            "views": ["list", "form", "kanban", "calendar", "graph"],
            "security": ["access rules needed"],
            "dependencies": ["other modules this depends on"]
        }}
        
        Ensure the module name follows Odoo conventions (lowercase with underscores).
        """
        
        try:
            response = self.generate_text(prompt, temperature=0.2)
            if not response:
                return {"error": "Failed to generate analysis"}
            
            # Extract JSON from the response
            try:
                # Try to parse the entire response as JSON
                result = json.loads(response)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the text
                import re
                json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        return {"error": "Failed to parse JSON from response", "raw_response": response}
                else:
                    return {"error": "Failed to extract JSON from response", "raw_response": response}
            
            return result
        except Exception as e:
            logger.error(f"Error analyzing requirements: {str(e)}")
            return {"error": f"Error analyzing requirements: {str(e)}"}
    
    def create_plan(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create a plan based on the analysis.
        
        Args:
            analysis: The analysis results
            
        Returns:
            Dictionary with the plan
        """
        prompt = f"""
        You are an expert Odoo developer specializing in Odoo 18. Create a detailed plan for implementing an Odoo module based on the following analysis:
        
        ANALYSIS: {json.dumps(analysis, indent=2)}
        
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
            "estimated_time": "Estimated time to implement the module"
        }}
        """
        
        try:
            response = self.generate_text(prompt, temperature=0.2)
            if not response:
                return {"error": "Failed to generate plan"}
            
            # Extract JSON from the response
            try:
                # Try to parse the entire response as JSON
                result = json.loads(response)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the text
                import re
                json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        return {"error": "Failed to parse JSON from response", "raw_response": response}
                else:
                    return {"error": "Failed to extract JSON from response", "raw_response": response}
            
            return result
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
        1. __init__.py files
        2. __manifest__.py with proper dependencies
        3. Model definitions
        4. View definitions
        5. Security files (ir.model.access.csv)
        6. Demo data if applicable
        
        Follow Odoo 18 best practices and coding standards.
        """
        
        try:
            response = self.generate_text(prompt, temperature=0.2, max_output_tokens=8192)
            if not response:
                return {"error": "Failed to generate module code"}
            
            # Extract JSON from the response
            try:
                # Try to parse the entire response as JSON
                result = json.loads(response)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the text
                import re
                json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        return {"error": "Failed to parse JSON from response", "raw_response": response}
                else:
                    return {"error": "Failed to extract JSON from response", "raw_response": response}
            
            return result
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
            ]
        }}
        
        Follow Odoo 18 best practices and coding standards.
        """
        
        try:
            response = self.generate_text(prompt, temperature=0.2, max_output_tokens=8192)
            if not response:
                return {"error": "Failed to process feedback"}
            
            # Extract JSON from the response
            try:
                # Try to parse the entire response as JSON
                result = json.loads(response)
            except json.JSONDecodeError:
                # If that fails, try to extract JSON from the text
                import re
                json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
                if json_match:
                    try:
                        result = json.loads(json_match.group(1))
                    except json.JSONDecodeError:
                        return {"error": "Failed to parse JSON from response", "raw_response": response}
                else:
                    return {"error": "Failed to extract JSON from response", "raw_response": response}
            
            return result
        except Exception as e:
            logger.error(f"Error processing feedback: {str(e)}")
            return {"error": f"Error processing feedback: {str(e)}"}