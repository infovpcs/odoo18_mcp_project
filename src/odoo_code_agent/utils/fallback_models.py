# src/agents/odoo_code_agent/utils/fallback_models.py
import logging
import os
import subprocess
from typing import Optional, Dict, Any

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
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            logger.error("Google API key not found in environment variables")
            return False
        
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Test the model
        model = genai.GenerativeModel('gemini-2.0-flash')
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
    Initialize the Ollama model.

    Returns:
        True if initialization was successful, False otherwise
    """
    global ollama_initialized
    
    try:
        # Check if the required packages are installed
        try:
            import ollama
        except ImportError:
            logger.warning("Ollama package not found. Installing...")
            subprocess.check_call(["pip", "install", "ollama"])
            import ollama
        
        # Test the model
        try:
            response = ollama.chat(model='deepseek-r1:latest', messages=[
                {
                    'role': 'user',
                    'content': 'Hello, world!'
                }
            ])
            
            if response:
                logger.info("Ollama model initialized successfully")
                ollama_initialized = True
                return True
            else:
                logger.error("Failed to get response from Ollama model")
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
        
        model = genai.GenerativeModel('gemini-2.0-flash')
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
    Generate text using Ollama model.

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
        import ollama
        
        response = ollama.chat(model='deepseek-r1:latest', messages=[
            {
                'role': 'user',
                'content': prompt
            }
        ])
        
        if response and 'message' in response and 'content' in response['message']:
            return response['message']['content']
        else:
            logger.error("Failed to get response from Ollama model")
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