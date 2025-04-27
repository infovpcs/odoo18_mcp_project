# Odoo 18 MCP Integration (18.0 Branch)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
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
- **Advanced Natural Language Search**: Parse natural language queries to search across multiple models
- **Multi-Model Query Support**: Handle complex queries that span multiple related models
- **Relationship-Aware Search**: Automatically identify and traverse relationships between models
- **Related Records Export/Import**: Export and import parent-child related records in a single operation
- **Relationship Maintenance**: Automatically maintain relationships between models during import/export
- **Direct Implementation Approach**: Efficient and reliable direct implementation for export/import operations
- **Streamlined Export/Import**: Simplified approach for handling complex export/import operations
- **Dynamic Query Parsing**: Natural language query parsing with dynamic model and field discovery using ir.model and ir.model.fields
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
- **Odoo Documentation Retrieval**: RAG-based retrieval of information from the official Odoo 18 documentation

## Installation

### Prerequisites

- Python 3.10 or higher
- Odoo 18.0 instance
- Access to Odoo database
- Claude Desktop (optional, for AI integration)
- Compatible PyTorch version (2.2.x recommended for macOS)
- NumPy <2.0.0 (for compatibility with other packages)

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
    "odoo18-mcp":{
        "name": "Odoo 18 Integration",
        "description": "Dynamic Odoo 18 integration with MCP",
        "command": "/full/path/to/your/python",
        "args": ["/Users/vinusoft85/workspace/odoo18_mcp_project/mcp_server.py"],
        "env": {
                "ODOO_URL": "http://localhost:8069",
                "ODOO_DB": "llmdb18",
                "ODOO_USERNAME": "admin",
                "ODOO_PASSWORD": "admin"
            }
    }
}
```

**Important**: Replace `/full/path/to/your/python` with the actual full path to your Python executable. You can find this by running `which python3` in your terminal. For example, if you're using a virtual environment, it might be something like `/Users/username/workspace/odoo18_mcp_project/.venv/bin/python3`.

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

The project includes comprehensive Docker support for development, testing, and production deployment.

#### Quick Start with Make

We provide a Makefile for common Docker operations:

```bash
# Set up required directories
make setup

# Build Docker images
make build

# Start development environment
make dev

# Run tests
make test

# Start production environment
make prod

# View logs
make logs

# Stop all services
make down

# Clean up everything
make clean
```

#### Docker Compose Configuration

The project includes multiple Docker Compose files for different environments:

- `docker-compose.yml`: Base configuration for all environments
- `docker-compose.override.yml`: Development-specific overrides (automatically used with `docker-compose up`)
- `docker-compose.prod.yml`: Production-specific configuration

#### Development Environment

For local development:

```bash
# Start all services in development mode
docker-compose up -d

# Or using the Makefile
make dev
```

This will:
- Mount your local code into the container for live development
- Enable debug mode and detailed logging
- Create required directories for logs, exports, and temporary files
- Set up appropriate environment variables

#### Production Deployment

For production deployment:

```bash
# Start production environment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or using the Makefile
make prod
```

Production mode includes:
- Multi-stage build for smaller image size
- Non-root user for better security
- Resource limits to prevent container resource exhaustion
- Health checks for better reliability
- Restart policies for automatic recovery
- Log rotation to prevent disk space issues
- Network isolation for better security

#### Container Architecture

The Docker setup includes three main services:

1. **mcp-server**: The main MCP server for integration with Claude Desktop
   - Exposes port 8000 for API access
   - Connects to Odoo via XML-RPC
   - Provides MCP tools for Claude Desktop

2. **standalone-server**: A standalone server for testing MCP tools
   - Exposes port 8001 for API access
   - Provides HTTP endpoints for testing MCP tools
   - Useful for development and testing without Claude Desktop

3. **test-runner**: A service for running automated tests
   - Runs function tests and tool tests
   - Validates the MCP server functionality
   - Useful for CI/CD pipelines

#### Environment Variables

You can customize the Docker environment by setting environment variables:

```bash
# In .env file or command line
ODOO_URL=http://your-odoo-server:8069
ODOO_DB=your_database
ODOO_USERNAME=your_username
ODOO_PASSWORD=your_password
MCP_DEBUG=true
MCP_LOG_LEVEL=DEBUG
```

#### Volume Management

The Docker setup includes several volumes for persistent data:

- `mcp_data`: Persistent data storage
- `mcp_logs`: Persistent logs storage
- `./exports`: Directory for exported files
- `./tmp`: Directory for temporary files

#### Health Checks

All services include health checks to ensure they're running properly:

```bash
# Check the health of the MCP server
docker inspect --format='{{json .State.Health}}' odoo18-mcp-server | jq
```

#### Custom Docker Builds

You can customize the Docker build process:

```bash
# Build with specific build arguments
docker build --build-arg BUILD_TARGET=production -t odoo18-mcp-integration:prod .

# Run with specific environment variables
docker run -p 8000:8000 -e ODOO_URL=http://your-odoo-server:8069 -e ODOO_DB=your_db odoo18-mcp-integration:prod
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
| **export_records_to_csv** | Export records from a model to CSV | `/tool export_records_to_csv model_name=res.partner fields=["id","name","email"]` | ✅ Working |
| **import_records_from_csv** | Import records from CSV to a model | `/tool import_records_from_csv model_name=res.partner import_path="exports/partners.csv"` | ✅ Working |
| **export_related_records_to_csv** | Export parent-child records to CSV | `/tool export_related_records_to_csv parent_model=account.move child_model=account.move.line relation_field=move_id move_type=out_invoice export_path="./tmp/customer_invoices.csv"` | ✅ Working |
| **import_related_records_from_csv** | Import parent-child records from CSV | `/tool import_related_records_from_csv parent_model=account.move child_model=account.move.line relation_field=move_id import_path="./tmp/customer_invoices.csv" reset_to_draft=true skip_readonly_fields=true` | ✅ Working |
| **advanced_search** | Perform advanced natural language search | `/tool advanced_search query="List all unpaid bills with respect of vendor details" limit=10` | ✅ Working |
| **retrieve_odoo_documentation** | Retrieve information from Odoo 18 documentation | `/tool retrieve_odoo_documentation query="How to create a custom module in Odoo 18" max_results=5` | ✅ Working |
| **validate_field_value** | Validate a field value for a model | `/tool validate_field_value model_name=res.partner field_name=email value="test@example.com"` | ✅ Working |

#### Available Prompts

| Prompt | Description | Example Usage |
|--------|-------------|--------------|
| **create_record_prompt** | Get guidance for creating a new record | `/prompt create_record_prompt model_name=res.partner` |
| **search_records_prompt** | Get guidance for searching records | `/prompt search_records_prompt model_name=product.product` |
| **export_records_prompt** | Get guidance for exporting records | `/prompt export_records_prompt model_name=res.partner` |
| **import_records_prompt** | Get guidance for importing records | `/prompt import_records_prompt model_name=res.partner` |
| **advanced_search_prompt** | Get guidance for advanced natural language search | `/prompt advanced_search_prompt` |
| **dynamic_export_import_prompt** | Get guidance for dynamic export/import | `/prompt dynamic_export_import_prompt` |
| **crm_lead_export_import_prompt** | Get guidance for CRM lead export/import | `/prompt crm_lead_export_import_prompt` |
| **invoice_export_import_prompt** | Get guidance for invoice export/import | `/prompt invoice_export_import_prompt` |
| **related_records_export_import_prompt** | Get guidance for related records export/import | `/prompt related_records_export_import_prompt` |
| **odoo_documentation_prompt** | Get guidance for retrieving Odoo documentation | `/prompt odoo_documentation_prompt` |

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

This will start a FastAPI server on port 8001 that you can use to test the MCP tools. You can then use the `test_mcp_tools.py` script to test all the tools:

```bash
python test_mcp_tools.py
```

The standalone server provides the same functionality as the MCP server used by Claude Desktop, but with a simple HTTP interface for testing purposes.

#### Testing Individual Tools

You can test individual tools using curl or any HTTP client:

```bash
# Test the retrieve_odoo_documentation tool
curl -X POST "http://127.0.0.1:8001/call_tool" \
  -H "Content-Type: application/json" \
  -d '{"tool": "retrieve_odoo_documentation", "params": {"query": "How to create a custom module in Odoo 18", "max_results": 5}}'

# Test the advanced_search tool
curl -X POST "http://127.0.0.1:8001/call_tool" \
  -H "Content-Type: application/json" \
  -d '{"tool": "advanced_search", "params": {"query": "List all unpaid bills with respect of vendor details", "limit": 10}}'
```

#### Listing Available Tools

You can list all available tools using the `/list_tools` endpoint:

```bash
curl -X GET "http://127.0.0.1:8001/list_tools"
```

#### Health Check

You can check if the server is running using the `/health` endpoint:

```bash
curl -X GET "http://127.0.0.1:8001/health"
```

### Using the Direct Export/Import Implementation

The project includes a direct implementation for export/import operations. This approach provides a straightforward process for exporting and importing data with proper field mapping and validation.

#### Export/Import Features

- Support for any Odoo model
- Dynamic field discovery using ir.model and ir.model.fields
- Field mapping and transformation
- Handling of complex field types (many2one, many2many, etc.)
- Parent-child relationship maintenance
- Error handling and validation
- CSV as the primary data format

```python
from direct_export_import import export_records, import_records

# Export records
result = export_records(
    model_name="res.partner",
    fields=["id", "name", "email", "phone"],
    filter_domain=[["is_company", "=", True]],
    export_path="./exports/companies.csv"
)

# Import records
result = import_records(
    import_path="./exports/companies.csv",
    model_name="res.partner",
    field_mapping={"id": "id", "name": "name", "email": "email", "phone": "phone"},
    create_if_not_exists=False,
    update_if_exists=True
)
```

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
│   ├── search/             # Advanced search functionality
│   │   ├── query_parser.py # Natural language query parser
│   │   ├── relationship_handler.py # Model relationship handler
│   │   └── advanced_search.py # Advanced search implementation
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
├── test_advanced_search.py # Advanced search test
├── query_parser.py         # Natural language query parser
├── relationship_handler.py # Model relationship handler
├── advanced_search.py      # Advanced search implementation
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
python test_advanced_search.py    # Test advanced search functionality
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
| `advanced_search` | Natural language query | Formatted search results | Formatted search results | ✅ Passed |

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

## Odoo Documentation RAG Tool

We've implemented a powerful Retrieval Augmented Generation (RAG) tool for accessing Odoo 18 documentation. This tool uses sentence-transformers and FAISS to provide semantic search capabilities for finding relevant information in the Odoo 18 documentation:

1. **Documentation Repository Integration**: The tool clones and processes the official Odoo 18 documentation repository (https://github.com/odoo/documentation/tree/18.0) to extract relevant content.

2. **Semantic Search**: Using sentence-transformers and FAISS vector database, the tool provides semantic search capabilities for finding relevant documentation based on natural language queries.

3. **Chunking and Processing**: The documentation is processed and chunked into manageable segments with proper metadata extraction for improved retrieval.

4. **MCP Integration**: The RAG tool is fully integrated with the MCP server, providing a new `retrieve_odoo_documentation` tool and `odoo_documentation_prompt` for Claude Desktop.

5. **Comprehensive Results**: Search results include relevant documentation sections with source information and context.

6. **Persistent Storage**: The tool uses persistent storage for embeddings and processed documentation, making subsequent queries faster.

7. **Automatic Updates**: The tool can update the documentation repository to ensure the latest information is available.

8. **Error Handling**: Comprehensive error handling ensures the tool works reliably even when dependencies are missing or the documentation repository is unavailable.

9. **Dependency Management**: The tool handles dependencies gracefully, with proper error messages when required packages are missing.

10. **Test Script**: A test script (`test_odoo_docs_rag.py`) is provided to verify the functionality works correctly with various query types.

### Example Usage

#### Using the MCP tool in Claude Desktop:

```
/tool retrieve_odoo_documentation query="How to create a custom module in Odoo 18" max_results=5
```

This will return relevant sections from the Odoo 18 documentation about creating custom modules, with source information and context.

#### Using the Standalone MCP Server:

```bash
curl -X POST "http://127.0.0.1:8001/call_tool" \
  -H "Content-Type: application/json" \
  -d '{"tool": "retrieve_odoo_documentation", "params": {"query": "How to create a custom module in Odoo 18", "max_results": 5}}'
```

#### Testing the RAG Tool

The quality of the RAG tool's responses depends on the documentation available in the index. The tool currently indexes 32 documents from the Odoo 18 documentation repository. To improve the quality of responses, you can add more documentation files to the `odoo_docs` directory and rebuild the index by setting `force_rebuild=True` in the `OdooDocsRetriever` constructor.

```python
odoo_docs_retriever_instance = OdooDocsRetriever(
    docs_dir=docs_dir,
    index_dir=index_dir,
    force_rebuild=True  # Force rebuilding the index
)
```

## Recent Improvements and Fixes

### Advanced Natural Language Search

We've implemented a powerful advanced search functionality that can handle complex natural language queries across multiple Odoo models:

1. **Natural Language Query Parsing**: The system can parse natural language queries like "List all unpaid bills with respect of vendor details" or "List all project tasks according to their deadline date" and convert them into appropriate Odoo domain filters.

2. **Multi-Model Query Support**: The advanced search can handle queries that span multiple related models, such as "List all sales orders under the customer's name, Gemini Furniture" or "List out all Project tasks for project name Research & Development".

3. **Relationship Handling**: The system automatically identifies relationships between models (one2many, many2one, many2many) and traverses these relationships to provide comprehensive results.

4. **Query Components**:
   - **QueryParser**: Parses natural language queries into model names, domain filters, and fields to display
   - **RelationshipHandler**: Identifies and handles relationships between models
   - **AdvancedSearch**: Executes searches and formats results in a user-friendly way

5. **MCP Integration**: The advanced search functionality is fully integrated with the MCP server, providing a new `advanced_search` tool and `advanced_search_prompt` for Claude Desktop.

6. **Comprehensive Testing**: We've created a test script (`test_advanced_search.py`) to verify the functionality works correctly with various query types.

7. **Field Mapping**: The system includes mappings for common fields across different models, making it easier to search for related information.

8. **Result Formatting**: Search results are formatted in a user-friendly way, with tables for single-model results and structured output for multi-model results.

9. **Dynamic Model Discovery**: The query parser now uses Odoo's ir.model and ir.model.fields to dynamically discover models and their fields, making it work with any Odoo model without hardcoding.

10. **Field Categorization**: Fields are automatically categorized based on their types and names (e.g., date fields, amount fields, status fields), making it easier to map natural language concepts to Odoo fields.

11. **Field Validation**: All field references are validated against the actual model fields to ensure they exist, with fallbacks for different Odoo versions.

12. **Enhanced Entity Extraction**: The system can extract entities from queries using dynamic model information, improving the accuracy of search results.

13. **Cross-Version Compatibility**: The query parser includes special handling for field name changes between Odoo versions (e.g., move_type vs. type, customer_rank vs. customer).

### Export/Import Functionality

We've implemented robust export and import functionality for Odoo models, with special attention to handling complex models like account.move (invoices):

1. **Related Records Export/Import**: Added tools to export and import parent-child related records in a single operation, maintaining relationships between models.

2. **Invoice Export/Import**: Implemented specialized handling for account.move (invoices) and account.move.line (invoice lines) with support for:
   - Different invoice types (out_invoice, in_invoice, out_refund, in_refund, etc.)
   - Handling posted invoices with reset_to_draft functionality
   - Skipping readonly fields to avoid validation errors
   - Proper handling of many2one and many2many fields
   - Maintaining relationships between parent and child records

3. **CSV Processing**: Added robust CSV export and import with proper field mapping and data transformation.

4. **Field Type Handling**: Implemented proper handling of different field types:
   - many2one fields (extracting IDs from string representations)
   - many2many fields (converting to proper Odoo format)
   - date and datetime fields (proper formatting)
   - selection fields (validation against allowed values)

5. **Error Handling**: Added comprehensive error handling for export/import operations with detailed error messages.

6. **Dual Implementation Approach**:
   - **LangGraph Implementation**: Created a structured agent-based approach using LangGraph for complex export/import operations with:
     - State management system (`AgentState` class)
     - Export nodes (`select_model`, `select_fields`, `set_filter`, `execute_export`)
     - Import nodes (`select_import_file`, `select_import_model`, `map_fields`, `validate_mapping`, `execute_import`)
     - Directed graph flow for step-by-step processing
     - Conversational interface for guided export/import operations
   - **Direct Implementation**: Created a simpler, procedural implementation for export/import functionality that can be used without LangGraph for straightforward operations.

7. **File System Integration**: Added support for exporting to and importing from the file system with proper path handling.

### Challenges and Solutions for Invoice Handling

Working with Odoo's account.move (invoice) model presented several challenges:

1. **Posted Invoices**: Odoo doesn't allow updating posted invoices directly. We implemented a reset_to_draft functionality that attempts to reset the invoice to draft state before updating.

2. **Readonly Fields**: Many fields in account.move are readonly when the invoice is posted. We added a skip_readonly_fields option to automatically remove these fields from the update data.

3. **Balance Requirements**: Odoo requires invoices to be balanced (debits = credits). When updating invoice lines, we need to ensure the invoice remains balanced.

4. **Many2one Field Handling**: Fields like account_id are stored as lists with both ID and name (e.g., [38, 'Local Sales']). We implemented proper extraction of just the ID for update operations.

5. **Move Types**: account.move has different move_types (out_invoice, in_invoice, etc.) with different field requirements. We added a move_type parameter to filter invoices by type.

6. **Relationship Maintenance**: Maintaining the relationship between account.move and account.move.line requires careful handling of the move_id field.

### MCP Server Fixes and Enhancements

We've made several improvements to the MCP server to ensure all tools work correctly with Odoo 18:

1. **Fixed `get_model_schema` function**: The function was trying to access the 'description' field in the 'ir.model' model, which doesn't exist in Odoo 18. We fixed this by using a different approach to get model information.

2. **Improved `analyze_field_importance` and `get_field_groups` tools**: These tools were relying on the `get_model_schema` function, which was failing. We updated them to use the `get_model_fields` function directly, which is more reliable.

3. **Enhanced `get_record_template` tool**: The tool was returning a minimal template with just the 'name' field. We improved it to provide more comprehensive templates for common models like 'res.partner' and 'product.product'.

4. **Added standalone MCP server for testing**: We created a standalone FastAPI server that exposes the MCP tools as HTTP endpoints for easier testing without Claude Desktop.

5. **Added comprehensive test suite**: We created test scripts to verify all MCP functions and tools work correctly with Odoo 18.

6. **Added advanced search functionality**: We implemented a powerful natural language search capability that can handle complex queries across multiple models.

7. **Created query parser and relationship handler**: We developed components to parse natural language queries and handle relationships between models for advanced search.

### Performance Improvements

1. **Optimized model discovery**: Improved the performance of model discovery by caching model information.

2. **Reduced XML-RPC calls**: Minimized the number of XML-RPC calls to Odoo for better performance.

3. **Improved error handling**: Added better error handling and reporting for more reliable operation.

### Dependency Management Improvements

1. **Python version compatibility**: Updated the project to require Python 3.10+ for compatibility with the MCP SDK.

2. **PyTorch version constraints**: Added version constraints for PyTorch to ensure compatibility with macOS.

3. **NumPy version constraints**: Added version constraints for NumPy to ensure compatibility with FAISS and other dependencies.

4. **Standalone MCP server**: Created a standalone MCP server for testing tools without Claude Desktop.

5. **Improved error handling**: Enhanced error handling for dependency issues with clear error messages.

6. **Documentation updates**: Updated documentation with dependency management best practices.

## Troubleshooting

### Dependency Management

#### Python Version Compatibility

The project requires Python 3.10 or higher due to the MCP SDK dependency. If you're using an older version of Python, you'll need to upgrade.

#### PyTorch Version Compatibility

On macOS, you may encounter issues with PyTorch compatibility. We recommend using PyTorch 2.2.x for best compatibility:

```bash
pip install "torch>=2.2.0,<=2.2.2"
```

#### NumPy Version Compatibility

Some dependencies (like FAISS) may have issues with NumPy 2.x. We recommend using NumPy <2.0.0 for compatibility:

```bash
pip install "numpy>=1.26.0,<2.0.0"
```

#### Using uv for Dependency Management

We recommend using uv for dependency management as it provides better error messages and faster installation:

```bash
# Install uv
pip install uv

# Create a virtual environment
uv venv

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .
```

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

#### "spawn python ENOENT" Error in Claude Desktop

- **Issue**: Error message "spawn python ENOENT" in Claude Desktop logs
- **Solution**: This error occurs when Claude Desktop can't find the Python executable. Update the Claude Desktop configuration to use the full path to your Python executable instead of just "python". For example, use "/Users/username/workspace/odoo18_mcp_project/.venv/bin/python3" instead of "python". You can find the full path by running `which python3` in your terminal.

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