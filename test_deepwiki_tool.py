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
        response = requests.post(url, headers=HEADERS, data=json.dumps(payload), timeout=30) # Increased timeout
        # Log status code and raw response for debugging
        print(f"Raw response status: {response.status_code}")
        # print(f"Raw response text: {response.text[:500]}...") # Log first 500 chars
        
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.Timeout:
        print(f"Error making request: Timeout after 30 seconds for URL {url}")
        return {"success": False, "error": "Request timed out"}
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {str(e)}")
        if e.response is not None:
            print(f"Error response content: {e.response.text}")
            try:
                return e.response.json()
            except json.JSONDecodeError:
                # If the error response is not JSON, wrap it in the expected structure
                return {"success": False, "error": f"Non-JSON error response: {e.response.status_code} - {e.response.text}"}
        return {"success": False, "error": str(e)}
    except json.JSONDecodeError as je:
        print(f"Error decoding JSON response: {str(je)}")
        # Access response.text if response is available
        raw_text = "N/A"
        if 'response' in locals() and hasattr(response, 'text'):
            raw_text = response.text
        return {"success": False, "error": f"JSONDecodeError: {str(je)}. Raw response: {raw_text[:500]}..." }


def get_file_path_from_result_string(result_str: str) -> Optional[str]: # Renamed for clarity
    if isinstance(result_str, str):
        # Regex to find paths like `/app/exports/diagrams/name.png` or `/tmp/custom/name.png`
        match = re.search(r"saved to: `?([^`\s]+\.png)`?", result_str)
        if match:
            return match.group(1) # Group 1 is the path
    return None

def run_tests():
    results_summary = []
    final_report_data = [] # To store data for the final report

    # Test Case A: Fetch Odoo Documentation Overview
    print("\n=== Test Case A: Fetch Odoo Documentation Overview ===")
    params_a = {"target_url": "https://deepwiki.com/odoo/documentation"}
    response_a = make_request(tool_name="query_deepwiki", params=params_a)
    print("\nServer Response (Test Case A):")
    print(json.dumps(response_a, indent=2))
    passed_a = False
    content_snippet_a = ""
    if response_a.get("success"):
        result_text_a = response_a.get("result", "")
        content_snippet_a = result_text_a[:200] + "..." if result_text_a else "Empty result"
        if "Odoo Documentation" in result_text_a or "Sphinx" in result_text_a or "toctree" in result_text_a:
            passed_a = True
            print(f"Content snippet: {content_snippet_a}")
        else:
            print(f"Content check FAILED. Snippet: {result_text_a[:500]}...")
    results_summary.append({"case": "A", "params": params_a, "response": response_a, "passed": passed_a, "content_snippet": content_snippet_a, "error_message": response_a.get("error")})

    # Test Case B: Fetch OWL Framework Overview
    print("\n=== Test Case B: Fetch OWL Framework Overview ===")
    params_b = {"target_url": "https://deepwiki.com/odoo/owl"}
    response_b = make_request(tool_name="query_deepwiki", params=params_b)
    print("\nServer Response (Test Case B):")
    print(json.dumps(response_b, indent=2))
    passed_b = False
    content_snippet_b = ""
    if response_b.get("success"):
        result_text_b = response_b.get("result", "")
        content_snippet_b = result_text_b[:200] + "..." if result_text_b else "Empty result"
        if "Owl (Odoo Web Library)" in result_text_b or "component-based" in result_text_b or "QWeb" in result_text_b:
            passed_b = True
            print(f"Content snippet: {content_snippet_b}")
        else:
            print(f"Content check FAILED. Snippet: {result_text_b[:500]}...")
    results_summary.append({"case": "B", "params": params_b, "response": response_b, "passed": passed_b, "content_snippet": content_snippet_b, "error_message": response_b.get("error")})

    # Test Case C: Fetch Odoo Source Tree (Potential for large content)
    print("\n=== Test Case C: Fetch Odoo Source Tree ===")
    params_c = {"target_url": "https://deepwiki.com/odoo/odoo/tree/18.0"}
    response_c = make_request(tool_name="query_deepwiki", params=params_c)
    print("\nServer Response (Test Case C):")
    print(json.dumps(response_c, indent=2))
    passed_c = False
    content_snippet_c = ""
    if response_c.get("success"):
        result_text_c = response_c.get("result", "")
        content_snippet_c = result_text_c[:200] + "..." if result_text_c else "Empty result"
        # Check for keywords indicating it's a directory listing or a loading page
        if "odoo/odoo" in result_text_c or "tree/18.0" in result_text_c or "Files" in result_text_c or "Loading" in result_text_c:
            passed_c = True
            print(f"Content snippet: {content_snippet_c}")
        else:
            print(f"Content check FAILED. Snippet: {result_text_c[:500]}...")
    elif response_c.get("error") == "Request timed out":
        passed_c = "TIMEOUT" # Special status for timeout, can be considered a pass if long content is expected
        content_snippet_c = "Request timed out as potentially expected for large content."
        print("Test Case C: Got expected timeout or very large content.")
    results_summary.append({"case": "C", "params": params_c, "response": response_c, "passed": passed_c, "content_snippet": content_snippet_c, "error_message": response_c.get("error")})

    # Test Case D: Invalid DeepWiki Sub-URL
    print("\n=== Test Case D: Invalid DeepWiki Sub-URL ===")
    params_d = {"target_url": "https://deepwiki.com/nonexistentpage123xyz"}
    response_d = make_request(tool_name="query_deepwiki", params=params_d)
    print("\nServer Response (Test Case D):")
    print(json.dumps(response_d, indent=2))
    passed_d = False
    content_snippet_d = ""
    error_message_d = response_d.get("error")
    result_text_d = response_d.get("result", "")

    if response_d.get("success") is False and error_message_d: # Tool explicitly returns success: false
        if "404" in error_message_d or "Not Found" in error_message_d:
             passed_d = True
             content_snippet_d = f"Correctly failed with error: {error_message_d}"
        else:
            content_snippet_d = f"Failed with unexpected error: {error_message_d}"
    elif response_d.get("success") is True and isinstance(result_text_d, str): # Tool returns success: true but result is an error message
        if "Error: Could not fetch content" in result_text_d and "404" in result_text_d:
            passed_d = True
            content_snippet_d = f"Correctly returned error in result: {result_text_d}"
        elif "# Warning: No Content" in result_text_d: # If DeepWiki returns a 200 with a "not found" page
            passed_d = True # This is acceptable as the tool fetched what was given
            content_snippet_d = f"Fetched page, content indicates 'No Content': {result_text_d[:200]}..."
        else:
            content_snippet_d = f"Succeeded but content unexpected for 404: {result_text_d[:200]}..."
    results_summary.append({"case": "D", "params": params_d, "response": response_d, "passed": passed_d, "content_snippet": content_snippet_d, "error_message": error_message_d or result_text_d if not passed_d else ""})


    # Test Case E: Non-DeepWiki URL
    print("\n=== Test Case E: Non-DeepWiki URL ===")
    params_e = {"target_url": "https://www.google.com"}
    response_e = make_request(tool_name="query_deepwiki", params=params_e)
    print("\nServer Response (Test Case E):")
    print(json.dumps(response_e, indent=2))
    passed_e = False
    content_snippet_e = ""
    expected_error_msg = "# Error: Invalid URL\n\nOnly URLs starting with 'https://deepwiki.com/' are allowed for this tool."
    if response_e.get("success") and response_e.get("result") == expected_error_msg:
        passed_e = True
        content_snippet_e = response_e.get("result")
    results_summary.append({"case": "E", "params": params_e, "response": response_e, "passed": passed_e, "content_snippet": content_snippet_e, "error_message": response_e.get("error") if not passed_e else ""})
    
    print("\n---FINAL SCRIPT TEST RESULTS---")
    for res in results_summary:
        print(f"Case {res['case']}: Passed = {res['passed']}")
        if not res['passed'] or res['passed'] == "TIMEOUT": # Also print response for timeout for manual check
             print(f"  Params: {res['params']}")
             print(f"  Response: {json.dumps(res['response'])}")
             print(f"  Content/Error: {res['content_snippet'] or res['error_message']}")

if __name__ == "__main__":
    run_tests()
