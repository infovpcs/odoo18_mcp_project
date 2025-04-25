# Vendor Bill Analytic Line Generator

This tool automatically generates analytic lines for vendor bills and bill refunds in Odoo 18. It processes invoice lines with subtotals and creates corresponding analytic lines with the appropriate sign convention.

## Sign Convention

- **Vendor Bills (in_invoice)**: Analytic lines are created with **negative** amounts
- **Bill Refunds (in_refund)**: Analytic lines are created with **positive** amounts

This sign convention ensures that vendor bills (which represent expenses) decrease the analytic account balance, while bill refunds (which represent expense reversals) increase the analytic account balance.

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