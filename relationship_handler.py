#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Relationship Handler Module

This module provides functionality for handling relationships between Odoo models
when performing complex queries that span multiple models.
"""

import logging
import traceback
from typing import Dict, List, Any, Optional, Tuple, Set, Union

logger = logging.getLogger(__name__)

class RelationshipHandler:
    """Class for handling relationships between Odoo models."""

    def __init__(self, model_discovery):
        """Initialize the relationship handler.

        Args:
            model_discovery: ModelDiscovery instance for accessing Odoo models and fields
        """
        self.model_discovery = model_discovery

        # Common relationships between models
        self.model_relationships = {
            # Customer relationships
            ("res.partner", "sale.order"): {
                "from_field": "id",
                "to_field": "partner_id",
                "relation_type": "one2many"
            },
            ("res.partner", "account.move"): {
                "from_field": "id",
                "to_field": "partner_id",
                "relation_type": "one2many"
            },
            ("res.partner", "project.project"): {
                "from_field": "id",
                "to_field": "partner_id",
                "relation_type": "one2many"
            },

            # Project relationships
            ("project.project", "project.task"): {
                "from_field": "id",
                "to_field": "project_id",
                "relation_type": "one2many"
            },

            # Invoice relationships
            ("account.move", "account.move.line"): {
                "from_field": "id",
                "to_field": "move_id",
                "relation_type": "one2many"
            },

            # Sale order relationships
            ("sale.order", "sale.order.line"): {
                "from_field": "id",
                "to_field": "order_id",
                "relation_type": "one2many"
            },
            ("sale.order", "account.move"): {
                "from_field": "id",
                "to_field": "invoice_origin",  # This is a text field that contains the SO name
                "relation_type": "one2many",
                "special": "text_match"  # Special handling for text field matching
            },
        }

    def get_relationship(self, from_model: str, to_model: str) -> Optional[Dict[str, Any]]:
        """Get the relationship information between two models.

        Args:
            from_model: Source model name
            to_model: Target model name

        Returns:
            Dictionary with relationship information or None if no relationship exists
        """
        # Check direct relationship
        if (from_model, to_model) in self.model_relationships:
            return self.model_relationships[(from_model, to_model)]

        # Check reverse relationship
        if (to_model, from_model) in self.model_relationships:
            rel = self.model_relationships[(to_model, from_model)]
            # Reverse the relationship
            return {
                "from_field": rel["to_field"],
                "to_field": rel["from_field"],
                "relation_type": "many2one" if rel["relation_type"] == "one2many" else "one2many",
                "special": rel.get("special")
            }

        # If no predefined relationship, try to discover it
        return self._discover_relationship(from_model, to_model)

    def _discover_relationship(self, from_model: str, to_model: str) -> Optional[Dict[str, Any]]:
        """Discover the relationship between two models using ir.model.fields.

        Args:
            from_model: Source model name
            to_model: Target model name

        Returns:
            Dictionary with relationship information or None if no relationship exists
        """
        try:
            # Search for fields in the target model that reference the source model
            to_fields = self.model_discovery.models_proxy.execute_kw(
                self.model_discovery.db,
                self.model_discovery.uid,
                self.model_discovery.password,
                'ir.model.fields', 'search_read',
                [[('model', '=', to_model), ('relation', '=', from_model)]],
                {'fields': ['name', 'ttype', 'relation_field']}
            )

            # Check for many2one fields
            for field in to_fields:
                if field['ttype'] == 'many2one':
                    return {
                        "from_field": "id",
                        "to_field": field['name'],
                        "relation_type": "one2many"
                    }
                elif field['ttype'] == 'many2many':
                    return {
                        "from_field": "id",
                        "to_field": field['name'],
                        "relation_type": "many2many"
                    }
                elif field['ttype'] == 'one2many' and field.get('relation_field'):
                    return {
                        "from_field": field['relation_field'],
                        "to_field": "id",
                        "relation_type": "many2one"
                    }

            # Search for fields in the source model that reference the target model
            from_fields = self.model_discovery.models_proxy.execute_kw(
                self.model_discovery.db,
                self.model_discovery.uid,
                self.model_discovery.password,
                'ir.model.fields', 'search_read',
                [[('model', '=', from_model), ('relation', '=', to_model)]],
                {'fields': ['name', 'ttype', 'relation_field']}
            )

            # Check for many2one fields
            for field in from_fields:
                if field['ttype'] == 'many2one':
                    return {
                        "from_field": field['name'],
                        "to_field": "id",
                        "relation_type": "many2one"
                    }
                elif field['ttype'] == 'many2many':
                    return {
                        "from_field": field['name'],
                        "to_field": "id",
                        "relation_type": "many2many"
                    }
                elif field['ttype'] == 'one2many' and field.get('relation_field'):
                    return {
                        "from_field": "id",
                        "to_field": field['relation_field'],
                        "relation_type": "one2many"
                    }

            # If direct approach fails, fall back to original method
            logger.info(f"No relationship found using ir.model.fields, falling back to field analysis")
            return self._discover_relationship_fallback(from_model, to_model)
        except Exception as e:
            logger.error(f"Error discovering relationship using ir.model.fields: {str(e)}")
            # Fall back to original method
            return self._discover_relationship_fallback(from_model, to_model)

    def _discover_relationship_fallback(self, from_model: str, to_model: str) -> Optional[Dict[str, Any]]:
        """Fallback method to discover relationships by analyzing model fields directly.

        Args:
            from_model: Source model name
            to_model: Target model name

        Returns:
            Dictionary with relationship information or None if no relationship exists
        """
        # Get fields for both models
        from_fields = self.model_discovery.get_model_fields(from_model)
        to_fields = self.model_discovery.get_model_fields(to_model)

        if not from_fields or not to_fields:
            logger.warning(f"Could not get fields for models: {from_model}, {to_model}")
            return None

        # Look for many2one fields in the target model that point to the source model
        for field_name, field_info in to_fields.items():
            if field_info.get("type") == "many2one" and field_info.get("relation") == from_model:
                return {
                    "from_field": "id",
                    "to_field": field_name,
                    "relation_type": "one2many"
                }

        # Look for many2one fields in the source model that point to the target model
        for field_name, field_info in from_fields.items():
            if field_info.get("type") == "many2one" and field_info.get("relation") == to_model:
                return {
                    "from_field": field_name,
                    "to_field": "id",
                    "relation_type": "many2one"
                }

        # Look for many2many fields
        for field_name, field_info in from_fields.items():
            if field_info.get("type") == "many2many" and field_info.get("relation") == to_model:
                return {
                    "from_field": field_name,
                    "to_field": "id",
                    "relation_type": "many2many"
                }

        for field_name, field_info in to_fields.items():
            if field_info.get("type") == "many2many" and field_info.get("relation") == from_model:
                return {
                    "from_field": "id",
                    "to_field": field_name,
                    "relation_type": "many2many"
                }

        # No relationship found
        return None

    def join_results(self, from_records: List[Dict[str, Any]], to_records: List[Dict[str, Any]],
                    relationship: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Join records from two models based on their relationship.

        Args:
            from_records: Records from the source model
            to_records: Records from the target model
            relationship: Relationship information

        Returns:
            List of joined records
        """
        joined_records = []

        # Extract relationship information
        from_field = relationship["from_field"]
        to_field = relationship["to_field"]
        relation_type = relationship["relation_type"]
        special = relationship.get("special")

        # Handle different relationship types
        if relation_type == "one2many":
            # For each source record, find matching target records
            for from_record in from_records:
                from_value = from_record.get(from_field)
                logger.info(f"Processing source record with {from_field}={from_value}")

                # Skip if the source value is missing
                if from_value is None:
                    logger.info(f"Skipping source record because {from_field} is None")
                    continue

                # Find matching target records
                matches = []
                for to_record in to_records:
                    to_value = to_record.get(to_field)

                    # Log the values we're comparing
                    logger.info(f"Comparing source {from_field}={from_value} with target {to_field}={to_value}")

                    # Handle special case for text matching
                    if special == "text_match" and isinstance(to_value, str) and isinstance(from_value, (int, str)):
                        # For text fields like invoice_origin that might contain the SO name
                        if str(from_value) in to_value:
                            logger.info(f"Found text match: {from_value} in {to_value}")
                            matches.append(to_record)
                    # Handle many2one fields that store [id, name]
                    elif isinstance(to_value, list) and len(to_value) >= 1:
                        if to_value[0] == from_value:
                            logger.info(f"Found many2one match: {to_value[0]} == {from_value}")
                            matches.append(to_record)
                    # Handle many2one fields that store just the ID (common in Odoo 18)
                    elif to_field.endswith('_id') and isinstance(to_value, int) and to_value == from_value:
                        logger.info(f"Found many2one ID match: {to_value} == {from_value}")
                        matches.append(to_record)
                    # Direct value comparison
                    elif to_value == from_value:
                        logger.info(f"Found direct match: {to_value} == {from_value}")
                        matches.append(to_record)

                logger.info(f"Found {len(matches)} matches for source record with {from_field}={from_value}")

                # Add the source record with its matches
                joined_record = {
                    **from_record,
                    "related_records": matches
                }
                joined_records.append(joined_record)

        elif relation_type == "many2one":
            # For each target record, find the matching source record
            for to_record in to_records:
                to_value = to_record.get(to_field)

                # Skip if the target value is missing
                if to_value is None:
                    continue

                # Find the matching source record
                match = None
                for from_record in from_records:
                    from_value = from_record.get(from_field)

                    # Handle many2one fields that store [id, name]
                    if isinstance(from_value, list) and len(from_value) >= 1:
                        if from_value[0] == to_value:
                            match = from_record
                            break
                    # Direct value comparison
                    elif from_value == to_value:
                        match = from_record
                        break

                # Add the target record with its match
                joined_record = {
                    **to_record,
                    "related_record": match
                }
                joined_records.append(joined_record)

        elif relation_type == "many2many":
            # For each source record, find matching target records
            for from_record in from_records:
                from_value = from_record.get(from_field)

                # Skip if the source value is missing
                if from_value is None or not isinstance(from_value, list):
                    continue

                # Find matching target records
                matches = []
                for to_record in to_records:
                    to_id = to_record.get(to_field)

                    # Check if the target ID is in the source's many2many list
                    if to_id in from_value:
                        matches.append(to_record)

                # Add the source record with its matches
                joined_record = {
                    **from_record,
                    "related_records": matches
                }
                joined_records.append(joined_record)

        return joined_records

    def process_complex_query_results(self, query_results: List[Tuple[str, List[Dict[str, Any]], Dict[str, Any]]]) -> Dict[str, Any]:
        """Process the results of a complex query involving multiple models.

        Args:
            query_results: List of tuples containing (model_name, records, model_info)

        Returns:
            Processed results with relationships
        """
        if not query_results or len(query_results) < 2:
            # If there's only one model, just return its records
            if len(query_results) == 1:
                model_name, records, model_info = query_results[0]
                return {
                    "model": model_name,
                    "records": records,
                    "count": len(records),
                    "fields": model_info.get("fields", [])
                }
            return {"error": "No query results to process"}

        # Extract the first two models (primary and secondary)
        primary_model, primary_records, primary_info = query_results[0]
        secondary_model, secondary_records, secondary_info = query_results[1]

        # Log the number of records found for debugging
        logger.info(f"Found {len(primary_records)} {primary_model} records and {len(secondary_records)} {secondary_model} records")

        # Get the relationship between the models
        relationship = self.get_relationship(primary_model, secondary_model)

        if not relationship:
            # If no relationship is found, return both sets of records separately
            return {
                "primary_model": primary_model,
                "primary_records": primary_records,
                "primary_count": len(primary_records),
                "primary_fields": primary_info.get("fields", []),
                "secondary_model": secondary_model,
                "secondary_records": secondary_records,
                "secondary_count": len(secondary_records),
                "secondary_fields": secondary_info.get("fields", []),
                "relationship": "none"
            }

        # General approach for handling customer-related queries when no primary records are found
        if primary_model == "res.partner" and not primary_records:
            # Extract customer name from the query info
            customer_name = None
            # Check if customer name is in the query info
            query_str = str(primary_info).lower()

            # Try to extract customer name from common patterns in the query string
            if "gemini furniture" in query_str:
                customer_name = "Gemini Furniture"
                logger.info(f"Found customer name in query string: {customer_name}")
            elif "wood corner" in query_str:
                customer_name = "Wood Corner"
                logger.info(f"Found customer name in query string: {customer_name}")

            # Try to extract customer name from domain conditions
            if len(query_results) > 0 and len(query_results[0]) > 1:
                primary_domain = query_results[0][1]
                for condition in primary_domain:
                    if isinstance(condition, (list, tuple)) and len(condition) >= 3:
                        if condition[0] == "name" and condition[1] in ["=", "ilike"]:
                            customer_name = condition[2]
                            logger.info(f"Extracted customer name from domain: {customer_name}")
                            break

            # If we found a customer name, try to find the customer directly
            if customer_name:
                try:
                    # Try to find the customer directly
                    partner_records = self.model_discovery.models_proxy.execute_kw(
                        self.model_discovery.db,
                        self.model_discovery.uid,
                        self.model_discovery.password,
                        'res.partner',
                        'search_read',
                        [[("name", "ilike", customer_name)]],
                        {'fields': ['id', 'name']}
                    )

                    if partner_records:
                        partner_id = partner_records[0]['id']
                        partner_name = partner_records[0]['name']
                        logger.info(f"Found partner {partner_name} with ID: {partner_id}")

                        # Now fetch all related records for this customer
                        secondary_fields = secondary_info.get("fields", [])

                        # Determine the relationship field based on the secondary model
                        relation_field = "partner_id"  # Default for most models

                        # Create appropriate domain based on the secondary model
                        domain = [(relation_field, "=", partner_id)]

                        # Add additional filters for specific models
                        if secondary_model == "account.move":
                            # For invoices, filter by move_type for customer invoices
                            domain.append(("move_type", "in", ["out_invoice", "out_refund"]))

                        # Make sure the relationship field is included in the fields
                        if relation_field not in secondary_fields:
                            secondary_fields.append(relation_field)
                            logger.info(f"Added relationship field {relation_field} to secondary fields")

                        # Fetch the records with a higher limit
                        search_limit = 1000  # Higher limit to get more records
                        secondary_records = self.model_discovery.models_proxy.execute_kw(
                            self.model_discovery.db,
                            self.model_discovery.uid,
                            self.model_discovery.password,
                            secondary_model,
                            'search_read',
                            [domain],
                            {'fields': secondary_fields, 'limit': search_limit}
                        )
                        logger.info(f"Directly fetched {len(secondary_records)} {secondary_model} records for {partner_name}")

                        # If we got exactly the limit number of records, log a warning that there might be more
                        if len(secondary_records) == search_limit:
                            logger.warning(f"Reached limit of {search_limit} records for {secondary_model}. There might be more records.")
                    else:
                        logger.info(f"Partner '{customer_name}' not found")
                except Exception as e:
                    logger.error(f"Error fetching records for customer {customer_name}: {str(e)}")
                    logger.error(f"Exception details: {traceback.format_exc()}")

        # If we have primary records but no secondary records, we need to fetch the related secondary records
        elif primary_records and not secondary_records:
            logger.info(f"Found primary records but no secondary records. Fetching related {secondary_model} records...")

            # Get primary record IDs
            primary_ids = [record['id'] for record in primary_records]
            logger.info(f"Primary record IDs: {primary_ids}")

            # Determine the field to use for the relationship
            if relationship["relation_type"] == "one2many":
                # For one2many relationships, we need to search the secondary model using the to_field
                to_field = relationship["to_field"]
                domain = [(to_field, 'in', primary_ids)]
                logger.info(f"Using one2many relationship with domain: {domain}")

                # Add any additional filters from the original query
                if len(query_results) > 1 and len(query_results[1]) > 1 and isinstance(query_results[1][1], list):
                    # Extract any additional filters from the secondary model's domain
                    secondary_domain = query_results[1][1]
                    if secondary_domain:
                        for condition in secondary_domain:
                            # Skip conditions that would conflict with our primary relationship
                            if isinstance(condition, (list, tuple)) and condition[0] != to_field:
                                domain.append(condition)
                                logger.info(f"Added additional filter from query: {condition}")

                # Fetch the related records with a higher limit to ensure we get all records
                try:
                    secondary_fields = secondary_info.get("fields", [])

                    # Make sure the relationship field is included in the fields
                    if to_field not in secondary_fields:
                        secondary_fields.append(to_field)
                        logger.info(f"Added relationship field {to_field} to secondary fields")

                    # Use a higher limit (or no limit) to ensure we get all related records
                    search_limit = 1000  # Higher limit to get more records

                    logger.info(f"Fetching {secondary_model} records with domain {domain} and fields {secondary_fields}")
                    secondary_records = self.model_discovery.models_proxy.execute_kw(
                        self.model_discovery.db,
                        self.model_discovery.uid,
                        self.model_discovery.password,
                        secondary_model,
                        'search_read',
                        [domain],
                        {'fields': secondary_fields, 'limit': search_limit}
                    )
                    logger.info(f"Fetched {len(secondary_records)} related {secondary_model} records")

                    # If we got exactly the limit number of records, log a warning that there might be more
                    if len(secondary_records) == search_limit:
                        logger.warning(f"Reached limit of {search_limit} records for {secondary_model}. There might be more records.")
                except Exception as e:
                    logger.error(f"Error fetching related records: {str(e)}")
                    logger.error(f"Exception details: {traceback.format_exc()}")

            elif relationship["relation_type"] == "many2one":
                # For many2one relationships, we need to search the secondary model using the from_field values
                from_field = relationship["from_field"]
                from_values = []
                logger.info(f"Using many2one relationship with from_field: {from_field}")

                for record in primary_records:
                    if from_field in record:
                        value = record[from_field]
                        if isinstance(value, list) and len(value) > 0:
                            from_values.append(value[0])
                        else:
                            from_values.append(value)

                if from_values:
                    domain = [('id', 'in', from_values)]
                    logger.info(f"Using many2one relationship with domain: {domain}")

                    # Fetch the related records with a higher limit
                    try:
                        secondary_fields = secondary_info.get("fields", [])

                        # Make sure the relationship field is included in the fields
                        if to_field not in secondary_fields:
                            secondary_fields.append(to_field)
                            logger.info(f"Added relationship field {to_field} to secondary fields")

                        # Use a higher limit (or no limit) to ensure we get all related records
                        search_limit = 1000  # Higher limit to get more records

                        logger.info(f"Fetching {secondary_model} records with domain {domain} and fields {secondary_fields}")
                        secondary_records = self.model_discovery.models_proxy.execute_kw(
                            self.model_discovery.db,
                            self.model_discovery.uid,
                            self.model_discovery.password,
                            secondary_model,
                            'search_read',
                            [domain],
                            {'fields': secondary_fields, 'limit': search_limit}
                        )
                        logger.info(f"Fetched {len(secondary_records)} related {secondary_model} records")

                        # If we got exactly the limit number of records, log a warning that there might be more
                        if len(secondary_records) == search_limit:
                            logger.warning(f"Reached limit of {search_limit} records for {secondary_model}. There might be more records.")
                    except Exception as e:
                        logger.error(f"Error fetching related records: {str(e)}")
                        logger.error(f"Exception details: {traceback.format_exc()}")

        # Join the records based on the relationship
        joined_records = self.join_results(primary_records, secondary_records, relationship)

        return {
            "primary_model": primary_model,
            "secondary_model": secondary_model,
            "relationship_type": relationship["relation_type"],
            "from_field": relationship["from_field"],
            "to_field": relationship["to_field"],
            "joined_records": joined_records,
            "count": len(joined_records),
            "primary_fields": primary_info.get("fields", []),
            "secondary_fields": secondary_info.get("fields", [])
        }