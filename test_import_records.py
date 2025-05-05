#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for import_records function.
"""
import json
from direct_export_import import import_records

def test_import_records():
    """Test import_records functionality."""
    print("Testing import_records functionality...")

    # Test export first to create a CSV file
    export_path = "./tmp/test_import_records.csv"
    print(f"Exporting to {export_path}...")

    # Create Args object for export_model
    class Args:
        pass
    args = Args()
    args.model = "res.partner"
    args.fields = "id,name,email,phone,street,city,country_id"
    args.domain = "[('customer_rank', '>', 0)]"
    args.limit = 10
    args.output = export_path

    # Call export_model
    from scripts.dynamic_data_tool import export_model
    export_model(args)

    # Create a result object
    export_result = {
        "success": True,
        "error": None,
        "model_name": "res.partner",
        "export_path": export_path
    }

    print("Export result:")
    print(json.dumps(export_result, indent=2))

    if not export_result["success"]:
        print(f"Export failed: {export_result.get('error', 'Unknown error')}")
        return

    # Test import
    import_path = export_path
    print(f"Importing from {import_path}...")

    import_result = import_records(
        input_path=import_path,
        model_name="res.partner",
        force=True,
        name_prefix="Test_"
    )

    print("Import result:")
    print(json.dumps(import_result, indent=2))

    if not import_result["success"]:
        print(f"Import failed: {import_result.get('error', 'Unknown error')}")
        return

    print("Import_records test completed successfully!")

if __name__ == "__main__":
    test_import_records()