"""
Odoo Connector

This module provides utilities for connecting to and interacting with Odoo.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
import xmlrpc.client
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Odoo connection details from environment variables
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "llmdb18")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

# Set up XML-RPC connections
try:
    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common", allow_none=True)
    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object", allow_none=True)

    # Authenticate
    uid = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})

    if not uid:
        logger.error("Authentication failed: Invalid credentials")
    else:
        logger.info(f"Authenticated as user ID: {uid}")
except Exception as e:
    logger.error(f"Failed to connect to Odoo server: {str(e)}")
    uid = None
    models = None


def execute_kw(model: str, method: str, args: List = None, kwargs: Dict = None) -> Any:
    """Execute a method on an Odoo model.

    Args:
        model: Odoo model name
        method: Method name
        args: Method arguments as a list
        kwargs: Method keyword arguments as a dict

    Returns:
        Any: Method result
    """
    if not uid or not models:
        logger.error("Not connected to Odoo server")
        return None

    try:
        # Ensure args is a list
        pos_args = args if args is not None else []
        kw_args = kwargs if kwargs is not None else {}

        result = models.execute_kw(
            ODOO_DB,
            uid,
            ODOO_PASSWORD,
            model,
            method,
            pos_args,
            kw_args
        )
        return result
    except Exception as e:
        logger.error(f"Error executing {method} on {model}: {str(e)}")
        return None


def search_read(
    model: str,
    domain: List = None,
    fields: List[str] = None,
    offset: int = 0,
    limit: int = None,
    order: str = None
) -> List[Dict[str, Any]]:
    """Search and read records from an Odoo model.

    Args:
        model: Model name
        domain: Search domain
        fields: Fields to return
        offset: Offset for pagination
        limit: Limit for pagination
        order: Order by clause

    Returns:
        List[Dict[str, Any]]: Matching records
    """
    try:
        # Clean up domain to ensure no None values without explicit comparison
        domain = domain if domain else []

        # Prepare options for search_read
        options = {}
        if fields is not None:
            options['fields'] = fields
        if offset is not None:
            options['offset'] = offset
        if limit is not None:
            options['limit'] = limit
        if order is not None:
            options['order'] = order

        # Use search_read method directly as per Odoo documentation
        # The domain must be passed directly, not wrapped in another list
        return execute_kw(model, 'search_read', [domain], options)
    except Exception as e:
        logger.error(f"Search_read failed for {model}: {str(e)}")
        return []


def get_model_fields(model_name: str) -> Dict[str, Dict[str, Any]]:
    """Get fields for a specific model.

    Args:
        model_name: Model name

    Returns:
        Dict[str, Dict[str, Any]]: Model fields
    """
    try:
        fields = execute_kw(model_name, 'fields_get', [], {'attributes': ['string', 'help', 'type', 'required', 'readonly', 'selection', 'relation']})
        return fields or {}
    except Exception as e:
        logger.error(f"Failed to get fields for model {model_name}: {str(e)}")
        return {}


def get_field_groups(model_name: str) -> Dict[str, List[str]]:
    """Group fields by type for a specific model.

    Args:
        model_name: Model name

    Returns:
        Dict[str, List[str]]: Fields grouped by type
    """
    fields = get_model_fields(model_name)

    # Group fields by type
    field_groups = {}
    for field_name, field_info in fields.items():
        field_type = field_info.get('type')
        if field_type not in field_groups:
            field_groups[field_type] = []
        field_groups[field_type].append(field_name)

    return field_groups


def get_record_template(model_name: str) -> Dict[str, Any]:
    """Get a template for creating a record.

    Args:
        model_name: Model name

    Returns:
        Dict[str, Any]: Record template
    """
    fields = get_model_fields(model_name)

    # Create a template with default values
    template = {}
    for field_name, field_info in fields.items():
        # Skip computed fields, readonly fields, and fields with default values
        if field_info.get('readonly', False):
            continue

        field_type = field_info.get('type')

        # Set default values based on field type
        if field_type == 'char':
            template[field_name] = ""
        elif field_type == 'text':
            template[field_name] = ""
        elif field_type == 'integer':
            template[field_name] = 0
        elif field_type == 'float':
            template[field_name] = 0.0
        elif field_type == 'boolean':
            template[field_name] = False
        elif field_type == 'date':
            template[field_name] = ""
        elif field_type == 'datetime':
            template[field_name] = ""
        elif field_type == 'selection':
            selections = field_info.get('selection', [])
            if selections:
                template[field_name] = selections[0][0]
            else:
                template[field_name] = None
        elif field_type == 'many2one':
            template[field_name] = None
        elif field_type == 'many2many':
            template[field_name] = []
        elif field_type == 'one2many':
            template[field_name] = []

    return template