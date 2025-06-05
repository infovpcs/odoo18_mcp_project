#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Improved Odoo Code Generator for MCP Project

This module provides a direct, simplified approach to generating Odoo module code
using Gemini, with improved prompting and more robust extraction.
"""

import os
import re
import json
import logging
import traceback
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

# Import Gemini directly
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

try:
    class OdooCodeFile:
        """A code file that will be generated."""
        def __init__(self, path: str, content: str, language: str = "python"):
            self.path = path
            self.content = content
            self.language = language
            self.extension = self._determine_extension(path, language)
            
        def _determine_extension(self, path: str, language: str) -> str:
            """Determine the file extension based on path and language."""
            if path.endswith((".py", ".xml", ".js", ".css", ".scss")):
                return ""  # Extension already in path
            
            # Map language to extension
            extension_map = {
                "python": ".py",
                "xml": ".xml",
                "javascript": ".js",
                "css": ".css",
                "scss": ".scss",
                "html": ".html"
            }
            
            return extension_map.get(language.lower(), ".txt")
        
        def get_full_path(self) -> str:
            """Get the full path with extension."""
            return self.path + self.extension
        
        def __str__(self) -> str:
            return f"OdooCodeFile(path='{self.get_full_path()}', language='{self.language}', size={len(self.content)})"

    class OdooCodeGenerator:
        """Generator for Odoo module code."""
        
        def __init__(self, model: str = "gemini-2.0-flash", api_key: Optional[str] = None, template_dir: str = None):
            """Initialize the generator.
            
            Args:
                model: The model to use for generation
                api_key: Optional Google API key (if not provided, will use GEMINI_API_KEY env var)
                template_dir: Optional path to a directory containing template files
            """
            self.model = model or os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")
            self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
            
            if not self.api_key:
                raise ValueError("No API key provided. Set GEMINI_API_KEY environment variable or pass api_key parameter.")
            
            # Initialize Gemini
            genai.configure(api_key=self.api_key)
            self.llm = genai.GenerativeModel(self.model)
            
            # Load templates
            self.templates = self._load_templates(template_dir)
        
        def _load_templates(self, template_dir: str = None) -> Dict[str, str]:
            """Load templates for common Odoo module files.
            
            Args:
                template_dir: Optional path to a directory containing template files.
                              If not provided, uses default hardcoded templates.
            
            Returns:
                Dictionary of template strings keyed by template name.
            """
            # Default template directory if not specified
            if template_dir is None:
                template_dir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "streamlit_client", "templates", "default"
                )
            
            # Check if template directory exists
            if os.path.exists(template_dir) and os.path.isdir(template_dir):
                try:
                    templates = {}
                    # Load init template
                    init_path = os.path.join(template_dir, "__init__.py.template")
                    if os.path.exists(init_path):
                        with open(init_path, "r") as f:
                            templates["init"] = f.read()

                    # Load controllers init template
                    controllers_init_path = os.path.join(template_dir, "controllers", "__init__.py.template")
                    if os.path.exists(controllers_init_path):
                        with open(controllers_init_path, "r") as f:
                            templates["controllers_init"] = f.read()
                    # Load wizards init template
                    wizards_init_path = os.path.join(template_dir, "wizards", "__init__.py.template")
                    if os.path.exists(wizards_init_path):
                        with open(wizards_init_path, "r") as f:
                            templates["wizards_init"] = f.read()
                    # Load manifest template
                    manifest_path = os.path.join(template_dir, "__manifest__.py.template")
                    if os.path.exists(manifest_path):
                        with open(manifest_path, "r") as f:
                            templates["manifest"] = f.read()
                    
                    # Load init template
                    init_path = os.path.join(template_dir, "__init__.py")
                    if os.path.exists(init_path):
                        with open(init_path, "r") as f:
                            templates["init"] = f.read()
                    
                    # Load models init template
                    models_init_path = os.path.join(template_dir, "models", "__init__.py")
                    if os.path.exists(models_init_path):
                        with open(models_init_path, "r") as f:
                            templates["models_init"] = f.read()
                            
                    # If we successfully loaded all templates, return them
                    if all(k in templates for k in ["manifest", "init", "models_init"]):
                        print(f"DEBUG: Successfully loaded templates from {template_dir}")
                        return templates
                        
                    print(f"DEBUG: Some templates missing from {template_dir}, falling back to defaults")
                except Exception as e:
                    print(f"DEBUG: Error loading templates from {template_dir}: {e}")
                    import traceback
                    print(f"DEBUG: Traceback: {traceback.format_exc()}")
            else:
                print(f"DEBUG: Template directory {template_dir} not found, using default templates")
                
            # Fallback to hardcoded templates
            manifest_template = """# -*- coding: utf-8 -*-
{
    "name": "{module_title}",
    "version": "1.0",
    "category": "Uncategorized",
    "summary": "{summary}",
    "description": "{description}",
    "author": "Odoo MCP",
    "website": "https://www.example.com",
    "depends": {depends},
    "data": {data},
    "application": {is_app},
    "installable": True,
    "auto_install": False,
    "license": "LGPL-3"
}"""
            
            init_template = """# -*- coding: utf-8 -*-

from . import models
from . import controllers
from . import wizards
"""
            
            models_init_template = """# -*- coding: utf-8 -*-

from . import {model_imports}
"""

            controllers_init_template = """# -*- coding: utf-8 -*-

from . import {controller_imports}
"""

            wizards_init_template = """# -*- coding: utf-8 -*-

from . import {wizard_imports}
"""
            
            return {
                "manifest": manifest_template,
                "init": init_template,
                "models_init": models_init_template,
                "controllers_init": controllers_init_template,
                "wizards_init": wizards_init_template
            }
            
        async def _generate_initial_code(self, module_name: str, requirements: str, documentation: Optional[List[Dict[str, str]]]) -> Tuple[str, List[OdooCodeFile]]:
            """Generate the initial code for the module using Gemini."""
            try:
                # Prepare documentation context
                doc_str = "\nRelevant Documentation:\n\n"
                if documentation:
                    for doc in documentation:
                        doc_str += f"--- From {doc['source']} ---\n{doc['content'][:1000]}...\n\n"
            
                # Create the prompt
                prompt = f"""You are an expert Odoo 18 developer who specializes in creating high-quality,
                maintainable Odoo modules following best practices.
                
                Create a complete, functional Odoo 18 module named '{module_name}' that meets these requirements:
                
                {requirements}
                
                {doc_str}
                
                Follow these guidelines:
                1. Create a complete, functional module with all necessary files
                2. Follow Odoo 18 best practices and conventions
                3. Use modern OWL components for any JavaScript
                4. Ensure proper security with access rights and record rules
                5. Include proper docstrings and comments
                6. Ensure proper module structure
                7. Use proper naming conventions for models, fields, and methods
                
                Apply Odoo 18 best practices:
                - Use 'list' view instead of 'tree' view in XML definitions.
                - Replace deprecated 'attrs' tag with its related alternative.
                - Use the simplified `<chatter/>` tag for chatter functionality (e.g., `<chatter/>` instead of the full div structure).
                - Do not include `__init__.py` in the directory structure; it will be added by default.

                Provide your response by listing each file with a markdown header specifying the file path, followed by the complete file content in a code block.
                                
                Example format:
                
                # /path/to/file.py
                ```python
                # File content here
                ```
                
                # /path/to/another_file.xml
                ```xml
                <!-- File content here -->
                ```
                """
                
                # Generate response using Gemini directly
                response = self.llm.generate_content(prompt)
                
                if response and hasattr(response, 'text'):
                    logger.debug(f"Raw generation response:\n{response.text[:500]}...")
                    
                    # Extract the files from the response
                    files = self._extract_files_from_response(response.text, module_name)
                    
                    # Generate a summary
                    summary = f"Generated Odoo module '{module_name}' with {len(files)} files"
                    
                    return summary, files
                else:
                    logger.error("Failed to get response from Gemini")
                    return "Generation failed", []
            except Exception as e:
                logger.error(f"Error generating initial code: {str(e)}")
            return f"Error: {str(e)}", []

        def _extract_files_from_response(self, response: str, module_name: str) -> List[OdooCodeFile]:
            """Extract file paths and content from the LLM response.
            
            Args:
                response: The raw response from the LLM
                module_name: The name of the module being generated
                
            Returns:
                A list of OdooCodeFile objects
            """
            files = []
            
            # Pattern to match markdown headers with file paths and code blocks
            # This handles both formats:
            # # /path/to/file.py
            # ```python
            # code
            # ```
            # OR
            # # `/path/to/file.py`
            # ```python
            # code
            # ```
            pattern = r'#\s+(?:`?([^`\n]+)`?|([^\n]+))\s*```([a-z]*)\n([\s\S]*?)```'
            
            matches = re.finditer(pattern, response)
            
            for match in matches:
                # Get the file path (either from group 1 or 2)
                file_path = match.group(1) if match.group(1) else match.group(2)
                file_path = file_path.strip()
                
                # Clean up the path - remove any leading/trailing quotes or backticks
                file_path = file_path.strip('\'"` ')
                
                # Get the language and content
                language = match.group(3) or ""  # Default to empty string if no language specified
                content = match.group(4)
                
                # Normalize the file path
                if file_path.startswith("/"):
                    # Remove leading slash
                    file_path = file_path[1:]
                
                # If the path doesn't start with the module name, add it
                if not file_path.startswith(module_name + "/") and not file_path.startswith(module_name + "\\"):
                    file_path = f"{module_name}/{file_path}"
                
                # Create the OdooCodeFile object
                code_file = OdooCodeFile(file_path, content, language)
                files.append(code_file)
                
                logger.debug(f"Extracted file: {code_file}")
            
            return files
        
        async def _validate_and_enhance_code(self, module_name: str, requirements: str, files: List[OdooCodeFile], documentation: Optional[List[Dict[str, str]]]) -> List[OdooCodeFile]:
            """Validate and enhance the generated code using Gemini."""
            try:
                logger.info(f"Validating and enhancing code for module '{module_name}'")
            
                # Prepare documentation context
                doc_str = "\nRelevant Documentation:\n\n"
                if documentation:
                    for doc in documentation:
                        doc_str += f"--- From {doc['source']} ---\n{doc['content'][:1000]}...\n\n"
                    
                # Prepare files context
                files_str = ""
                for file in files:
                    files_str += f"\n# {file.get_full_path()}\n```{file.language}\n{file.content}\n```\n"
                    
                # Create the prompt
                prompt = f"""Review and improve the following Odoo 18 module named '{module_name}' that should meet these requirements:
            
                {requirements}
            
                {doc_str}
            
                Here are the current files:
            
                {files_str}
            
                Provide your improvements by listing each file that needs changes. For each file, start with a markdown header specifying the file path, then include the COMPLETE updated file content in a code block.
            
                Example format:
            
                # /path/to/file.py
                ```python
                # Updated file content here (complete file, not just the changes)
                ```
            
                # /path/to/another_file.xml
                ```xml
                <!-- Updated file content here (complete file, not just the changes) -->
                ```
            
                If a file is missing and should be added, include it in your response.
                If a file is fine as is, you don't need to include it in your response.
            
                Before each file, briefly explain what issues you found and how you fixed them.
                """
            
                # Generate response using Gemini directly
                response = self.llm.generate_content(prompt)
                
                if response and hasattr(response, 'text'):
                    logger.debug(f"Raw validation response:\n{response.text[:500]}...")
                    
                    # Extract the updated files
                    updated_files = self._extract_files_from_response(response.text, module_name)
                    
                    # Merge the updated files with the original files
                    return self._merge_files(files, updated_files)
                else:
                    logger.error("Failed to get response from Gemini")
                    return files
            except Exception as e:
                logger.error(f"Error validating code: {str(e)}")
                # Return the original files if validation fails
                return files
        
        def _merge_files(self, original_files: List[OdooCodeFile], updated_files: List[OdooCodeFile]) -> List[OdooCodeFile]:
            """Merge original files with updated files, preferring updated versions.
            
            Args:
                original_files: The original list of files
                updated_files: The updated list of files
                
            Returns:
                A merged list of files
            """
            # Create a dictionary of original files for easy lookup
            original_dict = {f.get_full_path(): f for f in original_files}
            
            # Create a dictionary for the result
            result_dict = original_dict.copy()
            
            # Update with the new files
            for updated_file in updated_files:
                result_dict[updated_file.get_full_path()] = updated_file
            
            return list(result_dict.values())
        
        def _format_manifest(self, module_name: str, module_title: str, summary: str, description: str, 
            depends: List[str], data_files: List[str], is_app: bool = False) -> str:
            """Format the __manifest__.py file content.
            
            Args:
                module_name: The technical name of the module
                module_title: The display name of the module
                summary: A short summary of the module
                description: A longer description of the module
                depends: List of module dependencies
                data_files: List of data files to include
                is_app: Whether this module is a standalone application
                
            Returns:
                The formatted manifest content
            """
            # Format the description with proper indentation for the manifest
            description_lines = description.strip().split('\n')
            indented_description = '\n'.join([f'    {line}' if line.strip() else line for line in description_lines])
            
            # Format the depends and data lists
            depends_str = json.dumps(depends, indent=4)
            data_str = json.dumps(data_files, indent=4)
            
            # Check if the template uses Jinja2-style templating
            if '{{' in self.templates["manifest"]:
                # Use a simple replacement for Jinja2 templates
                manifest = self.templates["manifest"]
                manifest = manifest.replace("{{ name|pascal }}", module_title)
                manifest = manifest.replace("{{ name|snake }}", module_name)
                
                # Replace the depends and data sections
                manifest = re.sub(r"'depends': \[.*?\],", f"'depends': {depends_str},", manifest, flags=re.DOTALL)
                manifest = re.sub(r"'data': \[.*?\],", f"'data': {data_str},", manifest, flags=re.DOTALL)
                
                # Replace application flag
                manifest = re.sub(r"'application': (?:True|False),", f"'application': {str(is_app).lower()},", manifest)
                
                # Replace summary and description
                manifest = re.sub(r"'summary': '.*?',", f"'summary': '{summary}',", manifest)
                manifest = re.sub(r"'description': '''.*?''',", f"'description': '''{indented_description}''',", manifest, flags=re.DOTALL)
                
                return manifest
            else:
                # Use string.format for our hardcoded template
                return self.templates["manifest"].format(
                    module_title=module_title,
                    summary=summary,
                    description=indented_description,
                    depends=depends_str,
                    data=data_str,
                    is_app=str(is_app).lower()
                )
        
        def _format_models_init(self, model_files: List[str]) -> str:
            """Format the models/__init__.py file content.
            
            Args:
                model_files: List of model file names (without .py extension)
                
            Returns:
                The formatted models/__init__.py content
            """
            model_imports = ', '.join(model_files)
            return self.templates["models_init"].format(model_imports=model_imports)
        
        def _save_files_to_disk(self, files: List[OdooCodeFile], output_dir: str) -> None:
            """Save the generated files to disk.
            
            Args:
                files: List of OdooCodeFile objects
                output_dir: Base directory to save files to
            """
            for file in files:
                # Get the full path
                full_path = os.path.join(output_dir, file.get_full_path())
                
                # Create the directory if it doesn't exist
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write the file
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(file.content)
                
                logger.info(f"Saved file: {full_path}")
        
        async def generate_odoo_module(self, module_name: str, requirements: str, 
                                     documentation: Optional[List[Dict[str, str]]] = None,
                                     save_to_disk: bool = True, output_dir: str = "./generated_modules",
                                     validation_iterations: int = 2) -> Dict[str, Any]:
            """Generate a complete Odoo module based on requirements.
            
            Args:
                module_name: The technical name of the module (snake_case)
                requirements: A detailed description of what the module should do
                documentation: Optional list of documentation references to include
                save_to_disk: Whether to save the generated files to disk
                output_dir: Directory to save the files to (if save_to_disk is True)
                validation_iterations: Number of iterations for validation and enhancement
                
            Returns:
                A dictionary containing the generated files and metadata
            """
            try:
                # Generate the initial code
                response, files = await self._generate_initial_code(module_name, requirements, documentation)
                
                # Validate and enhance the code
                for i in range(validation_iterations):
                    logger.info(f"Validation iteration {i+1}/{validation_iterations}")
                    files = await self._validate_and_enhance_code(module_name, requirements, files, documentation)
                
                # Save the files to disk if requested
                if save_to_disk:
                    self._save_files_to_disk(files, output_dir)
                
                # Prepare the result
                result = {
                    "module_name": module_name,
                    "requirements": requirements,
                    "files": [{
                        "path": f.get_full_path(),
                        "content": f.content,
                        "language": f.language
                    } for f in files],
                    "file_count": len(files)
                }
                
                return result
            except Exception as e:
                logger.error(f"Error generating module: {str(e)}")
                raise

    # Utility function for direct use
    async def generate_odoo_module(module_name: str, requirements: str, documentation: Optional[List[Dict[str, str]]] = None,
                                  save_to_disk: bool = True, output_dir: str = "./generated_modules",
                                  max_validation_iterations: int = 2) -> Dict[str, Any]:
        """Generate a complete Odoo module based on requirements.

        Args:
            module_name: The technical name of the module (snake_case)
            requirements: A detailed description of what the module should do
            documentation: Optional list of documentation references to include
            save_to_disk: Whether to save the generated files to disk
            output_dir: Directory to save the files to (if save_to_disk is True)
            max_validation_iterations: Maximum number of iterations for validation and enhancement

        Returns:
            A dictionary containing the generated files and metadata
        """
        generator = OdooCodeGenerator(template_dir=os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "streamlit_client", "templates", "default"
        ))
        
        try:
            # Generate the module files with validation
            files = await generator.generate_odoo_module(
                module_name=module_name,
                requirements=requirements,
                documentation=documentation,
                save_to_disk=save_to_disk,
                output_dir=output_dir,
                validation_iterations=max_validation_iterations
            )
            
            return files
        except Exception as e:
            logger.error(f"Error in generate_odoo_module: {str(e)}")
            raise

    # Validation wrapper function
    async def generate_odoo_module_with_validation(module_name: str, requirements: str, 
                                                documentation: Optional[List[Dict[str, str]]] = None,
                                                save_to_disk: bool = True, output_dir: str = "./generated_modules") -> Dict[str, Any]:
        """Generate an Odoo module with additional validation steps.

        This function adds extra validation to ensure the generated module meets quality standards.

        Args:
            module_name: The technical name of the module (snake_case)
            requirements: A detailed description of what the module should do
            documentation: Optional list of documentation references to include
            save_to_disk: Whether to save the generated files to disk
            output_dir: Directory to save the files to (if save_to_disk is True)

        Returns:
            A dictionary containing the generated files and metadata
        """
        # Validate module name
        if not re.match(r'^[a-z][a-z0-9_]*$', module_name):
            raise ValueError(f"Invalid module name: {module_name}. Module names must be lowercase, start with a letter, and contain only letters, numbers, and underscores.")
        
        # Generate the module
        return await generate_odoo_module(
            module_name=module_name,
            requirements=requirements,
            documentation=documentation,
            save_to_disk=save_to_disk,
            output_dir=output_dir,
            max_validation_iterations=2
        )

    # Main function for testing
    async def main():
        # Test the generator
        module_name = "test_module"
        requirements = """Create a simple Odoo module that manages a library of books. 
        The module should allow users to add, edit, and delete books. 
        Each book should have a title, author, ISBN, publication date, and genre.
        Users should be able to search and filter books by these attributes.
        The module should also track book borrowing - who borrowed a book and when it's due to be returned.
        """
        
        result = await generate_odoo_module_with_validation(
            module_name=module_name,
            requirements=requirements,
            save_to_disk=True,
            output_dir="./generated_modules"
        )
        
        print(f"Generated module '{module_name}' with {result['file_count']} files")

    # Run the main function if this file is executed directly
    if __name__ == "__main__":
        asyncio.run(main())

except Exception as e:
    print(f"ERROR in odoo_code_generator.py: {str(e)}")
    traceback.print_exc()

    async def improved_generate_odoo_module(self, module_name: str, requirements: str, documentation: Optional[List[Dict[str, str]]] = None, timeout: int = 180) -> Tuple[str, List[OdooCodeFile]]:
        """Generate an Odoo module with improved prompting and validation.
        
        Args:
            module_name: The name of the module to generate
            requirements: The requirements for the module
            documentation: Optional list of relevant documentation
            timeout: Timeout in seconds (default: 180)
            
        Returns:
            A tuple of (summary, list of files)
        """
        try:
            # Create an asyncio task for the generation
            task = asyncio.create_task(self._generate_initial_code(module_name, requirements, documentation))
            
            # Wait for the task with timeout
            summary, files = await asyncio.wait_for(task, timeout=timeout)
            
            # Validate and enhance the generated code
            files = await self._validate_and_enhance_code(module_name, requirements, files, documentation)
            
            return summary, files
        except asyncio.TimeoutError:
            logger.error(f"Timeout generating module '{module_name}' after {timeout} seconds")
            raise TimeoutError(f"Module generation timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"Error generating module '{module_name}': {str(e)}")
            raise
