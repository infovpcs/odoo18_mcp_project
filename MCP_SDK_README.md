# Odoo 18 MCP Integration with Standard MCP SDK

This document explains how to use the Odoo 18 MCP Integration with the standard Model Context Protocol (MCP) Python SDK.

## Overview

The `mcp_server.py` script provides a complete MCP server implementation using the standard MCP Python SDK that integrates with our existing Odoo 18 MCP project. This allows you to:

1. Use the standard MCP tools and workflows
2. Integrate with Claude Desktop and other MCP-compatible clients
3. Leverage the dynamic model handling capabilities of our Odoo integration

## Installation

### Prerequisites

- Python 3.8 or higher
- Odoo 18.0 instance
- Access to Odoo database

### Setup

1. Install the MCP SDK:

```bash
pip install "mcp[cli]"
```

2. Install our Odoo 18 MCP project:

```bash
pip install -e .
```

3. Configure your Odoo connection in the `.env` file:

```
ODOO_URL=http://your-odoo-server:8069
ODOO_DB=your_database_name
ODOO_USERNAME=your_username
ODOO_PASSWORD=your_password
```

## Running the MCP Server

### Development Mode

The fastest way to test and debug your server is with the MCP Inspector:

```bash
mcp dev mcp_server.py
```

This will start the MCP Inspector in your browser, allowing you to interact with your Odoo MCP server.

### Claude Desktop Integration

To install the server in Claude Desktop:

```bash
mcp install mcp_server.py
```

You can customize the installation:

```bash
# Custom name
mcp install mcp_server.py --name "Odoo 18 Integration"

# Environment variables
mcp install mcp_server.py -v ODOO_URL=http://localhost:8069 -v ODOO_DB=llmdb18
mcp install mcp_server.py -f .env
```

### Direct Execution

You can also run the server directly:

```bash
python mcp_server.py
```

Or using the MCP CLI:

```bash
mcp run mcp_server.py
```

## Features

### Resources

The MCP server exposes the following resources:

- `models://all` - List of all available Odoo models
- `model://{model_name}/metadata` - Metadata for a specific model
- `model://{model_name}/records` - Records for a specific model

### Tools

The MCP server provides the following tools:

- `search_records` - Search for records in an Odoo model
- `create_record` - Create a new record in an Odoo model
- `update_record` - Update an existing record in an Odoo model
- `delete_record` - Delete a record from an Odoo model
- `execute_method` - Execute a custom method on an Odoo model
- `analyze_field_importance` - Analyze the importance of fields in an Odoo model
- `get_field_groups` - Get field groups for an Odoo model
- `get_record_template` - Get a template for creating a record in an Odoo model

### Prompts

The MCP server includes the following prompts:

- `create_record_prompt` - Guide for creating a new record
- `search_records_prompt` - Guide for searching records

## Examples

### Listing Available Models

```
/resource models://all
```

### Getting Model Metadata

```
/resource model://res.partner/metadata
```

### Searching for Records

```
/tool search_records model_name=res.partner query=Company
```

### Creating a Record

First, get a template:

```
/tool get_record_template model_name=res.partner
```

Then create the record:

```
/tool create_record model_name=res.partner values={"name": "Test Company", "is_company": true, "email": "test@example.com"}
```

### Using Prompts

```
/prompt create_record_prompt model_name=res.partner
```

## Advanced Usage

### Custom Method Execution

You can execute any method available on Odoo models:

```
/tool execute_method model_name=res.partner method=name_search args=["Test"]
```

### Field Analysis

Analyze field importance using NLP:

```
/tool analyze_field_importance model_name=res.partner use_nlp=true
```

Get field groups:

```
/tool get_field_groups model_name=res.partner
```

## Troubleshooting

### Connection Issues

If you encounter connection issues with Odoo:

1. Verify that the Odoo server is running and accessible
2. Check that the URL, database name, username, and password in the `.env` file are correct
3. Ensure that the Odoo server allows XML-RPC connections

### MCP SDK Issues

If you encounter issues with the MCP SDK:

1. Make sure you have the latest version installed: `pip install -U "mcp[cli]"`
2. Check the [MCP SDK documentation](https://modelcontextprotocol.io) for troubleshooting tips
3. Try running the server with debug logging: `mcp run mcp_server.py --log-level debug`