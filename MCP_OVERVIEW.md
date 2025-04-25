# MCP (Model Context Protocol) Overview

## What is MCP?

MCP (Model Context Protocol) is a standardized protocol that enables AI models to interact with external tools, data sources, and services. It provides a structured way for Large Language Models (LLMs) like Claude to access and manipulate data outside their training context, extending their capabilities beyond text generation.

## MCP Architecture

The MCP architecture consists of several key components that work together to enable AI-powered interactions with external systems:

```
┌─────────────┐           ┌─────────────┐
│             │  tool use │             │
│    LLM      │ ◄────────►│  MCP Host   │
│ (e.g. Claude)│           │ (Claude Desktop)│
│             │ ◄────────►│             │
└─────────────┘  Q+tools  └──────┬──────┘
                                 │
                                 │ tool use
                                 ▼
                          ┌─────────────┐
                          │             │
                          │ MCP Server  │
                          │             │
                          └──────┬──────┘
                                 │
                                 ▼
                          ┌─────────────┐
                          │  DB/API/Code│
                          │  External   │
                          │  Systems    │
                          └─────────────┘
```

### Key Components

1. **LLM (Large Language Model)**
   - AI models like Claude that generate text and process natural language
   - Communicates with the MCP Host to use tools and access external data

2. **MCP Host**
   - Intermediary between the LLM and MCP Servers
   - Manages tool registration, validation, and execution
   - Examples: Claude Desktop, API integrations

3. **MCP Server**
   - Custom server that implements specific functionality
   - Exposes tools and resources to the MCP Host
   - Connects to external systems like databases, APIs, or custom code
   - Can be developed using the MCP SDK

4. **External Systems**
   - Databases, APIs, file systems, or any other external resources
   - Provide data and functionality that the LLM can access through MCP

## How MCP Works

1. **Tool Registration**
   - MCP Servers register tools and resources with the MCP Host
   - Tools define their parameters, return types, and descriptions

2. **Tool Discovery**
   - The LLM discovers available tools through the MCP Host
   - The LLM can see tool descriptions, parameters, and usage examples

3. **Tool Invocation**
   - The LLM requests to use a specific tool with parameters
   - The MCP Host validates the request and forwards it to the appropriate MCP Server
   - The MCP Server executes the tool and returns the result
   - The result is passed back to the LLM through the MCP Host

4. **Resource Access**
   - Similar to tools, but for accessing static or dynamic content
   - Resources can be URLs, file paths, or other identifiers
   - The LLM can request resources through the MCP Host

## Odoo 18 MCP Integration

Our Odoo 18 MCP Integration is a custom MCP Server that connects Claude and other LLMs to Odoo 18 ERP systems. It provides tools and resources for:

1. **Model Discovery and Metadata**
   - Discover available Odoo models
   - Get detailed metadata about models and fields
   - Analyze field importance and relationships

2. **CRUD Operations**
   - Create, read, update, and delete records in any Odoo model
   - Search for records using domain filters
   - Execute custom Odoo methods

3. **Export/Import Operations**
   - Export records to CSV files
   - Import records from CSV files
   - Handle related records (parent-child relationships)
   - Map fields between CSV and Odoo models

4. **Advanced Features**
   - Field grouping and categorization
   - NLP-based field importance analysis
   - Record templates for creating new records
   - Validation of field values

### Dual Implementation Approach

Our Odoo 18 MCP Integration uses two different approaches for handling export/import operations:

1. **LangGraph Implementation**
   - Structured agent-based approach using LangGraph
   - State management system with `AgentState` class
   - Export and import nodes for step-by-step processing
   - Directed graph flow for complex operations
   - Ideal for complex scenarios requiring guided processing

2. **Direct Implementation**
   - Simpler, procedural implementation without LangGraph
   - Direct calls to Odoo's XML-RPC API
   - More straightforward for simple operations
   - Better for batch processing and automation scripts

## Using the MCP Server

### With Claude Desktop

1. Install the MCP server in Claude Desktop:
   ```bash
   mcp install mcp_server.py --name "Odoo 18 Integration" -v ODOO_URL=http://localhost:8069 -v ODOO_DB=llmdb18 -v ODOO_USERNAME=admin -v ODOO_PASSWORD=admin
   ```

2. Select "Odoo 18 Integration" from the server dropdown in Claude Desktop

3. Use resources and tools in your conversation with Claude:
   ```
   /resource odoo://models/all
   /tool search_records model_name=res.partner query=company
   ```

### With the Standalone Server

1. Start the standalone MCP server:
   ```bash
   python standalone_mcp_server.py
   ```

2. Use the HTTP API to access tools and resources:
   ```bash
   curl -X POST http://localhost:8000/tools/search_records -d '{"model_name": "res.partner", "query": "company"}'
   ```

## Benefits of MCP

1. **Extended AI Capabilities**
   - LLMs can access and manipulate data beyond their training context
   - Enables AI to work with real-time, private, or specialized data

2. **Standardized Interface**
   - Consistent protocol for tool and resource access
   - Simplifies integration between LLMs and external systems

3. **Security and Control**
   - MCP Host validates and controls tool access
   - Data remains within your systems, not exposed to the LLM directly

4. **Flexibility and Extensibility**
   - Custom MCP Servers can implement any functionality
   - New tools and resources can be added without retraining the LLM

## Conclusion

MCP represents a significant advancement in AI capabilities, enabling LLMs to interact with external systems in a structured, secure, and extensible way. Our Odoo 18 MCP Integration leverages this protocol to provide a powerful interface between AI models and Odoo ERP systems, enabling sophisticated data operations and business process automation.