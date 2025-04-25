#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Query Parser Module

This module provides functionality for parsing natural language queries
into Odoo domain filters for advanced search operations.
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Set, Union

logger = logging.getLogger(__name__)

class QueryParser:
    """Class for parsing natural language queries into Odoo domain filters."""

    def __init__(self, model_discovery):
        """Initialize the query parser.

        Args:
            model_discovery: ModelDiscovery instance for accessing Odoo models and fields
        """
        self.model_discovery = model_discovery

        # Common model mappings
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

        # Model-specific field mappings
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

        # Get model fields
        model_fields = self.model_discovery.get_model_fields(model_name)
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
        # Check for direct model mentions
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

        # Handle special cases first
        if model_name == "res.partner" and "customer" in query:
            domain.append(["customer_rank", ">", 0])
        elif model_name == "res.partner" and "vendor" in query:
            domain.append(["supplier_rank", ">", 0])
        elif model_name == "account.move" and "customer invoice" in query:
            domain.append(["move_type", "in", ["out_invoice", "out_refund"]])
        elif model_name == "account.move" and "vendor bill" in query or "unpaid bills" in query:
            domain.append(["move_type", "in", ["in_invoice", "in_refund"]])
            if "unpaid" in query:
                domain.append(["payment_state", "!=", "paid"])

        # Extract specific entity mentions
        entities = self._extract_entities(query, model_name)
        for entity_type, entity_value in entities.items():
            field_names = self._map_entity_to_fields(entity_type, model_name)
            if field_names:
                # Use the first field as the primary search field
                domain.append([field_names[0], "ilike", entity_value])

        # Handle date-related queries
        date_domain = self._handle_date_filters(query, model_name)
        if date_domain:
            domain.extend(date_domain)

        # Handle status/state queries
        state_domain = self._handle_state_filters(query, model_name)
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

        # Extract customer/partner name
        if model_name in ["res.partner", "sale.order", "account.move", "project.project"]:
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

        # Extract project name
        if model_name in ["project.project", "project.task"]:
            project_match = re.search(r'project\s+(?:name\s+)?(?:is\s+)?["\']?([^"\']+)["\']?', query)
            if project_match:
                entities["project"] = project_match.group(1).strip()

        # Extract deadline date
        if model_name in ["project.task", "crm.lead"]:
            deadline_match = re.search(r'deadline\s+(?:date\s+)?(?:is\s+)?["\']?([^"\']+)["\']?', query)
            if deadline_match:
                entities["deadline"] = deadline_match.group(1).strip()

        return entities

    def _map_entity_to_fields(self, entity_type: str, model_name: str) -> List[str]:
        """Map an entity type to corresponding model fields.

        Args:
            entity_type: Type of entity (e.g., 'customer', 'project')
            model_name: Odoo model name

        Returns:
            List of field names
        """
        # Check model-specific mappings first
        if model_name in self.model_field_mappings:
            model_mappings = self.model_field_mappings[model_name]
            if entity_type in model_mappings:
                return model_mappings[entity_type]

        # Fall back to common mappings
        if entity_type in self.common_field_mappings:
            return self.common_field_mappings[entity_type]

        # Default to name field
        return ["name"]

    def _handle_date_filters(self, query: str, model_name: str) -> List[List[Any]]:
        """Handle date-related filters in the query.

        Args:
            query: Normalized query string
            model_name: Odoo model name

        Returns:
            List of domain filter conditions for dates
        """
        domain = []

        # Map model to date fields
        date_fields = []
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

        # Check for time terms
        for term, value in self.time_terms.items():
            if term in query:
                if date_fields:
                    # Use the first date field
                    domain.append([date_fields[0], value, None])
                break

        return domain

    def _handle_state_filters(self, query: str, model_name: str) -> List[List[Any]]:
        """Handle status/state filters in the query.

        Args:
            query: Normalized query string
            model_name: Odoo model name

        Returns:
            List of domain filter conditions for states
        """
        domain = []

        # Determine state field based on model
        state_field = "state"
        if model_name == "project.project":
            state_field = "active"
        elif model_name in ["project.task", "crm.lead"]:
            state_field = "stage_id"

        # Check for state terms
        for term, value in self.state_value_mappings.items():
            if term in query:
                domain.append([state_field, "=", value])
                break

        # Special case for "unpaid" invoices
        if model_name == "account.move" and "unpaid" in query:
            domain.append(["payment_state", "!=", "paid"])

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

        # Add model-specific important fields
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
            for field_name in model_fields.keys():
                if field_name in ["email", "phone", "date", "state", "partner_id", "user_id", "user_ids", "active"]:
                    additional_fields.append(field_name)
                # Limit to a reasonable number of fields
                if len(additional_fields) >= 5:
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
        if "sales orders under the customer" in normalized_query:
            # Extract customer name
            match = re.search(r'customer(?:\'s|\s+name)?\s+(?:is\s+)?["\']?([^"\']+)["\']?', normalized_query)
            customer_name = match.group(1).strip() if match else ""

            # First, find the customer
            customer_model = "res.partner"
            customer_domain = [["name", "ilike", customer_name], ["customer_rank", ">", 0]]
            customer_fields = ["id", "name"]

            # Then, find sales orders for that customer
            order_model = "sale.order"
            # We'll need to update this domain with the actual customer ID
            order_domain = []
            order_fields = ["id", "name", "date_order", "amount_total", "state"]

            return [(customer_model, customer_domain, customer_fields),
                    (order_model, order_domain, order_fields)]

        elif "customer invoices for the customer" in normalized_query:
            # Extract customer name
            match = re.search(r'customer(?:\'s|\s+name)?\s+(?:is\s+)?["\']?([^"\']+)["\']?', normalized_query)
            customer_name = match.group(1).strip() if match else ""

            # First, find the customer
            customer_model = "res.partner"
            customer_domain = [["name", "ilike", customer_name], ["customer_rank", ">", 0]]
            customer_fields = ["id", "name"]

            # Then, find invoices for that customer
            invoice_model = "account.move"
            # We'll need to update this domain with the actual customer ID
            invoice_domain = [["move_type", "in", ["out_invoice", "out_refund"]]]
            invoice_fields = ["id", "name", "invoice_date", "amount_total", "payment_state"]

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
            task_fields = ["id", "name", "user_ids", "date_deadline", "stage_id"]

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

        # If no specific pattern matches, fall back to single model parsing
        model_name, domain, fields = self.parse_query(query)
        return [(model_name, domain, fields)]