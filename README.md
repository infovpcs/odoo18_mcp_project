# Odoo 18 MCP Integration (18.0 Branch)

Last Updated: 2025-06-06

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Odoo 18.0](https://img.shields.io/badge/odoo-18.0-green.svg)](https://www.odoo.com/)
[![MCP SDK](https://img.shields.io/badge/mcp-sdk-purple.svg)](https://github.com/modelcontextprotocol/python-sdk)
[![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A robust integration server that connects MCP (Master Control Program) with Odoo 18.0 ERP system, focusing on efficient data synchronization, API management, and secure communications. This implementation provides a standardized interface for performing CRUD operations on Odoo 18 models through a simple API, with dynamic model discovery and field analysis capabilities.

## Project Structure

```
odoo18_mcp_project/
├── src/                     # Main source code
│   ├── agents/             # AI agents implementation
│   ├── core/               # Core functionality
│   ├── mcp/               # MCP integration code
│   │   ├── server.py     # MCP server implementation
│   │   └── ...           # Other MCP-related modules
│   ├── odoo/              # Odoo integration code
│   │   ├── client.py      # Odoo client implementation
│   │   ├── schemas.py     # Data schemas and models
│   │   └── ...            # Other Odoo-related modules
│   ├── odoo_docs_rag/     # Odoo documentation retrieval
│   ├── odoo_tools/        # Odoo utility tools
│   ├── simple_odoo_code_agent/ # Simplified code agent
│   └── streamlit_client/  # Streamlit UI client
├── tests/                  # Test files
├── exports/                # Exported data files
├── generated_modules/      # Generated Odoo modules
├── logs/                   # Log files
├── odoo_docs/             # Odoo documentation
├── odoo_docs_index/       # Documentation index
└── tmp/                   # Temporary files
```

## Features

- **Odoo Integration**
  - XML-RPC connection to Odoo 18
  - Model discovery using ir.model and ir.model.fields
  - Dynamic field analysis and grouping
  - NLP-based field importance analysis
  - Relationship-aware search and operations

- **CRUD Operations**
  - Create, Read, Update, Delete for any Odoo model
  - Batch operations support
  - Custom method execution
  - Record templates generation

- **Data Management**
  - Export/Import tools for CSV files
  - Related records handling
  - Relationship maintenance
  - Batch processing support

- **AI Integration**
  - DeepWiki integration for documentation
  - Gemini LLM integration
  - Natural language query parsing
  - Code generation capabilities

- **Development Tools**
  - Streamlit UI for module generation
  - Documentation search
  - CRUD testing interface
  - Workflow visualization
  - Mermaid diagram generation

## Setup

1. Clone the repository:

```bash
git clone https://github.com/infovpcs/odoo18_mcp_project.git
cd odoo18_mcp_project
```

2. Create and activate virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -e .
```

4. Configure environment:

```bash
cp .env.example .env
```

Edit `.env` with your Odoo connection details:

```
ODOO_URL=http://localhost:8069
ODOO_DB=llmdb18
ODOO_USERNAME=admin
ODOO_PASSWORD=admin

# Optional AI/LLM integration
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
```

## Usage

### Running the Server

```bash
python mcp_server.py
```

### Running Tests

```bash
python -m pytest tests/
```

### Using Streamlit UI

```bash
streamlit run app.py
```

## Tools

1. **Basic CRUD Operations**
   - `search_records`: Search for records in any Odoo model
   - `create_record`: Create new records
   - `update_record`: Update existing records
   - `delete_record`: Delete records
   - `get_record_template`: Get a template for creating records

2. **Advanced Search and Documentation**
   - `advanced_search`: Perform advanced natural language search
   - `retrieve_odoo_documentation`: Retrieve information from Odoo 18 documentation
   - `get_field_groups`: Get field groups for a model
   - `analyze_field_importance`: Analyze field importance using NLP

3. **Export/Import Tools**
   - `export_records_to_csv`: Export records to CSV
   - `import_records_from_csv`: Import records from CSV
   - `export_related_records_to_csv`: Export parent-child related records
   - `import_related_records_from_csv`: Import parent-child related records

4. **Code Generation Tools**
   - `generate_module`: Generate Odoo 18 module code using Simple Odoo Code Agent
   - `generate_npx`: Generate diagrams from Mermaid markdown

## Documentation

For more detailed documentation, see:
- [PLANNING.md](PLANNING.md) - Project planning and architecture
- [TASK.md](TASK.md) - Current tasks and progress
- [MCP_OVERVIEW.md](MCP_OVERVIEW.md) - MCP integration details
- [MCP_SDK_README.md](MCP_SDK_README.md) - MCP SDK documentation
- [CLIENT_README.md](CLIENT_README.md) - Client usage documentation

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Installation

### Prerequisites

- Python 3.10 or higher
- Odoo 18.0 instance
- Access to Odoo database
- Claude Desktop (optional, for AI integration)
- Compatible PyTorch version (2.2.x recommended for macOS)
- NumPy <2.0.0 (for compatibility with other packages)

### Odoo Module Generator UI

The project includes a user-friendly Streamlit interface for generating Odoo modules with advanced customization options:

### Features
- **Multiple Model Provider Support**: Choose between Gemini, OpenAI, Anthropic, or Ollama
- **Odoo Version Selection**: Target Odoo 18.0, 17.0, or 16.0
- **Module Customization**: Select from multiple module features
  - Basic CRUD operations
  - Search/Filter functionality
  - Multi-Company Support
  - Access Rights implementation
  - Kanban View
  - Calendar View
- **Demo Data**: Option to include sample demo data
- **Custom Module Naming**: Specify a custom module name or auto-generate from query
- **DeepWiki Integration**: Access to latest Odoo and OWL documentation patterns
- **File Download**: Download individual files or complete ZIP package
- **Organized Output**: Files organized by type (Models, Views, Security, etc.)

### Running the Streamlit App

```bash
# Navigate to the project directory
cd /path/to/odoo18_mcp_project

# Activate the virtual environment
source .venv/bin/activate  # or .venv/Scripts/activate on Windows

# Run the Streamlit app
streamlit run app.py
```

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

5. Edit the `.env` file with your Odoo connection details, optional Gemini API key, and optional Brave Search API key:

```
# Odoo connection details
ODOO_URL=http://localhost:8069
ODOO_DB=llmdb18
ODOO_USERNAME=admin
ODOO_PASSWORD=admin

# Gemini LLM integration for Odoo Module Generator and RAG tool
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Brave Search API for online search in RAG tool
BRAVE_API_KEY=your_brave_api_key_here

# Odoo documentation paths
ODOO_DOCS_DIR="/Users/vinusoft85/workspace/odoo18_mcp_project/odoo_docs",
ODOO_INDEX_DIR="/Users/vinusoft85/workspace/odoo18_mcp_project/odoo_docs_index",
ODOO_DB_PATH="/Users/vinusoft85/workspace/odoo18_mcp_project/odoo_docs_index/embeddings.db"
```

> **Note**: The `BRAVE_API_KEY` is required for the online search functionality in the enhanced RAG tool. You can obtain a Brave Search API key from the [Brave Search Developer Portal](https://brave.com/search/api/).

### Claude Desktop Integration

The project includes comprehensive integration with Claude Desktop, allowing you to use all the Odoo 18 MCP tools directly within the Claude AI assistant interface.

#### Installation Options

##### Option 1: Using the MCP CLI (Recommended)

1. Install the MCP SDK with CLI support:

```bash
pip install "mcp[cli]"
```

2. Install the MCP server in Claude Desktop:

```bash
# Make sure to set these environment variables in your shell or .env file first:
# export ODOO_URL=http://localhost:8069

# export ODOO_PASSWORD=admin
# export GEMINI_API_KEY=your_key
# export BRAVE_API_KEY=your_key

mcp install mcp_server.py --name "Odoo 18 Integration" \
  --command "$(which python3)" \
  --args "$(pwd)/mcp_server.py" \
  --env ODOO_URL=${ODOO_URL} \
  --env ODOO_DB=${ODOO_DB} \
  --env ODOO_USERNAME=${ODOO_USERNAME} \
  --env ODOO_PASSWORD=${ODOO_PASSWORD} \
  --env GEMINI_API_KEY=${GEMINI_API_KEY} \
  --env GEMINI_MODEL=gemini-2.0-flash \
  --env BRAVE_API_KEY=${BRAVE_API_KEY} \
  --env ODOO_DOCS_DIR="$(pwd)/odoo_docs" \
  --env ODOO_INDEX_DIR="$(pwd)/odoo_docs_index" \
  --env ODOO_DB_PATH="$(pwd)/odoo_docs_index/embeddings.db" \
```

This command will:
- Register the MCP server with Claude Desktop
- Configure the necessary environment variables
- Set up the server with the correct name and description

##### Option 2: Using the Automated Script

We provide a convenient script that automatically updates the Claude Desktop configuration:

```bash
# Make the script executable
chmod +x update_claude_config.sh

# Run the script
./update_claude_config.sh
```

This script will:
- Detect your Claude Desktop configuration location based on your OS
- Load environment variables from your `.env` file (including GEMINI_API_KEY)
- Update the Claude Desktop configuration with the correct values
- Handle environment variable substitution automatically
- Create a backup of your existing configuration
- Validate the updated configuration

##### Option 3: Manual Configuration

You can also manually update the Claude Desktop configuration file:

1. Locate your Claude Desktop configuration file:
   - **macOS**: `~/Library/Application Support/Claude/config.json`
   - **Windows**: `%APPDATA%\Claude\config.json`
   - **Linux**: `~/.config/Claude/config.json`

2. Open the `claude_config.json` file in a text editor and add the following to the `servers` section:

```json
{
    "odoo18-mcp": {
        "name": "Odoo 18 Integration",
        "description": "Dynamic Odoo 18 integration with MCP",
        "command": "/full/path/to/your/python",
        "args": ["/full/path/to/your/odoo18_mcp_project/mcp_server.py"],
        "env": {
            "ODOO_URL": "http://localhost:8069",
            "ODOO_DB": "llmdb18",
            "ODOO_USERNAME": "admin",
            "ODOO_PASSWORD": "admin",
            "GEMINI_API_KEY": "your_gemini_api_key_here",
            "GEMINI_MODEL": "gemini-2.0-flash",
            "BRAVE_API_KEY": "your_brave_api_key_here",
            "ODOO_DOCS_DIR": "/full/path/to/your/odoo18_mcp_project/odoo_docs",
            "ODOO_INDEX_DIR": "/full/path/to/your/odoo18_mcp_project/odoo_docs_index",
            "ODOO_DB_PATH" : "/full/path/to/your/odoo18_mcp_project/odoo_docs_index/embeddings.db"
        }
    }
}
```

**Important Configuration Notes**:
- Replace `/full/path/to/your/python` with the actual full path to your Python executable. You can find this by running `which python3` in your terminal. For example, if you're using a virtual environment, it might be something like `/Users/username/workspace/odoo18_mcp_project/.venv/bin/python3`.
- Replace `your_gemini_api_key_here` with your actual Google Gemini API key if you want to use the Odoo Module Generator with Gemini integration.
- Replace `your_brave_api_key_here` with your actual Brave Search API key if you want to use the online search functionality in the enhanced RAG tool. You can obtain a Brave Search API key from the [Brave Search Developer Portal](https://brave.com/search/api/).
- Make sure the path to `mcp_server.py` is correct for your installation.

#### Verifying the Installation

After configuring Claude Desktop:

1. Restart Claude Desktop to apply the changes
2. Open Claude Desktop and click on the server selection dropdown (top-right corner)
3. Select "Odoo 18 Integration" from the list
4. Check the Claude Desktop logs for successful connection to Odoo
5. Try a simple command like `/tool search_records model_name=res.partner query=company` to verify functionality

#### Troubleshooting Claude Desktop Integration

If you encounter issues with the Claude Desktop integration:

1. **Check the Claude Desktop logs**:
   - **macOS**: `~/Library/Logs/Claude/main.log`
   - **Windows**: `%APPDATA%\Claude\logs\main.log`
   - **Linux**: `~/.config/Claude/logs/main.log`

2. **Verify Python path**:
   - Make sure the Python path in the configuration is correct and accessible
   - The Python executable should have the MCP SDK installed

3. **Check environment variables**:
   - Verify that all environment variables are correctly set
   - Make sure the Odoo server is running and accessible at the specified URL

4. **Restart Claude Desktop**:
   - Sometimes a simple restart resolves connection issues

5. **Run the MCP server directly**:
   - Try running `python mcp_server.py` directly to check for any errors

6. **Use the standalone server for testing**:
   - Run `python standalone_mcp_server.py` and test the tools using curl commands

#### Using Claude Desktop with Odoo 18 Integration

Once configured, you can use all the Odoo 18 MCP tools directly within Claude Desktop:

1. **Tool Commands**: Use `/tool` commands to execute specific operations
   ```
   /tool search_records model_name=res.partner query="company"
   /tool get_record_template model_name=product.product
   /tool run_odoo_code_agent query="Create a customer feedback module" use_gemini=true
   ```

2. **Resource Commands**: Use `/resource` commands to access Odoo resources
   ```
   /resource odoo://models/all
   /resource odoo://model/res.partner/metadata
   /resource odoo://model/product.product/records
   ```

3. **Prompt Commands**: Use `/prompt` commands for guided assistance
   ```
   /prompt create_record_prompt model_name=res.partner
   /prompt export_records_prompt model_name=res.partner
   /prompt odoo_code_agent_prompt
   ```

The integration provides a seamless experience, allowing you to work with Odoo directly from Claude Desktop without switching between applications.

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
# Set up required directories (logs, exports, tmp, data, generated_modules)
make setup

# Build Docker images
make build

# Start development environment
make dev

# Run tests
make test

# Run specific test categories
make test-mcp         # Run MCP server tests
make test-agent       # Run Odoo code agent tests
make test-utils       # Run Odoo code agent utilities tests
make test-export-import  # Run export/import agent tests

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
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
BRAVE_API_KEY=your_brave_api_key_here
ODOO_DOCS_DIR="/Users/vinusoft85/workspace/odoo18_mcp_project/odoo_docs",
ODOO_INDEX_DIR="/Users/vinusoft85/workspace/odoo18_mcp_project/odoo_docs_index",
ODOO_DB_PATH="/Users/vinusoft85/workspace/odoo18_mcp_project/odoo_docs_index/embeddings.db"
MCP_DEBUG=true
MCP_LOG_LEVEL=DEBUG
```

#### Volume Management

The Docker setup includes several volumes for persistent data:

- `mcp_data`: Persistent data storage
- `mcp_logs`: Persistent logs storage
- `./exports`: Directory for exported files
- `./tmp`: Directory for temporary files
- `./generated_modules`: Directory for Odoo module files generated by the Odoo Module Generator

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
| **import_records_from_csv** | Import records from CSV to a model | `/tool import_records_from_csv model_name=res.partner input_path="exports/partners.csv"` | ✅ Working |
| **export_related_records_to_csv** | Export parent-child records to CSV | `/tool export_related_records_to_csv parent_model=account.move child_model=account.move.line relation_field=move_id move_type=out_invoice export_path="./tmp/customer_invoices.csv"` | ✅ Working |
| **import_related_records_from_csv** | Import parent-child records from CSV | `/tool import_related_records_from_csv parent_model=account.move child_model=account.move.line relation_field=move_id input_path="./tmp/customer_invoices.csv" reset_to_draft=true skip_readonly_fields=true` | ✅ Working |
| **advanced_search** | Perform advanced natural language search | `/tool advanced_search query="List all unpaid bills with respect of vendor details" limit=10` | ✅ Working |
| **retrieve_odoo_documentation** | Retrieve information from Odoo 18 documentation | `/tool retrieve_odoo_documentation query="How to create a custom module in Odoo 18" max_results=5 use_gemini=true use_online_search=true` | ✅ Working |
| **validate_field_value** | Validate a field value for a model | `/tool validate_field_value model_name=res.partner field_name=email value="test@example.com"` | ✅ Working |
| **run_odoo_code_agent** | Generate Odoo 18 module code | `/tool run_odoo_code_agent_tool query="Create a customer feedback module" use_gemini=true use_ollama=false` | ✅ Working |
| **generate_npx** | Generate PNG image from Mermaid markdown | `/tool generate_npx code="graph TD; A[Start] --> B[Process]; B --> C[End]" name="workflow" theme="default" backgroundColor="white"` | ✅ Working |

#### Mermaid Diagram Generation

The project includes a powerful Mermaid diagram generation tool that converts Mermaid markdown into PNG images. This feature is particularly useful for visualizing workflows, entity relationships, and other diagrams.

**Features:**
- Generate high-quality PNG images from Mermaid markdown
- Support for all Mermaid diagram types (flowchart, sequence, class, ER, etc.)
- Customizable themes (default, forest, dark, neutral)
- Configurable background color
- File caching to avoid regenerating unchanged diagrams
- Integrated with the Streamlit client for interactive visualization

**Usage in Streamlit Client:**
- The Code Agent Graph page automatically generates and displays workflow diagrams
- Cached diagrams are reused to improve performance
- A "Regenerate" button allows forcing regeneration when needed
- Timestamps show when diagrams were last generated

**Usage with MCP Tool:**
```bash
# Basic usage
/tool generate_npx code="graph TD; A[Start] --> B[Process]; B --> C[End]" name="simple_workflow"

# With custom theme and background color
/tool generate_npx code="sequenceDiagram; A->>B: Hello; B->>A: Hi there" name="sequence_diagram" theme="dark" backgroundColor="#f5f5f5"

# Complex flowchart
/tool generate_npx code="graph TD; A[Start] --> B{Decision}; B -->|Yes| C[Process 1]; B -->|No| D[Process 2]; C --> E[End]; D --> E" name="decision_flow" theme="forest" backgroundColor="white"
```

The generated PNG files are saved in the `exports/diagrams` directory and can be used in documentation, presentations, or embedded in web applications.

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
| **odoo_code_agent_prompt** | Get guidance for using the Odoo code agent | `/prompt odoo_code_agent_prompt` |

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

### MCP Connector Implementation

The project includes a flexible MCP connector implementation that supports both the official MCP Python SDK with STDIO transport and a custom HTTP API:

#### Using the MCP Connector with HTTP API

```python
from src.streamlit_client.utils.mcp_connector import MCPConnector, ConnectionType

# Create a connector using the HTTP API
connector = MCPConnector(
    connection_type=ConnectionType.HTTP,
    server_url="http://localhost:8001"
)

# Connect to the MCP server
import asyncio
async def run():
    # Connect to the server
    connected = await connector.connect()
    if not connected:
        print("Failed to connect")
        print("Make sure the standalone MCP server is running")
        return

    try:
        # Call a tool asynchronously
        result = await connector.async_call_tool(
            "search_records",
            {"model_name": "res.partner", "query": "company"}
        )
        print(result)

        # Call another tool
        result = await connector.async_call_tool(
            "advanced_search",
            {"query": "List all customers", "limit": 5}
        )
        print(result)
    finally:
        # Close the connection when done
        await connector.close()

# Run the async function
asyncio.run(run())

# Alternatively, you can use the synchronous interface
connector = MCPConnector(
    connection_type=ConnectionType.HTTP,
    server_url="http://localhost:8001"
)
if connector.health_check():
    result = connector.call_tool(
        "search_records",
        {"model_name": "res.partner", "query": "company"}
    )
```

#### Example Scripts

The project includes example scripts for using the MCP connector:

1. **HTTP API Example**:
```bash
# First, start the standalone MCP server
uv run standalone_mcp_server.py

# Then, in another terminal, run the example
uv run src/streamlit_client/examples/mcp_sdk_example.py
```

2. **Alternative HTTP API Example**:
```bash
# First, start the standalone MCP server
uv run standalone_mcp_server.py

# Then, in another terminal, run the example
uv run src/streamlit_client/examples/http_api_example.py
```

The connector automatically handles:
- Connection management
- Tool discovery and listing
- Asynchronous tool calls with proper error handling
- Polling for long-running operations
- Timeout management for different tools

See the example in `src/streamlit_client/examples/mcp_sdk_example.py` for a complete example.

### Standalone MCP Server for Testing

We've created a standalone MCP server that can be used for testing the MCP tools without Claude Desktop. This server exposes the MCP tools as HTTP endpoints:

```bash
python standalone_mcp_server.py
```

This will start a FastAPI server on port 8001 that you can use to test the MCP tools. You can customize the host and port using environment variables:

```bash
# Set custom host and port
export MCP_HOST=0.0.0.0
export MCP_PORT=8001
python standalone_mcp_server.py
```

You can then use the `test_mcp_tools.py` script to test all the tools:

```bash
python test_mcp_tools.py
```

The standalone server provides the same functionality as the MCP server used by Claude Desktop, but with a simple HTTP interface for testing purposes.

#### Testing Individual Tools

You can test individual tools using curl or any HTTP client:

```bash
# Test the retrieve_odoo_documentation tool with enhanced features
curl -X POST "http://127.0.0.1:8001/call_tool" \
  -H "Content-Type: application/json" \
  -d '{"tool": "retrieve_odoo_documentation", "params": {"query": "How to create a custom module in Odoo 18", "max_results": 5, "use_gemini": true, "use_online_search": true}}'

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

### Using the Odoo Module Generator

The Odoo Module Generator helps with creating Odoo 18 modules and code using a streamlined LangGraph workflow with DeepWiki integration for enhanced documentation lookups.

- **Analysis Phase**: Analyzes requirements and gathers relevant Odoo documentation
- **Planning Phase**: Creates a plan and tasks for implementing the requirements
- **First Human Validation Point**: Pauses for user feedback on the plan
- **Coding Phase**: Generates the code for the Odoo module using the code generator utility
- **Second Human Validation Point**: Pauses for user feedback on the code
- **Finalization Phase**: Finalizes the code based on feedback
- **Two-Stage Human Validation Workflow**: Interactive workflow with validation points after planning and coding
- **State Persistence**: Serialization and resumption of workflow state between validation steps
- **Fallback Models**: Integration with Google Gemini and Ollama for code generation
- **Code Generator Utility**: Comprehensive utility for generating Odoo 18 model classes, views, and other components
- **Odoo 18 Compliant Views**: Generate views following Odoo 18 guidelines (list view, single chatter tag)
- **Mail Thread Integration**: Support for mail.thread and mail.activity.mixin in generated models
- **Dynamic Model Discovery**: Generate models based on existing Odoo models

#### Odoo Module Generator Features

- **Streamlined Workflow**: Four-node LangGraph workflow for better performance and reduced complexity
- **DeepWiki Integration**: Enhanced documentation lookups using DeepWiki for Odoo and OWL frameworks
- **Visual Workflow Representation**: Interactive workflow visualization showing the current state
- **Model Provider Options**: Support for OpenAI, Anthropic, Google Gemini, and Ollama
- **Fully Asynchronous**: Built with async/await pattern for improved responsiveness
- **Two-section UI**: Workflow visualization and code generation in a single view
- **Direct File Downloads**: Download generated files individually or as a ZIP archive

#### Using the Odoo Module Generator

The Odoo Module Generator can be used in multiple ways:

#### 1. Using the MCP Tool in Claude Desktop

The easiest way to use the Odoo Module Generator is through the MCP tool in Claude Desktop:

```
/tool run_odoo_code_agent query="Create a customer feedback module for Odoo 18" use_gemini=true
```

This will generate an Odoo 18 module based on your query and return the results directly in Claude Desktop.

You can also save the generated files to disk:

```
/tool run_odoo_code_agent query="Create a customer feedback module for Odoo 18" use_gemini=true save_to_files=true output_dir="./generated_modules"
```

This will save the generated files to the specified directory (defaults to `./generated_modules` if not specified).

#### 2. Using the Standalone MCP Server

You can also use the Odoo Module Generator through the standalone MCP server:

```bash
# Start the standalone MCP server
python standalone_mcp_server.py

# In another terminal, call the tool using curl
curl -X POST "http://127.0.0.1:8001/call_tool" \
  -H "Content-Type: application/json" \
  -d '{"tool": "run_odoo_code_agent", "params": {"query": "Create a customer feedback module for Odoo 18", "use_gemini": true}}'
```

#### 3. Using the Test Script

For testing and development purposes, you can use the test script:

```bash
# Run the Odoo module generator with a query
python test_odoo_code_agent.py

# Run with Google Gemini as a fallback
python test_odoo_code_agent.py --gemini

# Run with Ollama as a fallback
python test_odoo_code_agent.py --ollama
```

#### 4. Using the Python API Directly

You can also use the Odoo Module Generator directly from your Python code:

```python
from src.odoo_code_agent.main import run_odoo_code_agent

# Use with Gemini integration
result = run_odoo_code_agent(
    query="Create an Odoo 18 module for customer feedback with ratings and comments",
    odoo_url="http://localhost:8069",
    odoo_db="llmdb18",
    odoo_username="admin",
    odoo_password="admin",
    use_gemini=True,  # Enable Gemini integration
    use_ollama=False
)

print(result)
```

### Streamlit User Interface

The Odoo Module Generator includes a dedicated Streamlit app that provides a user-friendly interface with enhanced documentation lookups via DeepWiki and visual workflow representation.

#### 1. Using the MCP Tool in Claude Desktop

To start the Streamlit app with the improved Odoo code generator:

```
/tool improved_generate_odoo_module module_name="customer_feedback" requirements="A module for managing customer feedback with ratings and comments"
```

Available parameters:

- `module_name`: Technical name for the module (snake_case)
- `requirements`: Detailed description of module requirements and functionality
- `documentation`: Optional list of documentation references to include in generation context
- `save_to_disk`: Whether to save generated files to disk (default: true)
- `output_dir`: Directory to save files if save_to_disk is true (default: ./generated_modules)
- `validation_iterations`: Number of validation and refinement loops to perform (default: 2)

#### 2. Using the Standalone MCP Server

The Streamlit app provides a user-friendly interface for generating Odoo modules. You can also use the API directly:

```bash
curl -X POST "http://127.0.0.1:8001/call_tool" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "improved_generate_odoo_module", 
    "params": {
      "module_name": "customer_feedback",
      "requirements": "A module for managing customer feedback with ratings and comments"
    }
  }'
```

#### 3. Using the Test Script

For testing and development purposes, you can use the test script:

```bash
# Features available in the Streamlit app
python -m pytest tests/
```

#### 4. Using the Python API Directly

The app provides several tabs for different aspects of module generation:

```python
import asyncio
from src.odoo_code_agent.workflow import run_workflow

async def generate_module():
    result = await run_workflow(
        query="Create a customer feedback module",
        model_provider="openai",  # or "anthropic", "gemini", "ollama"
        save_to_files=True,
        output_dir="./my_modules"
    )
    return result

result = asyncio.run(generate_module())
print(f"Module name: {result.get('module_name', '')}")
print(f"Generated files: {len(result.get('generated_files', []))}")
```

#### 5. Using the Streamlit App

The Streamlit app includes:

1. **Workflow Visualization**: Interactive visualization of the workflow state
2. **Code Generation**: Query input, results display, and file downloads

To launch the Streamlit app:

```bash
cd /Users/vinusoft85/workspace/odoo18_mcp_project
streamlit run app.py
```

This provides a user-friendly interface for generating Odoo modules with real-time workflow visualization.

#### Parameters

The Odoo Module Generator accepts the following parameters:

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `query` | string | The natural language query describing the module to create | (required) |
| `use_gemini` | boolean | Whether to use Google Gemini as a fallback | `false` |
| `use_ollama` | boolean | Whether to use Ollama as a fallback | `false` |
| `feedback` | string | Optional feedback to incorporate into the code generation | `null` |
| `wait_for_validation` | boolean | Whether to pause at human validation points | `false` |
| `current_phase` | string | Current phase for resuming the workflow | `null` |
| `state_dict` | object | Serialized state for workflow resumption | `null` |

#### Example Output

```
# Odoo Module Generator Results

## Query

Create a simple Odoo 18 module for managing customer feedback with ratings and comments

## Plan

This plan outlines the steps required to develop the 'customer_feedback' module in Odoo 18. It covers module structure creation, model definition, view implementation, security setup, and optional demo data addition.

## Tasks

1. Task 1: Create module structure
2. Task 2: Implement models
3. Task 3: Create views for the models
4. Task 4: Set up security and access rights
5. Task 5: Add demo data for testing

## Module Information

- **Module Name**: customer_feedback
- **Module Structure**:
  - __init__.py
  - __manifest__.py
  - models
  - views
  - security
  - static

## Generated Files (6)

### customer_feedback/__init__.py

```python
from . import models

```

### customer_feedback/__manifest__.py

```python
{
    'name': 'Customer Feedback',
    'version': '1.0',
    'category': 'Custom',
    'summary': 'Custom Odoo Module',
    'description': """
Customer Feedback
=============
This module provides custom functionality for Odoo 18.
""",
    'author': 'Your Company',
    'website': 'https://www.example.com',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
```

*...and 4 more files*

## Usage Instructions

To use the generated module:

1. Create a new directory with the module name in your Odoo addons path
2. Create the files as shown above
3. Install the module in Odoo

You can also provide feedback to refine the generated code by calling this tool again with the feedback parameter.
```

#### Human Validation Workflow

The Odoo Module Generator supports a workflow that allows you to provide feedback during the development process:

1. **First Validation Point (After Planning)**: The agent pauses after analyzing requirements and creating a plan, allowing you to review and provide feedback before code generation begins.

2. **Second Validation Point (After Coding)**: The agent pauses after generating the initial code, allowing you to review and provide feedback before finalizing the module.

To use the human validation workflow:

```
# Start the workflow and pause at the first validation point
/tool run_odoo_code_agent query="Create a customer feedback module" wait_for_validation=true

# Continue from the first validation point with feedback
/tool run_odoo_code_agent query="Create a customer feedback module" feedback="Please add a dashboard with key metrics" current_phase="human_feedback_1" wait_for_validation=true

# Continue from the second validation point with feedback
/tool run_odoo_code_agent query="Create a customer feedback module" feedback="Please add more comments to the code" current_phase="human_feedback_2" wait_for_validation=false
```

The Streamlit client provides a user-friendly interface for this workflow, with dedicated tabs for each phase and feedback forms at each validation point.

#### Iterative Development with Feedback

The Odoo Module Generator supports an iterative development process through the feedback parameter. After reviewing the initial code generation, you can provide feedback to refine the code:

```
/tool run_odoo_code_agent query="Create a customer feedback module" feedback="Please add a rating field with stars from 1 to 5 and make it required"
```

This allows you to iteratively improve the generated code based on your specific requirements.

#### Using Google Gemini for Enhanced Code Generation

For the best results, we recommend using Google Gemini as a fallback model. To enable this:

1. Get a Google Gemini API key from https://ai.google.dev/
2. Add your API key to the `.env` file:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.0-flash
   ```
3. Use the `model_provider="gemini"` parameter when calling the Odoo Module Generator

With Gemini enabled, the Odoo Module Generator can generate more sophisticated and context-aware code, with better analysis of requirements and more detailed implementation plans.

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
│   ├── odoo/               # Odoo integration
│   │   ├── client.py       # Odoo client
│   │   ├── schemas.py      # Data schemas
│   │   └── dynamic/        # Dynamic model handling
│   │       ├── model_discovery.py    # Model discovery
│   │       ├── field_analyzer.py     # Field analysis
│   │       ├── crud_generator.py     # CRUD operations
│   │       └── nlp_analyzer.py       # NLP-based analysis
│   ├── agents/             # Agent-based workflows
│   │   └── export_import/  # Export/Import agent
│   │       ├── main.py     # Main agent implementation
│   │       ├── state.py    # Agent state management
│   │       ├── nodes/      # LangGraph nodes
│   │       │   ├── export_nodes.py # Export workflow nodes
│   │       │   └── import_nodes.py # Import workflow nodes
│   │       └── utils/      # Utility functions
│   │           ├── csv_handler.py # CSV processing
│   │           └── field_mapper.py # Field mapping
│   ├── odoo_code_agent/    # Odoo code generation agent
│   │   ├── main.py         # Main agent implementation
│   │   ├── state.py        # Agent state management
│   │   ├── nodes/          # LangGraph nodes
│   │   │   ├── analysis_nodes.py # Analysis workflow nodes
│   │   │   ├── planning_nodes.py # Planning workflow nodes
│   │   │   ├── feedback_nodes.py # Feedback workflow nodes
│   │   │   └── coding_nodes.py   # Code generation nodes
│   │   └── utils/          # Utility functions
│   │       ├── code_generator.py # Code generation utilities
│   │       ├── documentation_helper.py # Documentation utilities
│   │       ├── fallback_models.py # Fallback model integration
│   │       ├── file_saver.py # File saving utilities
│   │       ├── gemini_client.py # Google Gemini API client
│   │       ├── module_structure.py # Module structure utilities
│   │       └── odoo_connector.py # Odoo connection utilities
│   └── odoo_docs_rag/      # Odoo documentation RAG
│       ├── docs_processor.py # Documentation processing
│       ├── docs_retriever.py # Documentation retrieval
│       ├── embedding_engine.py # Embedding engine
│       └── utils.py        # Utility functions
├── scripts/                # Utility scripts
│   └── dynamic_data_tool.py # Export/Import CLI tool
├── tests/                  # Test suite
│   ├── test_export_import_agent.py # Export/import agent tests
│   ├── test_mcp_server_consolidated.py # MCP server tests
│   ├── test_odoo_code_agent_consolidated.py # Odoo code agent tests
│   └── test_odoo_code_agent_utils_consolidated.py # Odoo code agent utilities tests
├── odoo_docs/              # Odoo documentation repository
├── odoo_docs_index/        # Odoo documentation index
│   ├── documents.pkl       # Processed documents
│   ├── faiss_index.bin       # FAISS vector index
│   └── embeddings.db       # Embeddings database
├── tmp/                    # Temporary files directory
├── mcp_server.py           # MCP server implementation
├── standalone_mcp_server.py # Standalone MCP server
├── query_parser.py         # Natural language query parser
├── relationship_handler.py # Model relationship handler
├── update_claude_config.sh # Claude Desktop config updater
├── .env.example            # Environment variables example
├── .dockerignore           # Docker ignore file
├── pyproject.toml          # Project configuration
├── setup.py                # Setup script
├── requirements.txt        # Project dependencies
├── README.md               # Main documentation
├── PLANNING.md             # Project planning
└── TASK.md                 # Task tracking
```

### Running Tests

```bash
python tests/test_mcp_server_consolidated.py --all         # Comprehensive MCP server and tools tests
python tests/test_odoo_code_agent_consolidated.py --all    # Consolidated Odoo code agent tests
python tests/test_odoo_code_agent_utils_consolidated.py --all  # Consolidated Odoo code agent utilities tests
python tests/test_export_import_agent.py                   # Export/import agent tests
```

#### Comprehensive Testing

We've created a comprehensive test suite with four consolidated test files that cover all aspects of the project:

1. **test_mcp_server_consolidated.py**: Tests all MCP server tools and functionality, including:
   - Server health and tool listing
   - Basic CRUD operations (search, create, update, delete)
   - Advanced search and documentation retrieval
   - Field analysis and validation
   - Export/import functionality for single and related models
   - Odoo code agent functionality
   - Mermaid diagram generation

2. **test_odoo_code_agent_consolidated.py**: Tests the Odoo Code Agent, including:
   - Basic functionality
   - Feedback handling
   - Testing with different LLM backends (Gemini, Ollama)
   - Complete workflow testing

3. **test_odoo_code_agent_utils_consolidated.py**: Tests the Odoo Code Agent utilities, including:
   - Documentation helper
   - Odoo connector
   - Human validation workflow
   - File handling
   - Module structure generation

4. **test_export_import_agent.py**: Tests the langgraph agent flow for exporting and importing Odoo records, including:
   - Export flow
   - Import flow
   - Export-import cycle
   - Related models export-import

To run the comprehensive MCP server tests:

```bash
python tests/test_mcp_server_consolidated.py --all
```

This will test all MCP server tools and report any issues. The test script is designed to be robust and handle various error conditions, making it ideal for validating the MCP server functionality.

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
| `export_records_to_csv` | Export partners to CSV | CSV file created | CSV file created with records | ✅ Passed |
| `import_records_from_csv` | Import partners from CSV | Records imported | Records imported successfully | ✅ Passed |
| `retrieve_odoo_documentation` | Query Odoo documentation | Relevant documentation | Relevant documentation sections | ✅ Passed |

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

#### Comprehensive Test Output

The comprehensive test script (`comprehensive_test.py`) provides detailed output for each test case:

```
Running comprehensive tests for MCP server...

=== Testing search_records ===
Test case 1: {'model_name': 'res.partner', 'query': 'company'}
Result: # Search Results for 'company' in res.partner

| ID | Name | Email | Phone |
|----| ---- | ---- | ---- |
| 44 | IN Company | info@company.inexample.com | +91 81234 56789 |
| 67 | Library Demo Company ...
✅ Test passed!

=== Testing create_record ===
Test case: {'model_name': 'res.partner', 'values': {'name': 'Test Partner 1746188702', 'email': 'test@example.com', 'phone': '+1 555-123-4567'}}
Result: Record created successfully with ID: 100
✅ Test passed!

=== Testing export_records_to_csv ===
Running command: /Users/vinusoft85/workspace/odoo18_mcp_project/.venv/bin/python scripts/dynamic_data_tool.py export --model res.partner --output ./tmp/test_export.csv
Return code: 0
Output: Exported 61 records to ./tmp/test_export.csv
✅ Test passed!

All tests completed!
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

2. **Enhanced Semantic Search**: Using the powerful all-mpnet-base-v2 model from sentence-transformers and FAISS vector database, the tool provides advanced semantic search capabilities for finding relevant documentation based on natural language queries.

3. **Intelligent Chunking and Processing**: The documentation is processed using intelligent chunking strategies that respect document structure, maintain context within sections, and ensure proper overlap between chunks. The tool handles Markdown, HTML, and RST files with specialized processing for each format.

4. **Comprehensive Metadata Extraction**: The tool extracts detailed metadata from file paths and content, including section, subsection, country information, and titles, providing better context for search results.

5. **Query Preprocessing and Enhancement**: Queries are preprocessed to improve search results, with specialized handling for tax and localization queries. The tool implements keyword replacement for better matching and adds context for version-specific queries.

6. **Keyword Boosting**: Documents containing relevant keywords are boosted in the search results, ensuring that the most relevant information appears at the top.

7. **Enhanced Result Formatting**: Search results include detailed source information with section and category details, related search suggestions, and helpful guidance when no results are found.

8. **MCP Integration**: The RAG tool is fully integrated with the MCP server, providing a new `retrieve_odoo_documentation` tool and `odoo_documentation_prompt` for Claude Desktop.

9. **Fallback Mechanisms**: When specific queries don't yield results, the tool automatically falls back to more general queries to ensure users always get helpful information.

10. **Persistent Storage**: The tool uses persistent storage for embeddings and processed documentation, making subsequent queries faster.

11. **Automatic Updates**: The tool can update the documentation repository to ensure the latest information is available.

12. **Comprehensive Error Handling**: Robust error handling ensures the tool works reliably even when dependencies are missing or the documentation repository is unavailable.

13. **Dependency Management**: The tool handles dependencies gracefully, with proper error messages when required packages are missing.

14. **Google Gemini Integration**: The tool integrates with Google's Gemini LLM to summarize and enhance search results, providing more coherent and comprehensive responses.

15. **Online Search Capability**: Using the Brave Search API, the tool can supplement local documentation with relevant information from the web, providing a more complete answer.

16. **Combined Results**: The enhanced query functionality combines local documentation, online search results, and Gemini summarization to provide the most comprehensive and useful responses.

17. **Test Scripts**: Comprehensive test scripts (`test_enhanced_rag.py`, `test_odoo_docs_rag.py`, and `test_specific_queries.py`) are provided to verify the functionality works correctly with various query types, including specialized tests for tax and localization queries.

### Example Usage

#### Using the MCP tool in Claude Desktop:

```
/tool retrieve_odoo_documentation query="How to create a custom module in Odoo 18" max_results=5 use_gemini=true use_online_search=true
```

This will return relevant sections from the Odoo 18 documentation about creating custom modules, combined with online search results and summarized by Gemini LLM for a more comprehensive response.

#### Using the Standalone MCP Server:

```bash
curl -X POST "http://127.0.0.1:8001/call_tool" \
  -H "Content-Type: application/json" \
  -d '{"tool": "retrieve_odoo_documentation", "params": {"query": "How to create a custom module in Odoo 18", "max_results": 5, "use_gemini": true, "use_online_search": true}}'
```

#### Testing the Enhanced RAG Tool

The enhanced RAG tool can be tested using the `test_enhanced_rag.py` script, which tests all aspects of the tool:

```bash
python tests/test_enhanced_rag.py --all
```

This will test the basic retrieval functionality, online search integration, Gemini summarization, enhanced query with all components, and MCP tool integration.

#### Configuration

To use the enhanced RAG tool with all features, you need to set up the following environment variables in your `.env` file:

```
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
BRAVE_API_KEY=your_brave_api_key_here
```

The tool is designed to be resilient and will work with whatever components are available. If Gemini or Brave Search is not available, it will fall back to using only the available components.

#### Customizing the RAG Tool

The quality of the RAG tool's responses depends on the documentation available in the index. The tool currently indexes 32 documents from the Odoo 18 documentation repository. To improve the quality of responses, you can add more documentation files to the `odoo_docs` directory and rebuild the index by setting `force_rebuild=True` in the `OdooDocsRetriever` constructor.

```python
odoo_docs_retriever_instance = OdooDocsRetriever(
    docs_dir=docs_dir,
    index_dir=index_dir,
    force_rebuild=True,  # Force rebuilding the index
    use_gemini=True,     # Enable Gemini integration
    use_online_search=True  # Enable online search
)
```

## Recent Improvements and Fixes

### Odoo Documentation RAG Improvements

We've made significant improvements to the Odoo documentation RAG tool to enhance its ability to find relevant information, particularly for tax and localization queries:

1. **Enhanced Document Processing**:
   - Improved file filtering to focus on relevant documentation files
   - Added better handling of RST files (reStructuredText) which are common in Odoo documentation
   - Enhanced text cleaning to remove irrelevant characters and improve search quality

2. **Improved Chunking Strategy**:
   - Implemented a more intelligent chunking algorithm that respects document structure
   - Added section-based chunking to maintain context within sections
   - Improved overlap handling to avoid missing information at chunk boundaries
   - Added minimum content length filtering to avoid tiny, irrelevant chunks

3. **Enhanced Metadata Extraction**:
   - Added more detailed metadata from file paths
   - Extracted section, subsection, and country information for better context
   - Added title extraction from filenames

4. **Improved Query Processing**:
   - Added query preprocessing to handle variations in terminology
   - Implemented keyword replacement for better matching
   - Added context for version-specific queries
   - Implemented keyword boosting for relevant documents

5. **Better Results Formatting**:
   - Enhanced result presentation with more context
   - Added source information with section and category details
   - Included related search suggestions
   - Added helpful guidance when no results are found

6. **MCP Server Integration**:
   - Updated the MCP server to use our improved implementation
   - Added query preprocessing specific to tax and localization queries
   - Implemented fallback to more general queries when specific queries fail
   - Added better logging for debugging

These improvements significantly enhance the RAG system's ability to find relevant information about Odoo taxes and Indian localization, which were the specific areas mentioned as having issues.

### Code Generator Utility

We've implemented a comprehensive code generator utility for the Odoo code agent:

1. **Model Class Generation**: The utility can generate Odoo model classes with proper field definitions, inheritance, and support for mail.thread and mail.activity.mixin.

2. **Odoo 18 Compliant Views**: The utility generates views following Odoo 18 guidelines, including:
   - Using list view instead of tree view
   - Implementing the single `<chatter/>` tag instead of separate message and activity fields
   - Removing deprecated attributes like string in form view

3. **Complete Module Generation**: The utility can generate all files needed for an Odoo module, including:
   - Model classes
   - Views (form, list, search)
   - Security access rights
   - Action windows and menu items
   - Controllers with routes
   - Manifest file

4. **Integration with Fallback Models**: The utility integrates with the fallback models system to use AI for generating more intelligent and context-aware code when available.

5. **Dynamic Model Discovery**: The utility can generate models based on existing Odoo models, using the model discovery system to get field information and other metadata.

6. **Test Suite**: A comprehensive test suite ensures the code generator works correctly and produces valid Odoo 18 code.

7. **Integration with Odoo Code Agent**: The code generator is fully integrated with the Odoo code agent, allowing it to generate code based on natural language descriptions.

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

### Streamlit Client Implementation

We've implemented a comprehensive Streamlit client for interacting with the Odoo 18 MCP tools:

1. **Modular Architecture**:
   - Created a modular architecture with separate pages for different functionality
   - Implemented reusable components for chat, file viewing, and feedback forms
   - Developed utility functions for MCP connection and session state management
   - Added responsive design that works on different screen sizes

2. **User-Friendly Interface**:
   - Implemented a navigation sidebar with page routing
   - Added custom styling and theming for better user experience
   - Created progress indicators for long-running operations
   - Implemented form validation and error handling
   - Added results formatting and display for better readability

3. **Asynchronous Polling Mechanism**:
   - Implemented an asynchronous polling mechanism for long-running operations
   - Added tool-specific polling configurations based on operation complexity
   - Created request tracking with unique IDs for better reliability
   - Implemented fallback messages for timeout situations
   - Added error recovery for failed requests

4. **MCP Server Integration**:
   - Created a robust MCP connector for communicating with the MCP server
   - Implemented tool-specific convenience methods for common operations
   - Added health check functionality to verify server status
   - Created detailed logging for debugging
   - Implemented intelligent query handling with fallback mechanisms

5. **Comprehensive Features**:
   - Code agent interface for Odoo module generation
   - Export/import interface for data operations
   - Documentation search for Odoo documentation
   - Advanced search for natural language queries
   - Chat interface for conversational interaction
   - Model documentation for detailed model information
   - Field validation for checking field values

6. **Testing and Documentation**:
   - Created comprehensive tests for the Streamlit client
   - Added detailed documentation for installation and usage
   - Implemented example workflows for common operations
   - Created troubleshooting guides for common issues

### Dependency Management Improvements

1. **Python version compatibility**: Updated the project to require Python 3.10+ for compatibility with the MCP SDK.

2. **PyTorch version constraints**: Added version constraints for PyTorch to ensure compatibility with macOS.

3. **NumPy version constraints**: Added version constraints for NumPy to ensure compatibility with FAISS and other dependencies.

4. **Standalone MCP server**: Created a standalone MCP server for testing tools without Claude Desktop.

5. **Improved error handling**: Enhanced error handling for dependency issues with clear error messages.

6. **Documentation updates**: Updated documentation with dependency management best practices.

## Troubleshooting

### Docker Container Issues

### Enhanced Dynamic Import Features

The import functionality has been significantly enhanced to work dynamically with any Odoo model:

- **Dynamic Unique Field Detection**: Automatically identifies potential unique fields for any model based on constraints and common patterns
- **Enhanced Many2One Handling**: Uses name_search for better record matching during import
- **Better Many2Many Support**: Handles both IDs and names in many2many fields with proper command format conversion
- **Date Field Parsing**: Supports multiple date formats in import data
- **Special Case Handling**: Includes model-specific handling for account.move (reset to draft) and product variants
- **Improved Reporting**: Provides enhanced feedback on import operations with counts for created, updated, skipped, and error records
- **Create/Update Control**: Offers fine-grained control over whether to create new records or update existing ones
- **Intelligent Record Matching**: Uses a multi-strategy approach to match existing records using IDs, external IDs, and unique fields

#### Example Usage

```python
# Import records with enhanced functionality
result = import_records(
    input_path="./exports/companies.csv",
    model_name="res.partner",
    create_if_not_exists=True,  # Create new records if they don't exist
    update_if_exists=True,      # Update existing records
    match_field="id",           # Field to use for matching existing records
    skip_invalid=True,          # Skip invalid values for selection fields
    reset_to_draft=False,       # Reset records to draft before updating (for account.move)
    skip_readonly_fields=True   # Skip readonly fields for posted records
)
- **Issue**: Docker containers fail to start with error: `exec: "/app/entrypoint.sh": stat /app/entrypoint.sh: no such file or directory`
- **Solution**: This is caused by a syntax issue in the entrypoint.sh script. The project includes a properly formatted entrypoint.sh file that should be copied to the container during the build process. If you encounter this issue, make sure the entrypoint.sh file exists in your project root and has the correct permissions:

```bash
# Check if entrypoint.sh exists
ls -la entrypoint.sh

# If it doesn't exist, create it with the correct content
cat > entrypoint.sh << 'EOF'
#!/bin/sh

# Create required directories with proper permissions
mkdir -p /app/logs /app/data /app/exports /app/tmp
chown -R mcp:mcp /app/logs /app/data /app/exports /app/tmp

# Switch to non-root user
exec su -s /bin/sh mcp -c "if [ \"\$1\" = \"standalone\" ]; then exec python standalone_mcp_server.py; elif [ \"\$1\" = \"test\" ]; then if [ \"\$2\" = \"functions\" ]; then exec python test_mcp_functions.py; elif [ \"\$2\" = \"tools\" ]; then exec python test_mcp_tools.py; elif [ \"\$2\" = \"all\" ]; then python test_mcp_functions.py && python test_mcp_tools.py; else echo \"Unknown test type: \$2\"; exit 1; fi; else exec python main.py \$@; fi"
EOF

# Set the correct permissions
chmod +x entrypoint.sh

# Rebuild and restart the Docker containers
docker-compose down
docker-compose build
docker-compose up -d
```

- **Issue**: ModuleNotFoundError: No module named 'src' in Docker container
- **Solution**: This occurs when the src directory is not properly copied to the final stage in the Dockerfile. Make sure your Dockerfile includes the line `COPY src ./src` after copying the other application files:

```dockerfile
# Copy the rest of the application
COPY main.py mcp_server.py standalone_mcp_server.py ./
COPY test_mcp_functions.py test_mcp_tools.py ./
COPY .env.example ./.env.example
COPY entrypoint.sh /app/entrypoint.sh
COPY src ./src
```

- **Issue**: Standalone server not accessible on expected port
- **Solution**: The standalone server now explicitly uses port 8001 by default. You can customize this using environment variables:

```bash
# Set custom host and port for standalone server
export MCP_HOST=0.0.0.0
export MCP_PORT=8001
python standalone_mcp_server.py
```

- **Issue**: Docker container fails with permission issues when writing to directories
- **Solution**: Make sure all required directories exist and have the correct permissions:

```bash
# Create required directories with correct permissions
mkdir -p ./exports ./tmp ./generated_modules
chmod 777 ./exports ./tmp ./generated_modules
```

### MCP Server Testing

If you're having issues with the MCP server, you can use the comprehensive test script to diagnose problems:

#### Testing MCP Server Functions Directly

```bash
python comprehensive_test.py
```

This will test all MCP server functions directly, without requiring the MCP server to be running. If any tests fail, the script will provide detailed error information.

#### Common MCP Server Issues

- **Issue**: MCP Inspector "Connect" button doesn't work
- **Solution**: This is likely due to permission issues with the `uv` command. Instead of using the Connect button, start the MCP server directly with `mcp dev mcp_server.py` and test it using the provided test scripts.

- **Issue**: Export/Import operations fail with field validation errors
- **Solution**: Some fields like `peppol_eas` and `autopost_bills` have strict validation requirements. Use a simplified CSV format with only essential fields for import operations.

- **Issue**: MCP server starts but tools don't work
- **Solution**: Run the comprehensive test script to identify which tools are failing and why. The script provides detailed error information for each tool.

- **Issue**: MCP server shows "Error in /stdio route: Error: spawn /usr/local/Cellar/uv EACCES"
- **Solution**: This is a permission issue with the `uv` command. Make sure the `uv` command is executable and in your PATH. You can also try running the MCP server directly with `python mcp_server.py` instead of using the MCP Inspector.

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

## Export/Import Tools

The project includes powerful tools for exporting and importing data from Odoo models:

- Export data from any Odoo model to CSV files
- Import data from CSV files into any Odoo model
- Export related models (parent-child relationships) to a single CSV file
- Import related models from a single CSV file
- Get information about models and their fields

### Command-Line Tool

Use `scripts/dynamic_data_tool.py` for dynamic, multi-model export and import:

```bash
# Export any model:
python3 scripts/dynamic_data_tool.py export \
  --model account.move \
  --output ./tmp/export.csv

# Import any model:
python3 scripts/dynamic_data_tool.py import \
  --model account.move \
  --input ./tmp/import.csv \
  --defaults "{'move_type': 'out_invoice'}" \
  --force

# Export related models (e.g., invoices and lines):
python3 scripts/dynamic_data_tool.py export-rel \
  --parent-model account.move \
  --child-model account.move.line \
  --relation-field move_id \
  --output ./tmp/export-rel.csv \
  --domain "[('move_type', '=', 'out_invoice')]"

# Import related models:
python3 scripts/dynamic_data_tool.py import-rel \
  --parent-model account.move \
  --child-model account.move.line \
  --relation-field move_id \
  --parent-fields name,date,move_type,partner_id \
  --child-fields account_id,product_id,quantity,price_unit \
  --input ./tmp/export-rel.csv \
  --reset-to-draft \
  --skip-readonly-fields

# Get model information:
python3 scripts/dynamic_data_tool.py info \
  --model res.partner \
  --required-only
```

### MCP Tools Integration

The export/import tools are also integrated with the MCP server, providing the following tools:

```
/tool export_records_to_csv model_name=res.partner export_path=./tmp/partners.csv

/tool import_records_from_csv model_name=res.partner input_path=./tmp/partners.csv

/tool export_related_records_to_csv parent_model=account.move child_model=account.move.line relation_field=move_id export_path=./tmp/invoices_with_lines.csv

/tool import_related_records_from_csv parent_model=account.move child_model=account.move.line relation_field=move_id input_path=./tmp/invoices_with_lines.csv
```

For detailed documentation, see [Export/Import Tools Documentation](docs/EXPORT_IMPORT_TOOLS.md).

The tool now includes improved CSV handling with better error reporting and support for:
- Move type filtering for invoices (`--move-type` parameter)
- Reset to draft functionality for posted invoices (`--reset-to-draft` flag)
- Skipping readonly fields for invoice updates (`--skip-readonly-fields` flag)
- Improved error handling for field validation issues

**Deprecated scripts**: `scripts/clean_import_csv.py`, `scripts/dynamic_export_import.py`, `direct_export_import.py`. Use `scripts/dynamic_data_tool.py` exclusively.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Streamlit Client

The project includes a Streamlit client that provides a user-friendly interface for interacting with the Odoo 18 MCP tools. The Streamlit client offers a comprehensive set of features and a robust architecture for a seamless user experience.

### Features

- **Code Agent Interface**: Generate Odoo 18 modules using the code agent with a user-friendly interface
- **Human Feedback Loop**: Provide feedback on the generated code and plans
- **Export/Import Interface**: Export and import records from Odoo models with a visual interface
- **Documentation Search**: Search for information in the Odoo 18 documentation
- **Chat Interface**: Chat with the Odoo 18 MCP server using natural language
- **File Viewer**: View and download generated code files
- **CSV Viewer**: View and download exported CSV files
- **Advanced Search**: Perform advanced natural language searches across multiple Odoo models
- **Model Documentation**: Get detailed information about Odoo models and their fields
- **Field Validation**: Validate field values against Odoo field requirements
- **Responsive Design**: User-friendly interface that works on different screen sizes
- **Progress Indicators**: Visual feedback during long-running operations
- **Error Handling**: Comprehensive error handling with helpful messages

### Installation

1. Install the Streamlit client dependencies:

```bash
pip install -r requirements-streamlit.txt
```

2. Start the Streamlit client:

```bash
streamlit run app.py
```

3. Open your browser and navigate to http://localhost:8501

### Usage

The Streamlit client provides a user-friendly interface for interacting with the Odoo 18 MCP tools:

1. **Code Agent**: Generate Odoo 18 modules using the code agent
   - Specify your requirements for the module
   - Review the plan and provide feedback
   - Review the generated code and provide feedback
   - Download the generated files
   - Choose between Gemini and Ollama for code generation
   - Save generated files to disk

2. **Export/Import**: Export and import records from Odoo models
   - Export records from any Odoo model to CSV files
   - Import records from CSV files into any Odoo model
   - Export and import related records (parent-child relationships)
   - Filter records using domain expressions
   - Select specific fields to export
   - Map CSV fields to Odoo fields during import
   - View and download exported CSV files

3. **Documentation**: Search for information in the Odoo 18 documentation
   - Search for information using natural language queries
   - View relevant documentation sections with source information
   - Get context-aware search results
   - See related search suggestions
   - Access comprehensive documentation on Odoo features

4. **Advanced**: Access advanced Odoo 18 tools
   - Get model documentation and field information
   - Validate field values against Odoo field requirements
   - Perform advanced natural language searches across multiple models
   - View field importance and grouping
   - Get record templates for creating new records

5. **Chat**: Chat with the Odoo 18 MCP server using natural language
   - Ask questions about Odoo 18
   - Request information about models and fields
   - Get help with Odoo 18 development
   - Perform searches using natural language
   - Access documentation through conversational interface

### Testing the MCP Server Connection

Before starting the Streamlit client, you can test the MCP server connection using the consolidated test script:

```bash
# Test if the MCP server is running
python tests/test_mcp_server_consolidated.py --health

# List available tools
python tests/test_mcp_server_consolidated.py --tools

# Test the search_records tool
python tests/test_mcp_server_consolidated.py --search

# Test the advanced_search tool
python tests/test_mcp_server_consolidated.py --advanced

# Test the retrieve_odoo_documentation tool
python tests/test_mcp_server_consolidated.py --docs

# Test the run_odoo_code_agent_tool tool
python tests/test_mcp_server_consolidated.py --code-agent

# Run all tests
python tests/test_mcp_server_consolidated.py --all
```

This script helps verify that the MCP server is running correctly and that all the required tools are available and functioning properly before launching the Streamlit client.

### Architecture

The Streamlit client is built with a modular architecture designed for extensibility and maintainability:

#### Core Components

- **Main App (`main.py`)**: The main entry point for the Streamlit app, handling page routing and navigation
- **Pages Directory**: Separate modules for different functionality:
  - `code_agent.py`: Interface for the Odoo code agent
  - `documentation.py`: Interface for Odoo documentation search
  - `export_import.py`: Interface for data export and import operations
- **Components Directory**: Reusable UI components:
  - `chat.py`: Chat interface component for human interaction
  - `file_viewer.py`: Component for viewing and downloading files
- **Utils Directory**: Utility functions and classes:
  - `mcp_connector.py`: Connector for MCP server communication
  - `session_state.py`: State management for the Streamlit app

#### Session State Management

The client uses a comprehensive session state management system to maintain state across page navigation:

1. **Global State**: Maintains global application state like current page and MCP server URL
2. **Page-Specific State**: Each page has its own state management for form values and results
3. **Chat History**: Maintains chat history for the chat interface
4. **Results Caching**: Caches results to avoid unnecessary server calls
5. **Form State**: Preserves form values when navigating between pages

#### MCP Connector

The MCP connector provides a robust interface for communicating with the MCP server:

1. **Connection Types**: Supports both HTTP and STDIO connection types
2. **Tool Discovery**: Automatically discovers available tools on the MCP server
3. **Tool-Specific Methods**: Provides convenience methods for common tools
4. **Error Handling**: Comprehensive error handling with detailed logging
5. **Health Check**: Verifies that the MCP server is running
6. **Asynchronous Support**: Supports asynchronous tool calls

### Asynchronous Polling Mechanism

The Streamlit client uses a sophisticated asynchronous polling mechanism to handle long-running operations:

1. **Initial Request**: The client sends a request to the MCP server and receives an initial response
2. **Request Tracking**: Each request is assigned a unique ID for tracking
3. **Intelligent Polling**: If the initial response doesn't contain data, the client polls the server at regular intervals
4. **Tool-Specific Configuration**: Different tools have different polling configurations based on their complexity:
   - Advanced search: 20 polling attempts with 3-second intervals
   - Code agent: 30 polling attempts with 3-second intervals
   - Documentation retrieval: 10 polling attempts with 2-second intervals
   - Export/import operations: 15 polling attempts with 2-second intervals
5. **Intelligent Timeout Calculation**: Timeout values are automatically calculated based on query complexity:
   - Simple queries: 60 seconds
   - Medium complexity: 120-180 seconds
   - High complexity: 180-300 seconds
6. **Optimized Polling Intervals**: Polling intervals are optimized for different tool types:
   - Advanced search: 3-second intervals (more complex queries)
   - Code agent: 3-second intervals (complex code generation)
   - Documentation retrieval: 2-second intervals (medium complexity)
   - Export/import operations: 2-second intervals (medium complexity)
7. **Progress Indicators**: While polling, the client shows progress indicators to provide feedback to the user
8. **Enhanced Timeout Handling**: If the server doesn't respond within a specified timeout, the client shows a detailed error message with troubleshooting suggestions
9. **Improved Fallback Messages**: If polling completes without receiving data, the client shows a helpful message with specific suggestions based on the tool type
10. **Enhanced Error Recovery**: The client can recover from network errors, timeouts, and other issues to continue polling
11. **Detailed Logging**: Comprehensive logging for debugging polling issues

This mechanism ensures that the client can handle operations that take a long time to complete, such as complex searches or code generation, while providing a responsive user experience.

### Server-Side Query Processing

The Streamlit client relies on the MCP server's advanced search capabilities to process natural language queries:

1. **Natural Language Processing**: The MCP server uses advanced NLP to understand and process queries
2. **Query Classification**: The client attempts to classify queries as search or documentation queries
3. **Dynamic Model Detection**: The server automatically identifies the relevant Odoo models based on the query
4. **Relationship Handling**: The server handles complex relationships between models (many2one, one2many)
5. **Field Mapping**: The server maps natural language terms to Odoo field names
6. **Query Execution**: The server executes the query against the Odoo database
7. **Response Formatting**: The server formats the response in a user-friendly way
8. **Fallback Mechanisms**: If one approach fails, the client tries alternative approaches:
   - If advanced search fails, try documentation retrieval
   - If both fail, try advanced search with a longer timeout
   - If all fail, show a helpful error message

This approach leverages the full power of the MCP server's capabilities, ensuring that queries are processed correctly and efficiently. The client focuses on its core responsibility: providing a user-friendly interface and handling the communication with the server.

### Requirements

- Streamlit 1.30.0 or higher
- Pandas 1.5.0 or higher
- Requests 2.31.0 or higher
- Python-dotenv 1.0.0 or higher
- Pydantic 2.0.0 or higher

### Recent Improvements

#### Enhanced Asynchronous Polling

We've significantly improved the asynchronous polling mechanism to better handle long-running operations:

1. **Tool-Specific Configurations**: Different tools now have customized polling configurations based on their complexity
2. **Request Tracking**: Each request is now assigned a unique ID for better tracking
3. **Improved Progress Indicators**: More detailed progress indicators during polling
4. **Intelligent Timeout Calculation**: Timeout values are automatically calculated based on query complexity
5. **Optimized Polling Intervals**: Polling intervals are optimized for different tool types
6. **Enhanced Timeout Handling**: More detailed error messages with troubleshooting suggestions
7. **Improved Fallback Messages**: Tool-specific helpful messages when polling completes without data
8. **Enhanced Error Recovery**: Better recovery from network errors, timeouts, and other issues
9. **Detailed Logging**: Comprehensive logging for debugging polling issues

#### Improved Query Processing

The client now uses a more sophisticated approach to query processing:

1. **Query Classification**: Attempts to classify queries as search or documentation queries
2. **Multiple Approaches**: Tries different approaches if the first one fails
3. **Longer Timeouts for Complex Queries**: Automatically uses longer timeouts for complex queries
4. **Helpful Error Messages**: More detailed error messages when queries fail
5. **Fallback Mechanisms**: Falls back to alternative approaches when primary approach fails

## Acknowledgements

- Odoo Community
- Python Community
- MCP SDK Team
- Streamlit Team

## Simple Odoo Code Agent

The Simple Odoo Code Agent is a streamlined version of the Odoo module generator, designed for efficient and focused code generation. It provides a simpler interface for generating Odoo modules while maintaining core functionality.

### Key Features

1. **Module Generation**
   - Generate complete Odoo modules with models, views, and security
   - Follows Odoo 18 best practices and conventions
   - Supports custom fields and relationships
   - Automatic model inheritance and relationships

2. **AI Integration**
   - Gemini LLM integration for code generation
   - Natural language query parsing
   - Context-aware code suggestions
   - Iterative code refinement

3. **Code Quality**
   - Proper docstrings and comments
   - Type hints and Pydantic models
   - Secure field definitions
   - Comprehensive test file generation

### Usage Example

```python
import asyncio
from src.simple_odoo_code_agent.code_generator import generate_module

# Generate a module with a query
await generate_module(
    query="Create a customer feedback module",
    use_gemini=True,
    use_ollama=False
)
```

### Feedback System

The Simple Odoo Code Agent supports an iterative development process through the feedback parameter. After reviewing the initial code generation, you can provide feedback to refine the code:

```
/tool generate_module query="Create a customer feedback module" feedback="Please add a rating field with stars from 1 to 5 and make it required"
```

### Module Structure

Generated modules follow a standard structure:

```
module_name/
├── __init__.py
├── __manifest__.py
├── models/
│   └── models.py
├── views/
│   └── views.xml
└── security/
    ├── ir.model.access.csv
    └── security.xml
```

The Odoo 18 Code Agent is a specialized agent that helps with generating Odoo 18 modules and code. It follows a structured workflow:

1. **Analysis Phase**: Analyzes the requirements and gathers relevant Odoo documentation
2. **Planning Phase**: Creates a plan and tasks for implementing the requirements
3. **Human Feedback Loop**: Gets feedback from the user on the plan
4. **Coding Phase**: Generates the code for the Odoo module
5. **Human Feedback Loop**: Gets feedback from the user on the code
6. **Finalization Phase**: Finalizes the code based on feedback

The agent can use Google Gemini or Ollama as fallback models if needed.

### Code Agent Graph Visualization

The Odoo Code Agent workflow can be visualized using LangGraph's graph visualization capabilities. This provides a clear understanding of the agent's workflow and how the different phases and steps are connected.

#### Dependencies for Graph Visualization

To use the graph visualization features, you need to install the following dependencies:

```bash
# Install graph visualization dependencies
pip install ipython>=8.12.0 graphviz>=0.20.1 pygraphviz>=1.10 mermaid-magic>=0.1.0
```

On macOS, you may need to install graphviz using Homebrew:

```bash
brew install graphviz
```

On Ubuntu/Debian, you can install graphviz using apt:

```bash
sudo apt-get install graphviz libgraphviz-dev pkg-config
```

#### Visualizing the Graph in Jupyter Notebook

You can visualize the Odoo Code Agent graph in a Jupyter notebook using the following code:

```python
from IPython.display import Image, display
from langgraph.graph import StateGraph, END
from src.odoo_code_agent.state import OdooCodeAgentState, AgentPhase

# Create the graph
graph = create_code_agent_graph()  # Function that creates the graph structure

# Display the graph
display(Image(graph.get_graph().draw_mermaid_png()))
```

The project includes a Jupyter notebook (`code_agent_graph_demo.ipynb`) that demonstrates how to create and display the graph.

#### Visualizing the Graph in Streamlit

The Streamlit client includes a dedicated page for visualizing the Odoo Code Agent graph. You can access it by clicking on the "Code Agent Graph" button in the navigation sidebar.

The graph visualization page includes:
- A visual representation of the agent workflow
- A detailed explanation of each phase and step
- Information about the current state of the agent

This visualization helps you understand how the Odoo Code Agent works and how the different phases and steps are connected.

### Google Gemini Integration

The Odoo Code Agent includes direct integration with Google's Gemini API for improved code generation:

1. **Environment Variables**: Set up your Gemini API key and model in the `.env` file:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_MODEL=gemini-2.0-flash
   ```

2. **Gemini Client**: The agent uses a dedicated Gemini client module for API calls

3. **Enhanced Analysis**: Gemini provides more detailed analysis of requirements

4. **Better Planning**: Gemini creates more comprehensive implementation plans

5. **Improved Code Generation**: Gemini generates higher quality Odoo module code

6. **Feedback Processing**: Gemini can process user feedback to improve the generated code

7. **Fallback Mechanisms**: The agent includes robust fallback mechanisms for when Gemini is not available

### Ollama Integration

The Odoo Code Agent also includes integration with Ollama for local code generation:

1. **Direct HTTP API**: Uses Ollama's HTTP API directly for reliable communication

2. **Configurable Models**: Works with any Ollama model, with deepseek-r1 recommended for Odoo code generation

3. **Improved Error Handling**: Enhanced error handling for timeouts and connection issues

4. **Simplified Prompts**: Uses simplified prompts optimized for Ollama models

5. **Code Block Extraction**: Advanced regex patterns to extract code blocks from Ollama responses

6. **Detailed Logging**: Comprehensive logging for troubleshooting Ollama interactions

7. **Fallback Mechanism**: Automatically falls back to basic code generation if Ollama is unavailable

### Usage

```python
from src.odoo_code_agent.main import run_odoo_code_agent

# Use with Gemini integration
result = run_odoo_code_agent(
    query="Create an Odoo 18 module for customer feedback with ratings and comments",
    odoo_url="http://localhost:8069",
    odoo_db="llmdb18",
    odoo_username="admin",
    odoo_password="admin",
    use_gemini=True,  # Enable Gemini integration
    use_ollama=False
)

# Use with Ollama integration
result = run_odoo_code_agent(
    query="Create an Odoo 18 module for customer feedback with ratings and comments",
    odoo_url="http://localhost:8069",
    odoo_db="llmdb18",
    odoo_username="admin",
    odoo_password="admin",
    use_gemini=False,
    use_ollama=True  # Enable Ollama integration
)

print(result)
```

### MCP Tool Usage

You can use the Odoo Code Agent as an MCP tool in Claude Desktop:

```
/tool run_odoo_code_agent_tool query="Create a simple Odoo 18 module for customer feedback" use_gemini=true use_ollama=false
```

Or with Ollama:

```
/tool run_odoo_code_agent_tool query="Create a simple Odoo 18 module for customer feedback" use_gemini=false use_ollama=true
```

You can also save the generated files to disk:

```
/tool run_odoo_code_agent_tool query="Create a simple Odoo 18 module for customer feedback" use_gemini=true save_to_files=true output_dir="./generated_modules"
```

## DeepWiki Integration

The MCP server now includes integration with DeepWiki for enhanced AI documentation lookups. This integration provides a more effective way to retrieve and utilize documentation from various AI frameworks and libraries.

### Using the DeepWiki Tool

You can query DeepWiki for documentation using the `query_deepwiki` tool:

```
/tool query_deepwiki target_url="https://deepwiki.com/odoo/odoo"
```

Parameters:
- `target_url`: The DeepWiki URL to query (must start with https://deepwiki.com/)

### DeepWiki Features

- **Enhanced Documentation Retrieval**: Access comprehensive documentation for AI frameworks like OpenAI, Google, Meta, Anthropic, and Hugging Face
- **Odoo Documentation**: Special support for Odoo core and OWL documentation
- **Recursive Documentation Loading**: Automatically follows documentation dependencies
- **Context-Aware References**: Provides AI-contextual references to improve understanding

### Supported Framework Documentation

- **AI Frameworks**: OpenAI (GPT, Assistants API, Function Calling), Google (LangGraph, Vertex AI, Gemini), Meta (LLaMA), Anthropic (Claude API), Hugging Face, and more
- **AI Toolkits**: LangChain, LangGraph, Haystack, AutoGPT, CrewAI, AgentVerse
- **ERP & Integration**: Odoo Core and OWL, Zapier, N8N agent pipelines

## Mermaid Diagram Generation

The MCP server includes a tool for generating diagrams from Mermaid markdown. This is useful for visualizing workflows, entity relationships, and other diagrams directly from Claude Desktop.

### Using the Mermaid Diagram Tool

You can generate diagrams using the `generate_npx` tool:

```
/tool generate_npx code="graph TD; A[Start] --> B[Process]; B --> C[End]" name="workflow" theme="default" backgroundColor="white"
```

Parameters:
- `code`: The Mermaid markdown code for the diagram (required)
- `name`: Name for the output file (optional, defaults to timestamp)
- `theme`: Theme for the diagram (optional, options: default, forest, dark, neutral)
- `backgroundColor`: Background color for the diagram (optional, e.g., white, transparent, #F0F0F0)
- `folder`: Custom output folder path (optional, defaults to exports/diagrams)

### Mermaid Diagram Types

You can create various types of diagrams:

1. **Flowcharts**:
```
graph TD;
    A[Start] --> B[Process];
    B --> C{Decision};
    C -->|Yes| D[End];
    C -->|No| B;
```

2. **Sequence Diagrams**:
```
sequenceDiagram
    participant User
    participant System
    User->>System: Request Data
    System->>User: Return Data
```

3. **Class Diagrams**:
```
classDiagram
    class Customer {
        +String name
        +String email
        +getOrders()
    }
    class Order {
        +int id
        +Customer customer
    }
    Customer "1" --> "*" Order
```

4. **Entity Relationship Diagrams**:
```
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
```

The generated diagrams are saved as PNG files in the exports/diagrams directory and can be accessed for further use.
