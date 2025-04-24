#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV handling utilities for Export/Import agent flow.
"""

import os
import csv
import logging
from typing import Dict, List, Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def export_to_csv(records: List[Dict[str, Any]], 
                  export_path: str, 
                  fields: Optional[List[str]] = None) -> str:
    """
    Export records to a CSV file.
    
    Args:
        records: List of records to export
        export_path: Path to export the CSV file
        fields: List of fields to include in the export (if None, all fields are included)
        
    Returns:
        Path to the exported CSV file
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(export_path)), exist_ok=True)
        
        # If no fields are specified, use all fields from the first record
        if not fields and records:
            fields = list(records[0].keys())
        
        # Convert to DataFrame for easier handling
        df = pd.DataFrame(records)
        
        # Select only the specified fields if provided
        if fields:
            # Only include fields that exist in the DataFrame
            existing_fields = [f for f in fields if f in df.columns]
            df = df[existing_fields]
        
        # Export to CSV
        df.to_csv(export_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
        
        logger.info(f"Exported {len(records)} records to {export_path}")
        return export_path
    
    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        raise


def import_from_csv(import_path: str) -> List[Dict[str, Any]]:
    """
    Import records from a CSV file.
    
    Args:
        import_path: Path to the CSV file
        
    Returns:
        List of records imported from the CSV file
    """
    try:
        # Check if file exists
        if not os.path.exists(import_path):
            raise FileNotFoundError(f"CSV file not found: {import_path}")
        
        # Import from CSV
        df = pd.read_csv(import_path)
        
        # Convert to list of dictionaries
        records = df.to_dict(orient='records')
        
        logger.info(f"Imported {len(records)} records from {import_path}")
        return records
    
    except Exception as e:
        logger.error(f"Error importing from CSV: {str(e)}")
        raise


def apply_field_mapping(records: List[Dict[str, Any]], 
                        field_mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Apply field mapping to records.
    
    Args:
        records: List of records to apply mapping to
        field_mapping: Mapping from CSV field names to Odoo field names
        
    Returns:
        List of records with mapped field names
    """
    try:
        mapped_records = []
        
        for record in records:
            mapped_record = {}
            
            # Apply mapping
            for csv_field, odoo_field in field_mapping.items():
                if csv_field in record:
                    mapped_record[odoo_field] = record[csv_field]
            
            # Add unmapped fields
            for field, value in record.items():
                if field not in field_mapping:
                    mapped_record[field] = value
            
            mapped_records.append(mapped_record)
        
        logger.info(f"Applied field mapping to {len(records)} records")
        return mapped_records
    
    except Exception as e:
        logger.error(f"Error applying field mapping: {str(e)}")
        raise


def get_csv_fields(import_path: str) -> List[str]:
    """
    Get the field names from a CSV file.
    
    Args:
        import_path: Path to the CSV file
        
    Returns:
        List of field names
    """
    try:
        # Check if file exists
        if not os.path.exists(import_path):
            raise FileNotFoundError(f"CSV file not found: {import_path}")
        
        # Read the first row to get field names
        with open(import_path, 'r') as f:
            reader = csv.reader(f)
            fields = next(reader)
        
        return fields
    
    except Exception as e:
        logger.error(f"Error getting CSV fields: {str(e)}")
        raise