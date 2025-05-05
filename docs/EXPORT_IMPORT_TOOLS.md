# Odoo 18 Export/Import Tools

This document provides comprehensive documentation for the enhanced export and import tools in the Odoo 18 MCP project.

## Overview

The export/import tools provide a flexible and powerful way to:

1. Export data from any Odoo model to CSV files
2. Import data from CSV files into any Odoo model
3. Export related models (parent-child relationships) to a single CSV file
4. Import related models from a single CSV file
5. Get information about models and their fields

## Command-Line Tool

The main command-line tool is `scripts/dynamic_data_tool.py`, which provides several commands:

- `export`: Export records from a single model to a CSV file
- `import`: Import records from a CSV file into a single model
- `export-rel`: Export records from related models (parent-child) to a CSV file
- `import-rel`: Import records from a CSV file into related models
- `info`: Get information about a model and its fields

## Export Command

Export records from a single model to a CSV file.

```bash
python3 scripts/dynamic_data_tool.py export \
  --model MODEL_NAME \
  --output OUTPUT_FILE \
  [--domain DOMAIN] \
  [--fields FIELDS]
```

### Parameters

- `--model`: The technical name of the Odoo model (e.g., `res.partner`, `account.move`)
- `--output`: The path to the output CSV file (default: `./tmp/export.csv`)
- `--domain`: Optional domain filter as a Python list of tuples (e.g., `"[('state', '=', 'posted')]"`)
- `--fields`: Optional comma-separated list of fields to export (default: all non-readonly fields)

### Examples

```bash
# Export all partners
python3 scripts/dynamic_data_tool.py export --model res.partner --output ./tmp/partners.csv

# Export only company partners
python3 scripts/dynamic_data_tool.py export --model res.partner --output ./tmp/companies.csv --domain "[('is_company', '=', True)]"

# Export specific fields
python3 scripts/dynamic_data_tool.py export --model res.partner --output ./tmp/partners_minimal.csv --fields "id,name,email,phone"

# Export paid customer invoices
python3 scripts/dynamic_data_tool.py export --model account.move --output ./tmp/paid_invoices.csv --domain "[('move_type', '=', 'out_invoice'), ('payment_state', '=', 'paid')]"
```

## Import Command

Import records from a CSV file into a single model.

```bash
python3 scripts/dynamic_data_tool.py import \
  --model MODEL_NAME \
  --input INPUT_FILE \
  [--defaults DEFAULTS] \
  [--force] \
  [--skip-invalid] \
  [--update] \
  [--match-field FIELD] \
  [--name-prefix PREFIX]
```

### Parameters

- `--model`: The technical name of the Odoo model (e.g., `res.partner`, `account.move`)
- `--input`: The path to the input CSV file (default: `./tmp/export.csv`)
- `--defaults`: Default values for fields as a Python dict (e.g., `"{'autopost_bills': 'never'}"`)
- `--force`: Force import even if required fields are missing
- `--skip-invalid`: Skip invalid values for selection fields
- `--update`: Update existing records instead of creating new ones
- `--match-field`: Field to match existing records (default: `id`)
- `--name-prefix`: Prefix for the name field during import

### Examples

```bash
# Import partners
python3 scripts/dynamic_data_tool.py import --model res.partner --input ./tmp/partners.csv

# Import partners with default values
python3 scripts/dynamic_data_tool.py import --model res.partner --input ./tmp/partners.csv --defaults "{'autopost_bills': 'never'}"

# Import partners and force even if required fields are missing
python3 scripts/dynamic_data_tool.py import --model res.partner --input ./tmp/partners.csv --force

# Import partners with a name prefix
python3 scripts/dynamic_data_tool.py import --model res.partner --input ./tmp/partners.csv --name-prefix "IMPORTED"
```

## Export Related Models Command

Export records from related models (parent-child) to a CSV file.

```bash
python3 scripts/dynamic_data_tool.py export-rel \
  --parent-model PARENT_MODEL \
  --child-model CHILD_MODEL \
  --relation-field RELATION_FIELD \
  --output OUTPUT_FILE \
  [--domain DOMAIN] \
  [--parent-fields PARENT_FIELDS] \
  [--child-fields CHILD_FIELDS]
```

### Parameters

- `--parent-model`: The technical name of the parent model (e.g., `account.move`)
- `--child-model`: The technical name of the child model (e.g., `account.move.line`)
- `--relation-field`: The field in the child model that relates to the parent (e.g., `move_id`)
- `--output`: The path to the output CSV file (default: `./tmp/export-rel.csv`)
- `--domain`: Optional domain filter for the parent model (e.g., `"[('move_type', '=', 'out_invoice')]"`)
- `--parent-fields`: Optional comma-separated list of parent fields to export
- `--child-fields`: Optional comma-separated list of child fields to export

### Examples

```bash
# Export invoices with their lines
python3 scripts/dynamic_data_tool.py export-rel \
  --parent-model account.move \
  --child-model account.move.line \
  --relation-field move_id \
  --output ./tmp/invoices_with_lines.csv

# Export only customer invoices with their lines
python3 scripts/dynamic_data_tool.py export-rel \
  --parent-model account.move \
  --child-model account.move.line \
  --relation-field move_id \
  --output ./tmp/customer_invoices_with_lines.csv \
  --domain "[('move_type', '=', 'out_invoice')]"

# Export specific fields
python3 scripts/dynamic_data_tool.py export-rel \
  --parent-model account.move \
  --child-model account.move.line \
  --relation-field move_id \
  --output ./tmp/invoices_minimal.csv \
  --parent-fields "id,name,partner_id,date,state,amount_total" \
  --child-fields "id,name,account_id,quantity,price_unit,price_subtotal"
```

## Import Related Models Command

Import records from a CSV file into related models.

```bash
python3 scripts/dynamic_data_tool.py import-rel \
  --parent-model PARENT_MODEL \
  --child-model CHILD_MODEL \
  --relation-field RELATION_FIELD \
  --parent-fields PARENT_FIELDS \
  --child-fields CHILD_FIELDS \
  --input INPUT_FILE \
  [--parent-defaults PARENT_DEFAULTS] \
  [--child-defaults CHILD_DEFAULTS] \
  [--force] \
  [--reset-to-draft] \
  [--skip-readonly-fields] \
  [--name-prefix PREFIX]
```

### Parameters

- `--parent-model`: The technical name of the parent model (e.g., `account.move`)
- `--child-model`: The technical name of the child model (e.g., `account.move.line`)
- `--relation-field`: The field in the child model that relates to the parent (e.g., `move_id`)
- `--parent-fields`: Comma-separated list of parent fields to import
- `--child-fields`: Comma-separated list of child fields to import
- `--input`: The path to the input CSV file (default: `./tmp/export-rel.csv`)
- `--parent-defaults`: Default values for parent fields as a Python dict
- `--child-defaults`: Default values for child fields as a Python dict
- `--force`: Force import even if required fields are missing
- `--reset-to-draft`: Reset records to draft before updating (for `account.move`)
- `--skip-readonly-fields`: Skip readonly fields for posted records
- `--name-prefix`: Prefix for the name field during import

### Examples

```bash
# Import invoices with their lines
python3 scripts/dynamic_data_tool.py import-rel \
  --parent-model account.move \
  --child-model account.move.line \
  --relation-field move_id \
  --parent-fields "name,partner_id,date,move_type" \
  --child-fields "name,account_id,quantity,price_unit" \
  --input ./tmp/invoices_with_lines.csv

# Import with default values
python3 scripts/dynamic_data_tool.py import-rel \
  --parent-model account.move \
  --child-model account.move.line \
  --relation-field move_id \
  --parent-fields "name,partner_id,date" \
  --child-fields "name,account_id,quantity,price_unit" \
  --input ./tmp/invoices_with_lines.csv \
  --parent-defaults "{'move_type': 'out_invoice'}" \
  --child-defaults "{'tax_ids': [(6, 0, [1])]}"

# Import and reset to draft
python3 scripts/dynamic_data_tool.py import-rel \
  --parent-model account.move \
  --child-model account.move.line \
  --relation-field move_id \
  --parent-fields "name,partner_id,date,move_type" \
  --child-fields "name,account_id,quantity,price_unit" \
  --input ./tmp/invoices_with_lines.csv \
  --reset-to-draft
```

## Info Command

Get information about a model and its fields.

```bash
python3 scripts/dynamic_data_tool.py info \
  --model MODEL_NAME \
  [--field FIELD_NAME] \
  [--required-only] \
  [--selection-only]
```

### Parameters

- `--model`: The technical name of the Odoo model (e.g., `res.partner`, `account.move`)
- `--field`: Get information about a specific field
- `--required-only`: Show only required fields
- `--selection-only`: Show only selection fields

### Examples

```bash
# Get information about a model
python3 scripts/dynamic_data_tool.py info --model res.partner

# Get information about a specific field
python3 scripts/dynamic_data_tool.py info --model res.partner --field autopost_bills

# Show only required fields
python3 scripts/dynamic_data_tool.py info --model res.partner --required-only

# Show only selection fields
python3 scripts/dynamic_data_tool.py info --model res.partner --selection-only
```

## MCP Tools Integration

The export/import tools are also integrated with the MCP server, providing the following tools:

- `export_records_to_csv`: Export records from a single model to a CSV file
- `import_records_from_csv`: Import records from a CSV file into a single model
- `export_related_records_to_csv`: Export records from related models to a CSV file
- `import_related_records_from_csv`: Import records from a CSV file into related models

### Example Usage in Claude Desktop

```
/tool export_records_to_csv model_name=res.partner export_path=./tmp/partners.csv

/tool import_records_from_csv model_name=res.partner input_path=./tmp/partners.csv

/tool export_related_records_to_csv parent_model=account.move child_model=account.move.line relation_field=move_id export_path=./tmp/invoices_with_lines.csv

/tool import_related_records_from_csv parent_model=account.move child_model=account.move.line relation_field=move_id input_path=./tmp/invoices_with_lines.csv
```

## Common Use Cases

### Exporting and Importing Partners

```bash
# Export all partners
python3 scripts/dynamic_data_tool.py export --model res.partner --output ./tmp/partners.csv

# Import partners
python3 scripts/dynamic_data_tool.py import --model res.partner --input ./tmp/partners.csv --defaults "{'autopost_bills': 'never'}"
```

### Exporting and Importing Invoices with Lines

```bash
# Export customer invoices with their lines
python3 scripts/dynamic_data_tool.py export-rel \
  --parent-model account.move \
  --child-model account.move.line \
  --relation-field move_id \
  --output ./tmp/customer_invoices_with_lines.csv \
  --domain "[('move_type', '=', 'out_invoice')]"

# Import invoices with their lines
python3 scripts/dynamic_data_tool.py import-rel \
  --parent-model account.move \
  --child-model account.move.line \
  --relation-field move_id \
  --parent-fields "name,partner_id,date,move_type" \
  --child-fields "name,account_id,quantity,price_unit" \
  --input ./tmp/customer_invoices_with_lines.csv
```

### Exporting Paid Invoices

```bash
# Export paid customer invoices
python3 scripts/dynamic_data_tool.py export \
  --model account.move \
  --output ./tmp/paid_invoices.csv \
  --domain "[('move_type', '=', 'out_invoice'), ('payment_state', '=', 'paid')]"
```

### Getting Field Information

```bash
# Get information about required fields in account.move
python3 scripts/dynamic_data_tool.py info --model account.move --required-only

# Get information about selection fields in res.partner
python3 scripts/dynamic_data_tool.py info --model res.partner --selection-only
```

## Troubleshooting

### Missing Required Fields

If you encounter errors about missing required fields during import:

1. Use the `info` command to identify required fields:
   ```bash
   python3 scripts/dynamic_data_tool.py info --model res.partner --required-only
   ```

2. Add the required fields to your CSV file or provide default values:
   ```bash
   python3 scripts/dynamic_data_tool.py import --model res.partner --input ./tmp/partners.csv --defaults "{'autopost_bills': 'never'}"
   ```

### Invalid Selection Values

If you encounter errors about invalid selection values:

1. Use the `info` command to identify valid values for selection fields:
   ```bash
   python3 scripts/dynamic_data_tool.py info --model res.partner --field autopost_bills
   ```

2. Update your CSV file with valid values or use the `--skip-invalid` option:
   ```bash
   python3 scripts/dynamic_data_tool.py import --model res.partner --input ./tmp/partners.csv --skip-invalid
   ```

### Readonly Fields

If you encounter errors about readonly fields:

1. For `account.move` records, use the `--reset-to-draft` option:
   ```bash
   python3 scripts/dynamic_data_tool.py import-rel \
     --parent-model account.move \
     --child-model account.move.line \
     --relation-field move_id \
     --parent-fields "name,partner_id,date,move_type" \
     --child-fields "name,account_id,quantity,price_unit" \
     --input ./tmp/invoices_with_lines.csv \
     --reset-to-draft
   ```

2. Use the `--skip-readonly-fields` option:
   ```bash
   python3 scripts/dynamic_data_tool.py import-rel \
     --parent-model account.move \
     --child-model account.move.line \
     --relation-field move_id \
     --parent-fields "name,partner_id,date,move_type" \
     --child-fields "name,account_id,quantity,price_unit" \
     --input ./tmp/invoices_with_lines.csv \
     --skip-readonly-fields
   ```