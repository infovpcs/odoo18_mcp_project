#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import traceback

# Set up basic logging
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("odoo_mcp")

try:
    """
    MCP Server for Odoo 18 Integration

    This module provides an MCP server implementation using the standard MCP Python SDK
    that integrates with our existing Odoo 18 MCP project.
    """

    import os
    import json
    import xmlrpc.client
    from typing import Dict, Any, List, Optional, Union, Tuple
    from contextlib import asynccontextmanager
    from collections.abc import AsyncIterator
    from dotenv import load_dotenv

    # Import the direct export/import implementation
    from direct_export_import import export_records, import_records

    # Import the advanced search implementation
    from advanced_search import AdvancedSearch

    from mcp.server.fastmcp import FastMCP, Context, Image

    # Load environment variables
    load_dotenv()

    # Get Odoo connection details from environment variables
    ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
    ODOO_DB = os.getenv("ODOO_DB", "llmdb18")
    ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
    ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

    logger.info(f"Connecting to Odoo at {ODOO_URL}, database {ODOO_DB}")

    # Odoo Model Discovery class
    class OdooModelDiscovery:
        def __init__(self, url, db, username, password):
            self.url = url
            self.db = db
            self.username = username
            self.password = password
            self.uid = None
            self.models_proxy = None
            self._connect()

        def _connect(self):
            """Establish connection to Odoo server"""
            try:
                common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common")
                self.uid = common.authenticate(self.db, self.username, self.password, {})
                if not self.uid:
                    logger.error("Authentication failed")
                    raise Exception("Authentication failed")
                self.models_proxy = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object")
                logger.info(f"Connected to Odoo as user ID {self.uid}")
            except Exception as e:
                logger.error(f"Error connecting to Odoo: {str(e)}")
                raise

        def get_all_models(self):
            """Get all available models"""
            try:
                model_ids = self.models_proxy.execute_kw(
                    self.db, self.uid, self.password,
                    'ir.model', 'search',
                    [[('transient', '=', False)]],  # Exclude transient models
                    {'order': 'model'}
                )

                models = self.models_proxy.execute_kw(
                    self.db, self.uid, self.password,
                    'ir.model', 'read',
                    [model_ids],
                    {'fields': ['name', 'model', 'description']}
                )
                return models
            except Exception as e:
                logger.error(f"Error getting models: {str(e)}")
                return []

        def get_model_fields(self, model_name):
            """Get all fields for a specific model"""
            try:
                fields = self.models_proxy.execute_kw(
                    self.db, self.uid, self.password,
                    model_name, 'fields_get',
                    [],
                    {'attributes': ['string', 'help', 'type', 'required', 'readonly', 'selection', 'relation']}
                )
                return fields
            except Exception as e:
                logger.error(f"Error getting fields for {model_name}: {str(e)}")
                return {}

        def get_model_records(self, model_name, limit=10, offset=0, domain=None):
            """Get records for a specific model"""
            if domain is None:
                domain = []

            try:
                # Get fields first to determine what to display
                fields = self.get_model_fields(model_name)

                # Select fields to display (prioritize name, id, and a few other common fields)
                fields_to_show = ['id']
                if 'name' in fields:
                    fields_to_show.append('name')

                # Add a few more useful fields based on type
                for field_name, field_info in fields.items():
                    if field_name in ['email', 'phone', 'default_code', 'code', 'reference', 'list_price', 'standard_price']:
                        fields_to_show.append(field_name)

                    # Limit to reasonable number of fields
                    if len(fields_to_show) >= 5:
                        break

                # Get records
                records = self.models_proxy.execute_kw(
                    self.db, self.uid, self.password,
                    model_name, 'search_read',
                    [domain],
                    {'fields': fields_to_show, 'limit': limit, 'offset': offset}
                )
                return records, fields_to_show, fields
            except Exception as e:
                logger.error(f"Error getting records for {model_name}: {str(e)}")
                return [], [], {}

        def get_model_schema(self, model_name):
            """Get detailed schema information for a model"""
            try:
                # Get model info - Odoo 18 may not have 'description' field in ir.model
                try:
                    model_info = self.models_proxy.execute_kw(
                        self.db, self.uid, self.password,
                        'ir.model', 'search',
                        [[('model', '=', model_name)]]
                    )

                    if model_info:
                        model_info = self.models_proxy.execute_kw(
                            self.db, self.uid, self.password,
                            'ir.model', 'read',
                            [model_info],
                            {'fields': ['name', 'model']}
                        )
                    else:
                        model_info = []
                except Exception as e:
                    logger.error(f"Error getting model info: {str(e)}")
                    model_info = []

                if not model_info:
                    return None

                # Get fields
                fields = self.get_model_fields(model_name)

                # Get required fields
                required_fields = [field for field, info in fields.items() if info.get('required', False)]

                # Get recommended fields for creation (required + important non-required fields)
                create_fields = required_fields.copy()
                for field, info in fields.items():
                    if field in ['name', 'code', 'default_code', 'email', 'phone', 'list_price'] and field not in create_fields:
                        create_fields.append(field)

                return {
                    "model": model_info[0] if model_info else {},
                    "fields": fields,
                    "required_fields": required_fields,
                    "create_fields": create_fields
                }
            except Exception as e:
                logger.error(f"Error getting schema for {model_name}: {str(e)}")
                return None

        def create_record(self, model_name, values):
            """Create a new record in a model"""
            try:
                record_id = self.models_proxy.execute_kw(
                    self.db, self.uid, self.password,
                    model_name, 'create',
                    [values]
                )
                return record_id
            except Exception as e:
                logger.error(f"Error creating record in {model_name}: {str(e)}")
                return None

        def update_record(self, model_name, record_id, values):
            """Update an existing record"""
            try:
                result = self.models_proxy.execute_kw(
                    self.db, self.uid, self.password,
                    model_name, 'write',
                    [[record_id], values]
                )
                return result
            except Exception as e:
                logger.error(f"Error updating record {record_id} in {model_name}: {str(e)}")
                return False

        def delete_record(self, model_name, record_id):
            """Delete a record"""
            try:
                result = self.models_proxy.execute_kw(
                    self.db, self.uid, self.password,
                    model_name, 'unlink',
                    [[record_id]]
                )
                return result
            except Exception as e:
                logger.error(f"Error deleting record {record_id} from {model_name}: {str(e)}")
                return False

        def execute_method(self, model_name, method, args_list, kwargs_dict=None):
            """Execute a custom method on a model

            Args:
                model_name: The name of the model
                method: The method to execute
                args_list: List of positional arguments
                kwargs_dict: Dictionary of keyword arguments (optional)

            Returns:
                The result of the method execution
            """
            try:
                if kwargs_dict:
                    # If we have keyword arguments, pass them as the 7th parameter
                    logger.debug(f"Executing {model_name}.{method} with args={args_list} and kwargs={kwargs_dict}")
                    result = self.models_proxy.execute_kw(
                        self.db, self.uid, self.password,
                        model_name, method, args_list, kwargs_dict
                    )
                else:
                    # Otherwise, just pass the positional arguments
                    logger.debug(f"Executing {model_name}.{method} with args={args_list}")
                    result = self.models_proxy.execute_kw(
                        self.db, self.uid, self.password,
                        model_name, method, args_list
                    )
                return result
            except Exception as e:
                logger.error(f"Error executing method {method} on {model_name}: {str(e)}")
                raise

    # Initialize Odoo model discovery
    try:
        model_discovery = OdooModelDiscovery(ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
        logger.info("Odoo model discovery initialized successfully")

        # Initialize advanced search
        advanced_search_instance = AdvancedSearch(model_discovery)
        logger.info("Advanced search initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Odoo model discovery: {str(e)}")
        model_discovery = None
        advanced_search_instance = None

    # Create the MCP server
    mcp = FastMCP(
        "Odoo 18 MCP",
        description="Dynamic Odoo 18 integration with MCP",
        dependencies=["fastapi", "pydantic", "requests"]
    )

    # Resource for discovering available models
    @mcp.resource("odoo://models/all")
    def get_all_models() -> str:
        """Get a list of all available Odoo models."""
        if not model_discovery:
            return "# Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."

        try:
            models = model_discovery.get_all_models()

            # Format the response
            result = "# Available Odoo Models\n\n"

            if not models:
                return result + "No models found or could not retrieve models."

            for model in models[:50]:  # Limit to 50 models to avoid too much text
                result += f"- **{model['name']}** (`{model['model']}`)\n"

            if len(models) > 50:
                result += f"\n*...and {len(models) - 50} more models*\n"

            return result
        except Exception as e:
            return f"# Error retrieving models\n\n{str(e)}"

    # Dynamic resource for model metadata
    @mcp.resource("odoo://model/{model_name}/metadata")
    def get_model_metadata(model_name: str) -> str:
        """Get metadata for a specific Odoo model."""
        if not model_discovery:
            return "# Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."

        try:
            metadata = model_discovery.get_model_schema(model_name)

            if not metadata:
                return f"# Metadata for {model_name}\n\nNo metadata available for this model."

            # Format the metadata as a readable string
            result = f"# Metadata for {model_name}\n\n"

            # Model info
            model_info = metadata.get("model", {})
            if model_info:
                result += f"## Model Information\n\n"
                result += f"- **Name**: {model_info.get('name')}\n"
                result += f"- **Technical Name**: {model_info.get('model')}\n"
                if model_info.get('description'):
                    result += f"- **Description**: {model_info.get('description')}\n"

            # Fields
            fields = metadata.get("fields", {})
            if fields:
                result += f"\n## Fields ({len(fields)})\n\n"
                for field_name, field_info in list(fields.items())[:20]:  # Limit to 20 fields
                    field_type = field_info.get('type', 'unknown')
                    field_string = field_info.get('string', field_name)
                    required = field_info.get('required', False)
                    readonly = field_info.get('readonly', False)

                    result += f"- **{field_string}** (`{field_name}`): {field_type}"
                    if required:
                        result += " (Required)"
                    if readonly:
                        result += " (Readonly)"
                    result += "\n"

                if len(fields) > 20:
                    result += f"\n*...and {len(fields) - 20} more fields*\n"

            # Required fields
            required_fields = metadata.get("required_fields", [])
            if required_fields:
                result += f"\n## Required Fields\n\n"
                result += ", ".join([f"`{field}`" for field in required_fields])
                result += "\n"

            # Recommended fields
            create_fields = metadata.get("create_fields", [])
            if create_fields:
                result += f"\n## Recommended Create Fields\n\n"
                result += ", ".join([f"`{field}`" for field in create_fields])
                result += "\n"

            return result
        except Exception as e:
            return f"# Error retrieving metadata\n\n{str(e)}"

    # Dynamic resource for model records
    @mcp.resource("odoo://model/{model_name}/records")
    def get_model_records(model_name: str) -> str:
        """Get records for a specific Odoo model."""
        if not model_discovery:
            return "# Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."

        try:
            records, fields_to_show, fields_info = model_discovery.get_model_records(model_name)

            # Format the records as a readable string
            result = f"# Records for {model_name}\n\n"

            if not records:
                return result + "No records found."

            # Create a table header
            header = "| ID | " + " | ".join([fields_info.get(field, {}).get('string', field) for field in fields_to_show if field != 'id']) + " |\n"
            separator = "|----| " + " | ".join(["----" for _ in fields_to_show if _ != 'id']) + " |\n"

            result += header + separator

            # Add records to the table
            for record in records:
                record_id = record.get('id', 'N/A')
                row = f"| {record_id} | "
                row += " | ".join([str(record.get(field, '')) for field in fields_to_show if field != 'id'])
                row += " |\n"
                result += row

            return result
        except Exception as e:
            return f"# Error retrieving records\n\n{str(e)}"

    # Tool for searching records
    @mcp.tool()
    def search_records(model_name: str, query: str) -> str:
        """Search for records in an Odoo model.

        Args:
            model_name: The technical name of the Odoo model to search
            query: The search query (will be converted to a domain)

        Returns:
            A formatted string with the search results
        """
        if not model_discovery:
            return "# Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."

        try:
            # Create a simple domain based on the query
            domain = []
            if query:
                if "List out all" in query or "list all" in query.lower():
                    # Just list all records with a reasonable limit
                    domain = []
                else:
                    # Try to find records matching the query in name field
                    domain = [('name', 'ilike', query)]

            records, fields_to_show, fields_info = model_discovery.get_model_records(
                model_name, limit=10, domain=domain
            )

            # Format the results
            result = f"# Search Results for '{query}' in {model_name}\n\n"

            if not records:
                return result + "No records found matching the query."

            # Create a table header
            header = "| ID | " + " | ".join([fields_info.get(field, {}).get('string', field) for field in fields_to_show if field != 'id']) + " |\n"
            separator = "|----| " + " | ".join(["----" for _ in fields_to_show if _ != 'id']) + " |\n"

            result += header + separator

            # Add records to the table
            for record in records:
                record_id = record.get('id', 'N/A')
                row = f"| {record_id} | "
                row += " | ".join([str(record.get(field, '')) for field in fields_to_show if field != 'id'])
                row += " |\n"
                result += row

            return result
        except Exception as e:
            return f"# Error searching records\n\n{str(e)}"

    # Tool for advanced searching across models
    @mcp.tool()
    def advanced_search(query: str, limit: int = 10) -> str:
        """Perform an advanced search using natural language queries.

        This tool can handle complex queries across multiple Odoo models,
        automatically identifying the relevant models and fields based on the query.

        Examples:
        - "List all sales orders under the customer's name, Gemini Furniture"
        - "List all customer invoices for the customer name Wood Corner"
        - "List out all projects"
        - "List out all Project tasks for project name Research & Development"
        - "List all unpaid bills with respect of vendor details"
        - "List all project tasks according to their deadline date"

        Args:
            query: Natural language query string
            limit: Maximum number of records to return per model

        Returns:
            A formatted string with the search results
        """
        if not model_discovery or not advanced_search_instance:
            return "# Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."

        try:
            # Execute the query
            return advanced_search_instance.execute_query(query, limit)
        except Exception as e:
            logger.error(f"Error in advanced search: {str(e)}")
            return f"# Error in Advanced Search\n\n{str(e)}"

    # Tool for creating records
    @mcp.tool()
    def create_record(model_name: str, values: Union[str, Dict[str, Any]]) -> str:
        """Create a new record in an Odoo model.

        Args:
            model_name: The technical name of the Odoo model
            values: JSON string or dictionary with field values for the new record

        Returns:
            A confirmation message with the new record ID
        """
        if not model_discovery:
            return "# Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."

        try:
            # Handle both string and dictionary inputs for values
            values_dict = {}
            if isinstance(values, str):
                try:
                    values_dict = json.loads(values)
                except json.JSONDecodeError:
                    return "Error: Invalid JSON format for values. Please provide a valid JSON object."
            elif isinstance(values, dict):
                values_dict = values
            else:
                return f"Error: Invalid type for values: {type(values)}. Please provide a JSON string or dictionary."

            # Log the values for debugging
            logger.debug(f"Creating record with values: {values_dict}")

            # Create the record
            record_id = model_discovery.create_record(model_name, values_dict)

            if not record_id:
                return f"Error creating record: Unknown error"

            # Return a success message
            return f"Record created successfully with ID: {record_id}"
        except Exception as e:
            logger.error(f"Error creating record: {str(e)}")
            return f"Error creating record: {str(e)}"

    # Tool for updating records
    @mcp.tool()
    def update_record(model_name: str, record_id: int, values: Union[str, Dict[str, Any]]) -> str:
        """Update an existing record in an Odoo model.

        Args:
            model_name: The technical name of the Odoo model
            record_id: The ID of the record to update
            values: JSON string or dictionary with field values to update

        Returns:
            A confirmation message
        """
        if not model_discovery:
            return "# Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."

        try:
            # Handle both string and dictionary inputs for values
            values_dict = {}
            if isinstance(values, str):
                try:
                    values_dict = json.loads(values)
                except json.JSONDecodeError:
                    return "Error: Invalid JSON format for values. Please provide a valid JSON object."
            elif isinstance(values, dict):
                values_dict = values
            else:
                return f"Error: Invalid type for values: {type(values)}. Please provide a JSON string or dictionary."

            # Log the values for debugging
            logger.debug(f"Updating record {record_id} with values: {values_dict}")

            # Update the record
            result = model_discovery.update_record(model_name, record_id, values_dict)

            if not result:
                return f"Error updating record: Unknown error"

            # Return a success message
            return f"Record {record_id} updated successfully"
        except Exception as e:
            logger.error(f"Error updating record: {str(e)}")
            return f"Error updating record: {str(e)}"

    # Tool for deleting records
    @mcp.tool()
    def delete_record(model_name: str, record_id: int) -> str:
        """Delete a record from an Odoo model.

        Args:
            model_name: The technical name of the Odoo model
            record_id: The ID of the record to delete

        Returns:
            A confirmation message
        """
        if not model_discovery:
            return "# Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."

        try:
            # Delete the record
            result = model_discovery.delete_record(model_name, record_id)

            if not result:
                return f"Error deleting record: Unknown error"

            # Return a success message
            return f"Record {record_id} deleted successfully"
        except Exception as e:
            return f"Error deleting record: {str(e)}"

    # Tool for executing custom Odoo methods
    @mcp.tool()
    def execute_method(model_name: str, method: str, args: Union[str, List, Dict[str, Any]]) -> str:
        """Execute a custom method on an Odoo model.

        Args:
            model_name: The technical name of the Odoo model
            method: The method name to execute
            args: Arguments for the method (can be a JSON string, list, or dictionary)

        Returns:
            The result of the method execution
        """
        if not model_discovery:
            return "# Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."

        try:
            # Handle different types of args input
            args_list = []
            kwargs_dict = None

            if isinstance(args, str):
                # If it's a string, try to parse it as JSON
                try:
                    parsed_args = json.loads(args)
                    if isinstance(parsed_args, list):
                        args_list = parsed_args
                    elif isinstance(parsed_args, dict):
                        # For name_search and similar methods, dictionaries should be passed as kwargs
                        if method in ['name_search', 'search', 'search_read', 'fields_get']:
                            kwargs_dict = parsed_args
                            args_list = []
                        else:
                            args_list = [parsed_args]
                    else:
                        args_list = [parsed_args]
                except json.JSONDecodeError:
                    # If not valid JSON, try to interpret as a simple list or string
                    if args.startswith('[') and args.endswith(']'):
                        # Try to evaluate as a Python list
                        import ast
                        try:
                            args_list = ast.literal_eval(args)
                        except (SyntaxError, ValueError):
                            # If that fails, treat as a single string argument
                            args_list = [args]
                    else:
                        # Treat as a single string argument
                        args_list = [args]
            elif isinstance(args, list):
                # If it's already a list, use it directly
                args_list = args
            elif isinstance(args, dict):
                # For name_search and similar methods, dictionaries should be passed as kwargs
                if method in ['name_search', 'search', 'search_read', 'fields_get']:
                    kwargs_dict = args
                    args_list = []
                else:
                    args_list = [args]
            else:
                # For any other type, convert to string and use as a single argument
                args_list = [str(args)]

            # Special handling for name_search with a single string
            if method == 'name_search' and len(args_list) == 1 and isinstance(args_list[0], str):
                # If args is just a string for name_search, convert it to the proper format
                kwargs_dict = {'name': args_list[0]}
                args_list = []

            # Log the arguments for debugging
            if kwargs_dict:
                logger.debug(f"Executing method {method} on {model_name} with args: {args_list} and kwargs: {kwargs_dict}")
            else:
                logger.debug(f"Executing method {method} on {model_name} with args: {args_list}")

            # Execute the method
            result = model_discovery.execute_method(model_name, method, args_list, kwargs_dict)

            # Format the result
            if isinstance(result, (dict, list)):
                return json.dumps(result, indent=2)
            else:
                return str(result)
        except Exception as e:
            logger.error(f"Error executing method: {str(e)}")
            return f"Error executing method: {str(e)}"

    # Tool for getting field importance
    @mcp.tool()
    def analyze_field_importance(model_name: str, use_nlp: bool = True) -> str:
        """Analyze the importance of fields in an Odoo model.

        Args:
            model_name: The technical name of the Odoo model
            use_nlp: Whether to use NLP for analysis

        Returns:
            A formatted string with field importance analysis
        """
        if not model_discovery:
            return "# Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."

        try:
            # Get model fields directly
            fields = model_discovery.get_model_fields(model_name)

            if not fields:
                return f"# Field Importance Analysis for {model_name}\n\nNo fields available for this model."

            # Calculate field importance
            importance = {}
            for field_name, field_info in fields.items():
                # Base score
                score = 50

                # Required fields are more important
                if field_info.get('required', False):
                    score += 30

                # Common important fields
                if field_name in ['name', 'code', 'default_code']:
                    score += 20
                elif field_name in ['email', 'phone', 'mobile']:
                    score += 15
                elif field_name in ['street', 'city', 'zip', 'country_id']:
                    score += 10
                elif field_name in ['list_price', 'standard_price', 'price']:
                    score += 15

                # Field types importance
                field_type = field_info.get('type', '')
                if field_type == 'many2one':
                    score += 5
                elif field_type == 'one2many':
                    score += 3

                # Cap at 100
                importance[field_name] = min(score, 100)

            # Format the importance as a readable string
            result = f"# Field Importance Analysis for {model_name}\n\n"

            # Sort fields by importance
            sorted_fields = sorted(importance.items(), key=lambda x: x[1], reverse=True)

            # Create a table
            result += "| Field | Importance |\n"
            result += "|-------|-----------|\n"

            for field, score in sorted_fields[:20]:  # Limit to 20 fields
                result += f"| {field} | {score} |\n"

            if len(sorted_fields) > 20:
                result += f"\n*...and {len(sorted_fields) - 20} more fields*\n"

            return result
        except Exception as e:
            return f"# Error analyzing field importance\n\n{str(e)}"

    # Tool for getting field groups
    @mcp.tool()
    def get_field_groups(model_name: str) -> str:
        """Get field groups for an Odoo model.

        Args:
            model_name: The technical name of the Odoo model

        Returns:
            A formatted string with field groups
        """
        if not model_discovery:
            return "# Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."

        try:
            # Get model fields directly
            fields = model_discovery.get_model_fields(model_name)

            if not fields:
                return f"# Field Groups for {model_name}\n\nNo fields available for this model."

            # Group fields by purpose
            groups = {
                "basic_info": [],
                "contact_info": [],
                "address_info": [],
                "business_info": [],
                "pricing_info": [],
                "inventory_info": [],
                "categorization": [],
                "dates": [],
                "other": []
            }

            for field_name, field_info in fields.items():
                field_type = field_info.get('type', '')

                # Skip binary fields and attachments
                if field_type == 'binary' or 'attachment' in field_name:
                    continue

                # Basic info
                if field_name in ['name', 'display_name', 'title', 'description', 'note', 'comment', 'lang', 'company_type']:
                    groups["basic_info"].append(field_name)

                # Contact info
                elif field_name in ['email', 'phone', 'mobile', 'website', 'fax']:
                    groups["contact_info"].append(field_name)

                # Address info
                elif field_name in ['street', 'street2', 'city', 'state_id', 'zip', 'country_id']:
                    groups["address_info"].append(field_name)

                # Business info
                elif field_name in ['vat', 'ref', 'industry_id', 'company_id', 'user_id', 'partner_id', 'currency_id']:
                    groups["business_info"].append(field_name)

                # Pricing info
                elif 'price' in field_name or field_name in ['list_price', 'standard_price', 'cost']:
                    groups["pricing_info"].append(field_name)

                # Inventory info
                elif field_name in ['default_code', 'barcode', 'qty_available', 'virtual_available', 'incoming_qty', 'outgoing_qty']:
                    groups["inventory_info"].append(field_name)

                # Categorization
                elif field_name in ['categ_id', 'uom_id', 'uom_po_id', 'product_tmpl_id', 'tag_ids', 'category_id']:
                    groups["categorization"].append(field_name)

                # Dates
                elif 'date' in field_name or field_type == 'datetime' or field_type == 'date':
                    groups["dates"].append(field_name)

                # Other
                else:
                    groups["other"].append(field_name)

            # Remove empty groups
            groups = {k: v for k, v in groups.items() if v}

            # Format the groups as a readable string
            result = f"# Field Groups for {model_name}\n\n"

            for group_name, fields in groups.items():
                result += f"## {group_name.replace('_', ' ').title()}\n\n"
                for field in fields[:10]:  # Limit to 10 fields per group
                    result += f"- `{field}`\n"

                if len(fields) > 10:
                    result += f"\n*...and {len(fields) - 10} more fields*\n"

                result += "\n"

            return result
        except Exception as e:
            return f"# Error getting field groups\n\n{str(e)}"

    # Tool for getting a record template
    @mcp.tool()
    def get_record_template(model_name: str) -> str:
        """Get a template for creating a record in an Odoo model.

        Args:
            model_name: The technical name of the Odoo model

        Returns:
            A JSON template for creating a record
        """
        if not model_discovery:
            return "# Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."

        try:
            # Get model schema
            schema = model_discovery.get_model_schema(model_name)

            # Create a template with recommended fields
            template = {}

            # If we couldn't get the schema, provide a default template based on the model
            if not schema:
                if model_name == 'res.partner':
                    template = {
                        "name": "",
                        "email": "",
                        "phone": "",
                        "is_company": False,
                        "street": "",
                        "city": "",
                        "country_id": False  # Will need to be set to a valid country ID
                    }
                elif model_name == 'product.product':
                    template = {
                        "name": "",
                        "default_code": "",  # Internal reference
                        "list_price": 0.0,   # Sales price
                        "standard_price": 0.0,  # Cost
                        "type": "consu",     # Product type: 'consu', 'service', 'product'
                        "categ_id": False,   # Will need to be set to a valid category ID
                        "uom_id": False,     # Will need to be set to a valid UoM ID
                        "uom_po_id": False,  # Will need to be set to a valid Purchase UoM ID
                        "description": ""    # Description
                    }
                else:
                    # Generic template with just a name field
                    template = {"name": ""}

                return json.dumps(template, indent=2)

            # If we have a schema, use it to create a template
            fields = schema.get("fields", {})
            create_fields = schema.get("create_fields", [])

            # If no create_fields were found, add some common fields based on the model
            if not create_fields:
                if model_name == 'res.partner':
                    create_fields = ['name', 'email', 'phone', 'is_company', 'street', 'city', 'country_id']
                elif model_name == 'product.product':
                    create_fields = ['name', 'default_code', 'list_price', 'standard_price', 'type', 'categ_id', 'uom_id', 'uom_po_id', 'description']
                else:
                    # For other models, just add the name field
                    create_fields = ['name']

            for field in create_fields:
                if field in fields:
                    field_info = fields[field]
                    field_type = field_info.get('type')

                    # Set default values based on field type
                    if field_type == 'char':
                        template[field] = ""
                    elif field_type == 'integer':
                        template[field] = 0
                    elif field_type == 'float':
                        template[field] = 0.0
                    elif field_type == 'boolean':
                        template[field] = False
                    elif field_type == 'many2one':
                        template[field] = False
                    elif field_type == 'selection':
                        selections = field_info.get('selection', [])
                        template[field] = selections[0][0] if selections else False
                    elif field_type == 'text' or field_type == 'html':
                        template[field] = ""
                    else:
                        template[field] = False
                else:
                    # Field not found in fields, add it with a default value based on field name
                    if field == 'name' or field.endswith('_name') or field == 'description':
                        template[field] = ""
                    elif field.endswith('_price') or field.endswith('_cost'):
                        template[field] = 0.0
                    elif field.endswith('_id'):
                        template[field] = False
                    elif field.startswith('is_') or field.startswith('has_'):
                        template[field] = False
                    else:
                        template[field] = ""

            return json.dumps(template, indent=2)
        except Exception as e:
            return f"# Error creating template\n\n{str(e)}"

    # Tool for exporting records to CSV
    @mcp.tool()
    def export_records_to_csv(model_name: str, fields: Optional[List[str]] = None, filter_domain: Optional[Union[str, List]] = None, limit: int = 1000, export_path: Optional[str] = None) -> str:
        """Export records from an Odoo model to a CSV file.

        Args:
            model_name: The technical name of the Odoo model to export
            fields: List of field names to export (if None, all fields are exported)
            filter_domain: Domain filter in string format (e.g., "[('name', 'ilike', 'Test')]")
            limit: Maximum number of records to export
            export_path: Path to export the CSV file (if None, a default path is used)

        Returns:
            A confirmation message with the export results
        """
        if not model_discovery:
            return "# Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."

        try:
            # Validate model exists
            model_schema = model_discovery.get_model_schema(model_name)
            if not model_schema:
                return f"# Error: Invalid Model\n\nThe model '{model_name}' does not exist in the Odoo database."

            # Get available fields for the model
            available_fields = model_schema.get("fields", {})
            if not available_fields:
                return f"# Error: No Fields Available\n\nCould not retrieve fields for model '{model_name}'."

            # Validate fields if provided
            if fields:
                invalid_fields = [field for field in fields if field not in available_fields]
                if invalid_fields:
                    return f"# Error: Invalid Fields\n\nThe following fields do not exist in model '{model_name}':\n- {', '.join(invalid_fields)}\n\nAvailable fields include:\n- {', '.join(list(available_fields.keys())[:20])}\n- ..."

            # Parse filter domain if provided
            domain = []
            if filter_domain:
                # If filter_domain is already a list, use it directly
                if isinstance(filter_domain, list):
                    domain = filter_domain
                else:
                    try:
                        # Try to parse as JSON
                        domain = json.loads(filter_domain)
                    except (json.JSONDecodeError, TypeError):
                        try:
                            # Try to evaluate as Python expression
                            import ast
                            domain = ast.literal_eval(filter_domain)
                        except (SyntaxError, ValueError):
                            return f"# Error: Invalid Filter Domain\n\nThe filter domain format is invalid: {filter_domain}\n\nExample valid formats:\n- [['name', 'ilike', 'Test']]\n- [('customer_rank', '>', 0)]\n- String representation: \"[('move_type', 'in', ['out_invoice', 'in_invoice']), ('state', '=', 'posted')]\""

                # Validate domain fields
                try:
                    for condition in domain:
                        if isinstance(condition, (list, tuple)) and len(condition) >= 3:
                            field_name = condition[0]
                            if field_name not in available_fields and field_name != 'id':
                                return f"# Error: Invalid Domain Field\n\nThe field '{field_name}' in the domain filter does not exist in model '{model_name}'."
                except Exception as e:
                    return f"# Error: Invalid Domain Structure\n\nThe domain filter has an invalid structure: {str(e)}"

            # Set default export path if not provided
            if not export_path:
                model_name_safe = model_name.replace('.', '_')
                export_path = f"./exports/{model_name_safe}_export.csv"

            # Create exports directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(export_path)), exist_ok=True)

            # Run the export flow
            result = export_records(
                model_name=model_name,
                fields=fields,
                filter_domain=domain,
                limit=limit,
                export_path=export_path
            )

            if not result["success"]:
                return f"# Error Exporting Records\n\n{result.get('error', 'Unknown error')}"

            # Format the results
            output = f"# Export Results\n\n"
            output += f"- **Model**: {result['model_name']}\n"
            output += f"- **Fields**: {', '.join(result['selected_fields'])}\n"
            output += f"- **Total Records**: {result['total_records']}\n"
            output += f"- **Exported Records**: {result['exported_records']}\n"
            output += f"- **Export Path**: {result['export_path']}\n"

            # Add field type information for reference
            output += f"\n## Field Types\n\n"
            output += "This information can be useful when importing the data back:\n\n"

            for field in result['selected_fields'][:10]:  # Limit to 10 fields to avoid too much text
                if field in available_fields:
                    field_type = available_fields[field].get('type', 'unknown')
                    field_string = available_fields[field].get('string', field)
                    output += f"- **{field_string}** (`{field}`): {field_type}\n"

            if len(result['selected_fields']) > 10:
                output += f"\n*...and {len(result['selected_fields']) - 10} more fields*\n"

            return output

        except Exception as e:
            logger.error(f"Error exporting records: {str(e)}")
            return f"# Error Exporting Records\n\n{str(e)}"

    # Tool for exporting related records to CSV
    @mcp.tool()
    def export_related_records_to_csv(parent_model: str, child_model: str, relation_field: str,
                                     parent_fields: Optional[List[str]] = None, child_fields: Optional[List[str]] = None,
                                     filter_domain: Optional[Union[str, List]] = None, limit: int = 1000,
                                     export_path: Optional[str] = None, move_type: Optional[str] = None) -> str:
        """Export records from related models (parent and child) to a structured CSV file.

        Args:
            parent_model: The technical name of the parent Odoo model (e.g., 'account.move')
            child_model: The technical name of the child Odoo model (e.g., 'account.move.line')
            relation_field: The field in the child model that relates to the parent (e.g., 'move_id')
            parent_fields: List of field names to export from the parent model
            child_fields: List of field names to export from the child model
            filter_domain: Domain filter for the parent model in string format
            limit: Maximum number of parent records to export
            export_path: Path to export the CSV file (if None, a default path is used)
            move_type: For account.move model, specify the move_type to filter by (e.g., 'out_invoice', 'in_invoice')

        Returns:
            A confirmation message with the export results
        """
        if not model_discovery:
            return "# Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."

        try:
            # Validate parent model exists
            parent_schema = model_discovery.get_model_schema(parent_model)
            if not parent_schema:
                return f"# Error: Invalid Parent Model\n\nThe model '{parent_model}' does not exist in the Odoo database."

            # Validate child model exists
            child_schema = model_discovery.get_model_schema(child_model)
            if not child_schema:
                return f"# Error: Invalid Child Model\n\nThe model '{child_model}' does not exist in the Odoo database."

            # Get available fields for the models
            parent_available_fields = parent_schema.get("fields", {})
            child_available_fields = child_schema.get("fields", {})

            if not parent_available_fields:
                return f"# Error: No Fields Available\n\nCould not retrieve fields for model '{parent_model}'."

            if not child_available_fields:
                return f"# Error: No Fields Available\n\nCould not retrieve fields for model '{child_model}'."

            # Validate relation field exists in child model
            if relation_field not in child_available_fields:
                return f"# Error: Invalid Relation Field\n\nThe field '{relation_field}' does not exist in model '{child_model}'."

            # Validate relation field is a many2one field
            if child_available_fields[relation_field].get('type') != 'many2one':
                return f"# Error: Invalid Relation Field Type\n\nThe field '{relation_field}' in model '{child_model}' is not a many2one field."

            # Validate relation field points to parent model
            if child_available_fields[relation_field].get('relation') != parent_model:
                return f"# Error: Invalid Relation\n\nThe field '{relation_field}' in model '{child_model}' does not point to model '{parent_model}'."

            # Validate parent fields if provided
            if parent_fields:
                invalid_parent_fields = [field for field in parent_fields if field not in parent_available_fields]
                if invalid_parent_fields:
                    return f"# Error: Invalid Parent Fields\n\nThe following fields do not exist in model '{parent_model}':\n- {', '.join(invalid_parent_fields)}\n\nAvailable fields include:\n- {', '.join(list(parent_available_fields.keys())[:20])}\n- ..."

            # Validate child fields if provided
            if child_fields:
                invalid_child_fields = [field for field in child_fields if field not in child_available_fields]
                if invalid_child_fields:
                    return f"# Error: Invalid Child Fields\n\nThe following fields do not exist in model '{child_model}':\n- {', '.join(invalid_child_fields)}\n\nAvailable fields include:\n- {', '.join(list(child_available_fields.keys())[:20])}\n- ..."

            # Parse filter domain if provided
            domain = []
            if filter_domain:
                # If filter_domain is already a list, use it directly
                if isinstance(filter_domain, list):
                    domain = filter_domain
                else:
                    try:
                        # Try to parse as JSON
                        domain = json.loads(filter_domain)
                    except (json.JSONDecodeError, TypeError):
                        try:
                            # Try to evaluate as Python expression
                            import ast
                            domain = ast.literal_eval(filter_domain)
                        except (SyntaxError, ValueError):
                            return f"# Error: Invalid Filter Domain\n\nThe filter domain format is invalid: {filter_domain}\n\nExample valid formats:\n- [['name', 'ilike', 'Test']]\n- [('customer_rank', '>', 0)]\n- String representation: \"[('move_type', 'in', ['out_invoice', 'in_invoice']), ('state', '=', 'posted')]\""

                # Validate domain fields
                try:
                    for condition in domain:
                        if isinstance(condition, (list, tuple)) and len(condition) >= 3:
                            field_name = condition[0]
                            if field_name not in parent_available_fields and field_name != 'id':
                                return f"# Error: Invalid Domain Field\n\nThe field '{field_name}' in the domain filter does not exist in model '{parent_model}'."
                except Exception as e:
                    return f"# Error: Invalid Domain Structure\n\nThe domain filter has an invalid structure: {str(e)}"

            # Set default export path if not provided
            if not export_path:
                parent_model_safe = parent_model.replace('.', '_')
                child_model_safe = child_model.replace('.', '_')
                # Use a path in the current working directory
                export_path = f"./exports/{parent_model_safe}_{child_model_safe}_export.csv"

            # Create exports directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(export_path)), exist_ok=True)

            # Import the direct export/import implementation
            from direct_export_import import export_related_records

            # Add move_type to filter domain if specified
            if parent_model == 'account.move' and move_type:
                # Check if we already have a move_type filter
                has_move_type_filter = False
                for condition in domain:
                    if isinstance(condition, (list, tuple)) and len(condition) >= 3 and condition[0] == 'move_type':
                        has_move_type_filter = True
                        break

                # If no move_type filter, add one based on the specified move_type
                if not has_move_type_filter:
                    if move_type in ['out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt']:
                        domain.append(['move_type', '=', move_type])
                    elif move_type == 'invoice':
                        domain.append(['move_type', 'in', ['out_invoice', 'in_invoice']])
                    elif move_type == 'refund':
                        domain.append(['move_type', 'in', ['out_refund', 'in_refund']])
                    elif move_type == 'receipt':
                        domain.append(['move_type', 'in', ['out_receipt', 'in_receipt']])
                    elif move_type == 'out':
                        domain.append(['move_type', 'in', ['out_invoice', 'out_refund', 'out_receipt']])
                    elif move_type == 'in':
                        domain.append(['move_type', 'in', ['in_invoice', 'in_refund', 'in_receipt']])

                    logger.info(f"Added move_type filter for account.move: {domain[-1]}")

            # Run the export flow
            result = export_related_records(
                parent_model=parent_model,
                child_model=child_model,
                relation_field=relation_field,
                parent_fields=parent_fields,
                child_fields=child_fields,
                filter_domain=domain,
                limit=limit,
                export_path=export_path
            )

            if not result["success"]:
                return f"# Error Exporting Related Records\n\n{result.get('error', 'Unknown error')}"

            # Format the results
            output = f"# Related Records Export Results\n\n"
            output += f"- **Parent Model**: {result['parent_model']}\n"
            output += f"- **Child Model**: {result['child_model']}\n"
            output += f"- **Relation Field**: {result['relation_field']}\n"
            output += f"- **Parent Records**: {result['parent_records']}\n"
            output += f"- **Child Records**: {result['child_records']}\n"
            output += f"- **Combined Records**: {result['combined_records']}\n"
            output += f"- **Export Path**: {result['export_path']}\n"

            # Add field type information for reference
            output += f"\n## Field Types\n\n"
            output += "This information can be useful when importing the data back:\n\n"

            output += "### Parent Fields\n\n"
            for field in result['parent_fields'][:5]:  # Limit to 5 fields to avoid too much text
                if field in parent_available_fields:
                    field_type = parent_available_fields[field].get('type', 'unknown')
                    field_string = parent_available_fields[field].get('string', field)
                    output += f"- **{field_string}** (`parent_{field}`): {field_type}\n"

            if len(result['parent_fields']) > 5:
                output += f"\n*...and {len(result['parent_fields']) - 5} more parent fields*\n"

            output += "\n### Child Fields\n\n"
            for field in result['child_fields'][:5]:  # Limit to 5 fields to avoid too much text
                if field in child_available_fields:
                    field_type = child_available_fields[field].get('type', 'unknown')
                    field_string = child_available_fields[field].get('string', field)
                    output += f"- **{field_string}** (`child_{field}`): {field_type}\n"

            if len(result['child_fields']) > 5:
                output += f"\n*...and {len(result['child_fields']) - 5} more child fields*\n"

            output += f"\n## CSV Structure\n\n"
            output += "The exported CSV file has the following structure:\n\n"
            output += "1. **Metadata columns**:\n"
            output += "   - `_model`: The model(s) for this record (e.g., 'account.move,account.move.line')\n"
            output += "   - `_record_type`: Either 'parent' (parent record only) or 'combined' (parent with child)\n"
            output += "   - `_child_count`: Number of child records for this parent\n"
            output += "   - `_child_index`: Index of this child record (for combined records)\n\n"
            output += "2. **Parent fields**: All parent fields are prefixed with 'parent_'\n"
            output += "3. **Child fields**: All child fields are prefixed with 'child_'\n\n"
            output += "This structure allows for importing the data back while maintaining the parent-child relationships."

            return output

        except Exception as e:
            logger.error(f"Error exporting related records: {str(e)}")
            return f"# Error Exporting Related Records\n\n{str(e)}"

    # Tool for importing related records from CSV
    @mcp.tool()
    def import_related_records_from_csv(import_path: str, parent_model: str, child_model: str, relation_field: str,
                                       create_if_not_exists: bool = True, update_if_exists: bool = True,
                                       draft_only: bool = False, reset_to_draft: bool = False,
                                       skip_readonly_fields: bool = True) -> str:
        """Import records from a structured CSV file into related models (parent and child).

        Args:
            import_path: Path to the CSV file to import
            parent_model: The technical name of the parent Odoo model (e.g., 'account.move')
            child_model: The technical name of the child Odoo model (e.g., 'account.move.line')
            relation_field: The field in the child model that relates to the parent (e.g., 'move_id')
            create_if_not_exists: Whether to create new records if they don't exist
            update_if_exists: Whether to update existing records
            draft_only: Whether to only update records in draft state (important for account.move)
            reset_to_draft: Whether to reset records to draft before updating (use with caution)
            skip_readonly_fields: Whether to automatically skip readonly fields for posted records

        Returns:
            A confirmation message with the import results
        """
        if not model_discovery:
            return "# Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."

        try:
            # Validate parent model exists
            parent_schema = model_discovery.get_model_schema(parent_model)
            if not parent_schema:
                return f"# Error: Invalid Parent Model\n\nThe model '{parent_model}' does not exist in the Odoo database."

            # Validate child model exists
            child_schema = model_discovery.get_model_schema(child_model)
            if not child_schema:
                return f"# Error: Invalid Child Model\n\nThe model '{child_model}' does not exist in the Odoo database."

            # Get available fields for the models
            parent_available_fields = parent_schema.get("fields", {})
            child_available_fields = child_schema.get("fields", {})

            if not parent_available_fields:
                return f"# Error: No Fields Available\n\nCould not retrieve fields for model '{parent_model}'."

            if not child_available_fields:
                return f"# Error: No Fields Available\n\nCould not retrieve fields for model '{child_model}'."

            # Validate relation field exists in child model
            if relation_field not in child_available_fields:
                return f"# Error: Invalid Relation Field\n\nThe field '{relation_field}' does not exist in model '{child_model}'."

            # Validate relation field is a many2one field
            if child_available_fields[relation_field].get('type') != 'many2one':
                return f"# Error: Invalid Relation Field Type\n\nThe field '{relation_field}' in model '{child_model}' is not a many2one field."

            # Validate relation field points to parent model
            if child_available_fields[relation_field].get('relation') != parent_model:
                return f"# Error: Invalid Relation\n\nThe field '{relation_field}' in model '{child_model}' does not point to model '{parent_model}'."

            # Check if import file exists
            if not os.path.exists(import_path):
                return f"# Error: File Not Found\n\nThe file '{import_path}' does not exist."

            # Check if file is a CSV
            if not import_path.lower().endswith('.csv'):
                return f"# Error: Invalid File Format\n\nThe file '{import_path}' is not a CSV file."

            # Import the direct export/import implementation
            from direct_export_import import import_related_records

            # Run the import flow
            result = import_related_records(
                import_path=import_path,
                parent_model=parent_model,
                child_model=child_model,
                relation_field=relation_field,
                create_if_not_exists=create_if_not_exists,
                update_if_exists=update_if_exists,
                draft_only=draft_only,
                reset_to_draft=reset_to_draft,
                skip_readonly_fields=skip_readonly_fields
            )

            if not result["success"]:
                return f"# Error Importing Related Records\n\n{result.get('error', 'Unknown error')}"

            # Format the results
            output = f"# Related Records Import Results\n\n"
            output += f"- **Parent Model**: {result['parent_model']}\n"
            output += f"- **Child Model**: {result['child_model']}\n"
            output += f"- **Relation Field**: {result['relation_field']}\n"
            output += f"- **Total Records**: {result['total_records']}\n"
            output += f"- **Parent Records Created**: {result['parent_created']}\n"
            output += f"- **Parent Records Updated**: {result['parent_updated']}\n"
            output += f"- **Parent Records Failed**: {result['parent_failed']}\n"
            output += f"- **Child Records Created**: {result['child_created']}\n"
            output += f"- **Child Records Updated**: {result['child_updated']}\n"
            output += f"- **Child Records Failed**: {result['child_failed']}\n"

            if result['parent_failed'] > 0 or result['child_failed'] > 0:
                output += f"\n## Failed Records\n\n"

                # Show the first 5 validation errors
                for i, error in enumerate(result['validation_errors'][:5]):
                    output += f"### Error {i+1}\n"
                    output += f"- **Model**: {error.get('model', 'Unknown')}\n"
                    output += f"- **Error Message**: {error.get('error', 'Unknown error')}\n"

                    # Show record data if available
                    if 'record' in error:
                        output += f"- **Record Data**: ```json\n{json.dumps(error['record'], indent=2)}\n```\n"

                if len(result['validation_errors']) > 5:
                    output += f"\n*...and {len(result['validation_errors']) - 5} more errors*\n"

                # Add suggestions for fixing common errors
                output += f"\n## Suggestions for Fixing Errors\n\n"
                output += "1. **Many2one fields**: For fields like `parent_id`, make sure the value is an integer ID, not a string or list\n"
                output += "2. **Selection fields**: For fields like `state`, ensure the value matches one of the allowed options\n"
                output += "3. **Date fields**: Ensure dates are in YYYY-MM-DD format\n"
                output += "4. **Required fields**: Make sure all required fields have values when creating new records\n"
                output += "5. **Field types**: Check that field values match the expected types (numbers for numeric fields, etc.)\n"

            return output

        except Exception as e:
            logger.error(f"Error importing related records: {str(e)}")
            return f"# Error Importing Related Records\n\n{str(e)}"

    # Tool for importing records from CSV
    @mcp.tool()
    def import_records_from_csv(import_path: str, model_name: str, field_mapping: Optional[str] = None, create_if_not_exists: bool = True, update_if_exists: bool = True) -> str:
        """Import records from a CSV file into an Odoo model.

        Args:
            import_path: Path to the CSV file to import
            model_name: The technical name of the Odoo model to import into
            field_mapping: JSON string with mapping from CSV field names to Odoo field names
            create_if_not_exists: Whether to create new records if they don't exist
            update_if_exists: Whether to update existing records

        Returns:
            A confirmation message with the import results
        """
        if not model_discovery:
            return "# Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."

        try:
            # Validate model exists
            model_schema = model_discovery.get_model_schema(model_name)
            if not model_schema:
                return f"# Error: Invalid Model\n\nThe model '{model_name}' does not exist in the Odoo database."

            # Get available fields for the model
            available_fields = model_schema.get("fields", {})
            if not available_fields:
                return f"# Error: No Fields Available\n\nCould not retrieve fields for model '{model_name}'."

            # Check if import file exists
            if not os.path.exists(import_path):
                return f"# Error: File Not Found\n\nThe file '{import_path}' does not exist."

            # Check if file is a CSV
            if not import_path.lower().endswith('.csv'):
                return f"# Error: Invalid File Format\n\nThe file '{import_path}' is not a CSV file."

            # Read CSV headers to validate field mapping
            try:
                import csv
                with open(import_path, 'r') as f:
                    reader = csv.reader(f)
                    csv_headers = next(reader)
            except Exception as e:
                return f"# Error: Invalid CSV File\n\nCould not read headers from CSV file: {str(e)}"

            # Parse field mapping if provided
            mapping = None
            if field_mapping:
                try:
                    mapping = json.loads(field_mapping)
                except json.JSONDecodeError:
                    return f"# Error: Invalid Field Mapping\n\nThe field mapping format is invalid: {field_mapping}\n\nExample valid format:\n```json\n{{\n  \"csv_field1\": \"odoo_field1\",\n  \"csv_field2\": \"odoo_field2\"\n}}\n```"

                # Validate field mapping
                if mapping:
                    # Check if CSV fields exist in the CSV file
                    invalid_csv_fields = [field for field in mapping.keys() if field not in csv_headers]
                    if invalid_csv_fields:
                        return f"# Error: Invalid CSV Fields in Mapping\n\nThe following CSV fields in the mapping do not exist in the CSV file:\n- {', '.join(invalid_csv_fields)}\n\nAvailable CSV fields:\n- {', '.join(csv_headers)}"

                    # Check if Odoo fields exist in the model
                    invalid_odoo_fields = [field for field in mapping.values() if field not in available_fields and field != 'id']
                    if invalid_odoo_fields:
                        return f"# Error: Invalid Odoo Fields in Mapping\n\nThe following Odoo fields in the mapping do not exist in model '{model_name}':\n- {', '.join(invalid_odoo_fields)}\n\nAvailable Odoo fields include:\n- {', '.join(list(available_fields.keys())[:20])}\n- ..."
            else:
                # If no mapping is provided, suggest one based on matching field names
                mapping = {}
                for csv_field in csv_headers:
                    # Direct match
                    if csv_field in available_fields:
                        mapping[csv_field] = csv_field
                    # Try normalized match (lowercase, no underscores)
                    else:
                        normalized_csv_field = csv_field.lower().replace('_', '')
                        for odoo_field in available_fields.keys():
                            normalized_odoo_field = odoo_field.lower().replace('_', '')
                            if normalized_csv_field == normalized_odoo_field:
                                mapping[csv_field] = odoo_field
                                break

            # Check for required fields
            required_fields = [field for field, info in available_fields.items()
                              if info.get('required', False) and field != 'id']

            mapped_odoo_fields = set(mapping.values() if mapping else [])
            missing_required = [field for field in required_fields if field not in mapped_odoo_fields]

            if missing_required and create_if_not_exists:
                return f"# Warning: Missing Required Fields\n\nThe following required fields are not mapped but are needed for creating new records:\n- {', '.join(missing_required)}\n\nPlease update your field mapping to include these fields or set create_if_not_exists=False."

            # Run the import flow
            result = import_records(
                import_path=import_path,
                model_name=model_name,
                field_mapping=mapping,
                create_if_not_exists=create_if_not_exists,
                update_if_exists=update_if_exists
            )

            if not result["success"]:
                return f"# Error Importing Records\n\n{result.get('error', 'Unknown error')}"

            # Format the results
            output = f"# Import Results\n\n"
            output += f"- **Model**: {result['model_name']}\n"
            output += f"- **Import Path**: {result['import_path']}\n"
            output += f"- **Field Mapping**: {json.dumps(result['field_mapping'], indent=2)}\n"
            output += f"- **Total Records**: {result['total_records']}\n"
            output += f"- **Created Records**: {result['imported_records']}\n"
            output += f"- **Updated Records**: {result['updated_records']}\n"
            output += f"- **Failed Records**: {result['failed_records']}\n"

            if result['failed_records'] > 0 and 'validation_errors' in result:
                output += f"\n## Failed Records\n\n"

                # Show the first 5 validation errors
                for i, error in enumerate(result['validation_errors'][:5]):
                    output += f"### Error {i+1}\n"
                    output += f"- **Error Message**: {error.get('error', 'Unknown error')}\n"

                    # Show record data if available
                    if 'record' in error:
                        output += f"- **Record Data**: ```json\n{json.dumps(error['record'], indent=2)}\n```\n"

                if len(result['validation_errors']) > 5:
                    output += f"\n*...and {len(result['validation_errors']) - 5} more errors*\n"

                # Add suggestions for fixing common errors
                output += f"\n## Suggestions for Fixing Errors\n\n"
                output += "1. **Many2one fields**: For fields like `partner_id`, make sure the value is an integer ID, not a string or list\n"
                output += "2. **Selection fields**: For fields like `priority`, ensure the value matches one of the allowed options\n"
                output += "3. **Date fields**: Ensure dates are in YYYY-MM-DD format\n"
                output += "4. **Required fields**: Make sure all required fields have values when creating new records\n"
                output += "5. **Field types**: Check that field values match the expected types (numbers for numeric fields, etc.)\n"

            return output

        except Exception as e:
            logger.error(f"Error importing records: {str(e)}")
            return f"# Error Importing Records\n\n{str(e)}"

    # Add a prompt for advanced search
    @mcp.prompt()
    def advanced_search_prompt() -> str:
        """Create a prompt for performing advanced searches across Odoo models."""
        return """I need to search for information across multiple Odoo models using natural language.

Please help me by:
1. Using the advanced_search tool to interpret my query and find relevant records
2. Explaining the results and relationships between different models
3. Suggesting follow-up queries if needed

Examples of queries I can use:
- "List all sales orders under the customer's name, Gemini Furniture"
- "List all customer invoices for the customer name Wood Corner"
- "List out all projects"
- "List out all Project tasks for project name Research & Development"
- "List all unpaid bills with respect of vendor details"
- "List all project tasks according to their deadline date"
"""

    # Add a prompt for creating a new record
    @mcp.prompt()
    def create_record_prompt(model_name: str) -> str:
        """Create a prompt for creating a new record in an Odoo model."""
        return f"I need to create a new record in the Odoo model '{model_name}'.\n\nPlease help me by:\n1. Showing me the template for this model using the get_record_template tool\n2. Guiding me through filling in the required and important fields\n3. Creating the record using the create_record tool once I've provided all the necessary information"

    # Add a prompt for searching records
    @mcp.prompt()
    def search_records_prompt(model_name: str) -> str:
        """Create a prompt for searching records in an Odoo model."""
        return f"I need to search for records in the Odoo model '{model_name}'.\n\nPlease help me by:\n1. Asking me what I'm looking for\n2. Using the search_records tool to find matching records\n3. Explaining the results to me"

    # Add a prompt for exporting records
    @mcp.prompt()
    def export_records_prompt(model_name: str) -> str:
        """Create a prompt for exporting records from an Odoo model."""
        return f"""I need to export records from the Odoo model '{model_name}' to a CSV file.

Please help me by:
1. Showing me the available fields for this model using the get_model_metadata tool
2. Guiding me through selecting fields to export (including important fields like ID and name)
3. Helping me set up filter criteria if needed (e.g., [["customer_rank", ">", 0]] for customers)
4. Exporting the records using the export_records_to_csv tool
5. Explaining the field types in the exported data for future reference"""

    # Add a prompt for importing records
    @mcp.prompt()
    def import_records_prompt(model_name: str) -> str:
        """Create a prompt for importing records into an Odoo model."""
        return f"""I need to import records into the Odoo model '{model_name}' from a CSV file.

Please help me by:
1. Asking for the path to the CSV file
2. Showing me the required fields for this model using the get_model_metadata tool
3. Helping me create a proper field mapping from CSV fields to Odoo fields
4. Explaining how to handle special field types:
   - Many2one fields (like partner_id): Need to be integer IDs
   - Selection fields (like state): Need to match allowed values
   - Date fields: Need to be in YYYY-MM-DD format
5. Importing the records using the import_records_from_csv tool
6. Helping me understand and fix any import errors"""

    # Add a prompt for updating CRM lead descriptions
    @mcp.prompt()
    def update_crm_descriptions_prompt() -> str:
        """Create a prompt for updating CRM lead descriptions."""
        return f"""I need to update the descriptions of CRM leads (opportunities) in Odoo.

Please help me by:
1. Exporting CRM leads to a CSV file using the export_records_to_csv tool with these fields:
   - id (essential for updating existing records)
   - name (for identification)
   - description (the field we want to update)
   - partner_id, stage_id (important relationships)
   - email_from, phone (contact information)

2. Guiding me through modifying the descriptions in the CSV file

3. Helping me import the updated records back to Odoo with proper field mapping:
   - Handling many2one fields (partner_id, stage_id) by extracting IDs
   - Excluding problematic fields like priority and date_deadline
   - Focusing only on updating the description field

4. Explaining how to troubleshoot common import errors"""

    # Add a prompt for dynamic model export/import
    @mcp.prompt()
    def dynamic_export_import_prompt() -> str:
        """Create a prompt for dynamically exporting and importing any Odoo model."""
        return f"""I need to export data from an Odoo model and then import it back with modifications.

Please help me by:
1. Asking which Odoo model I want to work with
2. Showing me the available fields for that model using get_model_metadata
3. Guiding me through selecting fields to export, including:
   - id field (for record identification)
   - name or other descriptive fields
   - fields I want to modify
   - relationship fields (many2one, one2many, many2many)

4. Helping me export the data using export_records_to_csv

5. Explaining how to modify the CSV file based on field types:
   - Text fields: Can be directly edited
   - Many2one fields: Need special handling (extract IDs)
   - Selection fields: Must match allowed values
   - Date fields: Must use proper format

6. Creating a proper field mapping for import

7. Importing the modified data using import_records_from_csv

8. Helping me understand and fix any import errors"""

    # Add a prompt for invoice export/import
    @mcp.prompt()
    def invoice_export_import_prompt() -> str:
        """Create a prompt for exporting and importing invoices."""
        return f"""I need to work with invoices (account.move) in Odoo, including exporting existing invoices and importing new ones.

Please help me by:
1. Explaining the different invoice types in Odoo:
   - Customer Invoices (out_invoice)
   - Vendor Bills (in_invoice)
   - Credit Notes (out_refund, in_refund)

2. Showing me how to export existing invoices:
   - Using export_records_to_csv with account.move model
   - Including important fields like id, name, partner_id, invoice_date, amount_total
   - Filtering by invoice type and state

3. Guiding me through exporting invoice lines:
   - Using export_records_to_csv with account.move.line model
   - Including fields like move_id, product_id, account_id, quantity, price_unit
   - Explaining the relationship between invoices and invoice lines

4. Helping me create new invoices via CSV import:
   - Creating the invoice header CSV with required fields
   - Creating the invoice lines CSV with required fields
   - Importing the header first, then the lines with the correct move_id

5. Explaining how to handle special field types:
   - Many2one fields (partner_id, product_id, account_id)
   - Selection fields (move_type, state)
   - Monetary fields (price_unit, amount_total)
   - Tax fields (tax_ids)

6. Showing me how to update existing invoices:
   - Exporting draft invoices
   - Modifying fields like reference, date, or amounts
   - Importing back with the correct field mapping

7. Helping me understand and fix any import errors"""

    # Add a prompt for related records export/import
    @mcp.prompt()
    def related_records_export_import_prompt() -> str:
        """Create a prompt for exporting and importing related records."""
        return f"""I need to work with related models in Odoo, exporting and importing parent and child records together while maintaining their relationships.

Please help me by:
1. Explaining how parent-child relationships work in Odoo:
   - Many2one fields (e.g., move_id in account.move.line)
   - One2many fields (e.g., invoice_line_ids in account.move)
   - How these relationships are maintained during import/export

2. Guiding me through exporting related records:
   - Using export_related_records_to_csv with parent and child models
   - Identifying the relation field that connects them
   - Selecting appropriate fields from both models
   - Setting up filter criteria for the parent records

3. Explaining the structure of the exported CSV file:
   - How parent and child records are combined
   - The meaning of metadata columns (_model, _record_type, etc.)
   - How to interpret the prefixed fields (parent_*, child_*)

4. Helping me modify the exported data:
   - Which fields are safe to modify
   - How to handle special field types in both parent and child records
   - Best practices for maintaining data integrity

5. Showing me how to import the modified data:
   - Using import_related_records_from_csv
   - Understanding how parent-child relationships are preserved
   - Options for creating new records vs. updating existing ones
   - Special handling for posted invoices (draft_only and reset_to_draft parameters)
   - How to handle computed fields and restricted fields

6. Demonstrating with a real example:
   - Exporting invoices (account.move) with their lines (account.move.line)
   - Modifying some fields in both the parent and child records
   - Importing the data back while maintaining the relationships

7. Helping me understand and fix any import errors

This approach is much more efficient than exporting and importing parent and child records separately, as it automatically maintains the relationships between them."""

    # Tool for validating and converting field values
    @mcp.tool()
    def validate_field_value(model_name: str, field_name: str, value: str) -> str:
        """Validate and convert a value for a specific field in an Odoo model.

        Args:
            model_name: The technical name of the Odoo model
            field_name: The name of the field to validate
            value: The value to validate and convert

        Returns:
            A formatted string with validation results and conversion suggestions
        """
        if not model_discovery:
            return "# Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."

        try:
            # Get model schema
            schema = model_discovery.get_model_schema(model_name)

            if not schema:
                return f"# Error: Invalid Model\n\nThe model '{model_name}' does not exist or could not be accessed."

            fields = schema.get("fields", {})

            if not field_name in fields:
                return f"# Error: Invalid Field\n\nThe field '{field_name}' does not exist in model '{model_name}'."

            field_info = fields[field_name]
            field_type = field_info.get("type", "unknown")
            field_string = field_info.get("string", field_name)

            # Format the results
            output = f"# Field Validation: {field_string} ({field_name})\n\n"
            output += f"- **Field Type**: {field_type}\n"
            output += f"- **Input Value**: `{value}`\n\n"

            # Validate based on field type
            if field_type == "char" or field_type == "text":
                output += "## Validation Result\n\n"
                output += "✅ **Valid**: Text values are accepted for this field.\n\n"
                output += "## Import Format\n\n"
                output += "Text fields can be imported directly as strings.\n"

            elif field_type == "integer":
                try:
                    int_value = int(value)
                    output += "## Validation Result\n\n"
                    output += f"✅ **Valid**: The value `{value}` is a valid integer.\n\n"
                    output += "## Import Format\n\n"
                    output += "Integer fields should be imported as numbers without decimal points.\n"
                except ValueError:
                    output += "## Validation Result\n\n"
                    output += f"❌ **Invalid**: The value `{value}` is not a valid integer.\n\n"
                    output += "## Suggested Fix\n\n"
                    output += "Use a whole number without decimal points or commas.\n"

            elif field_type == "float":
                try:
                    float_value = float(value)
                    output += "## Validation Result\n\n"
                    output += f"✅ **Valid**: The value `{value}` is a valid float.\n\n"
                    output += "## Import Format\n\n"
                    output += "Float fields should be imported as numbers, optionally with decimal points.\n"
                except ValueError:
                    output += "## Validation Result\n\n"
                    output += f"❌ **Invalid**: The value `{value}` is not a valid float.\n\n"
                    output += "## Suggested Fix\n\n"
                    output += "Use a number with or without decimal points. Do not use commas for thousands separators.\n"

            elif field_type == "boolean":
                if value.lower() in ["true", "1", "yes", "y"]:
                    output += "## Validation Result\n\n"
                    output += f"✅ **Valid**: The value `{value}` is interpreted as TRUE.\n\n"
                    output += "## Import Format\n\n"
                    output += "Boolean fields accept 'true', '1', 'yes', 'y' for TRUE and 'false', '0', 'no', 'n' for FALSE.\n"
                elif value.lower() in ["false", "0", "no", "n"]:
                    output += "## Validation Result\n\n"
                    output += f"✅ **Valid**: The value `{value}` is interpreted as FALSE.\n\n"
                    output += "## Import Format\n\n"
                    output += "Boolean fields accept 'true', '1', 'yes', 'y' for TRUE and 'false', '0', 'no', 'n' for FALSE.\n"
                else:
                    output += "## Validation Result\n\n"
                    output += f"❌ **Invalid**: The value `{value}` is not a valid boolean.\n\n"
                    output += "## Suggested Fix\n\n"
                    output += "Use 'true' or 'false' (or '1'/'0', 'yes'/'no').\n"

            elif field_type == "date":
                try:
                    import datetime
                    # Try different date formats
                    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%m-%d-%Y"]:
                        try:
                            date_value = datetime.datetime.strptime(value, fmt).date()
                            output += "## Validation Result\n\n"
                            output += f"✅ **Valid**: The value `{value}` is a valid date.\n\n"
                            output += "## Import Format\n\n"
                            output += f"For import, convert to ISO format: **{date_value.isoformat()}**\n"
                            break
                        except ValueError:
                            continue
                    else:
                        output += "## Validation Result\n\n"
                        output += f"❌ **Invalid**: The value `{value}` is not a valid date.\n\n"
                        output += "## Suggested Fix\n\n"
                        output += "Use the format YYYY-MM-DD (e.g., 2023-05-15).\n"
                except Exception:
                    output += "## Validation Result\n\n"
                    output += f"❌ **Invalid**: The value `{value}` is not a valid date.\n\n"
                    output += "## Suggested Fix\n\n"
                    output += "Use the format YYYY-MM-DD (e.g., 2023-05-15).\n"

            elif field_type == "datetime":
                try:
                    import datetime
                    # Try different datetime formats
                    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y %H:%M:%S"]:
                        try:
                            dt_value = datetime.datetime.strptime(value, fmt)
                            output += "## Validation Result\n\n"
                            output += f"✅ **Valid**: The value `{value}` is a valid datetime.\n\n"
                            output += "## Import Format\n\n"
                            output += f"For import, convert to ISO format: **{dt_value.isoformat()}**\n"
                            break
                        except ValueError:
                            continue
                    else:
                        output += "## Validation Result\n\n"
                        output += f"❌ **Invalid**: The value `{value}` is not a valid datetime.\n\n"
                        output += "## Suggested Fix\n\n"
                        output += "Use the format YYYY-MM-DD HH:MM:SS (e.g., 2023-05-15 14:30:00).\n"
                except Exception:
                    output += "## Validation Result\n\n"
                    output += f"❌ **Invalid**: The value `{value}` is not a valid datetime.\n\n"
                    output += "## Suggested Fix\n\n"
                    output += "Use the format YYYY-MM-DD HH:MM:SS (e.g., 2023-05-15 14:30:00).\n"

            elif field_type == "selection":
                # Try to get selection options
                selection_options = field_info.get("selection", [])

                if selection_options:
                    valid_values = [opt[0] for opt in selection_options]
                    valid_labels = [opt[1] for opt in selection_options]

                    if value in valid_values:
                        output += "## Validation Result\n\n"
                        output += f"✅ **Valid**: The value `{value}` is a valid selection option.\n\n"
                        output += "## Import Format\n\n"
                        output += "Selection fields should use the technical value, not the display label.\n"
                    else:
                        # Check if the value matches a label instead of a value
                        matching_values = [opt[0] for opt in selection_options if opt[1].lower() == value.lower()]

                        if matching_values:
                            output += "## Validation Result\n\n"
                            output += f"⚠️ **Warning**: You provided a display label instead of a technical value.\n\n"
                            output += "## Suggested Fix\n\n"
                            output += f"Use the technical value `{matching_values[0]}` instead of the label `{value}`.\n"
                        else:
                            output += "## Validation Result\n\n"
                            output += f"❌ **Invalid**: The value `{value}` is not a valid selection option.\n\n"
                            output += "## Suggested Fix\n\n"
                            output += "Use one of the following values:\n\n"

                            for i, (val, label) in enumerate(selection_options):
                                output += f"- `{val}` ({label})\n"
                else:
                    output += "## Validation Result\n\n"
                    output += "⚠️ **Warning**: Could not retrieve selection options for validation.\n\n"
                    output += "## Import Format\n\n"
                    output += "Selection fields should use the technical value, not the display label.\n"

            elif field_type == "many2one":
                # Check if the value is a valid ID
                try:
                    # If it's a number, it might be an ID
                    int_value = int(value)
                    output += "## Validation Result\n\n"
                    output += f"✅ **Valid Format**: The value `{value}` is a valid ID format.\n\n"
                    output += "## Import Format\n\n"
                    output += "Many2one fields should be imported as integer IDs.\n\n"
                    output += "## Note\n\n"
                    output += f"This validation only checks the format. It does not verify if ID {int_value} exists in the related model.\n"
                except ValueError:
                    # If it's not a number, it might be a string representation like "[id, 'name']"
                    import re
                    match = re.search(r'\[(\d+)', value)

                    if match:
                        extracted_id = match.group(1)
                        output += "## Validation Result\n\n"
                        output += f"⚠️ **Warning**: The value appears to be a string representation of a many2one field.\n\n"
                        output += "## Suggested Fix\n\n"
                        output += f"Extract the ID: `{extracted_id}`\n\n"
                        output += "## Import Format\n\n"
                        output += "Many2one fields should be imported as integer IDs, not string representations.\n"
                    else:
                        output += "## Validation Result\n\n"
                        output += f"❌ **Invalid**: The value `{value}` is not a valid ID format for a many2one field.\n\n"
                        output += "## Suggested Fix\n\n"
                        output += "Use an integer ID for many2one fields.\n"

            elif field_type in ["one2many", "many2many"]:
                output += "## Validation Result\n\n"
                output += "⚠️ **Warning**: One2many and many2many fields are complex to import directly.\n\n"
                output += "## Import Format\n\n"
                output += "For many2many fields, you can use a comma-separated list of IDs: `1,2,3`\n"
                output += "For one2many fields, direct import is usually not supported. Consider importing the related records separately.\n"

            else:
                output += "## Validation Result\n\n"
                output += f"⚠️ **Unknown field type**: `{field_type}`\n\n"
                output += "## Import Format\n\n"
                output += "The validation for this field type is not implemented. Proceed with caution.\n"

            return output

        except Exception as e:
            logger.error(f"Error validating field value: {str(e)}")
            return f"# Error validating field value\n\n{str(e)}"

    # Main entry point
    if __name__ == "__main__":
        try:
            logger.info("Starting MCP server...")
            mcp.run()
        except Exception as e:
            logger.error(f"Error running MCP server: {str(e)}")
            traceback.print_exc()

except Exception as e:
    logger.error(f"Error during initialization: {str(e)}")
    traceback.print_exc()
