#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Standalone MCP Server for testing MCP tools
This script creates a simple FastAPI server that exposes the MCP tools as HTTP endpoints
"""

import os
import sys
import json
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List, Union
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("standalone_mcp_server")

# Load environment variables
load_dotenv()

# Import the OdooModelDiscovery class from mcp_server.py
try:
    from mcp_server import OdooModelDiscovery
except ImportError:
    logger.error("Could not import OdooModelDiscovery from mcp_server.py")
    sys.exit(1)

# Get Odoo connection details from environment variables
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "llmdb18")
ODOO_USERNAME = os.getenv("ODOO_USERNAME", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

# Initialize the OdooModelDiscovery class
try:
    model_discovery = OdooModelDiscovery(ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
    logger.info("OdooModelDiscovery initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize OdooModelDiscovery: {str(e)}")
    model_discovery = None

# Create FastAPI app
app = FastAPI(title="Standalone MCP Server", description="A simple FastAPI server that exposes the MCP tools as HTTP endpoints")

# Define request models for each tool
class SearchRecordsRequest(BaseModel):
    model_name: str
    query: str

class GetRecordTemplateRequest(BaseModel):
    model_name: str

class CreateRecordRequest(BaseModel):
    model_name: str
    values: str

class UpdateRecordRequest(BaseModel):
    model_name: str
    record_id: int
    values: str

class DeleteRecordRequest(BaseModel):
    model_name: str
    record_id: int

class ExecuteMethodRequest(BaseModel):
    model_name: str
    method: str
    args: str

class AnalyzeFieldImportanceRequest(BaseModel):
    model_name: str
    use_nlp: bool = True

class GetFieldGroupsRequest(BaseModel):
    model_name: str

# Define response model
class ToolResponse(BaseModel):
    success: bool
    result: str

# Define tool endpoints
@app.post("/tool/search_records", response_model=ToolResponse)
async def search_records(request: SearchRecordsRequest):
    """Search for records in an Odoo model"""
    if not model_discovery:
        return {"success": False, "result": "Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."}
        
    try:
        # Create a simple domain based on the query
        domain = []
        if request.query:
            if "List out all" in request.query or "list all" in request.query.lower():
                # Just list all records with a reasonable limit
                domain = []
            else:
                # Try to find records matching the query in name field
                domain = [('name', 'ilike', request.query)]
        
        records, fields_to_show, fields_info = model_discovery.get_model_records(
            request.model_name, limit=10, domain=domain
        )
        
        # Format the results
        result = f"# Search Results for '{request.query}' in {request.model_name}\n\n"
        
        if not records:
            return {"success": True, "result": result + "No records found matching the query."}
        
        # Create a table header
        header = "| ID | " + " | ".join([fields_info.get(field, {}).get('string', field) for field in fields_to_show if field != 'id']) + " |\n"
        separator = "|----| " + " | ".join(["----" for _ in fields_to_show if _ != 'id']) + " |\n"
        
        result += header + separator
        
        # Add records to the table
        for record in records:
            record_id = record.get('id', 'N/A')
            row = f"| {record_id} | "
            row += " | ".join([str(record.get(field, '')) for field in fields_to_show if field != 'id'])
            row += " |\n"
            result += row
        
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error searching records: {str(e)}")
        return {"success": False, "result": f"Error searching records: {str(e)}"}

@app.post("/tool/get_record_template", response_model=ToolResponse)
async def get_record_template(request: GetRecordTemplateRequest):
    """Get a template for creating a record in an Odoo model"""
    if not model_discovery:
        return {"success": False, "result": "Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."}
        
    try:
        # Get model schema
        schema = model_discovery.get_model_schema(request.model_name)
        
        if not schema:
            return {"success": True, "result": json.dumps({"name": ""}, indent=2)}
        
        # Create a template with recommended fields
        template = {}
        fields = schema.get("fields", {})
        create_fields = schema.get("create_fields", [])
        
        for field in create_fields:
            if field in fields:
                field_info = fields[field]
                field_type = field_info.get('type')
                
                # Set default values based on field type
                if field_type == 'char':
                    template[field] = ""
                elif field_type == 'integer':
                    template[field] = 0
                elif field_type == 'float':
                    template[field] = 0.0
                elif field_type == 'boolean':
                    template[field] = False
                elif field_type == 'many2one':
                    template[field] = False
                elif field_type == 'selection':
                    selections = field_info.get('selection', [])
                    template[field] = selections[0][0] if selections else False
                else:
                    template[field] = False
        
        return {"success": True, "result": json.dumps(template, indent=2)}
    except Exception as e:
        logger.error(f"Error creating template: {str(e)}")
        return {"success": False, "result": f"Error creating template: {str(e)}"}

@app.post("/tool/create_record", response_model=ToolResponse)
async def create_record(request: CreateRecordRequest):
    """Create a new record in an Odoo model"""
    if not model_discovery:
        return {"success": False, "result": "Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."}
        
    try:
        # Parse the values JSON
        values_dict = json.loads(request.values)
        
        # Create the record
        record_id = model_discovery.create_record(request.model_name, values_dict)
        
        if not record_id:
            return {"success": False, "result": "Error creating record: Unknown error"}
        
        # Return a success message
        return {"success": True, "result": f"Record created successfully with ID: {record_id}"}
    except json.JSONDecodeError:
        return {"success": False, "result": "Error: Invalid JSON format for values. Please provide a valid JSON object."}
    except Exception as e:
        logger.error(f"Error creating record: {str(e)}")
        return {"success": False, "result": f"Error creating record: {str(e)}"}

@app.post("/tool/update_record", response_model=ToolResponse)
async def update_record(request: UpdateRecordRequest):
    """Update an existing record in an Odoo model"""
    if not model_discovery:
        return {"success": False, "result": "Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."}
        
    try:
        # Parse the values JSON
        values_dict = json.loads(request.values)
        
        # Update the record
        result = model_discovery.update_record(request.model_name, request.record_id, values_dict)
        
        if not result:
            return {"success": False, "result": f"Error updating record: Unknown error"}
        
        # Return a success message
        return {"success": True, "result": f"Record {request.record_id} updated successfully"}
    except json.JSONDecodeError:
        return {"success": False, "result": "Error: Invalid JSON format for values. Please provide a valid JSON object."}
    except Exception as e:
        logger.error(f"Error updating record: {str(e)}")
        return {"success": False, "result": f"Error updating record: {str(e)}"}

@app.post("/tool/delete_record", response_model=ToolResponse)
async def delete_record(request: DeleteRecordRequest):
    """Delete a record from an Odoo model"""
    if not model_discovery:
        return {"success": False, "result": "Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."}
        
    try:
        # Delete the record
        result = model_discovery.delete_record(request.model_name, request.record_id)
        
        if not result:
            return {"success": False, "result": f"Error deleting record: Unknown error"}
        
        # Return a success message
        return {"success": True, "result": f"Record {request.record_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting record: {str(e)}")
        return {"success": False, "result": f"Error deleting record: {str(e)}"}

@app.post("/tool/execute_method", response_model=ToolResponse)
async def execute_method(request: ExecuteMethodRequest):
    """Execute a custom method on an Odoo model"""
    if not model_discovery:
        return {"success": False, "result": "Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."}
        
    try:
        # Parse the args JSON
        try:
            args_list = json.loads(request.args)
            if not isinstance(args_list, list):
                args_list = [args_list]
        except json.JSONDecodeError:
            # If not valid JSON, try to interpret as a simple list or string
            if request.args.startswith('[') and request.args.endswith(']'):
                # Try to evaluate as a Python list
                import ast
                args_list = ast.literal_eval(request.args)
            else:
                # Treat as a single string argument
                args_list = [request.args]
        
        # Execute the method
        result = model_discovery.execute_method(request.model_name, request.method, args_list)
        
        # Format the result
        if isinstance(result, (dict, list)):
            return {"success": True, "result": json.dumps(result, indent=2)}
        else:
            return {"success": True, "result": str(result)}
    except Exception as e:
        logger.error(f"Error executing method: {str(e)}")
        return {"success": False, "result": f"Error executing method: {str(e)}"}

@app.post("/tool/analyze_field_importance", response_model=ToolResponse)
async def analyze_field_importance(request: AnalyzeFieldImportanceRequest):
    """Analyze the importance of fields in an Odoo model"""
    if not model_discovery:
        return {"success": False, "result": "Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."}
        
    try:
        # Get model schema
        schema = model_discovery.get_model_schema(request.model_name)
        
        if not schema:
            return {"success": True, "result": f"# Field Importance Analysis for {request.model_name}\n\nNo schema available for this model."}
        
        fields = schema.get("fields", {})
        
        # Calculate field importance
        importance = {}
        for field_name, field_info in fields.items():
            # Base score
            score = 50
            
            # Required fields are more important
            if field_info.get('required', False):
                score += 30
            
            # Common important fields
            if field_name in ['name', 'code', 'default_code']:
                score += 20
            elif field_name in ['email', 'phone', 'mobile']:
                score += 15
            elif field_name in ['street', 'city', 'zip', 'country_id']:
                score += 10
            elif field_name in ['list_price', 'standard_price', 'price']:
                score += 15
            
            # Field types importance
            field_type = field_info.get('type', '')
            if field_type == 'many2one':
                score += 5
            elif field_type == 'one2many':
                score += 3
            
            # Cap at 100
            importance[field_name] = min(score, 100)
        
        # Format the importance as a readable string
        result = f"# Field Importance Analysis for {request.model_name}\n\n"
        
        # Sort fields by importance
        sorted_fields = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        
        # Create a table
        result += "| Field | Importance |\n"
        result += "|-------|-----------|\n"
        
        for field, score in sorted_fields[:20]:  # Limit to 20 fields
            result += f"| {field} | {score} |\n"
        
        if len(sorted_fields) > 20:
            result += f"\n*...and {len(sorted_fields) - 20} more fields*\n"
        
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error analyzing field importance: {str(e)}")
        return {"success": False, "result": f"Error analyzing field importance: {str(e)}"}

@app.post("/tool/get_field_groups", response_model=ToolResponse)
async def get_field_groups(request: GetFieldGroupsRequest):
    """Get field groups for an Odoo model"""
    if not model_discovery:
        return {"success": False, "result": "Error: Odoo Connection\n\nCould not connect to Odoo server. Please check your connection settings."}
        
    try:
        # Get model schema
        schema = model_discovery.get_model_schema(request.model_name)
        
        if not schema:
            return {"success": True, "result": f"# Field Groups for {request.model_name}\n\nNo schema available for this model."}
        
        fields = schema.get("fields", {})
        
        # Group fields by purpose
        groups = {
            "basic_info": [],
            "contact_info": [],
            "address_info": [],
            "business_info": [],
            "pricing_info": [],
            "inventory_info": [],
            "categorization": [],
            "dates": [],
            "other": []
        }
        
        for field_name, field_info in fields.items():
            field_type = field_info.get('type', '')
            
            # Skip binary fields and attachments
            if field_type == 'binary' or 'attachment' in field_name:
                continue
            
            # Basic info
            if field_name in ['name', 'display_name', 'title', 'description', 'note', 'comment', 'lang', 'company_type']:
                groups["basic_info"].append(field_name)
            
            # Contact info
            elif field_name in ['email', 'phone', 'mobile', 'website', 'fax']:
                groups["contact_info"].append(field_name)
            
            # Address info
            elif field_name in ['street', 'street2', 'city', 'state_id', 'zip', 'country_id']:
                groups["address_info"].append(field_name)
            
            # Business info
            elif field_name in ['vat', 'ref', 'industry_id', 'company_id', 'user_id', 'partner_id', 'currency_id']:
                groups["business_info"].append(field_name)
            
            # Pricing info
            elif 'price' in field_name or field_name in ['list_price', 'standard_price', 'cost']:
                groups["pricing_info"].append(field_name)
            
            # Inventory info
            elif field_name in ['default_code', 'barcode', 'qty_available', 'virtual_available', 'incoming_qty', 'outgoing_qty']:
                groups["inventory_info"].append(field_name)
            
            # Categorization
            elif field_name in ['categ_id', 'uom_id', 'uom_po_id', 'product_tmpl_id', 'tag_ids', 'category_id']:
                groups["categorization"].append(field_name)
            
            # Dates
            elif 'date' in field_name or field_type == 'datetime' or field_type == 'date':
                groups["dates"].append(field_name)
            
            # Other
            else:
                groups["other"].append(field_name)
        
        # Remove empty groups
        groups = {k: v for k, v in groups.items() if v}
        
        # Format the groups as a readable string
        result = f"# Field Groups for {request.model_name}\n\n"
        
        for group_name, fields in groups.items():
            result += f"## {group_name.replace('_', ' ').title()}\n\n"
            for field in fields[:10]:  # Limit to 10 fields per group
                result += f"- `{field}`\n"
            
            if len(fields) > 10:
                result += f"\n*...and {len(fields) - 10} more fields*\n"
            
            result += "\n"
        
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Error getting field groups: {str(e)}")
        return {"success": False, "result": f"Error getting field groups: {str(e)}"}

# Add a health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if model_discovery and model_discovery.uid:
        return {"status": "ok", "message": "Server is running and connected to Odoo"}
    else:
        return {"status": "error", "message": "Server is running but not connected to Odoo"}

# Main entry point
if __name__ == "__main__":
    # Run the server
    port = int(os.getenv("PORT", "8000"))
    logger.info(f"Starting standalone MCP server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
