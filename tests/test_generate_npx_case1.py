import json
import requests
import sys
import re # For parsing the file path
import os # For checking file existence
from typing import Dict, Any

# MCP server configuration
MCP_SERVER_URL_BASE = "http://localhost:8001"  # Server runs on 8001
HEADERS = {
    "Content-Type": "application/json"
}

def make_request(tool_name: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make a request to the MCP server's /call_tool endpoint."""
    url = f"{MCP_SERVER_URL_BASE}/call_tool"
    payload = {
        "tool": tool_name,
        "params": params if params is not None else {}
    }
    
    print(f"Requesting: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=HEADERS, data=json.dumps(payload))
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {str(e)}")
        if e.response is not None:
            print(f"Error response content: {e.response.text}")
        sys.exit(1)

def run_test_case1():
    print("\n=== Test Case 1: Basic Diagram Generation ===")
    mermaid_code = "graph TD; A-->B;"
    diagram_name = "test_diagram_case1" # Will be used for the filename
    
    response = make_request(tool_name="generate_npx", params={"code": mermaid_code, "name": diagram_name})
    
    print("\nServer Response:")
    print(json.dumps(response, indent=2))
    
    file_path_str = None
    if response.get("success"):
        tool_result_str = response.get("result")
        if isinstance(tool_result_str, str):
            # Try to extract path using regex, assuming format "saved to: /path/to/file.png" or "saved to: `/path/to/file.png`"
            match = re.search(r"saved to: (`?)([^`\s]+\.png)(`?)", tool_result_str) # Adjusted regex
            if match:
                file_path_str = match.group(2) # Group 2 is the path without backticks
                print("\nTest Case 1: SUCCESS reported by tool.")
                print(f"Extracted file path: {file_path_str}")
                
                # Attempt to verify file existence
                if os.path.exists(file_path_str):
                    print(f"File VERIFIED at: {file_path_str}")
                    try:
                        with open(file_path_str, 'rb') as f:
                            # Try reading a small part to ensure it's not empty/corrupt (basic check)
                            content_sample = f.read(10) 
                            if content_sample:
                                print(f"File content seems OK (read {len(content_sample)} bytes).")
                            else:
                                print("File content is EMPTY.")
                    except Exception as e:
                        print(f"Error reading file {file_path_str}: {e}")
                else:
                    print(f"File NOT FOUND at reported path: {file_path_str}")
                    # Let's check the directory structure as well
                    exports_dir = "/Users/vinusoft85/workspace/odoo18_mcp_project/exports"
                    diagrams_dir = "/Users/vinusoft85/workspace/odoo18_mcp_project/exports/diagrams"
                    print(f"Checking existence of {exports_dir}: {os.path.exists(exports_dir)}")
                    if os.path.exists(exports_dir):
                        print(f"Contents of {exports_dir}: {os.listdir(exports_dir)}")
                    print(f"Checking existence of {diagrams_dir}: {os.path.exists(diagrams_dir)}")
                    if os.path.exists(diagrams_dir):
                        print(f"Contents of {diagrams_dir}: {os.listdir(diagrams_dir)}")

            else:
                print("\nTest Case 1: FAILED - Could not parse file_path from tool result string.")
                print(f"Full tool result string: {tool_result_str}")
        else:
            print("\nTest Case 1: FAILED - Tool result is not a string as expected.")
            print(f"Full tool result: {tool_result_str}")
    else:
        print(f"\nTest Case 1: FAILED - Server reported error: {response.get('error')}")

if __name__ == "__main__":
    run_test_case1()
