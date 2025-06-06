#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepWiki client for the Simple Odoo Code Agent.

This module provides functionality to query the DeepWiki documentation service
to retrieve relevant documentation for Odoo module development.
"""

import logging
import json
import re
import os
from typing import Dict, Any, Optional, List
import aiohttp
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

# MCP server configuration for local development
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8001")
MCP_TIMEOUT = int(os.environ.get("MCP_TIMEOUT", "30"))


async def query_deepwiki(target_url: str) -> str:
    """
    Query the DeepWiki service to retrieve documentation.
    
    Args:
        target_url: The DeepWiki URL to query (must start with https://deepwiki.com/)
        
    Returns:
        The retrieved documentation as a string
        
    Raises:
        ValueError: If the target_url is not a valid DeepWiki URL
        ConnectionError: If the request to the MCP server fails
    """
    if not target_url.startswith("https://deepwiki.com/"):
        raise ValueError("Only URLs starting with 'https://deepwiki.com/' are allowed")
    
    try:
        # Prepare the request to the MCP server
        url = f"{MCP_SERVER_URL}/call_tool"
        payload = {
            "tool": "query_deepwiki",
            "params": {
                "target_url": target_url
            }
        }
        
        logger.info(f"Querying DeepWiki: {target_url}")
        
        # Make the request asynchronously
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, 
                json=payload,
                timeout=MCP_TIMEOUT
            ) as response:
                # Parse the response
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Error querying DeepWiki: {error_text}")
                    raise ConnectionError(f"Error querying DeepWiki: {error_text}")
                
                result = await response.json()
                
                if not result.get("success", False):
                    error = result.get("error", "Unknown error")
                    logger.error(f"DeepWiki query failed: {error}")
                    raise ConnectionError(f"DeepWiki query failed: {error}")
                
                documentation = result.get("result", "")
                
                # Check if the documentation is valid
                if "# Warning: No Content" in documentation:
                    logger.warning(f"DeepWiki returned no content for {target_url}")
                    return f"No documentation found for {target_url}"
                
                logger.info(f"Successfully retrieved documentation from DeepWiki ({len(documentation)} characters)")
                return documentation
    
    except aiohttp.ClientError as e:
        logger.error(f"Network error querying DeepWiki: {str(e)}")
        raise ConnectionError(f"Network error querying DeepWiki: {str(e)}")
    
    except asyncio.TimeoutError:
        logger.error(f"Timeout querying DeepWiki after {MCP_TIMEOUT} seconds")
        raise ConnectionError(f"Timeout querying DeepWiki after {MCP_TIMEOUT} seconds")
    
    except Exception as e:
        logger.error(f"Unexpected error querying DeepWiki: {str(e)}")
        raise


async def query_odoo_documentation(version: str = "18.0", topic: Optional[str] = None) -> List[Dict[str, str]]:
    """
    Query the Odoo documentation for a specific version and topic.
    
    Args:
        version: The Odoo version to query documentation for
        topic: Optional topic to focus the documentation retrieval
        
    Returns:
        A list of documentation entries with source and content
    """
    docs = []
    
    # URLs to query
    urls = [
        f"https://deepwiki.com/odoo/odoo/documentation/{version}",
        "https://deepwiki.com/odoo/owl"
    ]
    
    # Add topic-specific URLs if a topic is provided
    if topic:
        sanitized_topic = re.sub(r'[^a-zA-Z0-9_]', '_', topic.lower())
        urls.append(f"https://deepwiki.com/odoo/odoo/documentation/{version}/{sanitized_topic}")
    
    # Query each URL in parallel
    tasks = [query_deepwiki(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process the results
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.warning(f"Failed to retrieve documentation from {urls[i]}: {str(result)}")
            continue
        
        docs.append({
            "source": urls[i],
            "content": result
        })
    
    return docs


# For testing
if __name__ == "__main__":
    async def test():
        try:
            result = await query_deepwiki("https://deepwiki.com/odoo/odoo")
            print(f"Result length: {len(result)}")
            print(result[:500] + "...")
        except Exception as e:
            print(f"Error: {str(e)}")
    
    asyncio.run(test())