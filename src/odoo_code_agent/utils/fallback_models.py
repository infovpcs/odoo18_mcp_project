#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fallback models for the Odoo Code Agent.

This module provides fallback models for generating code when the primary models are not available.
"""

import logging
import os
import json
import subprocess
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Global variables to track model initialization
gemini_initialized = False
ollama_initialized = False


def initialize_gemini() -> bool:
    """
    Initialize the Google Gemini model.

    Returns:
        True if initialization was successful, False otherwise
    """
    global gemini_initialized

    try:
        # Check if the required packages are installed
        try:
            import google.generativeai as genai
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
        except ImportError:
            logger.warning("Google Generative AI package not found. Installing...")
            subprocess.check_call(["pip", "install", "google-generativeai"])
            import google.generativeai as genai
            from google.generativeai.types import HarmCategory, HarmBlockThreshold

        # Check if API key is available
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logger.error("Gemini API key not found in environment variables")
            return False

        # Configure the API
        genai.configure(api_key=api_key)

        # Get the model name from environment variables or use default
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

        # Test the model
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, world!")

        if response:
            logger.info("Google Gemini model initialized successfully")
            gemini_initialized = True
            return True
        else:
            logger.error("Failed to get response from Google Gemini model")
            return False

    except Exception as e:
        logger.error(f"Error initializing Google Gemini model: {str(e)}")
        return False


def initialize_ollama() -> bool:
    """
    Initialize the Ollama model using direct HTTP API calls.

    This function checks if the Ollama server is running and if the qwen2.5-coder:7b model is available.
    To install Ollama, follow the instructions at https://github.com/ollama/ollama
    To download the model, run: ollama pull qwen2.5-coder:7b

    Returns:
        True if initialization was successful, False otherwise
    """
    global ollama_initialized

    try:
        # Check if the required packages are installed
        try:
            import requests
        except ImportError:
            logger.warning("Requests package not found. Installing...")
            subprocess.check_call(["pip", "install", "requests"])
            import requests

        # Test the Ollama API
        try:
            # First check if the Ollama server is running
            version_response = requests.get("http://localhost:11434/api/version", timeout=10)
            if version_response.status_code != 200:
                logger.error(f"Ollama server returned status code {version_response.status_code}")
                return False

            logger.info(f"Ollama server version: {version_response.json()}")

            # Test with a simple chat request
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "qwen2.5-coder:7b",
                    "messages": [
                        {
                            "role": "user",
                            "content": "Hello, world!"
                        }
                    ],
                    "stream": False  # Request a complete response instead of streaming
                },
                timeout=60
            )

            if response.status_code == 200:
                logger.info("Ollama model initialized successfully")
                ollama_initialized = True
                return True
            else:
                logger.error(f"Failed to get response from Ollama model. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error communicating with Ollama: {str(e)}")
            return False

    except Exception as e:
        logger.error(f"Error initializing Ollama model: {str(e)}")
        return False


def generate_with_gemini(prompt: str) -> Optional[str]:
    """
    Generate text using Google Gemini model.

    Args:
        prompt: The prompt to send to the model

    Returns:
        The generated text, or None if generation failed
    """
    global gemini_initialized

    if not gemini_initialized:
        if not initialize_gemini():
            logger.error("Failed to initialize Google Gemini model")
            return None

    try:
        import google.generativeai as genai

        # Get the model name from environment variables or use default
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

        model = genai.GenerativeModel(model_name)
        response = model.generate_content(prompt)

        if response:
            return response.text
        else:
            logger.error("Failed to get response from Google Gemini model")
            return None

    except Exception as e:
        logger.error(f"Error generating text with Google Gemini model: {str(e)}")
        return None


def generate_with_ollama(prompt: str) -> Optional[str]:
    """
    Generate text using Ollama model via direct HTTP API calls.

    This function uses the qwen2.5-coder:7b model for code generation.
    The model is particularly good at generating code and understanding programming concepts.

    Args:
        prompt: The prompt to send to the model

    Returns:
        The generated text, or None if generation failed
    """
    global ollama_initialized

    if not ollama_initialized:
        if not initialize_ollama():
            logger.error("Failed to initialize Ollama model")
            return None

    try:
        import requests

        # Log the prompt for debugging
        logger.info(f"Sending prompt to Ollama (first 100 chars): {prompt[:100]}...")

        # Make the API request with stream=false to get a complete response
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "qwen2.5-coder:7b",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False  # Request a complete response instead of streaming
            },
            timeout=600  # 10 minutes timeout for code generation
        )

        # Check if the request was successful
        if response.status_code == 200:
            try:
                # Try to parse the JSON response
                result = response.json()
                if result and 'message' in result and 'content' in result['message']:
                    content = result['message']['content']
                    logger.info(f"Received response from Ollama (first 100 chars): {content[:100]}...")
                    return content
                else:
                    logger.error(f"Unexpected response format from Ollama: {result}")
                    return None
            except json.JSONDecodeError as e:
                # If JSON parsing fails, try to extract the content directly from the response text
                logger.warning(f"Failed to parse JSON response: {e}")
                logger.warning(f"Attempting to extract content from raw response")

                # The response might be a streaming response with multiple JSON objects
                try:
                    # Try to extract the first JSON object
                    import re
                    json_match = re.search(r'(\{.*?\})', response.text, re.DOTALL)
                    if json_match:
                        first_json = json.loads(json_match.group(1))
                        if 'message' in first_json and 'content' in first_json['message']:
                            content = first_json['message']['content']
                            logger.info(f"Extracted content from raw response (first 100 chars): {content[:100]}...")
                            return content

                    # If that fails, just return the raw text
                    logger.warning("Returning raw response text")
                    return response.text
                except Exception as inner_e:
                    logger.error(f"Error extracting content from raw response: {inner_e}")
                    logger.error(f"Raw response: {response.text[:500]}...")
                    return None
        else:
            logger.error(f"Failed to get response from Ollama model. Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return None

    except Exception as e:
        logger.error(f"Error generating text with Ollama model: {str(e)}")
        return None


def generate_with_fallback(prompt: str, use_gemini: bool = True, use_ollama: bool = True) -> Optional[str]:
    """
    Generate text using fallback models.

    Args:
        prompt: The prompt to send to the model
        use_gemini: Whether to try Google Gemini
        use_ollama: Whether to try Ollama

    Returns:
        The generated text, or None if all fallbacks failed
    """
    # Try Gemini first if enabled
    if use_gemini:
        result = generate_with_gemini(prompt)
        if result:
            return result

    # Try Ollama if enabled and Gemini failed or is disabled
    if use_ollama:
        result = generate_with_ollama(prompt)
        if result:
            return result

    # All fallbacks failed
    logger.error("All fallback models failed to generate text")
    return None