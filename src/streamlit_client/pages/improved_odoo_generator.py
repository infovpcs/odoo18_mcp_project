#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Improved Odoo Generator Page for Streamlit Client

This module provides a clean interface for the improved Odoo code generator
that integrates with DeepWiki for better documentation and context handling.
"""

import logging
import streamlit as st
import json
import base64
import io
import os
import re
import time
import hashlib
import zipfile
from typing import Dict, List, Optional, Any, Union

from ..utils.mcp_connector import MCPConnector
from ..utils.session_state import SessionState

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("improved_odoo_generator_page")

# Helper functions for string case conversion
def snake_case(text):
    """Convert a string to snake_case."""
    # Replace non-alphanumeric characters with spaces
    s1 = re.sub(r'[^\w\s]', ' ', str(text))
    # Replace sequences of spaces with a single space
    s1 = re.sub(r'\s+', ' ', s1).strip().lower()
    # Replace spaces with underscores
    return re.sub(r'\s+', '_', s1)

def title_case(text):
    """Convert a string to Title Case."""
    # Replace underscores and hyphens with spaces
    s = re.sub(r'[_-]', ' ', str(text))
    # Capitalize each word
    return ' '.join(word.capitalize() for word in s.split())

def create_zip_download(files):
    """Create a ZIP file from a list of file dictionaries."""
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file in files:
            file_path = file.get('path', '')
            file_content = file.get('content', '')
            
            # Add the file to the ZIP archive
            zip_file.writestr(file_path, file_content)
    
    # Reset the buffer position to the beginning
    zip_buffer.seek(0)
    return zip_buffer

def render_improved_odoo_generator_page(session_state: SessionState, mcp_connector: MCPConnector) -> None:
    """Render the improved Odoo generator page.

    Args:
        session_state: Session state
        mcp_connector: MCP connector
    """
    st.title("Improved Odoo Module Generator")
    
    # Description of the page
    st.markdown("""
    ### Generate high-quality Odoo 18 modules with AI
    
    This advanced generator uses:
    - DeepWiki integration for better documentation context
    - Enhanced code structure with proper Odoo 18 best practices
    - Improved prompt engineering for better quality code
    """)
    
    # Initialize session state for improved generator if not present
    if not hasattr(session_state, "improved_generator"):
        session_state.improved_generator = type('', (), {})()
        session_state.improved_generator.module_name = ""
        session_state.improved_generator.requirements = ""
        session_state.improved_generator.documentation = []
        session_state.improved_generator.save_to_disk = True
        session_state.improved_generator.output_dir = "./generated_modules"
        session_state.improved_generator.result = None
        session_state.improved_generator.is_generating = False
        session_state.improved_generator.generation_complete = False
    
    # Main layout with two columns
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Module requirements input
        requirements = st.text_area(
            "Module Requirements",
            value=session_state.improved_generator.requirements,
            height=150,
            placeholder="Describe the Odoo module you want to create in detail...",
            help="Provide detailed requirements for your Odoo module. Include features, fields, views, and functionality."
        )
        session_state.improved_generator.requirements = requirements
        
        # Documentation sources
        with st.expander("Add Documentation Context (Optional)", expanded=False):
            st.markdown("""
            Add documentation snippets or references to provide additional context for the code generator.
            This can improve code quality by providing domain-specific knowledge.
            """)
            
            # Display existing documentation
            if session_state.improved_generator.documentation:
                st.markdown("### Current Documentation Sources")
                for i, doc in enumerate(session_state.improved_generator.documentation):
                    with st.container():
                        col_a, col_b = st.columns([4, 1])
                        with col_a:
                            st.markdown(f"**Source**: {doc.get('source', 'Unknown')}")
                            st.text_area(
                                f"Content {i+1}",
                                value=doc.get('content', ''),
                                height=100,
                                key=f"doc_content_{i}",
                                disabled=True
                            )
                        with col_b:
                            if st.button("Remove", key=f"remove_doc_{i}"):
                                session_state.improved_generator.documentation.pop(i)
                                st.rerun()
            
            # Add new documentation
            st.markdown("### Add New Documentation")
            new_doc_source = st.text_input(
                "Documentation Source",
                placeholder="e.g., Odoo 18 Documentation, External API, etc.",
                key="new_doc_source"
            )
            
            new_doc_content = st.text_area(
                "Documentation Content",
                placeholder="Paste relevant documentation here...",
                height=150,
                key="new_doc_content"
            )
            
            if st.button("Add Documentation"):
                if new_doc_source and new_doc_content:
                    session_state.improved_generator.documentation.append({
                        "source": new_doc_source,
                        "content": new_doc_content
                    })
                    st.success("Documentation added successfully!")
                    # Clear the inputs
                    st.session_state.new_doc_source = ""
                    st.session_state.new_doc_content = ""
                    st.rerun()
                else:
                    st.warning("Please provide both source and content for the documentation.")
    
    with col2:
        st.subheader("Module Settings")
        
        # Module name input
        module_name = st.text_input(
            "Module Name",
            value=session_state.improved_generator.module_name,
            placeholder="e.g., my_module",
            help="Technical name for the module (use snake_case)"
        )
        
        # Validate and convert module name to snake_case
        if module_name:
            module_name = snake_case(module_name)
            
        session_state.improved_generator.module_name = module_name
        
        # Options
        st.subheader("Generation Options")
        
        save_to_disk = st.checkbox(
            "Save to Server Disk", 
            value=session_state.improved_generator.save_to_disk,
            help="Save generated files to disk on the server"
        )
        session_state.improved_generator.save_to_disk = save_to_disk
        
        output_dir = st.text_input(
            "Output Directory",
            value=session_state.improved_generator.output_dir,
            help="Directory to save the generated files on the server"
        )
        session_state.improved_generator.output_dir = output_dir
        
        # Add option for validation iterations
        validation_iterations = st.slider(
            "Validation Iterations",
            min_value=0,
            max_value=5,
            value=getattr(session_state.improved_generator, "validation_iterations", 2),
            step=1,
            help="Number of validation and refinement loops (0 to disable, 2-3 recommended for complex modules)"
        )
        session_state.improved_generator.validation_iterations = validation_iterations
        
        # Add info about validation iterations
        if validation_iterations > 0:
            st.info(f"Using {validation_iterations} validation iteration{'s' if validation_iterations > 1 else ''}. This helps ensure all requirements are fully implemented, especially for complex modules.")
        else:
            st.warning("Validation disabled. For complex requirements like car sales modules, 2-3 validation iterations are recommended.")
    
    # Generation button
    if st.button("Generate Odoo Module", type="primary", disabled=session_state.improved_generator.is_generating):
        if not module_name:
            st.error("Please provide a module name.")
            return
            
        if not requirements:
            st.error("Please provide module requirements.")
            return
        
        # Update session state
        session_state.improved_generator.module_name = module_name
        session_state.improved_generator.requirements = requirements
        session_state.improved_generator.is_generating = True
        session_state.improved_generator.generation_complete = False
        
        # Show a spinner while generating
        with st.spinner("Generating Odoo module... This may take a minute or two."):
            try:
                # Call the improved Odoo module generator via MCP with increased timeout
                result = mcp_connector.call_tool(
                    "improved_generate_odoo_module",
                    {
                        "module_name": module_name,
                        "requirements": requirements,
                        "documentation": session_state.improved_generator.documentation if session_state.improved_generator.documentation else None,
                        "save_to_disk": save_to_disk,
                        "output_dir": output_dir,
                        "validation_iterations": session_state.improved_generator.validation_iterations
                    }
                )
                
                # Store the result in session state
                session_state.improved_generator.result = result
                session_state.improved_generator.generation_complete = True
                
            except Exception as e:
                error_msg = str(e)
                st.error(f"Error during module generation: {error_msg}")
                
                # Check if files were still generated despite the timeout
                if "timeout" in error_msg.lower():
                    st.warning("The operation timed out, but files may have been generated. Checking generated files...")
                    
                    # Check the output directory for generated files
                    module_path = os.path.join(output_dir, module_name)
                    if os.path.exists(module_path):
                        try:
                            # Get list of generated files
                            generated_files = []
                            for root, _, files in os.walk(module_path):
                                for file in files:
                                    file_path = os.path.join(root, file)
                                    rel_path = os.path.relpath(file_path, module_path)
                                    with open(file_path, 'r') as f:
                                        content = f.read()
                                    generated_files.append({
                                        "path": rel_path,
                                        "content": content
                                    })
                            
                            if generated_files:
                                # Create a success result with the found files
                                result = {
                                    "success": True,
                                    "result": {
                                        "files": generated_files,
                                        "save_result": {
                                            "path": module_path,
                                            "success": True
                                        }
                                    }
                                }
                                session_state.improved_generator.result = result
                                session_state.improved_generator.generation_complete = True
                                st.success(f"Found {len(generated_files)} generated files!")
                                
                        except Exception as read_error:
                            logger.error(f"Error reading generated files: {str(read_error)}")
                            st.error("Could not read the generated files.")
                
                logger.error(f"Error generating Odoo module: {str(e)}", exc_info=True)
            finally:
                # Reset the generating flag
                session_state.improved_generator.is_generating = False
    
    # Display generation results if available
    if session_state.improved_generator.generation_complete and session_state.improved_generator.result:
        st.markdown("---")
        st.header("Generation Results")
        
        result = session_state.improved_generator.result
        success = result.get("success", False)
        
        if success:
            # Extract the result data - handle different result formats
            if isinstance(result.get("result"), dict):
                # Direct result object
                data = result.get("result", {})
            elif isinstance(result.get("result"), str):
                # JSON string result
                try:
                    data = json.loads(result.get("result", "{}"))
                except:
                    data = {"message": result.get("result", "")}
            else:
                data = {}
            
            # Show success message
            st.success(f"Successfully generated Odoo module: {module_name}")
            
            # Create tabs for different views
            files_tab, download_tab = st.tabs(["Files", "Download"])
            
            with files_tab:
                # Get the files from the result
                files = data.get("files", [])
                
                if not files:
                    st.warning("No files were generated.")
                    return
                
                # Group files by type for better organization
                file_groups = {
                    "Main Files": [],  # __init__.py, __manifest__.py
                    "Models": [],      # model files
                    "Views": [],       # view files
                    "Security": [],    # security files
                    "Data": [],        # data files
                    "Reports": [],     # report files
                    "Static": [],      # static files
                    "Other": []        # other files
                }
                
                for file in files:
                    file_path = file.get("path", "")
                    
                    if file_path in ["__init__.py", "__manifest__.py"]:
                        file_groups["Main Files"].append(file)
                    elif "models/" in file_path:
                        file_groups["Models"].append(file)
                    elif "views/" in file_path:
                        file_groups["Views"].append(file)
                    elif "security/" in file_path:
                        file_groups["Security"].append(file)
                    elif "data/" in file_path:
                        file_groups["Data"].append(file)
                    elif "reports/" in file_path:
                        file_groups["Reports"].append(file)
                    elif "static/" in file_path:
                        file_groups["Static"].append(file)
                    else:
                        file_groups["Other"].append(file)
                
                # Display files by group with improved organization
                for group_name, group_files in file_groups.items():
                    if not group_files:
                        continue
                    
                    st.markdown(f"### {group_name}")
                    for file in sorted(group_files, key=lambda x: x.get("path", "")):
                        file_path = file.get("path", "")
                        file_content = file.get("content", "")
                        
                        # Determine language for syntax highlighting
                        extension = file_path.split(".")[-1] if "." in file_path else ""
                        language = {
                            "py": "python",
                            "xml": "xml",
                            "js": "javascript",
                            "css": "css",
                            "scss": "scss",
                            "json": "json",
                            "md": "markdown"
                        }.get(extension, "text")
                        
                        # Create an expander with icon based on file type
                        icon = {
                            "py": "🐍",
                            "xml": "📄",
                            "js": "📜",
                            "css": "🎨",
                            "json": "📋",
                            "md": "📝"
                        }.get(extension, "📎")
                        
                        with st.expander(f"{icon} {file_path}"):
                            # Show file metadata
                            st.markdown(f"**Type:** {language.capitalize()}")
                            st.markdown(f"**Size:** {len(file_content)} bytes")
                            
                            # Code display with copy button
                            st.code(file_content, language=language)
                            
                            # File actions in columns
                            col1, col2 = st.columns([1, 4])
                            with col1:
                                # Download individual file
                                st.download_button(
                                    label="📥 Download",
                                    data=file_content,
                                    file_name=file_path.split("/")[-1],
                                    mime="text/plain",
                                    key=f"file_download_{hashlib.md5(file_path.encode()).hexdigest()[:8]}"
                                )
                            with col2:
                                if file_path.endswith(".py"):
                                    st.markdown("📌 *Python module with Odoo models/fields*")
                                elif file_path.endswith(".xml"):
                                    st.markdown("📌 *XML file with views/data definitions*")
                                elif file_path == "__manifest__.py":
                                    st.markdown("📌 *Module manifest with metadata*")
                                elif file_path == "__init__.py":
                                    st.markdown("📌 *Module initializer*")
            
            with download_tab:
                st.markdown("### Download Complete Module")
                
                # Get the files from the result
                files = data.get("files", [])
                
                if not files:
                    st.warning("No files were generated.")
                    return
                
                # Create a ZIP file with all generated files
                zip_buffer = create_zip_download(files)
                
                # Add module banner
                st.markdown(f"""
                ### 📦 {title_case(module_name)}
                Ready to download your generated Odoo module with the following structure:
                """)
                
                # Display module structure
                structure = {}
                for file in files:
                    path = file.get("path", "")
                    parts = path.split("/")
                    current = structure
                    for part in parts[:-1]:
                        current = current.setdefault(part, {})
                    current[parts[-1]] = "file"
                
                def display_structure(struct, indent=0):
                    for key, value in sorted(struct.items()):
                        if value == "file":
                            st.markdown(f"{'  ' * indent}📄 `{key}`")
                        else:
                            st.markdown(f"{'  ' * indent}📁 `{key}/`")
                            display_structure(value, indent + 1)
                
                display_structure(structure)
                
                # Module statistics
                st.markdown("### 📊 Module Statistics")
                col1, col2 = st.columns(2)
                
                with col1:
                    # Count files by type
                    file_types = {}
                    for file in files:
                        file_path = file.get("path", "")
                        extension = file_path.split(".")[-1] if "." in file_path else "unknown"
                        file_types[extension] = file_types.get(extension, 0) + 1
                    
                    st.markdown("#### File Types:")
                    for ext, count in sorted(file_types.items()):
                        st.markdown(f"- `.{ext}` files: {count}")
                
                with col2:
                    # Module information
                    st.markdown("#### Module Info:")
                    st.markdown(f"- **Total Files:** {len(files)}")
                    total_size = sum(len(f.get("content", "")) for f in files)
                    st.markdown(f"- **Total Size:** {total_size/1024:.1f} KB")
                    st.markdown(f"- **Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Download section with prominent button
                st.markdown("### 📥 Download Module")
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.download_button(
                        label=f"Download {module_name}.zip",
                        data=zip_buffer,
                        file_name=f"{module_name}.zip",
                        mime="application/zip",
                        key=f"module_download_{module_name}",
                        help="Download all generated files as a ZIP archive"
                    )
                
                with col2:
                    if save_to_disk:
                        save_result = data.get("save_result", {})
                        save_path = save_result.get("path", "Unknown")
                        st.info(f"💾 Module also saved to server at: `{save_path}`")
        else:
            # Show error message
            error_msg = result.get("error", "Unknown error")
            st.error(f"Error generating Odoo module: {error_msg}")
            
            # Show detailed error information in an expander
            with st.expander("Error Details"):
                st.json(result)
