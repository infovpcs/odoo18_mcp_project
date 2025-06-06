#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Improved CSV Import Tool for Odoo 18.

This module provides a clean, well-structured implementation for importing
CSV data into Odoo models with proper error handling, logging, and support
for both create and update operations.
"""

import os
import csv
import logging
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Union
import xmlrpc.client

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("odoo_csv_import")


class OdooCSVImporter:
    """
    A class for importing CSV data into Odoo models with proper error handling.
    """
    
    def __init__(
        self,
        url: str,
        db: str,
        username: str,
        password: str,
        timeout: int = 300
    ):
        """
        Initialize the OdooCSVImporter with connection parameters.
        
        Args:
            url: The URL of the Odoo server (e.g., http://localhost:8069)
            db: The database name
            username: The username for authentication
            password: The password for authentication
            timeout: Connection timeout in seconds
        """
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.timeout = timeout
        self.uid = None
        self.models = None
        self.common = None
        
        # Initialize connections
        self._connect()
    
    def _connect(self) -> None:
        """
        Establish connections to Odoo server.
        
        Raises:
            Exception: If connection fails
        """
        try:
            # Connect to common service
            logger.info(f"Connecting to Odoo server at {self.url}")
            self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common", allow_none=True)
            
            # Authenticate
            self.uid = self.common.authenticate(self.db, self.username, self.password, {})
            if not self.uid:
                raise Exception("Authentication failed")
            
            logger.info(f"Successfully authenticated as user ID: {self.uid}")
            
            # Connect to models service
            self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object", allow_none=True)
            
        except Exception as e:
            logger.error(f"Failed to connect to Odoo server: {e}")
            raise
    
    def import_csv(
        self,
        model_name: str,
        csv_file_path: str,
        id_field: str = "id",
        create_if_not_exists: bool = True,
        update_if_exists: bool = True,
        batch_size: int = 100,
        skip_rows: int = 0,
        delimiter: str = ",",
        encoding: str = "utf-8-sig"
    ) -> Dict[str, Any]:
        """
        Import data from a CSV file into an Odoo model.
        
        Args:
            model_name: The name of the Odoo model (e.g., res.partner)
            csv_file_path: Path to the CSV file
            id_field: The field to use as the unique identifier
            create_if_not_exists: Whether to create records that don't exist
            update_if_exists: Whether to update records that already exist
            batch_size: Number of records to process in each batch
            skip_rows: Number of rows to skip at the beginning of the file
            delimiter: CSV delimiter character
            encoding: File encoding
        
        Returns:
            Dict containing results of the import operation
        
        Raises:
            FileNotFoundError: If the CSV file doesn't exist
            Exception: For other errors during import
        """
        if not os.path.exists(csv_file_path):
            logger.error(f"CSV file not found: {csv_file_path}")
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        try:
            # Initialize counters
            result = {
                "total": 0,
                "created": 0,
                "updated": 0,
                "skipped": 0,
                "failed": 0,
                "errors": []
            }
            
            # Read the CSV file
            logger.info(f"Reading CSV file: {csv_file_path}")
            with open(csv_file_path, 'r', encoding=encoding) as f:
                reader = csv.reader(f, delimiter=delimiter)
                
                # Skip header rows if needed
                for _ in range(skip_rows):
                    next(reader)
                
                # Get headers
                headers = next(reader)
                logger.info(f"CSV headers: {headers}")
                
                # Check if id_field is in headers
                if id_field not in headers:
                    logger.error(f"ID field '{id_field}' not found in CSV headers")
                    raise ValueError(f"ID field '{id_field}' not found in CSV headers")
                
                # Process records in batches
                records_batch = []
                id_field_index = headers.index(id_field)
                
                for row_num, row in enumerate(reader, start=skip_rows+2):  # +2 for header and 0-indexing
                    try:
                        # Skip empty rows
                        if not row:
                            logger.debug(f"Skipping empty row {row_num}")
                            continue
                        
                        # Create record dict from row
                        record = {headers[i]: value for i, value in enumerate(row) if i < len(headers) and value}
                        
                        # Add record to batch
                        records_batch.append(record)
                        result["total"] += 1
                        
                        # Process batch when it reaches batch_size
                        if len(records_batch) >= batch_size:
                            self._process_batch(
                                model_name, records_batch, id_field, 
                                create_if_not_exists, update_if_exists, result
                            )
                            records_batch = []
                    
                    except Exception as e:
                        logger.error(f"Error processing row {row_num}: {e}")
                        result["failed"] += 1
                        result["errors"].append({
                            "row": row_num,
                            "error": str(e)
                        })
                
                # Process remaining records
                if records_batch:
                    self._process_batch(
                        model_name, records_batch, id_field,
                        create_if_not_exists, update_if_exists, result
                    )
            
            # Log results
            logger.info(f"Import completed: {result['total']} total, "
                       f"{result['created']} created, {result['updated']} updated, "
                       f"{result['skipped']} skipped, {result['failed']} failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during CSV import: {e}")
            raise
    
    def _process_batch(
        self,
        model_name: str,
        records: List[Dict[str, Any]],
        id_field: str,
        create_if_not_exists: bool,
        update_if_exists: bool,
        result: Dict[str, Any]
    ) -> None:
        """
        Process a batch of records for import.
        
        Args:
            model_name: The name of the Odoo model
            records: List of record dictionaries
            id_field: The field to use as the unique identifier
            create_if_not_exists: Whether to create records that don't exist
            update_if_exists: Whether to update records that already exist
            result: Dict to update with operation results
        """
        if not records:
            logger.debug("Skipping empty batch")
            return
        
        # Get unique values for the id_field
        id_values = [record[id_field] for record in records if id_field in record]
        
        # Skip if no valid records
        if not id_values:
            logger.warning(f"No records with {id_field} field in batch, skipping")
            for record in records:
                result["skipped"] += 1
            return
        
        # Find existing records
        domain = [(id_field, 'in', id_values)]
        try:
            existing_records = self.models.execute_kw(
                self.db, self.uid, self.password,
                model_name, 'search_read',
                [domain, [id_field]]
            )
            
            # Create dictionary of existing records by id_field
            existing_ids = {record[id_field]: record['id'] for record in existing_records}
            
            # Process each record
            for record in records:
                try:
                    record_id = record.get(id_field)
                    
                    # Skip if no ID field
                    if not record_id:
                        logger.warning(f"Record missing {id_field}, skipping")
                        result["skipped"] += 1
                        continue
                    
                    # Check if record exists
                    if record_id in existing_ids:
                        # Update existing record
                        if update_if_exists:
                            odoo_id = existing_ids[record_id]
                            success = self._update_record(model_name, odoo_id, record)
                            if success:
                                result["updated"] += 1
                            else:
                                result["failed"] += 1
                                result["errors"].append({
                                    "record": record_id,
                                    "error": "Failed to update record"
                                })
                        else:
                            logger.info(f"Record with {id_field}={record_id} exists but update_if_exists=False, skipping")
                            result["skipped"] += 1
                    else:
                        # Create new record
                        if create_if_not_exists:
                            success = self._create_record(model_name, record)
                            if success:
                                result["created"] += 1
                            else:
                                result["failed"] += 1
                                result["errors"].append({
                                    "record": record_id,
                                    "error": "Failed to create record"
                                })
                        else:
                            logger.info(f"Record with {id_field}={record_id} doesn't exist but create_if_not_exists=False, skipping")
                            result["skipped"] += 1
                
                except Exception as e:
                    logger.error(f"Error processing record {record.get(id_field, 'unknown')}: {e}")
                    result["failed"] += 1
                    result["errors"].append({
                        "record": record.get(id_field, "unknown"),
                        "error": str(e)
                    })
                    
        except Exception as e:
            logger.error(f"Error searching for existing records: {e}")
            # Skip the entire batch on search error
            for record in records:
                result["failed"] += 1
                result["errors"].append({
                    "record": record.get(id_field, "unknown"),
                    "error": f"Failed to search for existing records: {str(e)}"
                })
    
    def _create_record(self, model_name: str, record: Dict[str, Any]) -> bool:
        """
        Create a new record in Odoo.
        
        Args:
            model_name: The name of the Odoo model
            record: Record data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove the id_field from the record if it's an Odoo reserved field
            if 'id' in record and not record['id'].isdigit():
                record = record.copy()  # Create a copy to avoid modifying the original
                logger.debug(f"Removing 'id' field with value '{record['id']}' for create operation")
                del record['id']
            
            # Create the record
            new_id = self.models.execute_kw(
                self.db, self.uid, self.password,
                model_name, 'create',
                [record]
            )
            
            logger.info(f"Created new record in {model_name} with ID: {new_id}")
            return bool(new_id)
        
        except Exception as e:
            logger.error(f"Error creating record: {e}")
            return False
    
    def _update_record(self, model_name: str, record_id: int, record: Dict[str, Any]) -> bool:
        """
        Update an existing record in Odoo.
        
        Args:
            model_name: The name of the Odoo model
            record_id: The Odoo ID of the record to update
            record: Record data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create a copy to avoid modifying the original
            update_data = record.copy()
            
            # Remove fields that shouldn't be updated
            for field in ['id', 'create_date', 'create_uid']:
                if field in update_data:
                    logger.debug(f"Removing '{field}' field for update operation")
                    del update_data[field]
            
            # Skip update if no fields to update
            if not update_data:
                logger.warning("No fields to update, skipping")
                return True
            
            # Update the record
            result = self.models.execute_kw(
                self.db, self.uid, self.password,
                model_name, 'write',
                [[record_id], update_data]
            )
            
            logger.info(f"Updated record in {model_name} with ID: {record_id}")
            return bool(result)
        
        except Exception as e:
            logger.error(f"Error updating record: {e}")
            return False


# Example usage
def import_csv_file(
    url: str,
    db: str, 
    username: str, 
    password: str,
    model_name: str,
    csv_file_path: str,
    id_field: str = "id",
    create_if_not_exists: bool = True,
    update_if_exists: bool = True
) -> Dict[str, Any]:
    """
    Helper function to import a CSV file into an Odoo model.
    
    Args:
        url: The URL of the Odoo server
        db: The database name
        username: The username for authentication
        password: The password for authentication
        model_name: The name of the Odoo model
        csv_file_path: Path to the CSV file
        id_field: The field to use as the unique identifier
        create_if_not_exists: Whether to create records that don't exist
        update_if_exists: Whether to update records that already exist
        
    Returns:
        Dict containing results of the import operation
    """
    importer = OdooCSVImporter(url, db, username, password)
    return importer.import_csv(
        model_name=model_name,
        csv_file_path=csv_file_path,
        id_field=id_field,
        create_if_not_exists=create_if_not_exists,
        update_if_exists=update_if_exists
    )


if __name__ == "__main__":
    # Example usage (uncomment and modify to use)
    """
    result = import_csv_file(
        url="http://localhost:8069",
        db="llmdb18",
        username="admin",
        password="admin",
        model_name="res.partner",
        csv_file_path="partners.csv",
        id_field="email"
    )
    print(f"Import results: {result}")
    """
