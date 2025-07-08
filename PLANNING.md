# Odoo 18 Integration MCP Server - Project Planning

Last Updated: 2025-05-29

## Project Overview
This project aims to create a robust integration server that connects MCP (Master Control Program) with Odoo 18.0 ERP system, focusing on efficient data synchronization, API management, and secure communications. The implementation provides a standardized interface for performing CRUD operations on Odoo 18 models through a simple API, with dynamic model discovery and field analysis capabilities. The project includes direct implementation for advanced operations like data export and import, with dynamic model and field discovery using ir.model and ir.model.fields. Additionally, the project includes an Odoo code agent that helps with generating Odoo 18 modules and code using a structured workflow with analysis, planning, human feedback, coding, and finalization phases.

## Architecture

### Core Components
1. **MCP Integration Layer**
   - Connection management ✅
   - Request/Response handling ✅
   - Data transformation ✅
   - Error handling and logging ✅
   - Claude Desktop integration ✅
   - MCP SDK compatibility ✅
   - Resource endpoints for model discovery ✅
   - Tools for CRUD operations ✅
   - Prompts for common operations ✅
   - Direct implementation for advanced operations ✅
   - Export/Import data processing ✅
   - Related records export/import ✅
   - Field mapping and transformation ✅
   - CSV handling and processing ✅
   - Odoo documentation retrieval (RAG) ✅
   - Mermaid diagram generation ✅
   - DeepWiki integration for documentation lookups ✅

2. **Simple Odoo Code Agent**
   - Streamlined code generation workflow without LangGraph dependency ✅
   - Modern Odoo 18 conventions and best practices ✅
   - DeepWiki integration for technical documentation ✅
   - Simplified planning and design process ✅
   - Efficient code generation with proper module structure ✅
   - Robust error handling and validation ✅
   - Input validation and sanitization ✅
   - Automatic retry for transient failures ✅
   - Comprehensive logging ✅
   - Security features including path validation ✅
   - Performance optimizations ✅
   - Streamlit UI integration ✅
   - Code visualization and download options ✅
   - File saving functionality ✅
   - Support for model providers (Gemini, Ollama) ✅
   - Automatic code validation ✅
   - Type hints and documentation ✅
   - Unit tests ✅
   - **Simplified Code Generator**: New module `odoo_code_generator.py` with streamlined prompting and validation. ✅
   - **Integrated into MCP Server**: MCP tool adapter created for the simplified generator. ✅
   - **Efficient Workflow**: Removed LangGraph dependency for a simpler workflow. ✅
   - **Documentation Integration**: DeepWiki integration for documentation context. ✅
   - **Core Features**: Input validation, retries, error handling, and path sanitization. ✅
   - **Streamlit Interface**: Streamlit page with file management and validation. ✅

3. **Odoo 18 Connector**
   - XML-RPC client implementation ✅
   - Session management ✅
   - Model operations (CRUD) ✅
   - Authentication handling ✅
   - Dynamic model discovery ✅
   - Field introspection ✅
   - Custom method execution ✅
   - NLP-based field analysis ✅
   - Field importance analysis ✅
   - Automatic field grouping ✅
   - Smart search field identification ✅
   - Record templates ✅
   - Advanced natural language search ✅

4. **Data Models**
   - Pydantic models for validation ✅
   - Data transformation utilities ✅
   - Schema versioning ✅
   - Type safety ✅
   - Serialization utilities ✅

5. **Security Layer**
   - Authentication ✅
   - Authorization ✅
   - API key management ✅
   - Rate limiting ✅
   - Environment variable management ✅
   - Secure credential storage ✅
   - Encryption utilities ✅

### Directory Structure
```
odoo18_mcp_project/
├── src/
│   ├── __init__.py
│   ├── agents/              # Agents for specific tasks
│   │   └── export_import/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Configuration management
│   │   └── logger.py        # Logging configuration
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── client.py        # MCP client implementation
│   │   ├── dynamic_handlers.py # Dynamic model handlers
│   │   └── handlers.py      # MCP request handlers
│   ├── odoo/
│   │   ├── __init__.py
│   │   ├── client.py        # Odoo client implementation
│   │   ├── dynamic/         # Dynamic model handling
│   │   └── schemas.py       # Pydantic schemas
│   ├── odoo_docs_rag/       # Odoo documentation RAG tool
│   │   ├── __init__.py
│   │   ├── db_storage.py
│   │   ├── docs_processor.py
│   │   ├── docs_retriever.py
│   │   ├── embedding_engine.py
│   │   ├── gemini_summarizer.py
│   │   ├── online_search.py
│   │   └── utils.py
│   ├── odoo_tools/
│   │   ├── __init__.py
│   │   └── csv_import.py
│   ├── simple_odoo_code_agent/ # Odoo code generation agent
│   │   ├── __init__.py
│   │   ├── odoo_code_generator.py
│   │   └── utils/
│   └── streamlit_client/
│       ├── __init__.py
│       ├── components/
│       ├── examples/
│       ├── main.py
│       ├── pages/
│       │   ├── __init__.py # List of pages
│       │   ├── crud_test.py # CRUD and method execution test page
│       │   ├── documentation.py # Odoo documentation search
│       │   ├── export_import.py # Export/Import data
│       │   ├── graph_visualization.py # Diagram visualizations
│       │   └── improved_odoo_generator.py # Improved module generator
│       ├── templates/
│       └── utils/
├── tests/
│   ├── __init__.py
│   ├── data/
│   ├── test_deepwiki_tool.py
│   ├── test_enhanced_rag.py
│   ├── test_export_import_agent.py
│   ├── test_gemini_code_gen.py
│   ├── test_generate_npx_advanced.py
│   ├── test_generate_npx_case1.py
│   ├── test_generate_npx_case2.py
│   ├── test_generator.py
│   ├── test_mcp_server_consolidated.py
│   └── test_odoo_code_generator.py
├── .env.example             # Environment variables example
├── app.py
├── claude_config.json
├── direct_export_import.py
├── docker-compose.override.yml
├── docker-compose.prod.yml
├── docker-compose.yml
├── entrypoint.sh
├── export_import_test.py
├── export_import_tools.py
├── field_converter.py
├── get_product_fields.py
├── main.py
├── mcp_client_test.py
├── mcp_server.py
├── mcp_server_master.py
├── mcp_wrapper.py
├── odoo18_api_test.py
├── pyproject.toml           # Project configuration
├── query_parser.py
├── relationship_handler.py
├── requirements-streamlit.txt
├── requirements.txt
├── scripts/
│   └── dynamic_data_tool.py
├── setup.py
├── simple_mcp_server.py
├── standalone_mcp_server.py
└── update_claude_config.sh
```

## Technical Specifications

### Python Requirements
- Python 3.10+ ✅
- Pydantic 2.x ✅
- XML-RPC client (standard library) ✅
- FastAPI (for API endpoints) ✅
- MCP SDK (for Claude Desktop integration) ✅
- pytest (for testing) ✅
- python-dotenv (for configuration) ✅
- uv (for virtual environment management) ✅
- pandas (for data processing) ✅
- csv (standard library, for CSV handling) ✅
- sentence-transformers (for document embedding) ✅
- torch (for sentence-transformers, version constraints for macOS) ✅
- numpy (version <2.0.0 for compatibility) ✅
- faiss-cpu (for vector storage and retrieval) ✅
- beautifulsoup4 (for documentation processing) ✅
- markdown (for documentation processing) ✅
- gitpython (for documentation repository management) ✅

### Odoo Requirements
- Odoo 18.0 compatibility ✅
- XML-RPC interface ✅
- Custom module support ✅
- External API access ✅
- Model introspection via ir.model and ir.model.fields ✅
- Support for custom method execution ✅
- Dynamic field discovery ✅
- Record template generation ✅

## Development Guidelines

### Code Style
- Follow PEP 8 guidelines ✅
- Use type hints ✅
- Black code formatting ✅
- Docstring format (Google style) ✅
- Maximum line length: 88 characters ✅

### Testing Strategy
1. **Unit Tests** ✅
   - Model validation ✅
   - Data transformation ✅
   - Authentication logic ✅
   - Error handling ✅

2. **Integration Tests** ✅
   - Odoo connectivity ✅
   - MCP communication ✅
   - End-to-end workflows ✅
   - Error scenarios ✅

3. **Performance Tests** ✅
   - Connection pooling (planned)
   - Concurrent operations ✅
   - Resource usage ✅

4. **MCP Server Tests** ✅
   - Comprehensive test script for all MCP tools ✅
   - Direct function testing ✅
   - Tool-specific test cases ✅
   - Error handling tests ✅
   - Edge case testing ✅
   - Export/Import testing ✅
   - CSV format validation ✅
   - Field validation testing ✅

### Security Considerations
1. **Authentication** ✅
   - API key validation ✅
   - Session management ✅
   - Token expiration ✅

2. **Data Protection** ✅
   - Encryption in transit ✅
   - Secure credential storage ✅
   - Input validation ✅

3. **Access Control** ✅
   - Role-based permissions ✅
   - Resource limitations ✅
   - IP whitelisting ✅

### Error Handling
- Detailed error messages ✅
- Proper exception hierarchy ✅
- Logging with context ✅
- Retry mechanisms (planned)

## Export/Import Functionality

### Design Principles
- Support for exporting and importing any Odoo model ✅
- Handling of parent-child relationships ✅
- Proper field mapping and transformation ✅
- CSV as the primary data format ✅
- Support for complex field types (many2one, many2many, etc.) ✅
- Error handling and validation ✅
- Direct implementation for reliability ✅
- Dynamic model and field discovery using ir.model and ir.model.fields ✅

### Export Process
1. **Model Validation**: Verify that the model exists and is accessible ✅
2. **Field Selection**: Determine which fields to export ✅
3. **Record Retrieval**: Fetch records from Odoo based on criteria ✅
4. **Data Transformation**: Convert Odoo data to CSV-compatible format ✅
5. **CSV Generation**: Create CSV file with proper headers and data ✅
6. **File System Integration**: Save CSV to specified location ✅
7. **Enhanced Field Filtering**: Support for filtering specific fields to export ✅
8. **Improved Error Handling**: Better error reporting and recovery ✅
9. **Directory Creation**: Automatic creation of output directories ✅
10. **Binary Field Handling**: Special handling for binary fields ✅
11. **Progress Reporting**: Detailed progress messages during export ✅

### Import Process
1. **CSV Parsing**: Read and parse CSV file ✅
2. **Field Mapping**: Map CSV columns to Odoo fields ✅
3. **Data Transformation**: Convert CSV data to Odoo-compatible format ✅
4. **Validation**: Validate data against Odoo field requirements ✅
5. **Record Creation/Update**: Create or update records in Odoo ✅
6. **Error Handling**: Handle and report any errors during import ✅
7. **Default Values**: Support for default values for required fields ✅
8. **Selection Field Validation**: Validation for selection fields ✅
9. **Force Import Option**: Option to force import even with missing required fields ✅
10. **Skip Invalid Values**: Option to skip invalid selection values ✅
11. **Row-Level Error Reporting**: Error reporting with row numbers ✅
12. **Import Summary Statistics**: Summary of import results ✅
13. **Consistent Parameter Naming**: Use input_path instead of import_path for consistency ✅
14. **Detailed Result Information**: Enhanced result objects with detailed statistics ✅
15. **Comprehensive Testing**: Test scripts for verifying functionality ✅

### Import Process Enhancements
1. **Dynamic Unique Field Detection**: Automatically identify potential unique fields for any model based on constraints and common patterns
2. **Enhanced Many2One Handling**: Improved name_search for better record matching during import
3. **Better Many2Many Support**: Handle both IDs and names in many2many fields with proper command format conversion
4. **Date Field Parsing**: Support for multiple date formats in import data
5. **Special Case Handling**: Model-specific handling for account.move (reset to draft) and product variants
6. **Improved Reporting**: Enhanced feedback on import operations with counts for created, updated, skipped, and error records
7. **Create/Update Control**: Fine-grained control over whether to create new records or update existing ones
8. **Intelligent Record Matching**: Multi-strategy approach to match existing records using IDs, external IDs, and unique fields

### Special Handling for Complex Models
1. **account.move (Invoices)**
   - Support for different invoice types ✅
   - Handling of posted invoices ✅
   - Reset to draft functionality ✅
   - Skipping readonly fields ✅
   - Maintaining balance requirements ✅
   - Proper handling of many2one fields ✅

2. **account.move.line (Invoice Lines)**
   - Maintaining relationship with parent invoice ✅
   - Handling of account_id field ✅
   - Proper tax_ids formatting ✅
   - Handling of computed fields ✅

3. **crm.lead (CRM Leads)**
   - Support for description field updates ✅
   - Handling of stage_id and user_id fields ✅
   - Proper date formatting ✅

### Related Records Export/Import
1. **Parent-Child Relationship**
   - Identify relationship field ✅
   - Export parent and child records together ✅
   - Maintain relationship during import ✅
   - Handle multiple children per parent ✅
   - Filter parent and child fields ✅
   - Support default values for parent and child fields ✅
   - Reset-to-draft functionality for account.move records ✅
   - Skip readonly fields option ✅

2. **CSV Format**
   - Combined format with parent and child data ✅
   - Metadata columns for record type and relationships ✅
   - Support for multiple children per parent ✅
   - Improved error handling and reporting ✅
   - Export parent records even without child records ✅

### Advanced Natural Language Search
1. **Query Parsing**
   - Natural language query parsing ✅
   - Dynamic model discovery using ir.model ✅
   - Dynamic field mapping using ir.model.fields ✅
   - Field categorization based on field types and names ✅
   - Field validation against model_fields ✅
   - Support for different Odoo versions ✅
   - Enhanced entity extraction with dynamic model information ✅

2. **Relationship Handling**
   - Identify relationships between models ✅
   - Traverse relationships for complex queries ✅
   - Join results from multiple models ✅
   - Handle one2many, many2one, and many2many relationships ✅

3. **Search Execution**
   - Convert natural language to Odoo domains ✅
   - Execute searches across multiple models ✅
   - Format results in a user-friendly way ✅
   - Handle complex multi-model queries ✅

### Odoo Documentation RAG Tool
1. **Documentation Processing**
   - Clone and process Odoo 18 documentation repository ✅
   - Extract text from Markdown, HTML, and RST files ✅
   - Implement intelligent chunking strategies ✅
   - Extract comprehensive metadata from file paths and content ✅
   - Handle documentation updates ✅
   - Improve text cleaning for better search quality ✅
   - Implement section-based chunking to maintain context ✅
   - Add minimum content length filtering ✅

2. **Embedding and Vector Storage**
   - Generate embeddings using sentence-transformers ✅
   - Upgrade to more powerful embedding model (all-mpnet-base-v2) ✅
   - Store embeddings in FAISS vector database ✅
   - Implement efficient similarity search ✅
   - Persist index and documents for reuse ✅
   - Handle model loading and initialization ✅
   - Optimize chunk size and overlap for better context ✅

3. **Retrieval and Integration**
   - Implement semantic search for documentation ✅
   - Add query preprocessing for better search results ✅
   - Implement keyword boosting for relevant documents ✅
   - Format search results with enhanced context ✅
   - Add related search suggestions ✅
   - Integrate with MCP server as a tool ✅
   - Provide prompt for documentation queries ✅
   - Handle error cases and fallbacks ✅
   - Add fallback to more general queries when specific queries fail ✅
   - Implement specialized handling for tax and localization queries ✅
   - Add Google Gemini integration for result summarization ✅
   - Implement online search capability using Brave Search API ✅
   - Create enhanced query method combining local docs, online search, and Gemini ✅
   - Add proper error handling and fallbacks for enhanced features ✅
   - Update MCP tool to support enhanced query parameters ✅

### Mermaid Diagram Generation
1. **Diagram Generation Tool**
   - MCP tool implementation ✅
   - Support for multiple diagram types (flowchart, sequence, class, ER) ✅
   - Custom theme and styling options (default, forest, dark, neutral) ✅
   - Background color customization ✅
   - Output file naming options ✅
   - Custom output directory support ✅
   - Error handling and logging ✅
   - Fallback mechanisms for different Mermaid CLI tools ✅
   - Integration with external MCP servers ✅
   - Support for @peng-shawn/mermaid-mcp-server ✅
   - Documentation and examples ✅
   - File caching to avoid regenerating unchanged diagrams ✅
   - Timestamp tracking for diagram generation ✅
   - Regeneration option for forcing diagram updates ✅

2. **Streamlit Client Integration**
   - Diagram visualization in Code Agent Graph page ✅
   - Cached diagram reuse for improved performance ✅
   - Regenerate button for forcing diagram updates ✅
   - Timestamp display for diagram generation time ✅
   - Progress indicators during diagram generation ✅
   - Error handling and fallback to text representation ✅
   - Directory structure management for diagram storage ✅
   - Automatic diagram path resolution ✅
   - MCPConnector helper method for diagram generation ✅
   - Interactive diagram display with Streamlit ✅

### Odoo Code Agent
1. **Agent Workflow**
   - Analysis phase for understanding requirements ✅
   - Documentation search and context gathering ✅
   - Planning phase for code structure design ✅
   - Code generation with modern Odoo 18 practices ✅
   - Automatic code validation and completeness checks ✅
   - Continuous progress updates via Streamlit UI ✅
   - Easy code download and module packaging ✅

2. **State Management**
   - Simplified state tracking with Pydantic models ✅
   - Progress tracking and status updates ✅
   - Error handling and recovery mechanisms ✅
   - Clear validation status reporting ✅
   - Automatic file completeness verification ✅

3. **Module Generation**
   - Dynamic module name extraction ✅
   - Standard Odoo module structure creation ✅
   - Model definition generation ✅
   - View definition generation ✅
   - Security configuration ✅
   - Manifest file creation ✅
   - Odoo 18 compliant code generation ✅
   - List view instead of tree view ✅
   - Single chatter tag implementation ✅
   - Mail thread integration ✅
   - Controller generation ✅
   - Complete module file generation ✅
   - File saving functionality ✅
   - Generated module directory structure ✅
   - Module name suffix (_vpcs_ext) to prevent conflicts ✅
   - Improved model name derivation from query ✅
   - Enhanced field suggestions based on model type ✅
   - Dynamic field generation based on query context ✅

5. **Fallback Models**
   - Google Gemini integration ✅
   - Ollama integration ✅
   - Direct HTTP API integration for Ollama ✅
   - Improved error handling for Ollama timeouts ✅
   - Enhanced code parsing from Ollama responses ✅
   - Simplified prompts for Ollama code generation ✅
   - Fallback model selection ✅
   - Error handling and recovery ✅
   - API key management ✅
   - Environment variable loading for API keys ✅
   - Gemini model selection from environment variables ✅
   - Improved module name extraction from queries ✅
   - Enhanced model field generation for specific module types ✅
   - Gemini-based analysis functionality ✅
   - Gemini-based planning functionality ✅
   - Gemini-based code generation functionality ✅
   - Gemini-based feedback processing functionality ✅

6. **MCP Server Integration**
   - MCP tool implementation ✅
   - Parameter validation and error handling ✅
   - Odoo connection validation ✅
   - Gemini API key validation ✅
   - Ollama server validation ✅
   - Formatted output with syntax highlighting ✅
   - File saving integration ✅
   - Standalone server support ✅
   - Test script for MCP tool ✅
   - Documentation for MCP tool usage ✅
   - Human validation workflow support ✅
   - Wait for validation parameter ✅
   - Current phase parameter ✅
   - State dictionary parameter ✅
   - Comprehensive testing of validation workflow ✅

## Performance Goals
- Response time < 200ms ✅
- Support for concurrent connections ✅
- Efficient resource usage ✅
- Connection pooling (planned)

## Container Architecture

The Docker setup includes three main services:

1. **mcp-server**: The main MCP server for integration with Claude Desktop
   - Exposes port 8000 for API access
   - Connects to Odoo via XML-RPC
   - Provides MCP tools for Claude Desktop
   - **Environment Variables**:
     - `ODOO_DOCS_DIR`: Directory to store the Odoo documentation (default: ./odoo_docs)
     - `ODOO_INDEX_DIR`: Directory to store the index and documents (default: ./odoo_docs_index)
     - `ODOO_DB_PATH`: Path to the database file (default: ./odoo_docs_index/embeddings.db)

2. **standalone-server**: A standalone server for testing MCP tools
   - Exposes port 8001 for API access (configurable via environment variables)
   - Provides HTTP endpoints for testing MCP tools
   - Useful for development and testing without Claude Desktop
   - Supports custom host and port configuration via MCP_HOST and MCP_PORT environment variables

3. **test-runner**: A service for running automated tests
   - Runs function tests and tool tests
   - Validates the MCP server functionality
   - Useful for CI/CD pipelines

## Streamlit Client Architecture

The Streamlit client provides a user-friendly interface for interacting with the Odoo 18 MCP tools:

1. **Core Components**
   - Main application entry point ✅
   - Navigation sidebar ✅
   - Page routing system ✅
   - Session state management ✅
   - MCP connector for tool integration ✅
   - Asynchronous polling mechanism ✅
   - Progress indicators for long-running operations ✅
   - Error handling and recovery ✅
   - Responsive UI design ✅
   - Custom styling and theming ✅

2. **Pages**
   - Code Agent page for module generation ✅
   - Export/Import page for data operations ✅
   - Documentation page for Odoo documentation search ✅
   - Advanced page for model and field information ✅
   - Chat page for natural language interaction ✅

3. **Components**
   - Chat component for human interaction ✅
   - File viewer for generated code and CSV files ✅
   - Feedback forms for code agent workflow ✅
   - Progress indicators for long-running operations ✅
   - Error handling and display ✅
   - Form validation ✅
   - Results formatting and display ✅
   - Two-stage validation UI for code agent ✅
   - State persistence between validation steps ✅
   - Workflow resumption from saved state ✅

4. **MCP Connector**
   - HTTP API integration ✅
   - Tool discovery and listing ✅
   - Asynchronous tool calls ✅
   - Polling for long-running operations ✅
   - Timeout management ✅
   - Error handling and recovery ✅
   - Tool-specific convenience methods ✅
   - Connection type support (HTTP/STDIO) ✅
   - Health check functionality ✅

5. **Session State Management**
   - Persistent state across page navigation ✅
   - Tool-specific state management ✅
   - Chat history management ✅
   - Form state persistence ✅
   - Results caching ✅
   - Error state handling ✅
   - Code agent state serialization ✅
   - Validation status tracking ✅
   - Current phase tracking ✅
   - State dictionary for workflow resumption ✅

6. **Asynchronous Polling Mechanism**
   - Initial request handling ✅
   - Polling for complete results ✅
   - Progress indicators during polling ✅
   - Timeout handling ✅
   - Error recovery ✅
   - Tool-specific polling configurations ✅
   - Request tracking with unique IDs ✅
   - Enhanced error handling for timeout situations ✅
   - Improved fallback messages for timeout situations ✅
   - Intelligent timeout calculation based on query complexity ✅
   - Optimized polling intervals for different tool types ✅

7. **Server-Side Query Processing**
   - Natural language query handling ✅
   - Dynamic model detection ✅
   - Relationship handling between models ✅
   - Field mapping for natural language terms ✅
   - Query execution against Odoo database ✅
   - Response formatting for display ✅

## Documentation Requirements
- API documentation ✅
- Setup guides ✅
- Configuration reference ✅
- Example implementations ✅
- Troubleshooting guide ✅
- Deployment documentation ✅
- Release notes ✅
