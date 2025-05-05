#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dynamic Odoo data export/import utility.
Supports exporting any model's stored fields and importing CSV back via XML-RPC.
"""
import os
import csv
import argparse
import xmlrpc.client
from dotenv import load_dotenv
import ast

def connect():
    load_dotenv()
    url = os.getenv('ODOO_URL', 'http://localhost:8069')
    db = os.getenv('ODOO_DB')
    user = os.getenv('ODOO_USERNAME')
    pwd = os.getenv('ODOO_PASSWORD')
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
    uid = common.authenticate(db, user, pwd, {})
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    return models, db, uid, pwd

def fetch_fields(models, db, uid, pwd, model):
    # Only stored fields; exclude readonly
    dom = [[('model','=',model),('store','=',True)]]
    fields = models.execute_kw(db, uid, pwd,
        'ir.model.fields', 'search_read', dom,
        {'fields':['name','ttype','relation','required','readonly'], 'order':'name'})
    # filter out readonly fields
    stored_fields = [f for f in fields if not f.get('readonly')]
    field_names = [f['name'] for f in stored_fields]
    return stored_fields, field_names

def export_model(args):
    """Export model records to CSV file."""
    models, db, uid, pwd = connect()

    # Get all fields metadata
    all_fields_meta, all_field_names = fetch_fields(models, db, uid, pwd, args.model)

    # Filter fields if specified
    if hasattr(args, 'fields') and args.fields:
        requested_fields = [f.strip() for f in args.fields.split(',')]
        # Validate requested fields
        invalid_fields = [f for f in requested_fields if f not in all_field_names]
        if invalid_fields:
            print(f"Warning: The following fields do not exist in {args.model}: {', '.join(invalid_fields)}")

        # Filter to only requested valid fields
        field_names = [f for f in requested_fields if f in all_field_names]
        fields_meta = [fm for fm in all_fields_meta if fm['name'] in field_names]
    else:
        fields_meta = all_fields_meta
        field_names = all_field_names

    if not field_names:
        print(f"Error: No valid fields to export for {args.model}")
        return

    # Support optional domain filter
    domain = []
    if getattr(args, 'domain', None):
        try:
            # Parse domain and convert to tuple of tuples for XML-RPC
            parsed = ast.literal_eval(args.domain)
            # Ensure it's a sequence of tuples
            domain = tuple(tuple(x) for x in parsed)
        except Exception as e:
            print(f"Error: Invalid domain: {args.domain}")
            print(f"Exception: {e}")
            print("Domain should be a Python list of tuples, e.g. \"[('state', '=', 'posted')]\"")
            return

    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

        # Perform search_read with optional domain
        print(f"Searching for records in {args.model}...")
        recs = models.execute_kw(db, uid, pwd,
            args.model, 'search_read', [domain], {'fields': field_names, 'limit': False})

        if not recs:
            print(f"No records found in {args.model} with the given domain")
            # Still create the CSV with headers
            with open(args.output, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(field_names)
            print(f"Created empty CSV file with headers at {args.output}")
            return

        print(f"Found {len(recs)} records. Exporting to CSV...")

        with open(args.output, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(field_names)

            for rec in recs:
                row = []
                for fm in fields_meta:
                    name = fm['name']; t = fm['ttype']
                    val = rec.get(name)

                    # Normalize falsy values to empty string
                    if val is False or val is None:
                        row.append('')
                        continue

                    if t == 'many2one':
                        # For many2one, export the ID
                        row.append(val[0] if isinstance(val,(list,tuple)) else '')
                    elif t in ('one2many','many2many'):
                        # For one2many and many2many, export comma-separated IDs
                        if val:
                            ids = [v[0] if isinstance(v,(list,tuple)) else v for v in val]
                            row.append(','.join(str(x) for x in ids))
                        else:
                            row.append('')
                    elif t == 'binary':
                        # For binary fields, indicate presence but don't export the data
                        row.append('[BINARY DATA]' if val else '')
                    else:
                        # For other fields, export the value directly
                        row.append(val)

                writer.writerow(row)

        print(f"Successfully exported {len(recs)} records to {args.output}")

    except Exception as e:
        print(f"Error exporting {args.model}: {e}")
        return

def safe_int(s, default=None):
    try: return int(s)
    except: return default

def import_model(args):
    models, db, uid, pwd = connect()
    fields_meta, field_names = fetch_fields(models, db, uid, pwd, args.model)

    # Get required fields
    required_fields = [f['name'] for f in fields_meta if f.get('required')]

    # Parse default values if provided
    default_values = {}
    if hasattr(args, 'defaults') and args.defaults:
        try:
            default_values = ast.literal_eval(args.defaults)
            if not isinstance(default_values, dict):
                print(f"Warning: Defaults must be a dictionary. Got {type(default_values)}. Ignoring defaults.")
                default_values = {}
        except Exception as e:
            print(f"Warning: Could not parse defaults: {e}. Ignoring defaults.")

    # Check if required fields are covered by defaults or CSV
    with open(args.input, newline='') as f:
        sample_reader = csv.DictReader(f)
        csv_fields = sample_reader.fieldnames if sample_reader.fieldnames else []

    missing_required = [f for f in required_fields if f not in csv_fields and f not in default_values]
    if missing_required:
        print(f"Warning: The following required fields are missing and have no defaults: {', '.join(missing_required)}")
        print("You can provide defaults using --defaults '{\"field1\": \"value1\", \"field2\": \"value2\"}'")
        if not args.force:
            print("Use --force to import anyway (may fail if required fields are missing)")
            return

    # Get selection fields to validate values
    selection_fields = {}
    for fm in fields_meta:
        if fm['ttype'] == 'selection':
            field_info = models.execute_kw(db, uid, pwd, args.model, 'fields_get', [[fm['name']]])
            if fm['name'] in field_info and 'selection' in field_info[fm['name']]:
                selection_fields[fm['name']] = [s[0] for s in field_info[fm['name']]['selection']]

    # counter for name updates
    counter = 1
    success_count = 0
    error_count = 0

    with open(args.input, newline='') as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header row
            vals = {}

            # Add default values first
            for key, value in default_values.items():
                vals[key] = value

            # Process CSV values
            for fm in fields_meta:
                name = fm['name']; t = fm['ttype']

                # Skip if field not in CSV
                if name not in row:
                    continue

                raw = row.get(name)
                # normalize raw to string and strip
                raw_str = str(raw).strip() if raw is not None else ''
                # skip empty or false-like
                if not raw_str or raw_str.lower() in ('false', 'none'):
                    continue
                # now use raw_str
                raw = raw_str
                # skip one2many fields on import (not direct importable)
                if t == 'one2many':
                    continue

                # Validate selection fields
                if t == 'selection' and name in selection_fields:
                    if raw not in selection_fields[name]:
                        print(f"Warning: Invalid value '{raw}' for selection field '{name}' in row {row_num}.")
                        print(f"Valid values are: {', '.join(selection_fields[name])}")
                        if args.skip_invalid:
                            continue

                if t in ('integer','float'):
                    vals[name] = safe_int(raw, 0)
                elif t == 'boolean':
                    vals[name] = raw.lower() in ('1','true','yes')
                elif t == 'many2one':
                    # Try to handle name lookup for many2one fields
                    if not raw.isdigit() and '/' not in raw:  # Not an ID or external ID
                        relation = fm.get('relation')
                        if relation:
                            try:
                                # Try to find the record by name
                                rel_ids = models.execute_kw(db, uid, pwd, relation, 'search',
                                                          [[('name', '=', raw)]], {'limit': 1})
                                if rel_ids:
                                    vals[name] = rel_ids[0]
                                else:
                                    print(f"Warning: Could not find {relation} with name '{raw}' for field '{name}' in row {row_num}")
                            except Exception as e:
                                print(f"Error looking up {relation} by name: {e}")
                                vals[name] = safe_int(raw)
                        else:
                            vals[name] = safe_int(raw)
                    else:
                        vals[name] = safe_int(raw)
                elif t == 'many2many':
                    ids = [safe_int(x) for x in raw.split(',') if x]
                    vals[name] = [(6,0,ids)]
                else:
                    vals[name] = raw

            # override name if prefix provided
            if hasattr(args, 'name_prefix') and args.name_prefix:
                vals['name'] = f"{args.name_prefix}-{counter:03d}"
                counter += 1

            # Final check for required fields
            missing_vals = [f for f in required_fields if f not in vals]
            if missing_vals and not args.force:
                print(f"Error: Missing required fields in row {row_num}: {', '.join(missing_vals)}")
                error_count += 1
                continue

            try:
                rid = models.execute_kw(db, uid, pwd, args.model, 'create', [vals])
                print(f"Created {args.model} {rid}")
                success_count += 1
            except Exception as e:
                print(f"Error creating {args.model} in row {row_num}: {e}")
                error_count += 1

    print(f"Import summary: {success_count} records created, {error_count} errors")
    return

def export_rel(args):
    """Export parent and child model relation to a flat CSV."""
    models, db, uid, pwd = connect()

    # Fetch all available fields
    all_p_meta, all_p_fields = fetch_fields(models, db, uid, pwd, args.parent_model)
    all_c_meta, all_c_fields = fetch_fields(models, db, uid, pwd, args.child_model)

    # Filter parent fields if specified
    if hasattr(args, 'parent_fields') and args.parent_fields:
        requested_p_fields = [f.strip() for f in args.parent_fields.split(',')]
        # Validate requested fields
        invalid_p_fields = [f for f in requested_p_fields if f not in all_p_fields]
        if invalid_p_fields:
            print(f"Warning: The following parent fields do not exist in {args.parent_model}: {', '.join(invalid_p_fields)}")
        p_fields = [f for f in requested_p_fields if f in all_p_fields]
    else:
        p_fields = all_p_fields

    # Filter child fields if specified
    if hasattr(args, 'child_fields') and args.child_fields:
        requested_c_fields = [f.strip() for f in args.child_fields.split(',')]
        # Validate requested fields
        invalid_c_fields = [f for f in requested_c_fields if f not in all_c_fields]
        if invalid_c_fields:
            print(f"Warning: The following child fields do not exist in {args.child_model}: {', '.join(invalid_c_fields)}")
        c_fields = [f for f in requested_c_fields if f in all_c_fields]
    else:
        c_fields = all_c_fields

    # Ensure relation field is in child fields
    if args.relation_field not in c_fields:
        c_fields.insert(0, args.relation_field)

    # Validate fields
    if not p_fields:
        print(f"Error: No valid parent fields to export for {args.parent_model}")
        return
    if not c_fields:
        print(f"Error: No valid child fields to export for {args.child_model}")
        return

    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)

        # Apply optional parent domain filter
        if getattr(args, 'domain', None):
            try:
                parent_domain = ast.literal_eval(args.domain)
            except Exception as e:
                print(f"Error: Invalid domain: {args.domain}")
                print(f"Exception: {e}")
                print("Domain should be a Python list of tuples, e.g. \"[('move_type', '=', 'out_invoice')]\"")
                return
        else:
            parent_domain = []

        print(f"Searching for parent records in {args.parent_model}...")
        parents = models.execute_kw(db, uid, pwd,
            args.parent_model, 'search_read', [parent_domain], {'fields': p_fields, 'limit': False})

        if not parents:
            print(f"No parent records found in {args.parent_model} with the given domain")
            # Still create the CSV with headers
            with open(args.output, 'w', newline='') as f:
                writer = csv.writer(f)
                header = p_fields + c_fields
                writer.writerow(header)
            print(f"Created empty CSV file with headers at {args.output}")
            return

        print(f"Found {len(parents)} parent records.")

        # Create a map of parent records by ID
        parent_map = {rec['id']: rec for rec in parents}
        parent_ids = list(parent_map.keys())

        # Fetch child records
        print(f"Searching for child records in {args.child_model}...")
        domain = [(args.relation_field, 'in', parent_ids)]
        children = models.execute_kw(db, uid, pwd,
            args.child_model, 'search_read', [domain], {'fields': c_fields, 'limit': False})

        if not children:
            print(f"No child records found in {args.child_model} related to the parent records")
            # Still create the CSV with headers and parent data
            with open(args.output, 'w', newline='') as f:
                writer = csv.writer(f)
                header = p_fields + c_fields
                writer.writerow(header)
                # Write parent records with empty child fields
                for parent in parents:
                    row = []
                    for f in p_fields:
                        val = parent.get(f)
                        # Normalize values
                        if isinstance(val, (list, tuple)):
                            val = val[0] if val else ''
                        if val is False or val is None:
                            val = ''
                        row.append(val)
                    # Add empty values for child fields
                    row.extend([''] * len(c_fields))
                    writer.writerow(row)
            print(f"Exported {len(parents)} parent records (no child records) to {args.output}")
            return

        print(f"Found {len(children)} child records. Exporting to CSV...")

        # Write CSV
        with open(args.output, 'w', newline='') as f:
            writer = csv.writer(f)
            header = p_fields + c_fields
            writer.writerow(header)

            rows = []
            for ch in children:
                raw_pid = ch.get(args.relation_field)
                # Extract raw parent ID safely
                pid = raw_pid[0] if isinstance(raw_pid, (list, tuple)) and raw_pid else raw_pid
                parent = parent_map.get(pid)
                if not parent:
                    continue

                row = []
                # Add parent fields
                for f in p_fields:
                    val = parent.get(f)
                    # Normalize values
                    if isinstance(val, (list, tuple)):
                        val = val[0] if val else ''
                    if val is False or val is None:
                        val = ''
                    row.append(val)

                # Add child fields
                for f in c_fields:
                    val = ch.get(f)
                    # Normalize values
                    if isinstance(val, (list, tuple)):
                        val = val[0] if val else ''
                    if val is False or val is None:
                        val = ''
                    row.append(val)

                rows.append(row)
                writer.writerow(row)

        print(f"Successfully exported {len(rows)} rows to {args.output}")

    except Exception as e:
        print(f"Error exporting related records: {e}")
        return

def import_rel(args):
    """Import flat CSV to parent and child models using grouping on first parent field."""
    models, db, uid, pwd = connect()
    # read CSV
    with open(args.input, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Parse default values if provided
    parent_defaults = {}
    if hasattr(args, 'parent_defaults') and args.parent_defaults:
        try:
            parent_defaults = ast.literal_eval(args.parent_defaults)
        except Exception as e:
            print(f"Warning: Could not parse parent defaults: {e}")

    child_defaults = {}
    if hasattr(args, 'child_defaults') and args.child_defaults:
        try:
            child_defaults = ast.literal_eval(args.child_defaults)
        except Exception as e:
            print(f"Warning: Could not parse child defaults: {e}")

    # Get required fields
    parent_meta, _ = fetch_fields(models, db, uid, pwd, args.parent_model)
    child_meta, _ = fetch_fields(models, db, uid, pwd, args.child_model)

    parent_required = [f['name'] for f in parent_meta if f.get('required')]
    child_required = [f['name'] for f in child_meta if f.get('required')]

    # parse parent and child fields
    p_fields = [s.strip() for s in args.parent_fields.split(',')]
    c_fields = [s.strip() for s in args.child_fields.split(',')]

    # Check for missing required fields
    missing_parent = [f for f in parent_required if f not in p_fields and f not in parent_defaults]
    if missing_parent and not args.force:
        print(f"Warning: Missing required parent fields: {', '.join(missing_parent)}")
        print("Use --parent-defaults or --force to continue")
        return

    missing_child = [f for f in child_required if f not in c_fields and f not in child_defaults and f != args.relation_field]
    if missing_child and not args.force:
        print(f"Warning: Missing required child fields: {', '.join(missing_child)}")
        print("Use --child-defaults or --force to continue")
        return

    # Handle reset to draft for account.move
    if args.reset_to_draft and args.parent_model == 'account.move':
        print("Note: Will reset account.move records to draft before updating")

    parent_ids = {}
    counter = 1
    parent_success = 0
    parent_error = 0
    child_success = 0
    child_error = 0

    # create parent records
    for r in rows:
        key = r[p_fields[0]]
        if key in parent_ids:
            continue

        vals = {}
        # Add defaults first
        for k, v in parent_defaults.items():
            vals[k] = v

        # Add CSV values
        for f in p_fields:
            raw = r.get(f)
            if raw and raw.strip() and raw.lower() not in ('false', 'none'):
                vals[f] = raw.strip()

        if args.name_prefix:
            vals[p_fields[0]] = f"{args.name_prefix}-{counter:03d}"
            counter += 1

        try:
            pid = models.execute_kw(db, uid, pwd, args.parent_model, 'create', [vals])
            parent_ids[key] = pid
            print(f"Created {args.parent_model} {pid}")
            parent_success += 1
        except Exception as e:
            print(f"Error creating {args.parent_model}: {e}")
            parent_error += 1

    # create child records
    for r in rows:
        parent_key = r[p_fields[0]]
        pid = parent_ids.get(parent_key)
        if not pid:
            continue

        vals = {args.relation_field: pid}
        # Add defaults first
        for k, v in child_defaults.items():
            vals[k] = v

        # Add CSV values
        for f in c_fields:
            raw = r.get(f)
            if raw and raw.strip() and raw.lower() not in ('false', 'none'):
                vals[f] = raw.strip()

        try:
            cid = models.execute_kw(db, uid, pwd, args.child_model, 'create', [vals])
            print(f"Created {args.child_model} {cid}")
            child_success += 1
        except Exception as e:
            print(f"Error creating {args.child_model}: {e}")
            child_error += 1

    print(f"Import summary: {parent_success} parent records created ({parent_error} errors), {child_success} child records created ({child_error} errors)")
    return


def model_info(args):
    """Display information about a model and its fields."""
    models, db, uid, pwd = connect()

    try:
        # Get model information
        model_data = models.execute_kw(db, uid, pwd, 'ir.model', 'search_read',
                                      [[('model', '=', args.model)]],
                                      {'fields': ['name', 'model']})

        if not model_data:
            print(f"Error: Model '{args.model}' not found")
            return

        model_info = model_data[0]
        print(f"\nModel: {model_info['model']} ({model_info['name']})")

        # Get field information
        if args.field:
            # Get specific field info
            field_info = models.execute_kw(db, uid, pwd, args.model, 'fields_get', [[args.field]])
            if not field_info:
                print(f"Error: Field '{args.field}' not found in model '{args.model}'")
                return

            field = field_info[args.field]
            print(f"\nField: {args.field} ({field['string']})")
            print(f"Type: {field['type']}")
            if field.get('required'):
                print("Required: Yes")
            if field.get('readonly'):
                print("Readonly: Yes")
            if field.get('help'):
                print(f"Help: {field['help']}")
            if field['type'] == 'selection' and 'selection' in field:
                print("Selection values:")
                for value, label in field['selection']:
                    print(f"  - {value}: {label}")
            if field['type'] in ('many2one', 'one2many', 'many2many') and 'relation' in field:
                print(f"Relation: {field['relation']}")

        else:
            # Get all fields
            fields_meta = models.execute_kw(db, uid, pwd, args.model, 'fields_get', [])

            # Filter fields if needed
            if args.required_only:
                fields_meta = {k: v for k, v in fields_meta.items() if v.get('required')}
            if args.selection_only:
                fields_meta = {k: v for k, v in fields_meta.items() if v.get('type') == 'selection'}

            # Print field information
            print(f"\nFields ({len(fields_meta)}):")
            for name, field in sorted(fields_meta.items()):
                req = "*" if field.get('required') else " "
                ro = "R" if field.get('readonly') else " "
                ftype = field['type']
                if ftype in ('many2one', 'one2many', 'many2many') and 'relation' in field:
                    ftype = f"{ftype} ({field['relation']})"
                print(f"{req}{ro} {name:<30} {ftype:<25} {field['string']}")

            print("\nLegend: * = Required, R = Readonly")

            # Print selection fields if requested
            if args.selection_only:
                print("\nSelection field values:")
                for name, field in sorted(fields_meta.items()):
                    if field['type'] == 'selection' and 'selection' in field:
                        print(f"\n{name} ({field['string']}):")
                        for value, label in field['selection']:
                            print(f"  - {value}: {label}")

    except Exception as e:
        print(f"Error: {e}")
    return

def main():
    p = argparse.ArgumentParser(description='Dynamic export/import for Odoo models')
    sub = p.add_subparsers(dest='command')

    # Export command
    ex = sub.add_parser('export', help='Export model to CSV')
    ex.add_argument('--model', required=True, help='Model name (e.g., res.partner)')
    ex.add_argument('--output', default='./tmp/export.csv', help='Output CSV file path')
    ex.add_argument('--domain', help='Optional domain filter as Python list, e.g. "[(\'date_deadline\',\'!=\', False)]"')
    ex.add_argument('--fields', help='Comma-separated list of fields to export (default: all non-readonly fields)')

    # Import command
    im = sub.add_parser('import', help='Import model from CSV')
    im.add_argument('--model', required=True, help='Model name (e.g., res.partner)')
    im.add_argument('--input', default='./tmp/export.csv', help='Input CSV file path')
    im.add_argument('--name-prefix', help='Prefix for name field during import')
    im.add_argument('--defaults', help='Default values for fields as Python dict, e.g. "{\'autopost_bills\': \'never\'}"')
    im.add_argument('--force', action='store_true', help='Force import even if required fields are missing')
    im.add_argument('--skip-invalid', action='store_true', help='Skip invalid values for selection fields')
    im.add_argument('--update', action='store_true', help='Update existing records instead of creating new ones')
    im.add_argument('--match-field', default='id', help='Field to match existing records (default: id)')

    # Export related models command
    rel_ex = sub.add_parser('export-rel', help='Export parent and child model relation to a flat CSV')
    rel_ex.add_argument('--parent-model', required=True, help='Parent model name (e.g., account.move)')
    rel_ex.add_argument('--child-model', required=True, help='Child model name (e.g., account.move.line)')
    rel_ex.add_argument('--relation-field', required=True, help='Field in child model that relates to parent (e.g., move_id)')
    rel_ex.add_argument('--output', default='./tmp/export-rel.csv', help='Output CSV file path')
    rel_ex.add_argument('--domain', help='Optional parent domain filter as Python list, e.g. "[(\'move_type\',\'in\',[\'out_invoice\'])]"')
    rel_ex.add_argument('--parent-fields', help='Comma-separated list of parent fields to export (default: all non-readonly fields)')
    rel_ex.add_argument('--child-fields', help='Comma-separated list of child fields to export (default: all non-readonly fields)')

    # Import related models command
    rel_im = sub.add_parser('import-rel', help='Import flat CSV to parent and child models using grouping on first parent field')
    rel_im.add_argument('--parent-model', required=True, help='Parent model name (e.g., account.move)')
    rel_im.add_argument('--child-model', required=True, help='Child model name (e.g., account.move.line)')
    rel_im.add_argument('--relation-field', required=True, help='Field in child model that relates to parent (e.g., move_id)')
    rel_im.add_argument('--parent-fields', required=True, help='Comma-separated list of parent fields to import')
    rel_im.add_argument('--child-fields', required=True, help='Comma-separated list of child fields to import')
    rel_im.add_argument('--input', default='./tmp/export-rel.csv', help='Input CSV file path')
    rel_im.add_argument('--name-prefix', help='Prefix for name field during import')
    rel_im.add_argument('--parent-defaults', help='Default values for parent fields as Python dict')
    rel_im.add_argument('--child-defaults', help='Default values for child fields as Python dict')
    rel_im.add_argument('--force', action='store_true', help='Force import even if required fields are missing')
    rel_im.add_argument('--reset-to-draft', action='store_true', help='Reset records to draft before updating (for account.move)')
    rel_im.add_argument('--skip-readonly-fields', action='store_true', help='Skip readonly fields for posted records')

    # Info command to get model information
    info = sub.add_parser('info', help='Get information about a model')
    info.add_argument('--model', required=True, help='Model name (e.g., res.partner)')
    info.add_argument('--field', help='Get information about a specific field')
    info.add_argument('--required-only', action='store_true', help='Show only required fields')
    info.add_argument('--selection-only', action='store_true', help='Show only selection fields')

    args = p.parse_args()
    if args.command == 'export': export_model(args)
    elif args.command == 'import': import_model(args)
    elif args.command == 'export-rel': export_rel(args)
    elif args.command == 'import-rel': import_rel(args)
    elif args.command == 'info': model_info(args)
    else: p.print_help()

if __name__ == '__main__': main()
