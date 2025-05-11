# Odoo 18 MCP Project Tests

This directory contains consolidated test scripts for the Odoo 18 MCP Project. The test suite has been streamlined into four main test files that cover all functionality.

## Consolidated Test Files

- **test_mcp_server_consolidated.py**: Comprehensive tests for the MCP server and all its tools, including:
  - Server health and tool listing
  - Basic CRUD operations (search, create, update, delete)
  - Advanced search and documentation retrieval
  - Field analysis and validation
  - Export/import functionality for single and related models
  - Odoo code agent functionality
  - Mermaid diagram generation

- **test_odoo_code_agent_consolidated.py**: Consolidated tests for the Odoo Code Agent, including:
  - Basic functionality
  - Feedback handling
  - Testing with different LLM backends (Gemini, Ollama)
  - Complete workflow testing

- **test_odoo_code_agent_utils_consolidated.py**: Consolidated tests for the Odoo Code Agent utilities, including:
  - Documentation helper
  - Odoo connector
  - Human validation workflow
  - File handling
  - Module structure generation

- **test_export_import_agent.py**: Tests for the langgraph agent flow for exporting and importing Odoo records, including:
  - Export flow
  - Import flow
  - Export-import cycle
  - Related models export-import

- **test_enhanced_rag.py**: Tests for the enhanced RAG tool with Gemini integration and online search, including:
  - Basic retrieval functionality
  - Gemini integration for summarization
  - Online search integration
  - Combined functionality (local docs + online search + Gemini)
  - MCP tool integration

## Running the Tests

### 1. MCP Server Consolidated Tests

The `test_mcp_server_consolidated.py` file provides comprehensive testing for all MCP server tools and functionality.

```bash
# Run all tests
uv run tests/test_mcp_server_consolidated.py --all

# Run test categories
uv run tests/test_mcp_server_consolidated.py --server    # Server health and tools
uv run tests/test_mcp_server_consolidated.py --basic     # Basic functionality
uv run tests/test_mcp_server_consolidated.py --crud      # CRUD operations
uv run tests/test_mcp_server_consolidated.py --field-tools  # Field analysis tools
uv run tests/test_mcp_server_consolidated.py --export-import  # Export/import tools

# Run specific tool tests
# Server tests
uv run tests/test_mcp_server_consolidated.py --health --tools

# CRUD operations
uv run tests/test_mcp_server_consolidated.py --search --create --update --delete --execute

# Advanced search and documentation
uv run tests/test_mcp_server_consolidated.py --advanced --docs

# Field analysis
uv run tests/test_mcp_server_consolidated.py --validate --analyze --groups --template

# Export/import
uv run tests/test_mcp_server_consolidated.py --export --import --export-related --import-related

# Code agent and visualization
uv run tests/test_mcp_server_consolidated.py --code-agent --mermaid
```

### 2. Odoo Code Agent Consolidated Tests

The `test_odoo_code_agent_consolidated.py` file tests the Odoo Code Agent functionality.

```bash
# Run all Odoo Code Agent tests
uv run tests/test_odoo_code_agent_consolidated.py --all

# Run specific tests
uv run tests/test_odoo_code_agent_consolidated.py --basic     # Basic functionality
uv run tests/test_odoo_code_agent_consolidated.py --feedback  # Test with feedback
uv run tests/test_odoo_code_agent_consolidated.py --gemini    # Test with Gemini
uv run tests/test_odoo_code_agent_consolidated.py --ollama    # Test with Ollama
uv run tests/test_odoo_code_agent_consolidated.py --workflow  # Test complete workflow
```

### 3. Odoo Code Agent Utilities Consolidated Tests

The `test_odoo_code_agent_utils_consolidated.py` file tests the utilities used by the Odoo Code Agent.

```bash
# Run all Odoo Code Agent utilities tests
uv run tests/test_odoo_code_agent_utils_consolidated.py --all

# Run specific tests
uv run tests/test_odoo_code_agent_utils_consolidated.py --docs      # Documentation helper
uv run tests/test_odoo_code_agent_utils_consolidated.py --connector # Odoo connector
uv run tests/test_odoo_code_agent_utils_consolidated.py --workflow  # Human validation
uv run tests/test_odoo_code_agent_utils_consolidated.py --files     # File saver
uv run tests/test_odoo_code_agent_utils_consolidated.py --structure # Module structure
```

### 4. Export/Import Agent Tests

The `test_export_import_agent.py` file tests the langgraph agent flow for exporting and importing Odoo records.

```bash
# Run all tests with default model (res.partner)
uv run tests/test_export_import_agent.py

# Run specific tests
uv run tests/test_export_import_agent.py --export --model res.partner --limit 10
uv run tests/test_export_import_agent.py --import_data --model res.partner --limit 10
uv run tests/test_export_import_agent.py --cycle --model res.partner --limit 10
uv run tests/test_export_import_agent.py --related --model sale.order --limit 5
```

### Running All Tests

To run all tests in sequence:

```bash
# Run all consolidated tests
uv run tests/test_mcp_server_consolidated.py --all
uv run tests/test_odoo_code_agent_consolidated.py --all
uv run tests/test_odoo_code_agent_utils_consolidated.py --all
uv run tests/test_export_import_agent.py
```

## Test Data

Test data files are stored in the `tests/data` directory. This directory is created automatically when running the tests.

## Environment Variables

The tests use the following environment variables:

- `ODOO_URL`: Odoo server URL (default: http://localhost:8069)
- `ODOO_DB`: Odoo database name (default: llmdb18)
- `ODOO_USERNAME`: Odoo username (default: admin)
- `ODOO_PASSWORD`: Odoo password (default: admin)
- `MCP_SERVER_URL`: MCP server URL (default: http://127.0.0.1:8001)
- `GEMINI_API_KEY`: Google Gemini API key (required for Gemini tests)
- `GEMINI_MODEL`: Google Gemini model to use (default: gemini-2.0-flash)

You can set these variables in a `.env` file in the project root directory.

## Test Models

The tests support the following Odoo models:

- `res.partner`: Partners (customers, suppliers, etc.)
- `sale.order` and `sale.order.line`: Sales orders and order lines
- `account.move` and `account.move.line`: Accounting entries (invoices, bills, etc.)
- `project.project` and `project.task`: Projects and tasks

For related models tests, the following relationships are used:

- `res.partner` → `res.partner.bank` (relation field: `partner_id`)
- `sale.order` → `sale.order.line` (relation field: `order_id`)
- `account.move` → `account.move.line` (relation field: `move_id`)
- `project.project` → `project.task` (relation field: `project_id`)

## Adding New Tests

To add new tests:

1. Create a new test file in the `tests` directory
2. Import the necessary modules and functions
3. Define test functions for each feature to test
4. Add a `main()` function with argument parsing
5. Update this README with information about the new tests

## Consolidated Files and Redundant Tests

### Consolidated Test Files

The test suite has been streamlined into these four main test files:

1. **test_mcp_server_consolidated.py**: Comprehensive MCP server and tools tests
2. **test_odoo_code_agent_consolidated.py**: Consolidated Odoo code agent tests
3. **test_odoo_code_agent_utils_consolidated.py**: Consolidated Odoo code agent utilities tests
4. **test_export_import_agent.py**: Export/import agent tests

### Redundant Test Files (Can Be Removed)

The following test files are now redundant and can be removed as their functionality is covered by the consolidated test files:

#### MCP Server Tests (Consolidated into test_mcp_server_consolidated.py)
- `simple_mcp_test.py` - Basic MCP server connection test
- `client_test.py` - Tests client functionality
- `direct_test.py` - Direct test of MCP functionality
- `simple_test.py` - Simple test
- `test_advanced_search.py` - Advanced search test
- `test_advanced_search_tool.py` - Advanced search tool test
- `test_mcp_tools.py` - Export/import functionality test
- `test_direct_export_import.py` - Direct export/import test
- `test_specific_queries.py` - Specific query test
- `test_product_import.py` - Product import test
- `comprehensive_test.py` - Older comprehensive test

#### Odoo Code Agent Tests (Consolidated into test_odoo_code_agent_consolidated.py)
- `test_odoo_code_agent.py` - Legacy Odoo code agent test
- `test_odoo_code_agent_tool.py` - Odoo code agent tool test

#### Utility Tests (Consolidated into test_odoo_code_agent_utils_consolidated.py)
- `test_embedding_db.py` - Embedding database test
- `test_gemini_client.py` - Gemini client test
- `test_human_validation.py` - Human validation test
- `test_mermaid.py` - Mermaid diagram test
