#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for direct_export_import.py module.
"""
import os
import json
from direct_export_import import export_related_records, import_related_records

def test_export_import():
    """Test export and import functionality."""
    print("Testing export/import functionality...")
    
    # Test export
    export_path = "./tmp/test_direct_export.csv"
    print(f"Exporting to {export_path}...")
    
    export_result = export_related_records(
        parent_model="account.move",
        child_model="account.move.line",
        relation_field="move_id",
        parent_fields=["id", "name", "partner_id", "invoice_date", "amount_total"],
        child_fields=["id", "product_id", "account_id", "quantity", "price_unit"],
        filter_domain="[('move_type', '=', 'out_invoice')]",
        export_path=export_path
    )
    
    print("Export result:")
    print(json.dumps(export_result, indent=2))
    
    if not export_result["success"]:
        print(f"Export failed: {export_result.get('error', 'Unknown error')}")
        return
    
    # Test import
    import_path = export_path
    print(f"Importing from {import_path}...")
    
    import_result = import_related_records(
        parent_model="account.move",
        child_model="account.move.line",
        relation_field="move_id",
        input_path=import_path,
        force=True
    )
    
    print("Import result:")
    print(json.dumps(import_result, indent=2))
    
    if not import_result["success"]:
        print(f"Import failed: {import_result.get('error', 'Unknown error')}")
        return
    
    print("Export/import test completed successfully!")

if __name__ == "__main__":
    test_export_import()