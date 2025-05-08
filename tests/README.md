# Odoo 18 MCP Project Tests

This directory contains test scripts for the Odoo 18 MCP Project.

## Test Files

### Export/Import Tests

- **test_export_import_agent.py**: Tests the langgraph agent flow for exporting and importing Odoo records.
- **test_direct_export_import.py**: Tests the direct export and import functions without using the agent flow.

### MCP Server Tests

- **test_mcp_server_consolidated.py**: Comprehensive tests for the MCP server, including health checks, tool listing, and testing various tools.

### Odoo Code Agent Tests

- **test_odoo_code_agent_consolidated.py**: Consolidated tests for the Odoo Code Agent, including basic functionality, feedback handling, and testing with different LLM backends.
- **test_odoo_code_agent_utils_consolidated.py**: Consolidated tests for the Odoo Code Agent utilities, including documentation helper, Odoo connector, and file handling.
- **test_odoo_code_agent_playwright.ts**: End-to-end tests for the Odoo Code Agent using Playwright to test the Streamlit interface.
- **test_odoo_code_agent.py**: (Legacy) Tests the Odoo Code Agent with various queries.
- **run_playwright_test.py**: Helper script to run the Playwright tests.

## Running the Tests

### Export/Import Agent Tests

```bash
# Test export flow
python tests/test_export_import_agent.py --export --model res.partner --limit 10

# Test import flow
python tests/test_export_import_agent.py --import_data --model res.partner --limit 10

# Test export-import cycle
python tests/test_export_import_agent.py --cycle --model res.partner --limit 10

# Test related models export-import
python tests/test_export_import_agent.py --related --model sale.order --limit 5

# Run all tests with default model (res.partner)
python tests/test_export_import_agent.py
```

### Direct Export/Import Tests

```bash
# Test export_records_to_csv
python tests/test_direct_export_import.py --export --model res.partner --limit 10

# Test import_records_from_csv
python tests/test_direct_export_import.py --import_data --model res.partner --limit 10

# Test export-import cycle
python tests/test_direct_export_import.py --cycle --model res.partner --limit 10

# Test export_related_records_to_csv
python tests/test_direct_export_import.py --related-export --model sale.order --limit 5

# Test import_related_records_from_csv
python tests/test_direct_export_import.py --related-import --model sale.order --limit 5

# Run all tests with default model (res.partner)
python tests/test_direct_export_import.py
```

### MCP Server Tests

```bash
# Run all MCP server tests
uv run tests/test_mcp_server_consolidated.py --all

# Run specific tests
uv run tests/test_mcp_server_consolidated.py --health --tools --search

# Test advanced search
uv run tests/test_mcp_server_consolidated.py --advanced

# Test the Odoo code agent tool
uv run tests/test_mcp_server_consolidated.py --code-agent

# Test export/import tools
uv run tests/test_mcp_server_consolidated.py --export --import
```

### Odoo Code Agent Tests

```bash
# Run all Odoo Code Agent tests
uv run tests/test_odoo_code_agent_consolidated.py --all

# Run basic functionality test
uv run tests/test_odoo_code_agent_consolidated.py --basic

# Test with feedback
uv run tests/test_odoo_code_agent_consolidated.py --feedback

# Test with Google Gemini as a fallback
uv run tests/test_odoo_code_agent_consolidated.py --gemini

# Test with Ollama as a fallback
uv run tests/test_odoo_code_agent_consolidated.py --ollama

# Test complete workflow
uv run tests/test_odoo_code_agent_consolidated.py --workflow
```

### Odoo Code Agent Utilities Tests

```bash
# Run all Odoo Code Agent utilities tests
uv run tests/test_odoo_code_agent_utils_consolidated.py --all

# Test documentation helper
uv run tests/test_odoo_code_agent_utils_consolidated.py --docs

# Test Odoo connector
uv run tests/test_odoo_code_agent_utils_consolidated.py --connector

# Test human validation workflow
uv run tests/test_odoo_code_agent_utils_consolidated.py --workflow

# Test file saver
uv run tests/test_odoo_code_agent_utils_consolidated.py --files

# Test module structure
uv run tests/test_odoo_code_agent_utils_consolidated.py --structure
```
### Legacy Tests (For Reference)

```bash
# Test the Odoo Code Agent (legacy)
uv run tests/test_odoo_code_agent.py

# Test with Google Gemini as a fallback (legacy)
uv run tests/test_odoo_code_agent.py --gemini

# Test with Ollama as a fallback (legacy)
uv run tests/test_odoo_code_agent.py --ollama
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
