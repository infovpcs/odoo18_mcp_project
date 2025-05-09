#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Review nodes for the Odoo Code Agent.

This module provides nodes for reviewing the generated code for completeness.
"""

import logging
import re
from typing import Dict, List, Any, Optional

from ..state import OdooCodeAgentState, AgentPhase
from ..utils.gemini_client import GeminiClient

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def start_code_review(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """
    Start the code review phase.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    logger.info("Starting code review phase")
    
    # Set the phase to CODE_REVIEW
    state.phase = AgentPhase.CODE_REVIEW
    
    # Reset review state
    state.coding_state.incomplete_files = []
    state.coding_state.regenerated_files = []
    state.coding_state.review_complete = False
    
    # Add to history
    state.history.append(f"Starting code review for module: {state.coding_state.module_name}")
    
    # Set the next step
    state.current_step = "review_code_completeness"
    
    return state


def review_code_completeness(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """
    Review the generated code for completeness.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    logger.info("Reviewing code completeness")
    
    try:
        # Get the files to review
        files_to_create = state.coding_state.files_to_create
        
        if not files_to_create:
            logger.warning("No files to review")
            state.coding_state.error = "No files to review"
            state.current_step = "error"
            return state
        
        # Check for manifest file
        manifest_file = next((f for f in files_to_create if f.get("path", "").endswith("__manifest__.py")), None)
        if not manifest_file:
            logger.warning("No manifest file found")
            state.coding_state.incomplete_files.append({
                "file_type": "manifest",
                "reason": "Missing __manifest__.py file",
                "path": f"{state.coding_state.module_name}/__manifest__.py",
                "content": ""
            })
        
        # Check XML view files
        xml_files = [f for f in files_to_create if f.get("path", "").endswith(".xml")]
        incomplete_xml_files = []
        
        for xml_file in xml_files:
            content = xml_file.get("content", "")
            path = xml_file.get("path", "")
            
            # Check if XML file is incomplete
            if not content or content.strip() == "" or content.strip() == "<?xml version=\\":
                incomplete_xml_files.append({
                    "file_type": "xml",
                    "reason": "Empty or incomplete XML file",
                    "path": path,
                    "content": content
                })
            elif not content.strip().startswith("<?xml"):
                incomplete_xml_files.append({
                    "file_type": "xml",
                    "reason": "XML file missing XML declaration",
                    "path": path,
                    "content": content
                })
            elif "<odoo>" not in content:
                incomplete_xml_files.append({
                    "file_type": "xml",
                    "reason": "XML file missing <odoo> root element",
                    "path": path,
                    "content": content
                })
        
        # Check JavaScript files
        js_files = [f for f in files_to_create if f.get("path", "").endswith(".js")]
        incomplete_js_files = []
        
        for js_file in js_files:
            content = js_file.get("content", "")
            path = js_file.get("path", "")
            
            # Check if JS file is incomplete
            if not content or content.strip() == "":
                incomplete_js_files.append({
                    "file_type": "js",
                    "reason": "Empty JavaScript file",
                    "path": path,
                    "content": content
                })
            elif "odoo.define" in content and content.strip().endswith("\\"):
                incomplete_js_files.append({
                    "file_type": "js",
                    "reason": "Incomplete JavaScript module definition",
                    "path": path,
                    "content": content
                })
        
        # Combine all incomplete files
        state.coding_state.incomplete_files = incomplete_xml_files + incomplete_js_files
        
        # If there are incomplete files, regenerate them
        if state.coding_state.incomplete_files:
            logger.info(f"Found {len(state.coding_state.incomplete_files)} incomplete files")
            state.history.append(f"Found {len(state.coding_state.incomplete_files)} incomplete files that need regeneration")
            state.current_step = "regenerate_incomplete_files"
        else:
            logger.info("All files are complete")
            state.history.append("Code review completed: All files are complete")
            state.coding_state.review_complete = True
            state.phase = AgentPhase.HUMAN_FEEDBACK_2
            state.current_step = "request_feedback"
        
        return state
    
    except Exception as e:
        logger.error(f"Error reviewing code completeness: {str(e)}")
        state.coding_state.error = f"Error reviewing code completeness: {str(e)}"
        state.current_step = "error"
        return state


def regenerate_incomplete_files(state: OdooCodeAgentState) -> OdooCodeAgentState:
    """
    Regenerate incomplete files.

    Args:
        state: The current agent state

    Returns:
        Updated agent state
    """
    logger.info("Regenerating incomplete files")
    
    try:
        # Get the incomplete files
        incomplete_files = state.coding_state.incomplete_files
        
        if not incomplete_files:
            logger.warning("No incomplete files to regenerate")
            state.coding_state.review_complete = True
            state.phase = AgentPhase.HUMAN_FEEDBACK_2
            state.current_step = "request_feedback"
            return state
        
        # Use Gemini to regenerate the files if available
        if state.use_gemini:
            logger.info("Using Gemini to regenerate incomplete files")
            gemini_client = GeminiClient()
            
            # Process each incomplete file
            for incomplete_file in incomplete_files:
                file_type = incomplete_file.get("file_type", "")
                path = incomplete_file.get("path", "")
                reason = incomplete_file.get("reason", "")
                
                logger.info(f"Regenerating {file_type} file: {path}")
                
                # Create a prompt for regenerating the file
                prompt = create_regeneration_prompt(state, incomplete_file)
                
                # Generate the file content
                new_content = gemini_client.generate_text(prompt, temperature=0.2)
                
                if not new_content:
                    logger.warning(f"Failed to regenerate {path}")
                    continue
                
                # Extract the content from the response
                extracted_content = extract_file_content(new_content, file_type)
                
                if not extracted_content:
                    logger.warning(f"Failed to extract content for {path}")
                    continue
                
                # Update the file in files_to_create
                for i, file in enumerate(state.coding_state.files_to_create):
                    if file.get("path") == path:
                        state.coding_state.files_to_create[i]["content"] = extracted_content
                        break
                
                # Add to regenerated files
                state.coding_state.regenerated_files.append({
                    "path": path,
                    "content": extracted_content,
                    "reason": reason
                })
                
                # Add to history
                state.history.append(f"Regenerated {file_type} file: {path}")
        
        # Mark review as complete
        state.coding_state.review_complete = True
        
        # Transition to human feedback
        state.phase = AgentPhase.HUMAN_FEEDBACK_2
        state.current_step = "request_feedback"
        
        return state
    
    except Exception as e:
        logger.error(f"Error regenerating incomplete files: {str(e)}")
        state.coding_state.error = f"Error regenerating incomplete files: {str(e)}"
        state.current_step = "error"
        return state


def create_regeneration_prompt(state: OdooCodeAgentState, incomplete_file: Dict[str, Any]) -> str:
    """
    Create a prompt for regenerating an incomplete file.

    Args:
        state: The current agent state
        incomplete_file: The incomplete file information

    Returns:
        Prompt for regenerating the file
    """
    file_type = incomplete_file.get("file_type", "")
    path = incomplete_file.get("path", "")
    reason = incomplete_file.get("reason", "")
    content = incomplete_file.get("content", "")
    
    # Get module information
    module_name = state.coding_state.module_name
    
    # Base prompt
    prompt = f"""
    You are an expert Odoo 18 developer. I need you to generate a complete and functional {file_type} file for an Odoo module.
    
    Module name: {module_name}
    File path: {path}
    
    The current file is incomplete or has issues: {reason}
    
    Current content:
    ```
    {content}
    ```
    
    Please generate a complete and functional version of this file that follows Odoo 18 best practices.
    
    IMPORTANT:
    1. Generate ONLY the file content, no explanations or markdown
    2. Ensure the file is complete and properly formatted
    3. Follow Odoo 18 coding standards
    4. Include proper XML declaration and <odoo> root element for XML files
    5. Include proper module definition for JavaScript files
    """
    
    # Add specific instructions based on file type
    if file_type == "xml":
        # Extract the view type from the path
        view_type = "form"
        if "tree" in path or "list" in path:
            view_type = "list"
        elif "kanban" in path:
            view_type = "kanban"
        elif "search" in path:
            view_type = "search"
        
        prompt += f"""
        6. This is a {view_type} view XML file
        7. Use the <chatter/> tag for form views if the model inherits mail.thread
        8. Use 'list' instead of 'tree' for list views (Odoo 18 standard)
        9. Avoid deprecated 'attrs' in favor of 'invisible', 'readonly', etc.
        """
    
    elif file_type == "js":
        prompt += """
        6. Use proper ES6 syntax
        7. Use proper Odoo JS module definition with odoo.define
        8. Use proper imports with require
        9. Register components with Registries if applicable
        """
    
    return prompt


def extract_file_content(response: str, file_type: str) -> str:
    """
    Extract file content from the LLM response.

    Args:
        response: The LLM response
        file_type: The type of file

    Returns:
        Extracted file content
    """
    # Try to extract content from code blocks
    code_block_match = re.search(r'```(?:\w+)?\s*([\s\S]+?)\s*```', response)
    if code_block_match:
        return code_block_match.group(1).strip()
    
    # If no code block, try to extract based on file type
    if file_type == "xml":
        xml_match = re.search(r'(<\?xml[\s\S]+?</odoo>)', response)
        if xml_match:
            return xml_match.group(1).strip()
    
    elif file_type == "js":
        js_match = re.search(r'(odoo\.define[\s\S]+?\}\);)', response)
        if js_match:
            return js_match.group(1).strip()
    
    # If all else fails, return the entire response
    return response.strip()
