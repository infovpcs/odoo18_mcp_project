import json
import requests
import sys
import re
import os
from typing import Dict, Any

# MCP server configuration
MCP_SERVER_URL_BASE = "http://localhost:8001"
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
        response = requests.post(url, headers=HEADERS, data=json.dumps(data))
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {str(e)}")
        if e.response is not None:
            print(f"Error response content: {e.response.text}")
        sys.exit(1)

def run_test_case2():
    print("\n=== Test Case 2: Generation with Theme ===")
    mermaid_code = "graph TD; A-->B;"
    diagram_name = "test_diagram_theme"
    theme_name = "forest"
    
    response = make_request(tool_name="generate_npx", params={"code": mermaid_code, "name": diagram_name, "theme": theme_name})
    
    print("\nServer Response:")
    print(json.dumps(response, indent=2))
    
    file_path_str = None
    if response.get("success"):
        tool_result_str = response.get("result")
        if isinstance(tool_result_str, str):
            match = re.search(r"saved to: (`?)([^`\s]+\.png)(`?)", tool_result_str)
            if match:
                file_path_str = match.group(2)
                print("\nTest Case 2: SUCCESS reported by tool.")
                print(f"Extracted file path: {file_path_str}")
                
                if os.path.exists(file_path_str):
                    print(f"File VERIFIED at: {file_path_str}")
                else:
                    print(f"File NOT FOUND at reported path: {file_path_str}")
            else:
                print("\nTest Case 2: FAILED - Could not parse file_path from tool result string.")
                print(f"Full tool result string: {tool_result_str}")
        else:
            print("\nTest Case 2: FAILED - Tool result is not a string as expected.")
            print(f"Full tool result: {tool_result_str}")
    else:
        print(f"\nTest Case 2: FAILED - Server reported error: {response.get('error')}")

if __name__ == "__main__":
    run_test_case2()
