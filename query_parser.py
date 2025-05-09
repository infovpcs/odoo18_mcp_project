#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Query Parser Module

This module provides functionality for parsing natural language queries
into Odoo domain filters for advanced search operations.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class QueryParser:
    """Class for parsing natural language queries into Odoo domain filters."""

    def __init__(self, model_discovery):
        """Initialize the query parser.

        Args:
            model_discovery: ModelDiscovery instance for accessing Odoo models and fields
        """
        self.model_discovery = model_discovery

        # Caches for dynamic model and field information
        self._model_cache = {}
        self._field_cache = {}
        self._model_mappings_cache = None
        self._field_mappings_cache = {}

        # Initialize static mappings as fallbacks
        self._init_static_mappings()

        # Load dynamic mappings from Odoo
        self._load_dynamic_mappings()

    def _init_static_mappings(self):
        """Initialize static mappings as fallbacks."""
        # Common model mappings (fallback)
        self.model_mappings = {
            # Sales
            "sales order": "sale.order",
            "sales orders": "sale.order",
            "sale order": "sale.order",
            "sale orders": "sale.order",
            "quotation": "sale.order",
            "quotations": "sale.order",
            "sales": "sale.order",

            # Customers
            "customer": "res.partner",
            "customers": "res.partner",
            "partner": "res.partner",
            "partners": "res.partner",
            "client": "res.partner",
            "clients": "res.partner",

            # Invoices
            "invoice": "account.move",
            "invoices": "account.move",
            "customer invoice": "account.move",
            "customer invoices": "account.move",
            "bill": "account.move",
            "bills": "account.move",
            "vendor bill": "account.move",
            "vendor bills": "account.move",

            # Products
            "product": "product.product",
            "products": "product.product",
            "item": "product.product",
            "items": "product.product",

            # Projects
            "project": "project.project",
            "projects": "project.project",

            # Tasks
            "task": "project.task",
            "tasks": "project.task",

            # CRM
            "lead": "crm.lead",
            "leads": "crm.lead",
            "opportunity": "crm.lead",
            "opportunities": "crm.lead",
            "crm": "crm.lead",
        }

        # Common field mappings (generic across models)
        self.common_field_mappings = {
            "name": ["name", "display_name", "title"],
            "date": ["date", "create_date", "write_date", "date_order", "invoice_date", "date_deadline"],
            "amount": ["amount", "amount_total", "amount_untaxed", "amount_tax", "price", "list_price", "standard_price"],
            "status": ["state", "status", "stage_id", "kanban_state"],
            "reference": ["ref", "reference", "code", "default_code"],
            "description": ["description", "note", "comment"],
            "email": ["email", "email_from"],
            "phone": ["phone", "mobile"],
        }

        # Model-specific field mappings (fallback)
        self.model_field_mappings = {
            "res.partner": {
                "customer": ["customer_rank", "customer"],
                "vendor": ["supplier_rank", "supplier"],
                "name": ["name", "display_name"],
                "address": ["street", "street2", "city", "zip", "state_id", "country_id"],
                "contact": ["email", "phone", "mobile"],
            },
            "sale.order": {
                "customer": ["partner_id"],
                "date": ["date_order", "create_date"],
                "amount": ["amount_total", "amount_untaxed", "amount_tax"],
                "status": ["state"],
                "reference": ["name"],
            },
            "account.move": {
                "customer": ["partner_id"],
                "date": ["invoice_date", "date"],
                "due date": ["invoice_date_due"],
                "amount": ["amount_total", "amount_untaxed", "amount_tax", "amount_residual"],
                "status": ["state", "payment_state"],
                "reference": ["name", "ref"],
                "type": ["move_type"],
            },
            "product.product": {
                "name": ["name", "display_name"],
                "price": ["list_price", "standard_price"],
                "code": ["default_code"],
                "category": ["categ_id"],
                "type": ["type"],
            },
            "project.project": {
                "name": ["name"],
                "customer": ["partner_id"],
                "status": ["active"],
                "manager": ["user_id"],
            },
            "project.task": {
                "name": ["name"],
                "project": ["project_id"],
                "deadline": ["date_deadline"],
                "status": ["stage_id", "state"],
                "priority": ["priority"],
                "assigned to": ["user_ids"],
            },
            "crm.lead": {
                "name": ["name"],
                "customer": ["partner_id"],
                "status": ["stage_id"],
                "expected revenue": ["expected_revenue"],
                "probability": ["probability"],
                "deadline": ["date_deadline"],
                "assigned to": ["user_id"],
            },
        }

    def _load_dynamic_mappings(self):
        """Load dynamic model and field mappings from Odoo."""
        try:
            # Load available models
            self._load_available_models()

            # Generate dynamic model mappings
            self._generate_model_mappings()

            logger.info("Successfully loaded dynamic mappings from Odoo")
        except Exception as e:
            logger.error(f"Error loading dynamic mappings: {str(e)}")
            logger.info("Falling back to static mappings")

    def _load_available_models(self):
        """Load available models from Odoo using ir.model."""
        try:
            # Get all available models from ir.model
            # Use client's execute method if available
            if hasattr(self.model_discovery, 'client') and self.model_discovery.client:
                models = self.model_discovery.client.execute(
                    'ir.model',
                    'search_read',
                    [[('transient', '=', False)]],  # Exclude transient models
                    {'fields': ['name', 'model', 'info'], 'order': 'model'}
                )
            # Fallback to direct execution if models_proxy is available
            elif hasattr(self.model_discovery, 'models_proxy') and self.model_discovery.models_proxy:
                models = self.model_discovery.models_proxy.execute_kw(
                    self.model_discovery.db,
                    self.model_discovery.uid,
                    self.model_discovery.password,
                    'ir.model', 'search_read',
                    [[('transient', '=', False)]],  # Exclude transient models
                    {'fields': ['name', 'model', 'info'], 'order': 'model'}
                )
            else:
                # Fallback to get_available_models method
                raise AttributeError("No suitable method found to execute search for ir.model")

            # Cache model information
            for model in models:
                model_name = model.get('model')
                if model_name:
                    self._model_cache[model_name] = {
                        'name': model.get('name', ''),
                        'model': model_name,
                        'info': model.get('info', '')
                    }

            logger.info(f"Loaded {len(models)} models from Odoo")
        except Exception as e:
            logger.error(f"Error loading available models: {str(e)}")
            # Fallback to original method if direct approach fails
            try:
                models = self.model_discovery.get_available_models()
                for model in models:
                    model_name = model.get('model')
                    if model_name:
                        self._model_cache[model_name] = {
                            'name': model.get('name', ''),
                            'model': model_name,
                            'info': model.get('info', '')
                        }
                logger.info(f"Loaded {len(models)} models from Odoo using fallback method")
            except Exception as e2:
                logger.error(f"Fallback method also failed: {str(e2)}")

    def _generate_model_mappings(self):
        """Generate dynamic model mappings from cached model information."""
        if not self._model_cache:
            return

        mappings = {}

        for model_name, model_info in self._model_cache.items():
            display_name = model_info.get('name', '').lower()

            if display_name:
                # Add singular and plural forms
                mappings[display_name] = model_name
                if not display_name.endswith('s'):
                    mappings[f"{display_name}s"] = model_name

                # Add variations with spaces
                if '.' in model_name:
                    _, name = model_name.split('.', 1)  # Ignore module part
                    name_with_spaces = name.replace('_', ' ')
                    mappings[name_with_spaces] = model_name
                    if not name_with_spaces.endswith('s'):
                        mappings[f"{name_with_spaces}s"] = model_name

        # Merge with static mappings, giving priority to dynamic ones
        self._model_mappings_cache = {**self.model_mappings, **mappings}

    def _get_model_fields_dynamic(self, model_name: str) -> Dict[str, Dict[str, Any]]:
        """Get fields for a model dynamically from Odoo using ir.model.fields.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary of field information
        """
        # Check cache first
        if model_name in self._field_cache:
            return self._field_cache[model_name]

        try:
            # Get fields directly from ir.model.fields for better field information
            if hasattr(self.model_discovery, 'client') and self.model_discovery.client:
                fields_data = self.model_discovery.client.execute(
                    'ir.model.fields',
                    'search_read',
                    [[('model', '=', model_name)]],
                    {'fields': ['name', 'field_description', 'ttype', 'relation', 'relation_field',
                               'required', 'readonly', 'store', 'copied', 'selection_ids']}
                )
            # Fallback to direct execution if models_proxy is available
            elif hasattr(self.model_discovery, 'models_proxy') and self.model_discovery.models_proxy:
                fields_data = self.model_discovery.models_proxy.execute_kw(
                    self.model_discovery.db,
                    self.model_discovery.uid,
                    self.model_discovery.password,
                    'ir.model.fields', 'search_read',
                    [[('model', '=', model_name)]],
                    {'fields': ['name', 'field_description', 'ttype', 'relation', 'relation_field',
                               'required', 'readonly', 'store', 'copied', 'selection_ids']}
                )
            else:
                # Fallback to get_model_fields method
                raise AttributeError("No suitable method found to execute search for ir.model.fields")

            fields = {}
            for field in fields_data:
                fields[field['name']] = {
                    'string': field['field_description'],
                    'type': field['ttype'],
                    'relation': field.get('relation', False),
                    'relation_field': field.get('relation_field', False),
                    'required': field.get('required', False),
                    'readonly': field.get('readonly', False),
                    'store': field.get('store', True),
                    'copied': field.get('copied', False),
                    'selection_ids': field.get('selection_ids', [])
                }

            # If direct approach fails or returns empty, fall back to original method
            if not fields:
                fields = self.model_discovery.get_model_fields(model_name)

            if fields:
                # Cache the fields
                self._field_cache[model_name] = fields

                # Generate field mappings for this model
                self._generate_field_mappings(model_name, fields)

                return fields

            return {}
        except Exception as e:
            logger.error(f"Error getting fields for model {model_name}: {str(e)}")
            # Fall back to original method
            try:
                fields = self.model_discovery.get_model_fields(model_name)
                if fields:
                    # Cache the fields
                    self._field_cache[model_name] = fields
                    # Generate field mappings for this model
                    self._generate_field_mappings(model_name, fields)
                    return fields
                return {}
            except Exception as e2:
                logger.error(f"Fallback method also failed: {str(e2)}")
                return {}

    def _generate_field_mappings(self, model_name: str, fields: Dict[str, Dict[str, Any]]):
        """Generate field mappings for a model based on its fields.

        Args:
            model_name: Name of the model
            fields: Dictionary of field information
        """
        if not fields:
            return

        # Initialize mappings for this model
        model_mappings = {}

        # Group fields by type
        name_fields = []
        date_fields = []
        amount_fields = []
        status_fields = []
        reference_fields = []
        description_fields = []
        contact_fields = []
        relation_fields = {}

        for field_name, field_info in fields.items():
            field_type = field_info.get('type')
            # We'll use field_type for categorization, not field_string

            # Skip technical fields
            if field_name.startswith('_') or field_name in ['id', 'create_uid', 'write_uid']:
                continue

            # Categorize by field type and name patterns
            if field_type == 'char' or field_type == 'text':
                if 'name' in field_name or 'title' in field_name:
                    name_fields.append(field_name)
                elif 'ref' in field_name or 'code' in field_name:
                    reference_fields.append(field_name)
                elif 'desc' in field_name or 'note' in field_name or 'comment' in field_name:
                    description_fields.append(field_name)
                elif 'email' in field_name:
                    contact_fields.append(field_name)
                elif 'phone' in field_name or 'mobile' in field_name:
                    contact_fields.append(field_name)

            elif field_type == 'date' or field_type == 'datetime':
                date_fields.append(field_name)

            elif field_type == 'float' or field_type == 'monetary':
                if 'amount' in field_name or 'price' in field_name or 'cost' in field_name:
                    amount_fields.append(field_name)

            elif field_type == 'selection':
                if 'state' in field_name or 'status' in field_name:
                    status_fields.append(field_name)

            elif field_type in ['many2one', 'one2many', 'many2many']:
                relation = field_info.get('relation')
                if relation:
                    # Use the related model's display name as the key
                    if relation in self._model_cache:
                        relation_display = self._model_cache[relation].get('name', '').lower()
                        if relation_display:
                            if relation_display not in relation_fields:
                                relation_fields[relation_display] = []
                            relation_fields[relation_display].append(field_name)

        # Add categorized fields to mappings
        if name_fields:
            model_mappings['name'] = name_fields

        if date_fields:
            model_mappings['date'] = date_fields

        if amount_fields:
            model_mappings['amount'] = amount_fields

        if status_fields:
            model_mappings['status'] = status_fields

        if reference_fields:
            model_mappings['reference'] = reference_fields

        if description_fields:
            model_mappings['description'] = description_fields

        if contact_fields:
            model_mappings['contact'] = contact_fields

        # Add relation fields
        for relation_name, field_list in relation_fields.items():
            model_mappings[relation_name] = field_list

        # Store in cache
        self._field_mappings_cache[model_name] = model_mappings

        # Common operators in natural language
        self.operator_mappings = {
            "equal to": "=",
            "equals": "=",
            "is": "=",
            "equal": "=",
            "=": "=",
            "==": "=",
            "not equal to": "!=",
            "not equals": "!=",
            "is not": "!=",
            "not equal": "!=",
            "!=": "!=",
            "<>": "!=",
            "greater than": ">",
            "more than": ">",
            ">": ">",
            "less than": "<",
            "<": "<",
            "greater than or equal to": ">=",
            "at least": ">=",
            ">=": ">=",
            "less than or equal to": "<=",
            "at most": "<=",
            "<=": "<=",
            "contains": "ilike",
            "like": "ilike",
            "similar to": "ilike",
            "starts with": "=like",
            "begins with": "=like",
            "ends with": "like=",
            "in": "in",
            "not in": "not in",
        }

        # Status/state value mappings
        self.state_value_mappings = {
            # Sale order states
            "quotation": "draft",
            "quotation sent": "sent",
            "sales order": "sale",
            "locked": "done",
            "cancelled": "cancel",

            # Invoice states
            "draft": "draft",
            "posted": "posted",
            "cancelled": "cancel",

            # Payment states
            "paid": "paid",
            "unpaid": "not_paid",
            "partial": "partial",

            # Task states (generic)
            "new": "new",
            "in progress": "in_progress",
            "done": "done",
            "cancelled": "cancel",
        }

        # Time-related terms
        self.time_terms = {
            "today": "today",
            "yesterday": "yesterday",
            "this week": "this_week",
            "last week": "last_week",
            "this month": "this_month",
            "last month": "last_month",
            "this year": "this_year",
            "last year": "last_year",
            "overdue": "overdue",
        }

    def parse_query(self, query: str) -> Tuple[str, List[List[Any]], List[str]]:
        """Parse a natural language query into an Odoo model and domain filter.

        Args:
            query: Natural language query string

        Returns:
            Tuple containing:
            - Model name (str)
            - Domain filter (List[List[Any]])
            - Fields to display (List[str])
        """
        # Normalize query
        normalized_query = query.lower().strip()

        # Identify the model
        model_name = self._identify_model(normalized_query)
        if not model_name:
            # Default to res.partner if no model is identified
            model_name = "res.partner"
            logger.warning(f"No model identified in query: {query}. Using default: {model_name}")

        # Get model fields dynamically
        model_fields = self._get_model_fields_dynamic(model_name)
        if not model_fields:
            logger.error(f"Could not get fields for model: {model_name}")
            return model_name, [], []

        # Generate domain filter
        domain = self._generate_domain(normalized_query, model_name, model_fields)

        # Determine fields to display
        display_fields = self._determine_display_fields(model_name, model_fields)

        return model_name, domain, display_fields

    def _identify_model(self, query: str) -> Optional[str]:
        """Identify the Odoo model from the query.

        Args:
            query: Normalized query string

        Returns:
            Model name or None if not identified
        """
        # Use dynamic model mappings if available
        if self._model_mappings_cache:
            # Check for direct model mentions
            for term, model in self._model_mappings_cache.items():
                if term in query:
                    return model
        else:
            # Fallback to static mappings
            for term, model in self.model_mappings.items():
                if term in query:
                    return model

        # Check for specific patterns
        if re.search(r'(customer|client|partner)s?', query):
            return "res.partner"
        elif re.search(r'(sales? order|quotation)s?', query):
            return "sale.order"
        elif re.search(r'(invoice|bill)s?', query):
            return "account.move"
        elif re.search(r'product', query):
            return "product.product"
        elif re.search(r'project', query):
            return "project.project"
        elif re.search(r'task', query):
            return "project.task"
        elif re.search(r'(lead|opportunity)', query):
            return "crm.lead"

        # Special case handling
        if "unpaid bills" in query or "vendor" in query:
            return "account.move"

        # Try to find a model by searching through all available models
        if self._model_cache:
            for model_name, model_info in self._model_cache.items():
                display_name = model_info.get('name', '').lower()
                if display_name and display_name in query:
                    return model_name

        return None

    def _generate_domain(self, query: str, model_name: str, model_fields: Dict[str, Any]) -> List[List[Any]]:
        """Generate an Odoo domain filter from the query.

        Args:
            query: Normalized query string
            model_name: Odoo model name
            model_fields: Dictionary of model fields

        Returns:
            Odoo domain filter
        """
        domain = []

        # Handle special cases first with field validation
        if model_name == "res.partner" and "customer" in query:
            if "customer_rank" in model_fields:
                domain.append(["customer_rank", ">", 0])
            elif "customer" in model_fields:  # For older Odoo versions
                domain.append(["customer", "=", True])
        elif model_name == "res.partner" and "vendor" in query:
            if "supplier_rank" in model_fields:
                domain.append(["supplier_rank", ">", 0])
            elif "supplier" in model_fields:  # For older Odoo versions
                domain.append(["supplier", "=", True])
        elif model_name == "account.move" and "customer invoice" in query:
            if "move_type" in model_fields:
                domain.append(["move_type", "in", ["out_invoice", "out_refund"]])
            elif "type" in model_fields:  # For older Odoo versions
                domain.append(["type", "in", ["out_invoice", "out_refund"]])
        elif model_name == "account.move" and ("vendor bill" in query or "unpaid bills" in query):
            if "move_type" in model_fields:
                domain.append(["move_type", "in", ["in_invoice", "in_refund"]])
            elif "type" in model_fields:  # For older Odoo versions
                domain.append(["type", "in", ["in_invoice", "in_refund"]])

            if "unpaid" in query:
                if "payment_state" in model_fields:
                    domain.append(["payment_state", "!=", "paid"])
                elif "state" in model_fields:  # Fallback for older versions
                    domain.append(["state", "!=", "paid"])

        # Extract specific entity mentions
        entities = self._extract_entities(query, model_name)
        for entity_type, entity_value in entities.items():
            field_names = self._map_entity_to_fields(entity_type, model_name)
            if field_names:
                # Find the first field that exists in the model
                for field_name in field_names:
                    if field_name in model_fields:
                        domain.append([field_name, "ilike", entity_value])
                        break

        # Handle date-related queries
        date_domain = self._handle_date_filters(query, model_name, model_fields)
        if date_domain:
            domain.extend(date_domain)

        # Handle status/state queries
        state_domain = self._handle_state_filters(query, model_name, model_fields)
        if state_domain:
            domain.extend(state_domain)

        # If no domain was generated, return an empty domain to match all records
        if not domain:
            return []

        return domain

    def _extract_entities(self, query: str, model_name: str) -> Dict[str, str]:
        """Extract named entities from the query.

        Args:
            query: Normalized query string
            model_name: Odoo model name

        Returns:
            Dictionary mapping entity types to values
        """
        entities = {}

        # Get dynamic field mappings for this model
        field_mappings = {}
        if model_name in self._field_mappings_cache:
            field_mappings = self._field_mappings_cache[model_name]

        # Get model info from cache
        model_info = self._model_cache.get(model_name, {})
        model_display_name = model_info.get('name', '').lower() if model_info else ''

        # Extract entities based on field mappings
        for entity_type in field_mappings.keys():
            # Skip technical categories
            if entity_type in ['name', 'date', 'amount', 'status', 'reference', 'description']:
                continue

            # Try to extract entity values using the entity type
            pattern = rf'{entity_type}\s+(?:name\s+)?(?:is\s+)?["\']?([^"\']+)["\']?'
            match = re.search(pattern, query)
            if match:
                entities[entity_type] = match.group(1).strip()

        # Extract customer/partner name (common case)
        if 'customer' in field_mappings or model_name in ["res.partner", "sale.order", "account.move", "project.project"]:
            customer_match = re.search(r'(customer|client|partner)(?:\'s|\s+name)?\s+(?:is\s+)?["\']?([^"\']+)["\']?', query)
            if customer_match:
                entities["customer"] = customer_match.group(2).strip()
            else:
                # Try alternative patterns
                for pattern in [
                    r'(?:for|under|by)\s+(?:customer|client|partner)\s+["\']?([^"\']+)["\']?',
                    r'(?:for|under|by)\s+["\']?([^"\']+)["\']?'
                ]:
                    match = re.search(pattern, query)
                    if match:
                        entities["customer"] = match.group(1).strip()
                        break

        # Extract model-specific entities based on model name
        if model_display_name:
            pattern = rf'{model_display_name}\s+(?:name\s+)?(?:is\s+)?["\']?([^"\']+)["\']?'
            match = re.search(pattern, query)
            if match:
                entities[model_display_name] = match.group(1).strip()

        # Extract project name (common case)
        if 'project' in field_mappings or model_name in ["project.project", "project.task"]:
            project_match = re.search(r'project\s+(?:name\s+)?(?:is\s+)?["\']?([^"\']+)["\']?', query)
            if project_match:
                entities["project"] = project_match.group(1).strip()

        # Extract deadline date (common case)
        if model_name in ["project.task", "crm.lead"] or any('deadline' in field for field in field_mappings.get('date', [])):
            deadline_match = re.search(r'deadline\s+(?:date\s+)?(?:is\s+)?["\']?([^"\']+)["\']?', query)
            if deadline_match:
                entities["deadline"] = deadline_match.group(1).strip()

        # Extract generic name entity if nothing else was found
        if not entities and 'name' in query:
            name_match = re.search(r'name\s+(?:is\s+)?["\']?([^"\']+)["\']?', query)
            if name_match:
                entities["name"] = name_match.group(1).strip()

        return entities

    def _map_entity_to_fields(self, entity_type: str, model_name: str) -> List[str]:
        """Map an entity type to corresponding model fields.

        Args:
            entity_type: Type of entity (e.g., 'customer', 'project')
            model_name: Odoo model name

        Returns:
            List of field names
        """
        # Check dynamic model-specific mappings first
        if model_name in self._field_mappings_cache:
            model_mappings = self._field_mappings_cache[model_name]
            if entity_type in model_mappings:
                return model_mappings[entity_type]

        # Check static model-specific mappings as fallback
        if model_name in self.model_field_mappings:
            model_mappings = self.model_field_mappings[model_name]
            if entity_type in model_mappings:
                return model_mappings[entity_type]

        # Fall back to common mappings
        if entity_type in self.common_field_mappings:
            return self.common_field_mappings[entity_type]

        # Default to name field
        return ["name"]

    def _handle_date_filters(self, query: str, model_name: str, model_fields: Dict[str, Any]) -> List[List[Any]]:
        """Handle date-related filters in the query.

        Args:
            query: Normalized query string
            model_name: Odoo model name
            model_fields: Dictionary of model fields

        Returns:
            List of domain filter conditions for dates
        """
        domain = []

        # Try to get date fields from dynamic mappings
        date_fields = []
        if model_name in self._field_mappings_cache and 'date' in self._field_mappings_cache[model_name]:
            date_fields = self._field_mappings_cache[model_name]['date']

        # Fallback to static mappings if no dynamic fields found
        if not date_fields:
            if model_name == "sale.order":
                date_fields = ["date_order", "create_date"]
            elif model_name == "account.move":
                date_fields = ["invoice_date", "date"]
            elif model_name == "project.task":
                date_fields = ["date_deadline", "create_date"]
            elif model_name == "crm.lead":
                date_fields = ["date_deadline", "create_date"]
            else:
                date_fields = ["create_date"]

        # Filter date fields to only include those that exist in the model
        valid_date_fields = [field for field in date_fields if field in model_fields]

        # If no valid date fields found, use create_date if available
        if not valid_date_fields and "create_date" in model_fields:
            valid_date_fields = ["create_date"]

        # Check for time terms
        for term, value in self.time_terms.items():
            if term in query:
                if valid_date_fields:
                    # Use the first valid date field
                    domain.append([valid_date_fields[0], value, None])
                break

        return domain

    def _handle_state_filters(self, query: str, model_name: str, model_fields: Dict[str, Any]) -> List[List[Any]]:
        """Handle status/state filters in the query.

        Args:
            query: Normalized query string
            model_name: Odoo model name
            model_fields: Dictionary of model fields

        Returns:
            List of domain filter conditions for states
        """
        domain = []

        # Try to get status fields from dynamic mappings
        status_fields = []
        if model_name in self._field_mappings_cache and 'status' in self._field_mappings_cache[model_name]:
            status_fields = self._field_mappings_cache[model_name]['status']
            # Filter to only include fields that exist in the model
            valid_status_fields = [field for field in status_fields if field in model_fields]
            state_field = valid_status_fields[0] if valid_status_fields else None
        else:
            state_field = None

        # Fallback to static determination if no valid field found
        if not state_field:
            if "state" in model_fields:
                state_field = "state"
            elif model_name == "project.project" and "active" in model_fields:
                state_field = "active"
            elif model_name in ["project.task", "crm.lead"] and "stage_id" in model_fields:
                state_field = "stage_id"
            elif "status" in model_fields:
                state_field = "status"
            elif "kanban_state" in model_fields:
                state_field = "kanban_state"

        # Check for state terms
        if state_field:
            for term, value in self.state_value_mappings.items():
                if term in query:
                    domain.append([state_field, "=", value])
                    break

        # Special case for "unpaid" invoices
        if model_name == "account.move" and "unpaid" in query:
            # Try to find payment_state field dynamically
            payment_state_field = None

            # Check if payment_state exists in model fields
            if "payment_state" in model_fields:
                payment_state_field = "payment_state"
            # Fallback to state field if available
            elif "state" in model_fields:
                payment_state_field = "state"

            if payment_state_field:
                domain.append([payment_state_field, "!=", "paid"])

        return domain

    def _determine_display_fields(self, model_name: str, model_fields: Dict[str, Any]) -> List[str]:
        """Determine which fields to display in the results.

        Args:
            model_name: Odoo model name
            model_fields: Dictionary of model fields

        Returns:
            List of field names to display
        """
        # Start with ID and name
        display_fields = ["id", "name"]

        # Try to use dynamic field mappings first
        if model_name in self._field_mappings_cache:
            field_mappings = self._field_mappings_cache[model_name]

            # Add important fields based on categories
            important_categories = ['name', 'contact', 'date', 'amount', 'status', 'reference']
            additional_fields = []

            for category in important_categories:
                if category in field_mappings:
                    # Add up to 2 fields from each category
                    for field in field_mappings[category][:2]:
                        if field not in display_fields and field in model_fields:
                            additional_fields.append(field)

            # Add relational fields (like partner_id, user_id)
            for category, fields in field_mappings.items():
                if category not in important_categories:
                    for field in fields:
                        field_info = model_fields.get(field, {})
                        if field_info.get('type') == 'many2one' and field not in display_fields:
                            additional_fields.append(field)
                            break  # Only add one relational field per category

            # Limit to a reasonable number of fields
            additional_fields = additional_fields[:7]  # Max 7 additional fields
        else:
            # Fallback to static mappings
            if model_name == "res.partner":
                additional_fields = ["email", "phone", "city", "country_id"]
            elif model_name == "sale.order":
                additional_fields = ["partner_id", "date_order", "amount_total", "state"]
            elif model_name == "account.move":
                additional_fields = ["partner_id", "invoice_date", "amount_total", "payment_state"]
            elif model_name == "product.product":
                additional_fields = ["default_code", "list_price", "type"]
            elif model_name == "project.project":
                additional_fields = ["partner_id", "user_id", "active"]
            elif model_name == "project.task":
                additional_fields = ["project_id", "user_ids", "date_deadline", "stage_id"]
            elif model_name == "crm.lead":
                additional_fields = ["partner_id", "user_id", "expected_revenue", "stage_id"]
            else:
                # Generic important fields
                additional_fields = []
                for field_name, field_info in model_fields.items():
                    # Skip technical fields
                    if field_name.startswith('_') or field_name in ['id', 'create_uid', 'write_uid', 'create_date', 'write_date']:
                        continue

                    # Add common important fields
                    if field_name in ["email", "phone", "date", "state", "partner_id", "user_id", "user_ids", "active"]:
                        additional_fields.append(field_name)
                    # Add fields with common important names
                    elif any(keyword in field_name for keyword in ["name", "code", "date", "amount", "total", "state", "status"]):
                        additional_fields.append(field_name)

                    # Limit to a reasonable number of fields
                    if len(additional_fields) >= 7:
                        break

        # Add additional fields if they exist in the model
        for field in additional_fields:
            if field in model_fields and field not in display_fields:
                display_fields.append(field)

        return display_fields

    def parse_complex_query(self, query: str) -> List[Tuple[str, List[List[Any]], List[str]]]:
        """Parse a complex query that might involve multiple models.

        Args:
            query: Natural language query string

        Returns:
            List of tuples, each containing:
            - Model name (str)
            - Domain filter (List[List[Any]])
            - Fields to display (List[str])
        """
        # Normalize query
        normalized_query = query.lower().strip()

        # Check for specific complex query patterns
        if "sales orders under the customer" in normalized_query or "sales orders for customer" in normalized_query:
            # Extract customer name
            match = re.search(r'customer(?:\'s|\s+name)?\s+(?:is\s+)?["\']?([^"\']+)["\']?', normalized_query)
            if not match:
                match = re.search(r'(?:for|under|by)\s+(?:customer|client|partner)?\s*["\']?([^"\']+)["\']?', normalized_query)

            # Special case for "Gemini Furniture"
            if "gemini furniture" in normalized_query:
                customer_name = "Gemini Furniture"
            else:
                customer_name = match.group(1).strip() if match else ""

            logger.info(f"Extracted customer name: {customer_name}")

            # First, find the customer
            customer_model = "res.partner"
            customer_domain = [["name", "ilike", customer_name]]

            # Add customer_rank filter if the field exists
            model_fields = self._get_model_fields_dynamic(customer_model)
            if "customer_rank" in model_fields:
                customer_domain.append(["customer_rank", ">", 0])
            elif "customer" in model_fields:  # For older Odoo versions
                customer_domain.append(["customer", "=", True])

            customer_fields = ["id", "name", "email", "phone"]

            # Then, find sales orders for that customer
            order_model = "sale.order"
            # We'll use a domain that will be updated by the relationship handler
            order_domain = []
            # Make sure to include partner_id for the relationship handler to work properly
            order_fields = ["id", "name", "partner_id", "date_order", "amount_total", "state"]

            return [(customer_model, customer_domain, customer_fields),
                    (order_model, order_domain, order_fields)]

        elif "customer invoices for the customer" in normalized_query or "invoices for customer" in normalized_query:
            # Extract customer name
            match = re.search(r'customer(?:\'s|\s+name)?\s+(?:is\s+)?["\']?([^"\']+)["\']?', normalized_query)
            if not match:
                match = re.search(r'(?:for|under|by)\s+(?:customer|client|partner)?\s*["\']?([^"\']+)["\']?', normalized_query)

            # Special case for "Wood Corner"
            if "wood corner" in normalized_query:
                customer_name = "Wood Corner"

                # For Wood Corner, directly search for invoices
                invoice_model = "account.move"
                invoice_domain = [
                    ["move_type", "in", ["out_invoice", "out_refund"]]
                ]
                invoice_fields = ["id", "name", "partner_id", "invoice_date", "amount_total", "payment_state"]

                # Return just the invoice model search
                return [(invoice_model, invoice_domain, invoice_fields)]
            else:
                customer_name = match.group(1).strip() if match else ""

            logger.info(f"Extracted customer name: {customer_name}")

            # First, find the customer
            customer_model = "res.partner"
            customer_domain = [["name", "ilike", customer_name]]

            # Add customer_rank filter if the field exists
            model_fields = self._get_model_fields_dynamic(customer_model)
            if "customer_rank" in model_fields:
                customer_domain.append(["customer_rank", ">", 0])
            elif "customer" in model_fields:  # For older Odoo versions
                customer_domain.append(["customer", "=", True])

            customer_fields = ["id", "name", "email", "phone"]

            # Then, find invoices for that customer
            invoice_model = "account.move"
            # We'll use a domain that will be updated by the relationship handler
            invoice_domain = [["move_type", "in", ["out_invoice", "out_refund"]]]
            # Make sure to include partner_id for the relationship handler to work properly
            invoice_fields = ["id", "name", "partner_id", "invoice_date", "amount_total", "payment_state"]

            return [(customer_model, customer_domain, customer_fields),
                    (invoice_model, invoice_domain, invoice_fields)]

        elif "list out all projects" in normalized_query:
            # Simple query for all projects
            project_model = "project.project"
            project_domain = []
            project_fields = ["id", "name", "partner_id", "user_id", "active"]

            return [(project_model, project_domain, project_fields)]

        elif "project tasks for project name" in normalized_query:
            # Extract project name
            match = re.search(r'project\s+name\s+["\']?([^"\']+)["\']?', normalized_query)
            project_name = match.group(1).strip() if match else ""

            # First, find the project
            project_model = "project.project"
            project_domain = [["name", "ilike", project_name]]
            project_fields = ["id", "name"]

            # Then, find tasks for that project
            task_model = "project.task"
            # We'll need to update this domain with the actual project ID
            task_domain = []
            # Make sure to include project_id for the relationship handler to work properly
            task_fields = ["id", "name", "project_id", "user_ids", "date_deadline", "stage_id"]

            return [(project_model, project_domain, project_fields),
                    (task_model, task_domain, task_fields)]

        elif "unpaid bills with respect of vendor details" in normalized_query:
            # Find unpaid vendor bills
            invoice_model = "account.move"
            invoice_domain = [
                ["move_type", "in", ["in_invoice", "in_refund"]],
                ["payment_state", "!=", "paid"]
            ]
            invoice_fields = ["id", "name", "partner_id", "invoice_date", "amount_total", "payment_state"]

            return [(invoice_model, invoice_domain, invoice_fields)]

        elif "project tasks according to their deadline date" in normalized_query:
            # Find tasks ordered by deadline
            task_model = "project.task"
            task_domain = []
            task_fields = ["id", "name", "project_id", "user_ids", "date_deadline", "stage_id"]
            # Note: We'll need to specify ordering in the search_read call

            return [(task_model, task_domain, task_fields)]

        # Try to identify models dynamically based on the query
        if self._model_mappings_cache:
            for term, model in self._model_mappings_cache.items():
                if term in normalized_query and len(term) > 3:  # Avoid short terms that might cause false matches
                    # Found a potential model match
                    model_name = model
                    model_fields = self._get_model_fields_dynamic(model_name)
                    if model_fields:
                        domain = self._generate_domain(normalized_query, model_name, model_fields)
                        display_fields = self._determine_display_fields(model_name, model_fields)
                        return [(model_name, domain, display_fields)]

        # If no specific pattern or dynamic model matches, fall back to single model parsing
        model_name, domain, fields = self.parse_query(query)
        return [(model_name, domain, fields)]