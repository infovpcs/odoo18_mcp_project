#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Session State Management for Streamlit Client

This module provides session state management for the Streamlit client.
"""

import json
import logging
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import streamlit as st

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("session_state")

class AgentPhase(str, Enum):
    """Phase of operation for the agent flow."""
    ANALYSIS = "analysis"
    PLANNING = "planning"
    HUMAN_FEEDBACK_1 = "human_feedback_1"
    CODING = "coding"
    CODE_REVIEW = "code_review"
    HUMAN_FEEDBACK_2 = "human_feedback_2"
    FINALIZATION = "finalization"

@dataclass
class CodeAgentState:
    """State for the code agent."""
    query: str = ""
    phase: AgentPhase = AgentPhase.ANALYSIS
    plan: str = ""
    tasks: List[Union[str, Dict[str, Any]]] = field(default_factory=list)
    technical_considerations: List[str] = field(default_factory=list)  # Technical considerations for the module
    estimated_time: str = ""  # Estimated time for implementation
    module_name: str = ""
    files_to_create: Dict[str, str] = field(default_factory=dict)
    feedback: str = ""
    history: List[str] = field(default_factory=list)
    error: Optional[str] = None
    use_gemini: bool = False
    use_ollama: bool = False
    no_llm: bool = False  # Whether to disable all LLM models and use fallback analysis only
    save_to_files: bool = False
    output_dir: Optional[str] = None
    state_dict: Optional[Dict[str, Any]] = None  # Serialized state from the agent for resuming later
    requires_validation: bool = False  # Whether the agent is waiting for validation
    current_step: Optional[str] = None  # Current step in the agent workflow
    planning_state: Optional[Dict[str, Any]] = None  # Raw planning state from the agent
    analysis_state: Optional[Dict[str, Any]] = None  # Raw analysis state from the agent
    model_info: Dict[str, Any] = field(default_factory=dict)  # Information about relevant Odoo models
    detailed_model_info: Dict[str, Any] = field(default_factory=dict)  # Detailed information about Odoo models
    analysis_result: Optional[Dict[str, Any]] = None  # Result of the analysis phase
    proposed_models: List[Dict[str, Any]] = field(default_factory=list)  # Models proposed for the module
    incomplete_files: List[Dict[str, Any]] = field(default_factory=list)  # Files that need to be regenerated
    regenerated_files: List[Dict[str, Any]] = field(default_factory=list)  # Files that have been regenerated
    review_complete: bool = False  # Whether the code review is complete

@dataclass
class ExportImportState:
    """State for export/import operations."""
    model_name: str = ""
    fields: List[str] = field(default_factory=list)
    filter_domain: str = ""
    limit: int = 1000
    export_path: str = "/tmp/export.csv"
    input_path: str = "/tmp/import.csv"
    field_mapping: str = ""
    parent_field_mapping: str = ""
    child_field_mapping: str = ""
    create_if_not_exists: bool = True
    update_if_exists: bool = True
    parent_model: str = ""
    child_model: str = ""
    relation_field: str = ""
    parent_fields: List[str] = field(default_factory=list)
    child_fields: List[str] = field(default_factory=list)
    move_type: Optional[str] = None

@dataclass
class DocumentationState:
    """State for documentation retrieval."""
    query: str = ""
    max_results: int = 5
    results: List[Dict[str, Any]] = field(default_factory=list)
    raw_results: str = ""
    use_gemini: bool = True
    use_online_search: bool = True

    def get(self, key: str, default: Any = None) -> Any:
        """Get an attribute value by key with a default fallback.

        Args:
            key: The attribute name to get
            default: Default value if the attribute doesn't exist

        Returns:
            The attribute value or default
        """
        return getattr(self, key, default)

@dataclass
class ChatMessage:
    """Chat message."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str = ""

@dataclass
class ChatState:
    """State for chat."""
    messages: List[ChatMessage] = field(default_factory=list)
    current_message: str = ""

class SessionState:
    """Session state for the Streamlit client."""

    def __init__(self):
        """Initialize the session state."""
        # Initialize session state if not already initialized
        if 'initialized' not in st.session_state:
            st.session_state.initialized = True
            st.session_state.code_agent = CodeAgentState()
            st.session_state.export_import = ExportImportState()
            st.session_state.documentation = DocumentationState()
            st.session_state.chat = ChatState()
            st.session_state.mcp_server_url = "http://localhost:8001"
            st.session_state.current_page = "code_agent"
            st.session_state.deepwiki_documentation = ""
            st.session_state.last_generated_graph = ""
            st.session_state.last_mermaid_code = ""
            logger.info("Session state initialized")

    @property
    def code_agent(self) -> CodeAgentState:
        """Get the code agent state.

        Returns:
            Code agent state
        """
        return st.session_state.code_agent

    @property
    def export_import(self) -> ExportImportState:
        """Get the export/import state.

        Returns:
            Export/import state
        """
        return st.session_state.export_import

    @property
    def documentation(self) -> DocumentationState:
        """Get the documentation state.

        Returns:
            Documentation state
        """
        return st.session_state.documentation

    @property
    def chat(self) -> ChatState:
        """Get the chat state.

        Returns:
            Chat state
        """
        return st.session_state.chat

    @property
    def mcp_server_url(self) -> str:
        """Get the MCP server URL.

        Returns:
            MCP server URL
        """
        return st.session_state.mcp_server_url

    @mcp_server_url.setter
    def mcp_server_url(self, value: str):
        """Set the MCP server URL.

        Args:
            value: MCP server URL
        """
        st.session_state.mcp_server_url = value

    @property
    def current_page(self) -> str:
        """Get the current page.

        Returns:
            Current page
        """
        return st.session_state.current_page

    @current_page.setter
    def current_page(self, value: str):
        """Set the current page.

        Args:
            value: Current page
        """
        st.session_state.current_page = value

    def add_chat_message(self, role: str, content: str):
        """Add a chat message.

        Args:
            role: Role of the message sender ('user' or 'assistant')
            content: Content of the message
        """
        from datetime import datetime

        message = ChatMessage(
            role=role,
            content=content,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )

        st.session_state.chat.messages.append(message)

    def clear_chat(self):
        """Clear the chat history."""
        st.session_state.chat.messages = []
        st.session_state.chat.current_message = ""

    def reset_code_agent(self):
        """Reset the code agent state."""
        st.session_state.code_agent = CodeAgentState()

    def reset_export_import(self):
        """Reset the export/import state."""
        st.session_state.export_import = ExportImportState()

    def reset_documentation(self):
        """Reset the documentation state."""
        st.session_state.documentation = DocumentationState()
        
    def reset_deepwiki(self):
        """Reset the DeepWiki documentation."""
        st.session_state.deepwiki_documentation = ""
        
    def reset_graph_visualization(self):
        """Reset the graph visualization state."""
        st.session_state.last_generated_graph = ""
        st.session_state.last_mermaid_code = ""
