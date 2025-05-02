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
    models, db, uid, pwd = connect()
    fields_meta, field_names = fetch_fields(models, db, uid, pwd, args.model)
    # support optional domain filter
    domain = []
    if getattr(args, 'domain', None):
        try:
            # parse domain and convert to tuple of tuples for XML-RPC
            parsed = ast.literal_eval(args.domain)
            # ensure it's a sequence of tuples
            domain = tuple(tuple(x) for x in parsed)
        except Exception:
            raise ValueError(f"Invalid domain: {args.domain}")
    # perform search_read with optional domain
    recs = models.execute_kw(db, uid, pwd,
        args.model, 'search_read', [domain], {'fields': field_names, 'limit': False})
    with open(args.output, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(field_names)
        for rec in recs:
            row = []
            for fm in fields_meta:
                name = fm['name']; t = fm['ttype']
                val = rec.get(name)
                # normalize falsy values to empty string
                if val is False or val is None:
                    row.append('')
                    continue
                if t == 'many2one':
                    row.append(val[0] if isinstance(val,(list,tuple)) else '')
                elif t in ('one2many','many2many'):
                    # list of tuples or ints
                    if val:
                        ids = [v[0] if isinstance(v,(list,tuple)) else v for v in val]
                        row.append(','.join(str(x) for x in ids))
                    else:
                        row.append('')
                else:
                    row.append(val)
            writer.writerow(row)
    print(f"Exported {len(recs)} records to {args.output}")

def safe_int(s, default=None):
    try: return int(s)
    except: return default

def import_model(args):
    models, db, uid, pwd = connect()
    fields_meta, field_names = fetch_fields(models, db, uid, pwd, args.model)
    # counter for name updates
    counter = 1
    with open(args.input, newline='') as f:
        reader = csv.DictReader(f, fieldnames=field_names)
        next(reader)
        for row in reader:
            vals = {}
            for fm in fields_meta:
                name = fm['name']; t = fm['ttype']
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
                if t in ('integer','float'):
                    vals[name] = safe_int(raw, 0)
                elif t == 'boolean':
                    vals[name] = raw.lower() in ('1','true','yes')
                elif t == 'many2one':
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
            try:
                rid = models.execute_kw(db, uid, pwd, args.model, 'create', [vals])
                print(f"Created {args.model} {rid}")
            except Exception as e:
                print(f"Error creating {args.model}: {e}")
    return

def export_rel(args):
    """Export parent and child model relation to a flat CSV."""
    models, db, uid, pwd = connect()
    # fetch fields
    p_meta, p_fields = fetch_fields(models, db, uid, pwd, args.parent_model)
    c_meta, c_fields = fetch_fields(models, db, uid, pwd, args.child_model)
    # ensure relation field in child fields
    if args.relation_field not in c_fields:
        c_fields.insert(0, args.relation_field)
    # apply optional parent domain filter
    if getattr(args, 'domain', None):
        parent_domain = ast.literal_eval(args.domain)
    else:
        parent_domain = []
    parents = models.execute_kw(db, uid, pwd,
        args.parent_model, 'search_read', [parent_domain], {'fields': p_fields, 'limit': False})
    parent_map = {rec['id']: rec for rec in parents}
    parent_ids = list(parent_map.keys())
    # fetch child records
    domain = [(args.relation_field, 'in', parent_ids)]
    children = models.execute_kw(db, uid, pwd,
        args.child_model, 'search_read', [domain], {'fields': c_fields, 'limit': False})
    # write CSV
    with open(args.output, 'w', newline='') as f:
        writer = csv.writer(f)
        header = p_fields + c_fields
        writer.writerow(header)
        rows = []
        for ch in children:
            raw_pid = ch.get(args.relation_field)
            # extract raw parent ID safely
            pid = raw_pid[0] if isinstance(raw_pid, (list, tuple)) and raw_pid else raw_pid
            parent = parent_map.get(pid)
            if not parent:
                continue
            row = []
            for f in p_fields:
                val = parent.get(f)
                # normalize falsy and empty lists
                if isinstance(val, (list, tuple)):
                    val = val[0] if val else ''
                if val is False or val is None:
                    val = ''
                row.append(val)
            for f in c_fields:
                val = ch.get(f)
                # normalize falsy and empty lists
                if isinstance(val, (list, tuple)):
                    val = val[0] if val else ''
                if val is False or val is None:
                    val = ''
                row.append(val)
            rows.append(row)
            writer.writerow(row)
    print(f"Exported {len(rows)} rows to {args.output}")
    return

def import_rel(args):
    """Import flat CSV to parent and child models using grouping on first parent field."""
    models, db, uid, pwd = connect()
    # read CSV
    with open(args.input, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    # parse parent and child fields
    p_fields = [s.strip() for s in args.parent_fields.split(',')]
    c_fields = [s.strip() for s in args.child_fields.split(',')]
    parent_ids = {}
    counter = 1
    # create parent records
    for r in rows:
        key = r[p_fields[0]]
        if key in parent_ids:
            continue
        vals = {}
        for f in p_fields:
            raw = r.get(f)
            if raw:
                vals[f] = raw
        if args.name_prefix:
            vals[p_fields[0]] = f"{args.name_prefix}-{counter:03d}"
            counter += 1
        try:
            pid = models.execute_kw(db, uid, pwd, args.parent_model, 'create', [vals])
            parent_ids[key] = pid
            print(f"Created {args.parent_model} {pid}")
        except Exception as e:
            print(f"Error creating {args.parent_model}: {e}")
    # create child records
    for r in rows:
        parent_key = r[p_fields[0]]
        pid = parent_ids.get(parent_key)
        if not pid:
            continue
        vals = {args.relation_field: pid}
        for f in c_fields:
            raw = r.get(f)
            if raw:
                vals[f] = raw
        try:
            cid = models.execute_kw(db, uid, pwd, args.child_model, 'create', [vals])
            print(f"Created {args.child_model} {cid}")
        except Exception as e:
            print(f"Error creating {args.child_model}: {e}")
    return

def main():
    p = argparse.ArgumentParser(description='Dynamic export/import for Odoo models')
    sub = p.add_subparsers(dest='command')
    ex = sub.add_parser('export', help='Export model to CSV')
    ex.add_argument('--model', required=True)
    ex.add_argument('--output', default='/tmp/export.csv')
    ex.add_argument('--domain', help='Optional domain filter as Python list, e.g. "[(\'date_deadline\',\'!=\', False)]"')
    im = sub.add_parser('import', help='Import model from CSV')
    im.add_argument('--model', required=True)
    im.add_argument('--input', default='/tmp/export.csv')
    im.add_argument('--name-prefix', help='Prefix for name field during import')
    rel_ex = sub.add_parser('export-rel', help='Export parent and child model relation to a flat CSV')
    rel_ex.add_argument('--parent-model', required=True)
    rel_ex.add_argument('--child-model', required=True)
    rel_ex.add_argument('--relation-field', required=True)
    rel_ex.add_argument('--output', default='/tmp/export-rel.csv')
    rel_ex.add_argument('--domain', help='Optional parent domain filter as Python list, e.g. "[(\'move_type\',\'in\',[\'out_invoice\'])]"')
    rel_im = sub.add_parser('import-rel', help='Import flat CSV to parent and child models using grouping on first parent field')
    rel_im.add_argument('--parent-model', required=True)
    rel_im.add_argument('--child-model', required=True)
    rel_im.add_argument('--relation-field', required=True)
    rel_im.add_argument('--parent-fields', required=True)
    rel_im.add_argument('--child-fields', required=True)
    rel_im.add_argument('--input', default='/tmp/export-rel.csv')
    rel_im.add_argument('--name-prefix', help='Prefix for name field during import')
    args = p.parse_args()
    if args.command == 'export': export_model(args)
    elif args.command == 'import': import_model(args)
    elif args.command == 'export-rel': export_rel(args)
    elif args.command == 'import-rel': import_rel(args)
    else: p.print_help()

if __name__ == '__main__': main()
