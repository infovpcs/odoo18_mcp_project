#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chat Component for Streamlit Client

This module provides a reusable chat component for the Streamlit client.
"""

import logging
import os
from typing import Any, Callable, Dict, List, Optional, Union

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from ..utils.session_state import SessionState, ChatMessage

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("chat_component")

def render_chat(
    session_state: SessionState,
    container: Optional[DeltaGenerator] = None,
    on_submit: Optional[Callable[[str], None]] = None,
    placeholder: str = "Type your message here...",
    key_prefix: str = "chat",
    show_clear_button: bool = True,
    max_height: int = 400
) -> None:
    """Render a chat component.

    Args:
        session_state: Session state
        container: Container to render the chat in (if None, uses st)
        on_submit: Callback function to call when a message is submitted
        placeholder: Placeholder text for the input field
        key_prefix: Prefix for the component keys
        show_clear_button: Whether to show the clear button
        max_height: Maximum height of the chat container
    """
    # Use the provided container or st directly
    cont = container if container is not None else st

    # Create a container for the chat messages with a fixed height
    chat_container = cont.container(height=max_height)

    # Display chat messages
    with chat_container:
        for i, msg in enumerate(session_state.chat.messages):
            with st.chat_message(msg.role):
                st.markdown(msg.content)
                if msg.timestamp:
                    st.caption(f"Sent: {msg.timestamp}")

    # Create a container for the input field and buttons
    input_container = cont.container()

    with input_container:
        # Create columns for the input field and buttons
        col1, col2 = st.columns([5, 1])

        with col1:
            # Input field for the message
            message = st.text_area(
                "Message",
                value=session_state.chat.current_message,
                placeholder=placeholder,
                label_visibility="collapsed",
                key=f"{key_prefix}_message_input"
            )

        with col2:
            # Submit button
            submit_button = st.button(
                "Send",
                key=f"{key_prefix}_submit_button",
                use_container_width=True
            )

            # Clear button
            if show_clear_button:
                clear_button = st.button(
                    "Clear",
                    key=f"{key_prefix}_clear_button",
                    use_container_width=True
                )

                if clear_button:
                    session_state.clear_chat()
                    st.rerun()

        # Handle message submission
        if submit_button and message:
            # Add the message to the chat
            session_state.add_chat_message("user", message)

            # Clear the input field
            session_state.chat.current_message = ""

            # Call the callback function if provided
            if on_submit:
                on_submit(message)

            # Rerun to update the UI
            st.rerun()

def render_code_block(code: str, language: str = "python", container: Optional[DeltaGenerator] = None) -> None:
    """Render a code block.

    Args:
        code: Code to render
        language: Programming language of the code
        container: Container to render the code block in (if None, uses st)
    """
    # Use the provided container or st directly
    cont = container if container is not None else st

    # Render the code block
    cont.code(code, language=language)

def render_file_upload(
    session_state: SessionState,
    container: Optional[DeltaGenerator] = None,
    on_upload: Optional[Callable[[bytes], None]] = None,
    key_prefix: str = "file_upload",
    allowed_types: List[str] = ["csv", "txt", "py", "xml", "json"]
) -> None:
    """Render a file upload component.

    Args:
        session_state: Session state
        container: Container to render the file upload in (if None, uses st)
        on_upload: Callback function to call when a file is uploaded
        key_prefix: Prefix for the component keys
        allowed_types: List of allowed file types
    """
    # Use the provided container or st directly
    cont = container if container is not None else st

    # Create a container for the file upload
    upload_container = cont.container()

    with upload_container:
        # File upload
        uploaded_file = st.file_uploader(
            "Upload a file",
            type=allowed_types,
            key=f"{key_prefix}_file_uploader"
        )

        if uploaded_file is not None:
            # Display file info
            st.write(f"Uploaded file: {uploaded_file.name}")

            # Call the callback function if provided
            if on_upload:
                on_upload(uploaded_file.getvalue())

def render_feedback_form(
    session_state: SessionState,
    container: Optional[DeltaGenerator] = None,
    on_submit: Optional[Callable[[str], None]] = None,
    key_prefix: str = "feedback",
    placeholder: str = "Provide your feedback here..."
) -> None:
    """Render a feedback form.

    Args:
        session_state: Session state
        container: Container to render the feedback form in (if None, uses st)
        on_submit: Callback function to call when feedback is submitted
        key_prefix: Prefix for the component keys
        placeholder: Placeholder text for the input field
    """
    # Use the provided container or st directly
    cont = container if container is not None else st

    # Create a container for the feedback form
    feedback_container = cont.container()

    with feedback_container:
        # Check if we need to clear the input
        if f"{key_prefix}_clear_input" in st.session_state and st.session_state[f"{key_prefix}_clear_input"]:
            # Initialize with empty string
            if f"{key_prefix}_feedback_input" not in st.session_state:
                st.session_state[f"{key_prefix}_feedback_input"] = ""
            # Reset the clear flag
            st.session_state[f"{key_prefix}_clear_input"] = False

        # Feedback form
        feedback = st.text_area(
            "Feedback",
            placeholder=placeholder,
            key=f"{key_prefix}_feedback_input"
        )

        # Submit button
        submit_button = st.button(
            "Submit Feedback",
            key=f"{key_prefix}_submit_button"
        )

        if submit_button and feedback:
            # Call the callback function if provided
            if on_submit:
                on_submit(feedback)

            # Clear the input field - use a different approach to avoid the error
            # Instead of directly modifying session state, we'll use a flag to clear it on next render
            if f"{key_prefix}_clear_input" not in st.session_state:
                st.session_state[f"{key_prefix}_clear_input"] = True

            # Show a success message
            st.success("Feedback submitted successfully!")
