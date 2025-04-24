# Odoo 18 MCP Client Test Scripts

This directory contains scripts to test the Odoo 18 MCP integration with CRUD operations for various models.

## Prerequisites

- Python 3.12+
- Odoo 18 server running
- MCP server running
- `.env` file with proper configuration

## Basic Client Test

The `client_test.py` script demonstrates basic CRUD operations on `res.partner` and `product.product` models.

### Usage

```bash
python client_test.py
```

This script will:
1. Test the connection to the MCP server
2. Get model information for `res.partner` and `product.product`
3. Perform CRUD operations on `res.partner`:
   - Create a new partner
   - Read the partner
   - Update the partner
   - Delete the partner
4. Perform CRUD operations on `product.product`:
   - Create a new product
   - Read the product
   - Update the product
   - Delete the product

## Advanced Client Test

The `advanced_client_test.py` script demonstrates more advanced operations, including dynamic model discovery, complex searches, and relational operations.

### Usage

```bash
# Show help
python advanced_client_test.py

# List all models
python advanced_client_test.py --list-models

# Get fields for a specific model
python advanced_client_test.py --model-fields res.partner
python advanced_client_test.py --model-fields product.product

# Create a partner with address
python advanced_client_test.py --create-partner

# Create a product with attributes
python advanced_client_test.py --create-product

# Search partners by criteria
python advanced_client_test.py --search-partners "Test"

# Search products by criteria
python advanced_client_test.py --search-products "Test"

# Link a partner to a product as a supplier
python advanced_client_test.py --link
```

## Environment Variables

The scripts use the following environment variables from the `.env` file:

- `MCP_HOST`: MCP server host (default: "0.0.0.0")
- `MCP_PORT`: MCP server port (default: "8000")

## API Endpoints

The scripts use the following API endpoint:

- `http://{MCP_HOST}:{MCP_PORT}/api/v1/odoo`: Main endpoint for Odoo operations

## Request Format

The scripts send POST requests with the following JSON format:

```json
{
  "operation": "create|read|update|delete|execute",
  "model": "model.name",
  "params": {
    // Operation-specific parameters
  },
  "context": {
    // Optional context
  }
}
```

## Response Format

The API returns responses in the following format:

```json
{
  "success": true|false,
  "data": {
    // Operation-specific data
  },
  "error": "Error message if any",
  "timestamp": "Response timestamp"
}
```

## Examples

### Creating a Partner

```python
create_params = {
    "values": {
        "name": "Test Partner MCP",
        "email": "test.partner@example.com",
        "phone": "+1234567890",
        "is_company": True
    }
}
response = make_request("create", "res.partner", create_params)
```

### Reading Partners

```python
read_params = {
    "domain": [["name", "ilike", "Test"]],
    "limit": 10,
    "order": "name"
}
response = make_request("read", "res.partner", read_params)
```

### Updating a Partner

```python
update_params = {
    "id": partner_id,
    "values": {
        "name": "Updated Test Partner MCP",
        "comment": "This partner was updated via MCP"
    }
}
response = make_request("update", "res.partner", update_params)
```

### Deleting a Partner

```python
delete_params = {
    "ids": [partner_id]
}
response = make_request("delete", "res.partner", delete_params)
```

### Executing a Method

```python
execute_params = {
    "method": "fields_get",
    "args": [],
    "kwargs": {"attributes": ["string", "help", "type", "required", "relation"]}
}
response = make_request("execute", "res.partner", execute_params)
```