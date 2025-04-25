# Vendor Bill Analytic Line Generator

This tool automatically generates analytic lines for vendor bills and bill refunds in Odoo 18. It processes invoice lines with subtotals and creates corresponding analytic lines with the appropriate sign convention.

## Sign Convention

- **Vendor Bills (in_invoice)**: Analytic lines are created with **negative** amounts
- **Bill Refunds (in_refund)**: Analytic lines are created with **positive** amounts

This sign convention ensures that vendor bills (which represent expenses) decrease the analytic account balance, while bill refunds (which represent expense reversals) increase the analytic account balance.

## Project Analytics Setup

Before processing bills, the script will:

1. Check all projects in the system and ensure they have analytic accounts
2. If a project has a blank analytic account, create a new one or assign an existing one with the same name

This ensures that all projects have proper analytic accounts before processing bills.

## Odoo 18 Project-Analytic Integration

In Odoo 18, the `project.project` model has a many2one field named `account_id` that links to `account.analytic.account`. The script is specifically designed to work with this field structure.

The script will:
1. Check for the `account_id` field in projects
2. Use this field to link projects with analytic accounts
3. When creating new analytic accounts for projects, update the project's `account_id` field

## Analytic Account Selection

For invoice lines that already have analytic distributions set, the script will use those distributions to create analytic lines.

For invoice lines without analytic distributions, the script will:

1. First check if there's a project linked to the partner with an analytic account
2. If not, check for any existing analytic account for this partner
3. If still not found, create a new analytic account with the project name (or partner name if no project exists)

## Company Compatibility

The script includes special handling for company compatibility issues:

1. When creating analytic accounts, it uses the current user's company ID
2. If a partner belongs to a different company, the script will create the analytic account without linking to the partner
3. This prevents "Incompatible companies" errors when working with partners from different companies

## Purpose

This script is designed for generating historic data costing entries. For new bills, analytic entries will be automatically generated from the purchase order cycle with linked bills.

## Prerequisites

- Python 3.8 or higher
- Access to an Odoo 18 instance
- Proper permissions to read vendor bills and create analytic lines

## Installation

1. Ensure you have the required Python packages:

```bash
pip install python-dotenv
```

2. Configure your Odoo connection by creating a `.env` file with the following content:

```
ODOO_URL=http://localhost:8069
ODOO_DB=llmdb18
ODOO_USERNAME=admin
ODOO_PASSWORD=admin
```

## Usage

### Basic Usage

Run the script to process all posted vendor bills and bill refunds:

```bash
python vendor_bill_analytic_generator.py
```

### Limiting the Number of Bills

Process only a specific number of bills:

```bash
python vendor_bill_analytic_generator.py --limit=10
```

### Filtering Bills

Filter bills using a domain expression:

```bash
python vendor_bill_analytic_generator.py --filter="[('invoice_date', '>=', '2025-01-01')]"
```

### Combined Options

Combine limit and filter options:

```bash
python vendor_bill_analytic_generator.py --limit=5 --filter="[('invoice_date', '>=', '2025-01-01'), ('partner_id', '=', 42)]"
```

## Testing

Run the test script to verify functionality:

```bash
python test_vendor_bill_analytic.py
```

The test script performs the following checks:

1. Tests connection to Odoo
2. Tests retrieving vendor bills
3. Tests retrieving invoice lines
4. Tests creating analytic lines
5. Tests the sign convention for bill refunds
6. Tests the complete bill processing workflow

## How It Works

1. The script connects to the Odoo server using XML-RPC
2. It retrieves posted vendor bills and bill refunds
3. For each bill, it retrieves the invoice lines
4. For each invoice line with an analytic distribution, it creates analytic lines:
   - For vendor bills: with negative amounts
   - For bill refunds: with positive amounts
5. The analytic distribution percentage is respected when creating the analytic lines

## Troubleshooting

### No Analytic Lines Created

If no analytic lines are created, check the following:

1. Ensure the vendor bills have invoice lines with analytic distributions
2. Verify that the invoice lines have non-zero subtotals
3. Check that the bills are in the "posted" state

### Connection Issues

If you encounter connection issues:

1. Verify your Odoo server is running
2. Check your `.env` file for correct credentials
3. Ensure your user has proper permissions

## Notes

- The script only processes posted bills to ensure that the amounts are final
- Only invoice lines with analytic distributions will generate analytic lines
- The script respects the percentage distribution in the analytic_distribution field
- Existing analytic lines are not checked or deleted; running the script multiple times may create duplicate entries