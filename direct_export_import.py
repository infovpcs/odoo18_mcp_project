"""
Legacy direct export/import wrapper module.
"""

from scripts.dynamic_data_tool import export_rel, export_model


def export_related_records(parent_model, child_model, relation_field, parent_fields=None, child_fields=None, filter_domain=None, limit=1000, export_path=None):
    """
    Wrapper around dynamic_data_tool.export_rel.
    """
    class Args:
        pass
    args = Args()
    args.parent_model = parent_model
    args.child_model = child_model
    args.relation_field = relation_field

    # Convert parent_fields and child_fields to comma-separated strings if they are lists
    if parent_fields is None:
        args.parent_fields = None
    elif isinstance(parent_fields, list):
        args.parent_fields = ','.join(parent_fields)
    else:
        args.parent_fields = parent_fields

    if child_fields is None:
        args.child_fields = None
    elif isinstance(child_fields, list):
        args.child_fields = ','.join(child_fields)
    else:
        args.child_fields = child_fields

    # Handle domain filter
    args.domain = filter_domain

    args.output = export_path
    args.limit = limit

    # Call the export_rel function
    try:
        export_rel(args)
        success = True
        error = None
    except Exception as e:
        success = False
        error = str(e)

    # Count the number of records in the CSV file (if available)
    parent_records = 0
    child_records = 0
    combined_records = 0

    if success:
        try:
            import csv
            with open(export_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if '_record_type' in row:
                        if row['_record_type'] == 'parent':
                            parent_records += 1
                        elif row['_record_type'] == 'combined':
                            combined_records += 1
        except Exception:
            pass

    return {
        "success": success,
        "error": error,
        "parent_model": parent_model,
        "child_model": child_model,
        "relation_field": relation_field,
        "parent_fields": parent_fields or [],
        "child_fields": child_fields or [],
        "parent_records": parent_records,
        "child_records": child_records,
        "combined_records": combined_records,
        "export_path": export_path
    }


def import_related_records(parent_model, child_model, relation_field, parent_fields=None, child_fields=None,parent_field_mapping = None,
                           child_field_mapping = None,
                      input_path=None, name_prefix=None, parent_defaults=None, child_defaults=None,
                      force=False, reset_to_draft=False, skip_readonly_fields=False, create_if_not_exists=True, update_if_exists=True):
    """
    Wrapper around dynamic_data_tool.import_rel.

    Args:
        parent_model: The technical name of the parent Odoo model
        child_model: The technical name of the child Odoo model
        relation_field: The field in the child model that relates to the parent
        parent_fields: List of field names to import from the parent model
        child_fields: List of field names to import from the child model
        input_path: Path to the CSV file to import
        name_prefix: Prefix for the name field during import
        parent_defaults: Default values for parent fields as a Python dict
        child_defaults: Default values for child fields as a Python dict
        force: Whether to force import even if required fields are missing
        reset_to_draft: Whether to reset records to draft before updating (for account.move)
        skip_readonly_fields: Whether to skip readonly fields for posted records
        create_if_not_exists: Whether to create new records if they don't exist
        update_if_exists: Whether to update existing records
    """
    class Args:
        pass
    args = Args()
    args.parent_model = parent_model
    args.child_model = child_model
    args.relation_field = relation_field

    # For import_rel, we need to determine the parent and child fields from the CSV file
    # since the dynamic_data_tool.py script requires them
    try:
        import csv
        with open(input_path, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)

            # If parent_field_mapping or child_fields were provided, use them instead
            if parent_field_mapping:
                args.parent_field_mapping = parent_field_mapping

            if child_field_mapping:
                args.child_field_mapping = child_field_mapping

    except Exception as e:
        return {
            "success": False,
            "error": f"Error reading CSV file: {str(e)}",
            "parent_model": parent_model,
            "child_model": child_model,
            "relation_field": relation_field,
            "imported_records": 0,
            "import_path": input_path
        }

    args.input = input_path
    args.name_prefix = name_prefix

    # Handle default values
    if parent_defaults:
        import json
        if isinstance(parent_defaults, dict):
            args.parent_defaults = json.dumps(parent_defaults)
        else:
            args.parent_defaults = parent_defaults

    if child_defaults:
        import json
        if isinstance(child_defaults, dict):
            args.child_defaults = json.dumps(child_defaults)
        else:
            args.child_defaults = child_defaults

    # Handle other options
    args.force = force
    args.reset_to_draft = reset_to_draft
    args.skip_readonly_fields = skip_readonly_fields
    args.create_if_not_exists = create_if_not_exists
    args.update_if_exists = update_if_exists

    # Call the import_rel function
    try:
        from scripts.dynamic_data_tool import import_rel
        summary = import_rel(args)
        success = True
        error = None
    except Exception as e:
        success = False
        error = str(e)

    # Count the number of records in the CSV file (if available)
    total_records = 0
    if success:
        try:
            with open(input_path, 'r') as f:
                # Subtract 1 for the header row
                total_records = len(f.readlines()) - 1
                if total_records < 0:
                    total_records = 0
        except Exception:
            pass

    # Create a more detailed result with parent and child record counts
    # Since we don't have actual counts from import_rel, we'll use placeholders
    return {
        "success": success,
        "error": error,
        "parent_model": parent_model,
        "child_model": child_model,
        "relation_field": relation_field,
        "imported_records": total_records,
        "import_path": input_path,
        "total_records": total_records,
        "parent_created": summary["parent_created"],
        "parent_updated": summary["parent_updated"],
        "parent_failed": summary["parent_failed"],
        "child_created": summary["child_created"],
        "child_updated": summary["child_updated"],
        "child_failed": summary["child_failed"],
        "validation_errors": []  # Placeholder
    }


def export_records(model_name, output_path, filter_domain=None, fields=None, limit=1000):
    """
    Wrapper around dynamic_data_tool.export_model.
    """
    class Args:
        pass
    args = Args()
    args.model = model_name
    args.output = output_path

    # Handle fields parameter - convert to comma-separated string if it's a list
    if isinstance(fields, list):
        args.fields = ','.join(fields)
    else:
        args.fields = fields

    # Handle domain filter
    args.domain = filter_domain

    # Set limit
    args.limit = limit

    # Call the export_model function
    try:
        export_model(args)
        success = True
        error = None
    except Exception as e:
        success = False
        error = str(e)

    # Count the number of records in the CSV file (if available)
    total_records = 0
    if success:
        try:
            with open(output_path, 'r') as f:
                # Subtract 1 for the header row
                total_records = len(f.readlines()) - 1
                if total_records < 0:
                    total_records = 0
        except Exception:
            pass

    return {
        "success": success,
        "error": error,
        "model_name": model_name,
        "selected_fields": fields or [],
        "total_records": total_records,
        "exported_records": total_records,
        "export_path": output_path
    }


def import_records(input_path, model_name, field_mapping=None, create_if_not_exists=True,
               update_if_exists=True, defaults=None, force=False, skip_invalid=False, name_prefix=None, match_field='id'):
    """
    Wrapper around dynamic_data_tool.import_model.

    Args:
        input_path: Path to the CSV file to import
        model_name: The technical name of the Odoo model
        field_mapping: Mapping from CSV field names to Odoo field names
        create_if_not_exists: Whether to create new records if they don't exist
        update_if_exists: Whether to update existing records
        defaults: Default values for fields as a Python dict
        force: Whether to force import even if required fields are missing
        skip_invalid: Whether to skip invalid values for selection fields
        name_prefix: Prefix for the name field during import
        match_field: Field to use for matching existing records (default: id)
    """
    class Args:
        pass
    args = Args()
    args.model = model_name
    args.input = input_path

    # Handle field mapping
    if field_mapping:
        args.field_mapping = field_mapping

    # Handle default values
    if defaults:
        import json
        if isinstance(defaults, dict):
            args.defaults = json.dumps(defaults)
        else:
            args.defaults = defaults

    # Handle other options
    args.force = force
    args.skip_invalid = skip_invalid
    args.name_prefix = name_prefix
    args.create_if_not_exists = create_if_not_exists
    args.update = update_if_exists  # Set update flag for import_model
    args.match_field = match_field  # Field to use for matching existing records

    # Call the import_model function
    created_count = 0
    updated_count = 0
    error_count = 0

    try:
        from scripts.dynamic_data_tool import import_model
        # Capture stdout to parse the import summary
        import io
        import sys
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            summary = import_model(args)

        success = True
        error = None
    except Exception as e:
        success = False
        error = str(e)

    # Count the number of records in the CSV file (if available)
    total_records = 0
    if success:
        try:
            with open(input_path, 'r') as f:
                # Subtract 1 for the header row
                total_records = len(f.readlines()) - 1
                if total_records < 0:
                    total_records = 0
        except Exception:
            pass

    return {
        "success": success,
        "error": error,
        "model_name": model_name,
        "imported_records": summary["created_count"],
        "updated_records": summary["updated_count"],
        "import_path": input_path,
        "field_mapping": field_mapping or {},
        "total_records": total_records,
        "failed_records": summary["error_count"],
        "validation_errors": []  # Placeholder
    }
