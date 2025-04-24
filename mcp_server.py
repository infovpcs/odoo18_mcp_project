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
    except Exception as e:
        logger.error(f"Failed to initialize Odoo model discovery: {str(e)}")
        model_discovery = None

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
