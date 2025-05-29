import json
import requests
import sys
import re
import os
from typing import Dict, Any, Optional

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
        # For testing, we want to see the response even if it's an error, so don't sys.exit yet
        # Return the JSON response if available, otherwise a custom error dict
        if e.response is not None and e.response.headers.get('content-type') == 'application/json':
            return e.response.json()
        return {"success": False, "error": str(e)}


def get_file_path_from_result(result_str: str) -> Optional[str]:
    if isinstance(result_str, str): # Changed tool_result_str to result_str
        match = re.search(r"saved to: (`?)([^`\s]+\.png)(`?)", result_str)
        if match:
            return match.group(2)
    return None

def test_case_2_theme():
    print("\n=== Test Case 2: Generation with Theme ===")
    mermaid_code = "graph TD; A-->B;"
    diagram_name = "test_diagram_theme"
    theme_name = "forest"
    
    response = make_request(tool_name="generate_npx", params={"code": mermaid_code, "name": diagram_name, "theme": theme_name})
    
    print("\nServer Response (Test Case 2):")
    print(json.dumps(response, indent=2))
    
    file_path = None
    if response.get("success"):
        tool_result_str = response.get("result")
        file_path = get_file_path_from_result(tool_result_str)
        if file_path:
            print(f"Test Case 2: SUCCESS reported by tool. Extracted file path: {file_path}")
        else:
            print(f"Test Case 2: FAILED - Could not parse file_path from tool result string: {tool_result_str}")
    else:
        print(f"Test Case 2: FAILED - Server reported error: {response.get('error')}")
    return file_path

def test_case_3_background_color():
    print("\n=== Test Case 3: Generation with Background Color ===")
    mermaid_code = "graph TD; A-->B;"
    diagram_name = "test_diagram_bg"
    background_color = "transparent"
    
    response = make_request(tool_name="generate_npx", params={"code": mermaid_code, "name": diagram_name, "backgroundColor": background_color})
    
    print("\nServer Response (Test Case 3):")
    print(json.dumps(response, indent=2))

    file_path = None
    if response.get("success"):
        tool_result_str = response.get("result")
        file_path = get_file_path_from_result(tool_result_str)
        if file_path:
            print(f"Test Case 3: SUCCESS reported by tool. Extracted file path: {file_path}")
        else:
            print(f"Test Case 3: FAILED - Could not parse file_path from tool result string: {tool_result_str}")
    else:
        print(f"Test Case 3: FAILED - Server reported error: {response.get('error')}")
    return file_path

def test_case_4_custom_folder():
    print("\n=== Test Case 4: Generation with Custom Folder ===")
    mermaid_code = "graph TD; A-->B;"
    diagram_name = "test_diagram_custom_folder"
    custom_folder = "/Users/vinusoft85/workspace/odoo18_mcp_project/exports/diagrams/custom_diagrams_output" 
    
    # Ensure the custom folder exists for verification, though the tool should create it
    os.makedirs(custom_folder, exist_ok=True)

    response = make_request(tool_name="generate_npx", params={"code": mermaid_code, "name": diagram_name, "folder": custom_folder})
    
    print("\nServer Response (Test Case 4):")
    print(json.dumps(response, indent=2))

    file_path = None
    if response.get("success"):
        tool_result_str = response.get("result")
        file_path = get_file_path_from_result(tool_result_str)
        if file_path:
            print(f"Test Case 4: SUCCESS reported by tool. Extracted file path: {file_path}")
        else:
            print(f"Test Case 4: FAILED - Could not parse file_path from tool result string: {tool_result_str}")
    else:
        print(f"Test Case 4: FAILED - Server reported error: {response.get('error')}")
    return file_path

def test_case_5_invalid_code():
    print("\n=== Test Case 5: Invalid Mermaid Code ===")
    mermaid_code = "graph TD; A--invalid-->B;" # Invalid Mermaid syntax
    diagram_name = "test_diagram_invalid"
    
    response = make_request(tool_name="generate_npx", params={"code": mermaid_code, "name": diagram_name})
    
    print("\nServer Response (Test Case 5):")
    print(json.dumps(response, indent=2))
    
    if not response.get("success") and "Error generating diagram" in response.get("result", ""):
        print("\nTest Case 5: SUCCESS - Tool correctly reported an error for invalid code.")
        print(f"Error message: {response.get('result')}")
        return True # Indicates test success (error was expected)
    elif response.get("success"):
        print("\nTest Case 5: FAILED - Tool reported success for invalid code.")
        tool_result_str = response.get("result")
        file_path = get_file_path_from_result(tool_result_str)
        if file_path:
            print(f"File was unexpectedly created at: {file_path}")
        return False
    else:
        print(f"\nTest Case 5: FAILED - Unexpected error: {response.get('error')}")
        print(f"Full response: {response}")
        return False

if __name__ == "__main__":
    results = {}
    
    # Test Case 2
    results["case2_path"] = test_case_2_theme()
    
    # Test Case 3
    results["case3_path"] = test_case_3_background_color()

    # Test Case 4
    results["case4_path"] = test_case_4_custom_folder()

    # Test Case 5
    results["case5_passed"] = test_case_5_invalid_code()

    # Output results for agent to parse
    print("\n---FINAL TEST RESULTS---")
    print(json.dumps(results))
