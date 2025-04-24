# Odoo 18 MCP Integration (18.0 Branch)

A robust integration server that connects MCP (Master Control Program) with Odoo 18.0 ERP system, focusing on efficient data synchronization, API management, and secure communications. This implementation provides a standardized interface for performing CRUD operations on Odoo 18 models through a simple API.

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
- **Environment Configuration**: Easy configuration using environment variables
- **Type Safety**: Pydantic models for data validation and type checking
- **Logging**: Comprehensive logging system with detailed error information
- **Error Handling**: Robust error handling and reporting with proper exception hierarchy

## Installation

### Prerequisites

- Python 3.8 or higher
- Odoo 18.0 instance
- Access to Odoo database

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/odoo18-mcp-project.git
cd odoo18-mcp-project
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -e .
```

4. Create a `.env` file:

```bash
cp .env.example .env
```

5. Edit the `.env` file with your Odoo connection details:

```
ODOO_URL=http://your-odoo-server:8069
ODOO_DB=your_database_name
ODOO_USERNAME=your_username
ODOO_PASSWORD=your_password
```

### Building from Source

If you want to build the package for distribution:

```bash
python -m pip install build
python -m build
```

This will create distribution packages in the `dist/` directory.

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
├── client_test.py          # Client test script
├── advanced_client_test.py # Advanced client test
└── dynamic_model_test.py   # Dynamic model test
```

### Running Tests

```bash
python client_test.py       # Basic client test
python advanced_client_test.py  # Advanced client test
python dynamic_model_test.py    # Dynamic model test
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

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Odoo Community
- Python Community