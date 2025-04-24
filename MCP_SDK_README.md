# MCP SDK Integration for Odoo 18

This document provides detailed information about the MCP SDK integration for Odoo 18, which allows you to use Claude Desktop with your Odoo 18 instance.

## Overview

The MCP SDK integration provides a standardized interface for interacting with Odoo 18 through Claude Desktop. It allows you to:

- Discover available Odoo models
- Get metadata for specific models
- View records from models
- Search for records
- Create, update, and delete records
- Execute custom methods
- Analyze field importance
- Get field groups
- Get record templates

## Installation

### Prerequisites

- Python 3.8 or higher
- Odoo 18.0 instance
- Claude Desktop

### Setup

1. Install the MCP SDK:

```bash
pip install "mcp[cli]"
```

2. Install the MCP server in Claude Desktop:

```bash
mcp install mcp_server.py --name "Odoo 18 Integration" -v ODOO_URL=http://your-odoo-server:8069 -v ODOO_DB=your_database_name -v ODOO_USERNAME=your_username -v ODOO_PASSWORD=your_password
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
        "command": "python",
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

4. Restart Claude Desktop to apply the changes.

## Usage

### Resources

The MCP server provides the following resources:

| Resource | Description | Example |
|----------|-------------|---------|
| **Models List** | Get a list of all available models | `/resource odoo://models/all` |
| **Model Metadata** | Get metadata for a specific model | `/resource odoo://model/res.partner/metadata` |
| **Model Records** | Get records for a specific model | `/resource odoo://model/product.product/records` |

#### List All Models

```
/resource odoo://models/all
```

This resource returns a list of all available Odoo models.

#### Get Model Metadata

```
/resource odoo://model/{model_name}/metadata
```

This resource returns metadata for a specific Odoo model, including:
- Model information (name, technical name)
- Fields (name, type, required, readonly)
- Required fields
- Recommended create fields

Example:
```
/resource odoo://model/res.partner/metadata
```

#### Get Model Records

```
/resource odoo://model/{model_name}/records
```

This resource returns a list of records for a specific Odoo model.

Example:
```
/resource odoo://model/product.product/records
```

### Tools

The MCP server provides the following tools:

| Tool | Description | Status | Example Usage |
|------|-------------|--------|--------------|
| **search_records** | Search for records in a model | ✅ Working | `/tool search_records model_name=res.partner query=company` |
| **get_record_template** | Get a template for creating a record | ✅ Working | `/tool get_record_template model_name=product.product` |
| **create_record** | Create a new record | ✅ Working | `/tool create_record model_name=res.partner values={"name":"Test Partner"}` |
| **update_record** | Update an existing record | ✅ Working | `/tool update_record model_name=res.partner record_id=42 values={"name":"Updated"}` |
| **delete_record** | Delete a record | ✅ Working | `/tool delete_record model_name=res.partner record_id=42` |
| **execute_method** | Execute a custom method | ✅ Working | `/tool execute_method model_name=res.partner method=name_search args=["Test"]` |
| **analyze_field_importance** | Analyze field importance | ✅ Working | `/tool analyze_field_importance model_name=res.partner use_nlp=true` |
| **get_field_groups** | Group fields by purpose | ✅ Working | `/tool get_field_groups model_name=product.product` |

#### Search Records

```
/tool search_records model_name={model_name} query={query}
```

This tool searches for records in an Odoo model.

Example:
```
/tool search_records model_name=res.partner query=company
```

#### Create Record

```
/tool create_record model_name={model_name} values={values}
```

This tool creates a new record in an Odoo model.

Example:
```
/tool create_record model_name=res.partner values={"name":"Test Partner","email":"test@example.com"}
```

#### Update Record

```
/tool update_record model_name={model_name} record_id={record_id} values={values}
```

This tool updates an existing record in an Odoo model.

Example:
```
/tool update_record model_name=res.partner record_id=42 values={"name":"Updated Partner"}
```

#### Delete Record

```
/tool delete_record model_name={model_name} record_id={record_id}
```

This tool deletes a record from an Odoo model.

Example:
```
/tool delete_record model_name=res.partner record_id=42
```

#### Execute Method

```
/tool execute_method model_name={model_name} method={method} args={args}
```

This tool executes a custom method on an Odoo model.

Example:
```
/tool execute_method model_name=res.partner method=name_search args=["Test"]
```

#### Analyze Field Importance

```
/tool analyze_field_importance model_name={model_name} use_nlp={use_nlp}
```

This tool analyzes the importance of fields in an Odoo model.

Example:
```
/tool analyze_field_importance model_name=res.partner use_nlp=true
```

#### Get Field Groups

```
/tool get_field_groups model_name={model_name}
```

This tool gets field groups for an Odoo model.

Example:
```
/tool get_field_groups model_name=product.product
```

#### Get Record Template

```
/tool get_record_template model_name={model_name}
```

This tool gets a template for creating a record in an Odoo model.

Example:
```
/tool get_record_template model_name=product.product
```

### Prompts

The MCP server provides the following prompts:

| Prompt | Description | Example Usage |
|--------|-------------|--------------|
| **create_record_prompt** | Guidance for creating a record | `/prompt create_record_prompt model_name=res.partner` |
| **search_records_prompt** | Guidance for searching records | `/prompt search_records_prompt model_name=product.product` |

#### Create Record Prompt

```
/prompt create_record_prompt model_name={model_name}
```

This prompt helps you create a new record in an Odoo model.

Example:
```
/prompt create_record_prompt model_name=res.partner
```

#### Search Records Prompt

```
/prompt search_records_prompt model_name={model_name}
```

This prompt helps you search for records in an Odoo model.

Example:
```
/prompt search_records_prompt model_name=product.product
```

## Development

### Running the MCP Server Locally

You can run the MCP server locally for development:

```bash
python mcp_server.py
```

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

### Testing the MCP Server

The project includes several test scripts for verifying the MCP server functionality:

#### Direct Function Testing

Test the underlying functions directly:

```bash
python test_mcp_functions.py
```

This script tests the OdooModelDiscovery class functions directly, bypassing the MCP server interface.

#### HTTP Tool Testing

Test the MCP tools via HTTP using the standalone server:

```bash
# Start the standalone server
python standalone_mcp_server.py

# In another terminal, run the tests
python test_mcp_tools.py
```

This tests all the MCP tools by making HTTP requests to the standalone server.

#### MCP Client Testing

Test the MCP client interface:

```bash
python test_mcp_client.py
```

This script tests the MCP client interface by making requests to the MCP server.

### Using the MCP CLI

You can use the MCP CLI to interact with the MCP server:

```bash
mcp dev mcp_server.py
```

This will start the MCP server in development mode with the MCP Inspector.

## Troubleshooting

### Connection Issues

If you're having trouble connecting to the MCP server:

1. Check that your Odoo server is running and accessible
2. Verify your Odoo credentials in the environment variables
3. Check the MCP server logs for error messages
4. Try running the MCP server directly to see if there are any errors

### Authentication Issues

If you're having trouble authenticating with Odoo:

1. Verify your Odoo credentials in the environment variables
2. Check that your Odoo user has the necessary permissions
3. Try connecting to Odoo directly using the XML-RPC client

### Resource Not Found

If a resource is not found:

1. Check that the resource URI is correct
2. Verify that the model exists in your Odoo instance
3. Check that your Odoo user has access to the model

## License

This project is licensed under the MIT License - see the LICENSE file for details.