#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Connector for Streamlit Client

This module provides a connector to interact with the MCP server using the official MCP Python SDK.
It supports both the standard MCP protocol and a fallback to the custom HTTP API.
"""

import json
import logging
import os
import requests
import time
import uuid
import asyncio
from typing import Any, Dict, List, Optional
from enum import Enum
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import MCP SDK (for future use)
try:
    import mcp
    HAS_MCP_SDK = True
except ImportError:
    HAS_MCP_SDK = False
    logging.warning("MCP SDK not found. Using HTTP API. Install with: pip install mcp")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_connector")

class ConnectionType(Enum):
    """Connection type for MCP server."""
    STDIO = "stdio"
    HTTP = "http"

class MCPConnector:
    """Connector for interacting with the MCP server."""

    def __init__(self,
                 server_url: str = "http://localhost:8001",
                 connection_type: ConnectionType = ConnectionType.HTTP,
                 server_script_path: Optional[str] = None):
        """Initialize the MCP connector.

        Args:
            server_url: URL of the MCP server (for HTTP connection)
            connection_type: Type of connection to use (STDIO or HTTP)
            server_script_path: Path to the server script (for STDIO connection)
        """
        self.connection_type = connection_type
        self.server_url = server_url
        self.server_script_path = server_script_path

        # HTTP API endpoints
        self.call_tool_endpoint = f"{server_url}/call_tool"
        self.health_check_endpoint = f"{server_url}/health"
        self.list_tools_endpoint = f"{server_url}/list_tools"

        # MCP SDK client session
        self.mcp_session = None
        self.mcp_tools = []

        # Initialize MCP SDK if available and using STDIO connection
        if connection_type == ConnectionType.STDIO and HAS_MCP_SDK and server_script_path:
            self._init_mcp_sdk()

    def _init_mcp_sdk(self):
        """Initialize the MCP SDK client session."""
        if not HAS_MCP_SDK:
            logger.warning("MCP SDK not available. Install with: pip install mcp")
            return

        if not self.server_script_path:
            logger.warning("Server script path not provided for STDIO connection")
            return

        # This will be initialized when connect() is called
        self.mcp_session = None

    async def connect(self) -> bool:
        """Connect to the MCP server.

        Returns:
            True if connection was successful, False otherwise
        """
        if self.connection_type == ConnectionType.HTTP:
            # For HTTP, just check if the server is running
            return self.health_check()
        elif self.connection_type == ConnectionType.STDIO and HAS_MCP_SDK:
            try:
                # Let's use a simpler approach - just use the HTTP API
                # This is more reliable than trying to use the STDIO transport directly
                logger.info("Using HTTP API instead of STDIO transport for reliability")
                self.connection_type = ConnectionType.HTTP
                return self.health_check()
            except Exception as e:
                logger.error(f"Error connecting to MCP server: {str(e)}")
                return False
        else:
            logger.error("Cannot connect: MCP SDK not available or invalid connection type")
            return False

    async def async_call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool on the MCP server asynchronously.

        Args:
            tool_name: Name of the tool to call
            params: Parameters for the tool

        Returns:
            Response from the tool
        """
        # Always use HTTP API for now
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._http_call_tool(tool_name, params)
        )

    def _http_call_tool(self, tool_name: str, params: Dict[str, Any], timeout: int = 60,
                     use_polling: bool = False, max_polls: int = 15, poll_interval: int = 2) -> Dict[str, Any]:
        """Call a tool on the MCP server using HTTP API.

        Args:
            tool_name: Name of the tool to call
            params: Parameters for the tool
            timeout: Timeout in seconds for the request
            use_polling: Whether to use polling to wait for complete results
            max_polls: Maximum number of polling attempts
            poll_interval: Interval between polling attempts in seconds

        Returns:
            Response from the tool
        """
        try:
            payload = {
                "tool": tool_name,  # Use "tool" as the parameter name for the standalone_mcp_server.py
                "params": params
            }

            logger.info(f"Calling tool {tool_name} with params: {json.dumps(params, indent=2)}")

            # Configure tool-specific settings
            if tool_name == "advanced_search":
                # Advanced search needs more time and more aggressive polling
                timeout = max(timeout, 180)  # 3 minutes for advanced search
                use_polling = True
                poll_interval = 3  # Longer interval for advanced search
                max_polls = 20  # More polling attempts for advanced search
            elif tool_name in ["run_odoo_code_agent_tool", "retrieve_odoo_documentation"]:
                # Other complex tools
                timeout = max(timeout, 120)  # 2 minutes for complex tools
                use_polling = True
                poll_interval = 2
            elif tool_name in ["export_records_to_csv", "export_related_records_to_csv",
                              "import_records_from_csv", "import_related_records_from_csv"]:
                # Import/export operations
                timeout = max(timeout, 90)  # 1.5 minutes for import/export
                use_polling = True
                poll_interval = 2

            logger.info(f"Using timeout of {timeout} seconds for {tool_name} with polling interval {poll_interval}s")

            # Initial request
            response = requests.post(
                self.call_tool_endpoint,
                json=payload,
                timeout=timeout
            )

            if response.status_code != 200:
                error_msg = f"Error calling tool {tool_name}: {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}

            result = response.json()

            # Check for data in both 'data' and 'result' fields
            data_length = len(str(result.get('data', '')))
            result_length = len(str(result.get('result', '')))
            total_data_length = data_length + result_length

            logger.info(f"Initial response from {tool_name}: success={result.get('success', False)}, data_length={data_length}, result_length={result_length}")

            # For the Odoo code agent tool, check if the response contains structured data
            if tool_name == "run_odoo_code_agent_tool" and "result" in result:
                try:
                    # Try to parse the result as JSON
                    result_data = json.loads(result["result"]) if isinstance(result["result"], str) else result["result"]
                    if isinstance(result_data, dict) and "data" in result_data:
                        # Extract the data from the result
                        data = result_data["data"]
                        # Update the result with the data
                        result["data"] = data
                        # Set success to True
                        result["success"] = True
                        logger.info(f"Extracted data from result for Odoo code agent: {len(str(data))} bytes")
                except (json.JSONDecodeError, TypeError, KeyError) as e:
                    # If the result is not a valid JSON object or doesn't have the expected structure
                    logger.info(f"Could not extract structured data from result: {str(e)}")
                    pass

            # If the result already has data in either field, return it immediately
            if total_data_length > 0:
                logger.info(f"Initial response already contains data, returning immediately")
                return result

            # If polling is enabled and the result has no data but is successful, poll for complete results
            if use_polling and result.get('success', False):
                logger.info(f"Initial response has no data, starting polling for {tool_name}")

                # Add a request_id to the payload to track this specific request
                request_id = str(uuid.uuid4())
                payload["request_id"] = request_id

                # Poll for results
                for i in range(max_polls):
                    logger.info(f"Polling attempt {i+1}/{max_polls} for {tool_name}")

                    # Wait for the specified interval
                    time.sleep(poll_interval)

                    # Make a polling request
                    try:
                        poll_response = requests.post(
                            self.call_tool_endpoint,
                            json=payload,
                            timeout=timeout
                        )

                        if poll_response.status_code == 200:
                            poll_result = poll_response.json()

                            # Check for data in both 'data' and 'result' fields
                            poll_data_length = len(str(poll_result.get('data', '')))
                            poll_result_length = len(str(poll_result.get('result', '')))
                            poll_total_length = poll_data_length + poll_result_length

                            logger.info(f"Poll response from {tool_name}: success={poll_result.get('success', False)}, data_length={poll_data_length}, result_length={poll_result_length}")

                            # If we got data in either field, return the result
                            if poll_total_length > 0:
                                logger.info(f"Received complete response after {i+1} polling attempts")
                                return poll_result

                            # If the server indicates an error, stop polling
                            if not poll_result.get('success', True):
                                logger.warning(f"Server reported error during polling: {poll_result.get('error', 'Unknown error')}")
                                return poll_result
                        else:
                            logger.warning(f"Poll request failed with status {poll_response.status_code}")
                    except requests.exceptions.Timeout:
                        logger.warning(f"Timeout during polling attempt {i+1}")
                        # Continue polling despite timeout
                    except Exception as e:
                        logger.warning(f"Error during polling: {str(e)}")

                # If we get here, polling didn't yield results
                logger.warning(f"Polling completed without receiving data for {tool_name}")

                # Check if the original result had any data in either field
                if total_data_length == 0:
                    # Add a more detailed message based on the tool
                    if tool_name == "advanced_search":
                        result["data"] = f"The advanced search operation is taking longer than expected. This could be due to complex query processing or a large dataset. The server might still be processing your request. Please try a more specific query or check the server logs."
                    else:
                        result["data"] = f"The operation is taking longer than expected. The server might still be processing your request for '{tool_name}'. Please try again in a few moments or check the server logs."

            return result
        except requests.exceptions.Timeout:
            error_msg = f"Timeout error calling tool {tool_name} after {timeout} seconds"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Error calling tool {tool_name}: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    def health_check(self) -> bool:
        """Check if the MCP server is running.

        Returns:
            True if the server is running, False otherwise
        """
        try:
            response = requests.get(self.health_check_endpoint)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error checking MCP server health: {str(e)}")
            return False

    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools on the MCP server.

        Returns:
            List of available tools
        """
        try:
            response = requests.get(self.list_tools_endpoint)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error listing tools: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error listing tools: {str(e)}")
            return []

    def call_tool(self, tool_name: str, params: Dict[str, Any], timeout: int = 60,
                 use_polling: bool = False, max_polls: int = 10, poll_interval: int = 2) -> Dict[str, Any]:
        """Call a tool on the MCP server.

        Args:
            tool_name: Name of the tool to call
            params: Parameters for the tool
            timeout: Timeout in seconds for the request
            use_polling: Whether to use polling to wait for complete results
            max_polls: Maximum number of polling attempts
            poll_interval: Interval between polling attempts in seconds

        Returns:
            Response from the tool
        """
        try:
            payload = {
                "tool": tool_name,  # Use "tool" as the parameter name for the standalone_mcp_server.py
                "params": params
            }

            logger.info(f"Calling tool {tool_name} with params: {json.dumps(params, indent=2)}")

            # Use a longer timeout for complex queries
            if tool_name in ["advanced_search", "run_odoo_code_agent_tool", "retrieve_odoo_documentation"]:
                timeout = max(timeout, 120)  # At least 2 minutes for complex tools
                use_polling = True  # Always use polling for complex tools

            logger.info(f"Using timeout of {timeout} seconds for {tool_name}")

            # Initial request
            response = requests.post(
                self.call_tool_endpoint,
                json=payload,
                timeout=timeout
            )

            if response.status_code != 200:
                error_msg = f"Error calling tool {tool_name}: {response.text}"
                logger.error(error_msg)
                return {"success": False, "error": error_msg}

            result = response.json()
            data_length = len(str(result.get('data', '')))
            logger.info(f"Initial response from {tool_name}: success={result.get('success', False)}, data_length={data_length}")

            # If polling is enabled and the result has no data but is successful, poll for complete results
            if use_polling and result.get('success', False) and data_length == 0:
                logger.info(f"Initial response has no data, starting polling for {tool_name}")

                # Add a request_id to the payload to track this specific request
                request_id = str(uuid.uuid4())
                payload["request_id"] = request_id

                # Poll for results
                for i in range(max_polls):
                    logger.info(f"Polling attempt {i+1}/{max_polls} for {tool_name}")

                    # Wait for the specified interval
                    time.sleep(poll_interval)

                    # Make a polling request
                    try:
                        poll_response = requests.post(
                            self.call_tool_endpoint,
                            json=payload,
                            timeout=timeout
                        )

                        if poll_response.status_code == 200:
                            poll_result = poll_response.json()
                            poll_data_length = len(str(poll_result.get('data', '')))
                            logger.info(f"Poll response from {tool_name}: success={poll_result.get('success', False)}, data_length={poll_data_length}")

                            # For the Odoo code agent tool, check if the response contains structured data
                            if tool_name == "run_odoo_code_agent_tool" and "result" in poll_result:
                                try:
                                    # Try to parse the result as JSON
                                    result_data = json.loads(poll_result["result"]) if isinstance(poll_result["result"], str) else poll_result["result"]
                                    if isinstance(result_data, dict) and "data" in result_data:
                                        # Extract the data from the result
                                        data = result_data["data"]
                                        # Update the result with the data
                                        poll_result["data"] = data
                                        # Set success to True
                                        poll_result["success"] = True
                                        logger.info(f"Extracted data from poll result for Odoo code agent: {len(str(data))} bytes")
                                except (json.JSONDecodeError, TypeError, KeyError) as e:
                                    # If the result is not a valid JSON object or doesn't have the expected structure
                                    logger.info(f"Could not extract structured data from poll result: {str(e)}")
                                    pass

                            # If we got data, return the result
                            if poll_data_length > 0:
                                logger.info(f"Received complete response after {i+1} polling attempts")
                                return poll_result
                        else:
                            logger.warning(f"Poll request failed with status {poll_response.status_code}")
                    except Exception as e:
                        logger.warning(f"Error during polling: {str(e)}")

                # If we get here, polling didn't yield results
                logger.warning(f"Polling completed without receiving data for {tool_name}")

                # If the original result had no data, add a message
                if data_length == 0:
                    result["data"] = f"The operation is taking longer than expected. The server might still be processing your request for '{tool_name}'. Please try again in a few moments or check the server logs."

            return result
        except requests.exceptions.Timeout:
            error_msg = f"Timeout error calling tool {tool_name} after {timeout} seconds"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        except Exception as e:
            error_msg = f"Error calling tool {tool_name}: {str(e)}"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

    # Convenience methods for specific tools

    def search_records(self, model_name: str, query: str) -> Dict[str, Any]:
        """Search for records in an Odoo model.

        Args:
            model_name: The technical name of the Odoo model
            query: The search query

        Returns:
            Search results
        """
        params = {
            "model_name": model_name,
            "query": query
        }
        return self.call_tool("search_records", params)

    def advanced_search(self, query: str, limit: int = 100) -> Dict[str, Any]:
        """Perform an advanced search using natural language.

        Args:
            query: Natural language query
            limit: Maximum number of records to return

        Returns:
            Search results
        """
        params = {
            "query": query,
            "limit": limit
        }

        # Log the query for debugging
        logger.info(f"Performing advanced search with query: {query}")

        # Estimate complexity based on query length and presence of certain keywords
        complexity_keywords = ["list", "all", "where", "under", "customer", "order", "invoice", "product", "related"]
        query_complexity = len(query.split()) + sum(2 for keyword in complexity_keywords if keyword.lower() in query.lower())

        # Calculate timeout based on complexity (minimum 60 seconds, maximum 300 seconds)
        timeout = min(max(60, query_complexity * 10), 300)
        logger.info(f"Estimated query complexity: {query_complexity}, using timeout: {timeout} seconds")

        # For advanced search, use polling with more attempts and longer intervals
        max_polls = 15  # Try up to 15 times
        poll_interval = 3  # Wait 3 seconds between polls

        return self.call_tool(
            "advanced_search",
            params,
            timeout=timeout,
            use_polling=True,
            max_polls=max_polls,
            poll_interval=poll_interval
        )

    def retrieve_odoo_documentation(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Retrieve information from Odoo 18 documentation.

        Args:
            query: The query to search for
            max_results: Maximum number of results to return

        Returns:
            Documentation results
        """
        params = {
            "query": query,
            "max_results": max_results
        }

        # Log the query for debugging
        logger.info(f"Retrieving Odoo documentation with query: {query}")

        # Use a longer timeout for documentation retrieval (90 seconds)
        # Also use polling for documentation retrieval
        return self.call_tool(
            "retrieve_odoo_documentation",
            params,
            timeout=90,
            use_polling=True,
            max_polls=15,
            poll_interval=2
        )

    def generate_mermaid_diagram(self, mermaid_code: str, name: str = "diagram",
                                theme: str = "default", background_color: str = "white") -> Dict[str, Any]:
        """Generate a Mermaid diagram using the generate_npx tool.

        Args:
            mermaid_code: The Mermaid code to generate a diagram from
            name: Name of the diagram (used for the output file name)
            theme: Theme for the diagram (default, forest, dark, neutral)
            background_color: Background color for the diagram

        Returns:
            Response from the tool with the path to the generated image
        """
        params = {
            "code": mermaid_code,
            "name": name,
            "theme": theme,
            "backgroundColor": background_color
        }

        # Log the request for debugging
        logger.info(f"Generating Mermaid diagram with {len(mermaid_code)} characters of code")

        # Call the generate_npx tool
        return self.call_tool("generate_npx", params, timeout=60)



    def export_records_to_csv(self, model_name: str, fields: Optional[List[str]] = None,
                             filter_domain: Optional[str] = None, limit: int = 1000,
                             export_path: Optional[str] = None) -> Dict[str, Any]:
        """Export records from an Odoo model to a CSV file.

        Args:
            model_name: The technical name of the Odoo model to export
            fields: List of field names to export
            filter_domain: Domain filter in string format
            limit: Maximum number of records to export
            export_path: Path to export the CSV file

        Returns:
            Export results
        """
        params = {
            "model_name": model_name,
            "limit": limit
        }

        if fields:
            params["fields"] = fields

        if filter_domain:
            params["filter_domain"] = filter_domain

        if export_path:
            params["export_path"] = export_path

        # Log the export operation
        logger.info(f"Exporting records from {model_name} to {export_path or 'default path'}")

        # Use polling for export operations
        return self.call_tool(
            "export_records_to_csv",
            params,
            timeout=120,
            use_polling=True,
            max_polls=10,
            poll_interval=2
        )

    def import_records_from_csv(self, input_path: str, model_name: str,
                               field_mapping: Optional[str] = None,
                               create_if_not_exists: bool = True,
                               update_if_exists: bool = True) -> Dict[str, Any]:
        """Import records from a CSV file into an Odoo model.

        Args:
            input_path: Path to the CSV file to import
            model_name: The technical name of the Odoo model to import into
            field_mapping: JSON string with mapping from CSV field names to Odoo field names
            create_if_not_exists: Whether to create new records if they don't exist
            update_if_exists: Whether to update existing records

        Returns:
            Import results
        """
        params = {
            "input_path": input_path,
            "model_name": model_name,
            "create_if_not_exists": create_if_not_exists,
            "update_if_exists": update_if_exists
        }

        if field_mapping:
            params["field_mapping"] = field_mapping

        # Log the import operation
        logger.info(f"Importing records from {input_path} to {model_name}")

        # Use polling for import operations
        return self.call_tool(
            "import_records_from_csv",
            params,
            timeout=120,
            use_polling=True,
            max_polls=15,
            poll_interval=2
        )

    def health_check(self) -> bool:
        """Check if the MCP server is running.

        Returns:
            True if the server is running, False otherwise
        """
        try:
            response = requests.get(self.health_check_endpoint)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error checking MCP server health: {str(e)}")
            return False

    def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools on the MCP server.

        Returns:
            List of available tools
        """
        try:
            response = requests.get(self.list_tools_endpoint)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error listing tools: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error listing tools: {str(e)}")
            return []

    def call_tool(self, tool_name: str, params: Dict[str, Any], timeout: int = 60,
                 use_polling: bool = False, max_polls: int = 10, poll_interval: int = 2) -> Dict[str, Any]:
        """Call a tool on the MCP server.

        This method uses the HTTP API to call tools on the MCP server.

        Args:
            tool_name: Name of the tool to call
            params: Parameters for the tool
            timeout: Timeout in seconds for the request
            use_polling: Whether to use polling to wait for complete results
            max_polls: Maximum number of polling attempts
            poll_interval: Interval between polling attempts in seconds

        Returns:
            Response from the tool
        """
        # Always use HTTP API for now
        return self._http_call_tool(tool_name, params, timeout, use_polling, max_polls, poll_interval)

    # Convenience methods for specific tools

    def search_records(self, model_name: str, query: str) -> Dict[str, Any]:
        """Search for records in an Odoo model.

        Args:
            model_name: The technical name of the Odoo model
            query: The search query

        Returns:
            Search results
        """
        params = {
            "model_name": model_name,
            "query": query
        }
        return self.call_tool("search_records", params)

    def advanced_search(self, query: str, limit: int = 100) -> Dict[str, Any]:
        """Perform an advanced search using natural language.

        Args:
            query: Natural language query
            limit: Maximum number of records to return

        Returns:
            Search results
        """
        params = {
            "query": query,
            "limit": limit
        }

        # Log the query for debugging
        logger.info(f"Performing advanced search with query: {query}")

        # The tool-specific settings are now handled in _http_call_tool
        # We don't need to specify timeout, use_polling, max_polls, or poll_interval
        result = self.call_tool("advanced_search", params)

        # Check if the search was successful but returned no results
        if result.get("success", False) and not result.get("data") and not result.get("result"):
            logger.warning(f"Advanced search returned no results for query: {query}")

            # Add a helpful message
            result["data"] = f"No results found for query: {query}\n\nThis could be because:\n1. There are no matching records in the database\n2. The query couldn't be properly parsed\n3. The models or fields mentioned don't exist in your Odoo instance\n4. The server is still processing your request - try again in a few moments"

        return result

    def retrieve_odoo_documentation(self, query: str, max_results: int = 5, use_gemini: bool = True, use_online_search: bool = True) -> Dict[str, Any]:
        """Retrieve information from Odoo 18 documentation.

        Args:
            query: The query to search for
            max_results: Maximum number of results to return
            use_gemini: Whether to use Gemini LLM for summarization
            use_online_search: Whether to include online search results

        Returns:
            Documentation results
        """
        params = {
            "query": query,
            "max_results": max_results,
            "use_gemini": use_gemini,
            "use_online_search": use_online_search
        }

        # Log the query for debugging
        logger.info(f"Retrieving Odoo documentation with query: {query} (Gemini: {use_gemini}, Online Search: {use_online_search})")

        # Log environment variables for debugging (without showing sensitive values)
        brave_api_key = os.getenv('BRAVE_API_KEY')
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        logger.info(f"Environment check - BRAVE_API_KEY set: {'Yes' if brave_api_key else 'No'}")
        logger.info(f"Environment check - GEMINI_API_KEY set: {'Yes' if gemini_api_key else 'No'}")

        # The tool-specific settings are now handled in _http_call_tool
        return self.call_tool("retrieve_odoo_documentation", params)

    def run_odoo_code_agent(self, query: str, use_gemini: bool = False,
                           use_ollama: bool = False, no_llm: bool = False,
                           feedback: Optional[str] = None,
                           save_to_files: bool = False, output_dir: Optional[str] = None,
                           wait_for_validation: bool = False, current_phase: Optional[str] = None,
                           state_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run the Odoo code agent.

        Args:
            query: The natural language query describing the module to create
            use_gemini: Whether to use Google Gemini as a fallback
            use_ollama: Whether to use Ollama as a fallback
            no_llm: Whether to disable all LLM models and use fallback analysis only
            feedback: Optional feedback to incorporate
            save_to_files: Whether to save the generated files to disk
            output_dir: Directory to save the generated files to
            wait_for_validation: Whether to wait for human validation at validation points
            current_phase: The current phase to resume from (if continuing execution)
            state_dict: Serialized state to resume from (if continuing execution)

        Returns:
            Code generation results
        """
        # If no_llm is True, set use_gemini and use_ollama to False
        if no_llm:
            use_gemini = False
            use_ollama = False

        params = {
            "query": query,
            "use_gemini": use_gemini,
            "use_ollama": use_ollama
        }

        if feedback:
            params["feedback"] = feedback

        if save_to_files:
            params["save_to_files"] = save_to_files

        if output_dir:
            params["output_dir"] = output_dir

        if wait_for_validation:
            params["wait_for_validation"] = wait_for_validation

        if current_phase:
            params["current_phase"] = current_phase

        if state_dict:
            params["state_dict"] = state_dict

        # Log the query for debugging
        logger.info(f"Running Odoo code agent with query: {query}")
        logger.info(f"Wait for validation: {wait_for_validation}, Current phase: {current_phase}")

        # The tool-specific settings are now handled in _http_call_tool
        return self.call_tool("run_odoo_code_agent_tool", params)

    def export_records_to_csv(self, model_name: str, fields: Optional[List[str]] = None,
                             filter_domain: Optional[str] = None, limit: int = 1000,
                             export_path: Optional[str] = None) -> Dict[str, Any]:
        """Export records from an Odoo model to a CSV file.

        Args:
            model_name: The technical name of the Odoo model to export
            fields: List of field names to export
            filter_domain: Domain filter in string format
            limit: Maximum number of records to export
            export_path: Path to export the CSV file

        Returns:
            Export results
        """
        params = {
            "model_name": model_name,
            "limit": limit
        }

        if fields:
            params["fields"] = fields

        if filter_domain:
            params["filter_domain"] = filter_domain

        if export_path:
            params["export_path"] = export_path

        # Log the export operation
        logger.info(f"Exporting records from {model_name} to {export_path or 'default path'}")

        # The tool-specific settings are now handled in _http_call_tool
        return self.call_tool("export_records_to_csv", params)

    def import_records_from_csv(self, input_path: str, model_name: str,
                               field_mapping: Optional[str] = None,
                               create_if_not_exists: bool = True,
                               update_if_exists: bool = True) -> Dict[str, Any]:
        """Import records from a CSV file into an Odoo model.

        Args:
            input_path: Path to the CSV file to import
            model_name: The technical name of the Odoo model to import into
            field_mapping: JSON string with mapping from CSV field names to Odoo field names
            create_if_not_exists: Whether to create new records if they don't exist
            update_if_exists: Whether to update existing records

        Returns:
            Import results
        """
        params = {
            "input_path": input_path,
            "model_name": model_name,
            "create_if_not_exists": create_if_not_exists,
            "update_if_exists": update_if_exists
        }

        if field_mapping:
            params["field_mapping"] = field_mapping

        # Log the import operation
        logger.info(f"Importing records from {input_path} to {model_name}")

        # The tool-specific settings are now handled in _http_call_tool
        return self.call_tool("import_records_from_csv", params)

    async def close(self) -> None:
        """Close the MCP connection and clean up resources."""
        # Nothing to do for HTTP connection
        logger.info("MCP connection closed")

    def __del__(self):
        """Destructor to ensure resources are cleaned up."""
        # Nothing to do for HTTP connection
        pass