# Odoo 18 MCP Integration (18.0 Branch)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Odoo 18.0](https://img.shields.io/badge/odoo-18.0-green.svg)](https://www.odoo.com/)
[![MCP SDK](https://img.shields.io/badge/mcp-sdk-purple.svg)](https://github.com/modelcontextprotocol/python-sdk)
[![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A robust integration server that connects MCP (Master Control Program) with Odoo 18.0 ERP system, focusing on efficient data synchronization, API management, and secure communications. This implementation provides a standardized interface for performing CRUD operations on Odoo 18 models through a simple API, with dynamic model discovery and field analysis capabilities.

## Features

- **Odoo 18 Connectivity**: Connect to Odoo 18 using XML-RPC with proper authentication
- **CRUD Operations**: Create, Read, Update, and Delete operations for any Odoo model
- **Dynamic Model Support**: Work with any Odoo model including res.partner and product.product
- **Model Discovery**: Explore model fields and relationships using ir.model and ir.model.fields
- **Dynamic Field Analysis**: Automatically analyze field importance, requirements, and relationships
- **NLP-Based Field Importance**: Use NLP techniques to determine field importance based on names and descriptions
- **Intelligent CRUD Generation**: Generate appropriate CRUD operations based on model metadata
- **Field Grouping**: Automatically group fields by purpose (basic info, contact info, etc.)
- **Smart Search Fields**: Identify fields that are good candidates for search operations
- **MCP Integration**: API endpoints for MCP integration with standardized request/response format
- **Claude Desktop Integration**: Seamless integration with Claude Desktop using the MCP SDK
- **Environment Configuration**: Easy configuration using environment variables
- **Type Safety**: Pydantic models for data validation and type checking
- **Logging**: Comprehensive logging system with detailed error information
- **Error Handling**: Robust error handling and reporting with proper exception hierarchy
- **Record Templates**: Generate templates for creating new records based on field analysis
- **Batch Operations**: Support for batch CRUD operations
- **Custom Method Execution**: Execute custom Odoo methods directly
- **Schema Versioning**: Support for schema versioning and migration
- **Security Features**: API key validation, rate limiting, and access control
- **Performance Optimization**: Caching and resource usage optimization
- **Monitoring**: Built-in monitoring capabilities for tracking performance
- **Comprehensive Documentation**: API docs, setup guides, and troubleshooting information

## Installation

### Prerequisites

- Python 3.8 or higher
- Odoo 18.0 instance
- Access to Odoo database
- Claude Desktop (optional, for AI integration)

### Setup

1. Clone the repository:

```bash
git clone https://github.com/infovpcs/odoo18_mcp_project.git
cd odoo18_mcp_project
```

2. Create a virtual environment using uv (recommended) or venv:

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or using standard venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
# Using uv (recommended)
uv pip install -e .

# Or using standard pip
pip install -e .
```

4. Create a `.env` file:

```bash
cp .env.example .env
```

5. Edit the `.env` file with your Odoo connection details:

```
ODOO_URL=http://localhost:8069
ODOO_DB=llmdb18
ODOO_USERNAME=admin
ODOO_PASSWORD=admin
```

### Claude Desktop Integration

1. Install the MCP SDK:

```bash
pip install "mcp[cli]"
```

2. Install the MCP server in Claude Desktop:

```bash
mcp install mcp_server.py --name "Odoo 18 Integration" -v ODOO_URL=http://localhost:8069 -v ODOO_DB=llmdb18 -v ODOO_USERNAME=admin -v ODOO_PASSWORD=admin
```

3. Alternatively, manually update the Claude Desktop configuration file:

- **macOS**: `~/Library/Application Support/Claude/config.json`
- **Windows**: `%APPDATA%\Claude\config.json`
- **Linux**: `~/.config/Claude/config.json`

Add the following to the `servers` section:

```json
{
  "id": "odoo18-mcp",
  "name": "Odoo 18 Integration",
  "description": "Dynamic Odoo 18 integration with MCP",
  "command": "python",
  "args": ["/full/path/to/your/workspace/odoo18_mcp_project/mcp_server.py"],
  "env": {
    "ODOO_URL": "http://localhost:8069",
    "ODOO_DB": "llmdb18",
    "ODOO_USERNAME": "admin",
    "ODOO_PASSWORD": "admin"
  },
  "enabled": true
}
```

4. Restart Claude Desktop to apply the changes.

5. Verify the installation by checking the Claude Desktop logs for successful connection to Odoo.

### Building from Source

If you want to build the package for distribution:

```bash
python -m pip install build
python -m build
```

This will create distribution packages in the `dist/` directory.

### Docker Support

The project includes Docker support for easy deployment and testing:

#### Building the Docker Image

```bash
docker build -t odoo18-mcp-integration .
```

#### Running with Docker

Run the MCP server:
```bash
docker run -p 8000:8000 --name mcp-server odoo18-mcp-integration
```

Run the standalone MCP server for testing:
```bash
docker run -p 8000:8000 --name standalone-server odoo18-mcp-integration standalone
```

Run tests:
```bash
docker run --name test-runner odoo18-mcp-integration test all
```

#### Using Docker Compose

The project includes a `docker-compose.yml` file for easy orchestration:

```bash
# Start the MCP server
docker-compose up mcp-server

# Start the standalone server
docker-compose up standalone-server

# Run tests
docker-compose run test-runner
```

You can customize the Odoo connection details by setting environment variables:

```bash
ODOO_URL=http://your-odoo-server:8069 ODOO_DB=your_db docker-compose up mcp-server
```

### Using with Claude Desktop

Once you've configured Claude Desktop, you can use the Odoo 18 MCP integration:

1. Open Claude Desktop
2. Click on the server selection dropdown (top-right corner)
3. Select "Odoo 18 Integration"

#### Available Resources

| Resource | Description | Example |
|----------|-------------|---------|
| **Models List** | Get a list of all available models | `/resource odoo://models/all` |
| **Model Metadata** | Get metadata for a specific model | `/resource odoo://model/res.partner/metadata` |
| **Model Records** | Get records for a specific model | `/resource odoo://model/product.product/records` |

#### Available Tools

| Tool | Description | Example Usage | Status |
|------|-------------|--------------|--------|
| **search_records** | Search for records in a model based on a query | `/tool search_records model_name=res.partner query=company` | ✅ Working |
| **get_record_template** | Get a template for creating a new record | `/tool get_record_template model_name=product.product` | ✅ Working |
| **create_record** | Create a new record in a model | `/tool create_record model_name=res.partner values={"name":"Test Partner","email":"test@example.com"}` | ✅ Working |
| **update_record** | Update an existing record in a model | `/tool update_record model_name=res.partner record_id=42 values={"name":"Updated Partner"}` | ✅ Working |
| **delete_record** | Delete a record from a model | `/tool delete_record model_name=res.partner record_id=42` | ✅ Working |
| **execute_method** | Execute a custom method on a model | `/tool execute_method model_name=res.partner method=name_search args=["Test"]` | ✅ Working |
| **analyze_field_importance** | Analyze the importance of fields in a model | `/tool analyze_field_importance model_name=res.partner use_nlp=true` | ✅ Working |
| **get_field_groups** | Group fields by purpose for a model | `/tool get_field_groups model_name=product.product` | ✅ Working |

#### Available Prompts

| Prompt | Description | Example Usage |
|--------|-------------|--------------|
| **create_record_prompt** | Get guidance for creating a new record | `/prompt create_record_prompt model_name=res.partner` |
| **search_records_prompt** | Get guidance for searching records | `/prompt search_records_prompt model_name=product.product` |

## Usage

### Testing Odoo Connection

```bash
python main.py --test-connection
```

### Running the MCP Server

```bash
python main.py
```

You can specify host and port:

```bash
python main.py --host 127.0.0.1 --port 8080
```

### Standalone MCP Server for Testing

We've created a standalone MCP server that can be used for testing the MCP tools without Claude Desktop. This server exposes the MCP tools as HTTP endpoints:

```bash
python standalone_mcp_server.py
```

This will start a FastAPI server on port 8000 that you can use to test the MCP tools. You can then use the `test_mcp_tools.py` script to test all the tools:

```bash
python test_mcp_tools.py
```

The standalone server provides the same functionality as the MCP server used by Claude Desktop, but with a simple HTTP interface for testing purposes.

### API Endpoints

- `POST /api/v1/odoo`: Main endpoint for Odoo operations
- `GET /health`: Health check endpoint

### Example Requests

#### Reading Partners

```python
import requests
import json

url = "http://localhost:8000/api/v1/odoo"
headers = {
    "Content-Type": "application/json"
}
data = {
    "operation": "read",
    "model": "res.partner",
    "params": {
        "domain": [["is_company", "=", True]],
        "limit": 10
    }
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.json())
```

#### Creating a Product

```python
import requests
import json

url = "http://localhost:8000/api/v1/odoo"
headers = {
    "Content-Type": "application/json"
}
data = {
    "operation": "create",
    "model": "product.product",
    "params": {
        "values": {
            "name": "Test Product API",
            "default_code": "TEST-API-001",
            "list_price": 99.99,
            "type": "consu",  # Valid values: 'consu', 'service', 'combo'
            "description": "Created via External API"
        }
    }
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.json())
```

#### Executing Custom Methods

```python
import requests
import json

url = "http://localhost:8000/api/v1/odoo"
headers = {
    "Content-Type": "application/json"
}
data = {
    "operation": "execute",
    "model": "res.partner",
    "params": {
        "method": "fields_get",
        "args": [],
        "kwargs": {"attributes": ["string", "help", "type"]}
    }
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.json())
```

### Dynamic Model Operations

#### Discovering Available Models

```python
import requests
import json

url = "http://localhost:8000/api/v1/odoo"
headers = {
    "Content-Type": "application/json"
}
data = {
    "operation": "discover_models",
    "params": {
        "filter": "partner"  # Optional filter
    }
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.json())
```

#### Getting Model Metadata

```python
import requests
import json

url = "http://localhost:8000/api/v1/odoo"
headers = {
    "Content-Type": "application/json"
}
data = {
    "operation": "model_metadata",
    "model": "res.partner"
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.json())
```

#### Analyzing Field Importance

```python
import requests
import json

url = "http://localhost:8000/api/v1/odoo"
headers = {
    "Content-Type": "application/json"
}
data = {
    "operation": "field_importance",
    "model": "res.partner",
    "params": {
        "use_nlp": True  # Use NLP for more sophisticated analysis
    }
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.json())
```

#### Getting Field Groups

```python
import requests
import json

url = "http://localhost:8000/api/v1/odoo"
headers = {
    "Content-Type": "application/json"
}
data = {
    "operation": "field_groups",
    "model": "res.partner"
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.json())
```

#### Getting Record Template

```python
import requests
import json

url = "http://localhost:8000/api/v1/odoo"
headers = {
    "Content-Type": "application/json"
}
data = {
    "operation": "record_template",
    "model": "res.partner"
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.json())
```

## Development

### Project Structure

```
odoo18_mcp_project/
├── src/                    # Source code
│   ├── core/               # Core functionality
│   │   ├── config.py       # Configuration management
│   │   └── logger.py       # Logging system
│   ├── mcp/                # MCP integration
│   │   ├── client.py       # MCP client
│   │   ├── handlers.py     # Request handlers
│   │   └── dynamic_handlers.py # Dynamic model handlers
│   └── odoo/               # Odoo integration
│       ├── client.py       # Odoo client
│       ├── schemas.py      # Data schemas
│       └── dynamic/        # Dynamic model handling
│           ├── model_discovery.py    # Model discovery
│           ├── field_analyzer.py     # Field analysis
│           ├── crud_generator.py     # CRUD operations
│           └── nlp_analyzer.py       # NLP-based analysis
├── tests/                  # Test suite
├── main.py                 # Main entry point
├── mcp_server.py           # MCP server implementation
├── client_test.py          # Client test script
├── advanced_client_test.py # Advanced client test
├── dynamic_model_test.py   # Dynamic model test
├── test_mcp_client.py      # MCP client test
├── test_odoo_connection.py # Odoo connection test
├── sql_schema_generator.py # SQL schema generator
├── .env.example            # Environment variables example
├── pyproject.toml          # Project configuration
├── setup.py                # Setup script
├── README.md               # Main documentation
├── PLANNING.md             # Project planning
└── TASK.md                 # Task tracking
```

### Running Tests

```bash
python client_test.py             # Basic client test
python advanced_client_test.py    # Advanced client test
python dynamic_model_test.py      # Dynamic model test
python test_mcp_functions.py      # Test MCP server functions directly
python test_mcp_tools.py          # Test MCP server tools via HTTP
```

### Test Results

We've thoroughly tested all MCP server functionality to ensure it works correctly with Odoo 18. Here are the test results:

#### MCP Functions Test Results

| Function | Description | Status | Notes |
|----------|-------------|--------|-------|
| `get_all_models` | Get all available models in Odoo | ✅ Passed | Returns a list of all models |
| `get_model_fields` | Get all fields for a specific model | ✅ Passed | Returns field details including type, required, etc. |
| `get_model_records` | Get records for a specific model | ✅ Passed | Supports filtering, pagination |
| `get_model_schema` | Get schema information for a model | ✅ Passed | Fixed issue with 'description' field |
| `create_record` | Create a new record | ✅ Passed | Returns the ID of the created record |
| `update_record` | Update an existing record | ✅ Passed | Returns True on success |
| `delete_record` | Delete a record | ✅ Passed | Returns True on success |
| `execute_method` | Execute a custom method | ✅ Passed | Can execute any method on a model |

#### MCP Tools Test Results

| Tool | Test Case | Expected Result | Actual Result | Status |
|------|-----------|-----------------|--------------|--------|
| `search_records` | Search for companies | List of companies | List of companies | ✅ Passed |
| `get_record_template` | Get product template | JSON template | JSON template with fields | ✅ Passed |
| `create_record` | Create a partner | Record created | Record created with ID | ✅ Passed |
| `update_record` | Update partner name | Record updated | Record updated successfully | ✅ Passed |
| `delete_record` | Delete test partner | Record deleted | Record deleted successfully | ✅ Passed |
| `execute_method` | Execute name_search | List of matching records | List of matching records | ✅ Passed |
| `analyze_field_importance` | Analyze partner fields | Field importance table | Field importance table | ✅ Passed |
| `get_field_groups` | Group product fields | Grouped fields | Grouped fields by purpose | ✅ Passed |

#### Test Output Example

```
2025-04-24 14:47:43,287 - mcp_tools_test - INFO - Starting MCP tools tests
2025-04-24 14:47:43,287 - mcp_tools_test - INFO - === Test 1: search_records ===
2025-04-24 14:47:43,425 - mcp_tools_test - INFO - Success! Response: {
  "success": true,
  "result": "# Search Results for 'company' in res.partner\n\n| ID | Name | Email | Phone |\n|----| ---- | ---- | ---- |\n| 44 | IN Company | info@company.inexample.com | +91 81234 56789 |\n| 42 | My Company (Chicago) | chicago@yourcompany.com | +1 312 349 3030 |\n| 1 | My Company (San Francisco) | info@yourcompany.com | +1 555-555-5556 |\n"
}
2025-04-24 14:47:43,425 - mcp_tools_test - INFO - === Test 2: get_record_template ===
2025-04-24 14:47:43,563 - mcp_tools_test - INFO - Success! Response: {
  "success": true,
  "result": "{\n  \"product_tmpl_id\": false,\n  \"name\": \"\",\n  \"type\": \"consu\",\n  \"service_tracking\": \"no\",\n  \"categ_id\": false,\n  \"uom_id\": false,\n  \"uom_po_id\": false,\n  \"product_variant_ids\": false,\n  \"tracking\": \"serial\",\n  \"default_code\": \"\",\n  \"code\": \"\",\n  \"list_price\": 0.0\n}"
}
```

### Code Formatting

```bash
pip install black isort
black src tests
isort src tests
```

### Type Checking

```bash
pip install mypy
mypy src
```

### IDE Integration

#### VS Code

Create a `.vscode/settings.json` file:

```json
{
    "python.linting.enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "python.envFile": "${workspaceFolder}/.env",
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "python.testing.nosetestsEnabled": false,
    "python.testing.pytestArgs": [
        "tests"
    ]
}
```

#### PyCharm

1. Install the Black and Mypy plugins
2. Configure the Python interpreter to use your virtual environment
3. Set up the environment variables from your `.env` file
4. Configure code formatting to use Black

## Recent Improvements and Fixes

### MCP Server Fixes

We've made several improvements to the MCP server to ensure all tools work correctly with Odoo 18:

1. **Fixed `get_model_schema` function**: The function was trying to access the 'description' field in the 'ir.model' model, which doesn't exist in Odoo 18. We fixed this by using a different approach to get model information.

2. **Improved `analyze_field_importance` and `get_field_groups` tools**: These tools were relying on the `get_model_schema` function, which was failing. We updated them to use the `get_model_fields` function directly, which is more reliable.

3. **Enhanced `get_record_template` tool**: The tool was returning a minimal template with just the 'name' field. We improved it to provide more comprehensive templates for common models like 'res.partner' and 'product.product'.

4. **Added standalone MCP server for testing**: We created a standalone FastAPI server that exposes the MCP tools as HTTP endpoints for easier testing without Claude Desktop.

5. **Added comprehensive test suite**: We created test scripts to verify all MCP functions and tools work correctly with Odoo 18.

### Performance Improvements

1. **Optimized model discovery**: Improved the performance of model discovery by caching model information.

2. **Reduced XML-RPC calls**: Minimized the number of XML-RPC calls to Odoo for better performance.

3. **Improved error handling**: Added better error handling and reporting for more reliable operation.

## Troubleshooting

### Common Issues

#### Connection Problems

- **Issue**: Cannot connect to Odoo server
- **Solution**: Verify that your Odoo server is running and accessible at the URL specified in your `.env` file. Check that the database name, username, and password are correct.

#### Authentication Failures

- **Issue**: Authentication failed with Odoo
- **Solution**: Double-check your Odoo credentials in the `.env` file. Make sure the user has sufficient permissions to access the models you're trying to work with.

#### MCP Server Not Showing in Claude Desktop

- **Issue**: The Odoo 18 Integration server doesn't appear in Claude Desktop
- **Solution**: Verify that the MCP server is properly installed and enabled in the Claude Desktop configuration. Restart Claude Desktop after making changes to the configuration.

#### Model Not Found

- **Issue**: Error when trying to access a specific model
- **Solution**: Verify that the model exists in your Odoo installation and that you're using the correct technical name (e.g., `res.partner` instead of `Partner`).

#### Field Not Found

- **Issue**: Error when trying to access or update a specific field
- **Solution**: Check that the field exists in the model and that you're using the correct field name. Use the model metadata resource to see available fields.

### Getting Help

If you encounter issues not covered in this troubleshooting guide, please:

1. Check the logs for detailed error messages
2. Review the Odoo documentation for the specific model or operation
3. Open an issue on the GitHub repository with detailed information about the problem

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Odoo Community
- Python Community
- MCP SDK Team