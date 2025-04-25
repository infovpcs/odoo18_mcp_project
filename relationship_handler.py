#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Relationship Handler Module

This module provides functionality for handling relationships between Odoo models
when performing complex queries that span multiple models.
"""

import logging
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
        """Discover the relationship between two models by analyzing their fields.
        
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
                
                # Skip if the source value is missing
                if from_value is None:
                    continue
                
                # Find matching target records
                matches = []
                for to_record in to_records:
                    to_value = to_record.get(to_field)
                    
                    # Handle special case for text matching
                    if special == "text_match" and isinstance(to_value, str) and isinstance(from_value, (int, str)):
                        # For text fields like invoice_origin that might contain the SO name
                        if str(from_value) in to_value:
                            matches.append(to_record)
                    # Handle many2one fields that store [id, name]
                    elif isinstance(to_value, list) and len(to_value) >= 1:
                        if to_value[0] == from_value:
                            matches.append(to_record)
                    # Direct value comparison
                    elif to_value == from_value:
                        matches.append(to_record)
                
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