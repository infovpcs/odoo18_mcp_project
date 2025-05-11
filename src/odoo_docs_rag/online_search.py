"""
Online Search Module for Odoo Documentation RAG

This module provides functionality for searching the web for Odoo-related information
using the Brave Search API.
"""

import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional

from .utils import logger

class OnlineSearch:
    """Class for performing online searches using Brave Search API."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the online search.

        Args:
            api_key: Brave Search API key (defaults to environment variable)
        """
        self.api_key = api_key or os.getenv("BRAVE_API_KEY")
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        self.is_available = bool(self.api_key)

        if not self.is_available:
            logger.warning("Brave Search API key not found. Online search will not be available. Please add BRAVE_API_KEY to your .env file.")
        else:
            logger.info("Brave Search API key found. Online search is available.")

    def search(self, query: str, count: int = 5) -> List[Dict[str, Any]]:
        """Search the web for information related to the query.

        Args:
            query: Search query
            count: Number of results to return

        Returns:
            List of search results with metadata
        """
        if not self.is_available:
            logger.warning("Brave Search API is not available")
            return []

        try:
            # Add Odoo 18 to the query if not already present
            if "odoo" not in query.lower():
                query = f"Odoo 18 {query}"

            # Set up the request headers and parameters
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.api_key
            }

            params = {
                "q": query,
                "count": min(count, 20),  # Maximum 20 results per request
                "offset": 0,
                "search_lang": "en"
            }

            # Make the request
            response = requests.get(
                self.base_url,
                headers=headers,
                params=params,
                timeout=10
            )

            # Check if the request was successful
            if response.status_code == 200:
                data = response.json()

                # Extract and format the results
                results = []
                for item in data.get("web", {}).get("results", []):
                    result = {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "description": item.get("description", ""),
                        "source": "brave_search"
                    }
                    results.append(result)

                logger.info(f"Found {len(results)} results from online search")
                return results
            else:
                logger.error(f"Error searching online: {response.status_code} - {response.text}")
                return []

        except Exception as e:
            logger.error(f"Error performing online search: {str(e)}")
            return []

    def format_results(self, results: List[Dict[str, Any]]) -> str:
        """Format online search results as markdown.

        Args:
            results: List of search results

        Returns:
            Formatted markdown string
        """
        if not results:
            return "No online search results found."

        output = "## Online Search Results\n\n"

        for i, result in enumerate(results):
            output += f"### {i+1}. {result['title']}\n\n"
            output += f"**Source**: [{result['url']}]({result['url']})\n\n"
            output += f"{result['description']}\n\n"

        return output