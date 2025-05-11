"""
Gemini Summarizer for Odoo Documentation RAG

This module provides functionality for summarizing search results using Google's Gemini API.
"""

import os
import logging
from typing import List, Dict, Any, Optional

from .utils import logger

# Check if google.generativeai is available
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    logger.warning("Google Generative AI package not found. Install with 'pip install google-generativeai'")
    GEMINI_AVAILABLE = False

class GeminiSummarizer:
    """Class for summarizing search results using Google's Gemini API."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """Initialize the Gemini summarizer.

        Args:
            api_key: Gemini API key (defaults to environment variable)
            model_name: Gemini model name (defaults to environment variable or gemini-2.0-flash)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.is_available = GEMINI_AVAILABLE and bool(self.api_key)
        self.model = None

        if self.is_available:
            try:
                # Configure the Gemini API
                genai.configure(api_key=self.api_key)

                # Initialize the model
                self.model = genai.GenerativeModel(self.model_name)
                logger.info(f"Gemini summarizer initialized with model: {self.model_name}")
            except Exception as e:
                logger.error(f"Error initializing Gemini model: {str(e)}")
                self.is_available = False
        else:
            if not GEMINI_AVAILABLE:
                logger.warning("Google Generative AI package not available. Install with 'pip install google-generativeai'")
            if not self.api_key:
                logger.warning("Gemini API key not found in environment variables. Please add GEMINI_API_KEY to your .env file.")

    def summarize(
        self,
        query: str,
        doc_results: List[Dict[str, Any]],
        online_results: List[Dict[str, Any]]
    ) -> str:
        """Summarize search results using Gemini.

        Args:
            query: Original query
            doc_results: Results from documentation search
            online_results: Results from online search

        Returns:
            Summarized response
        """
        if not self.is_available or not self.model:
            logger.warning("Gemini summarizer is not available")
            return self._format_fallback_response(query, doc_results, online_results)

        try:
            # Prepare the context from documentation results
            doc_context = ""
            for i, result in enumerate(doc_results[:3]):  # Use top 3 doc results
                doc_context += f"Document {i+1}:\n"
                doc_context += f"Title: {result.get('title', 'Untitled')}\n"
                doc_context += f"Content: {result.get('text', '')}\n\n"

            # Prepare the context from online results
            online_context = ""
            for i, result in enumerate(online_results[:3]):  # Use top 3 online results
                online_context += f"Web Result {i+1}:\n"
                online_context += f"Title: {result.get('title', 'Untitled')}\n"
                online_context += f"Description: {result.get('description', '')}\n"
                online_context += f"URL: {result.get('url', '')}\n\n"

            # Create the prompt for Gemini
            prompt = f"""
            I need a comprehensive answer to the following query about Odoo 18:

            Query: {query}

            Here are relevant excerpts from the Odoo 18 documentation:

            {doc_context}

            Here are relevant online search results:

            {online_context}

            Please provide a detailed, well-structured response that:
            1. Directly answers the query based on the provided information
            2. Combines insights from both documentation and online sources
            3. Includes code examples if relevant
            4. Is formatted in Markdown
            5. Cites sources where appropriate
            6. Includes a "Related Topics" section at the end

            Your response should be comprehensive yet concise, focusing on the most relevant information.
            """

            # Generate the response
            response = self.model.generate_content(prompt)

            if response and hasattr(response, 'text'):
                return response.text
            else:
                logger.error("Failed to get response from Gemini")
                return self._format_fallback_response(query, doc_results, online_results)

        except Exception as e:
            logger.error(f"Error generating summary with Gemini: {str(e)}")
            return self._format_fallback_response(query, doc_results, online_results)

    def _format_fallback_response(
        self,
        query: str,
        doc_results: List[Dict[str, Any]],
        online_results: List[Dict[str, Any]]
    ) -> str:
        """Format a fallback response when Gemini is not available.

        Args:
            query: Original query
            doc_results: Results from documentation search
            online_results: Results from online search

        Returns:
            Formatted response
        """
        output = f"# Results for: {query}\n\n"

        # Add documentation results
        output += "## Documentation Results\n\n"
        for i, result in enumerate(doc_results[:3]):
            title = result.get('title', f"Result {i+1}")
            output += f"### {i+1}. {title}\n\n"

            # Add source information if available
            if 'source' in result:
                output += f"**Source**: {result['source']}\n\n"

            # Add the content
            output += result.get('text', 'No content available') + "\n\n"

        # Add online results
        if online_results:
            output += "## Online Search Results\n\n"
            for i, result in enumerate(online_results[:3]):
                output += f"### {i+1}. {result['title']}\n\n"
                output += f"**Source**: [{result['url']}]({result['url']})\n\n"
                output += f"{result['description']}\n\n"

        return output