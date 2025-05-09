#!/usr/bin/env python3
"""
Test script for the Mermaid diagram generation tool in the standalone MCP server.
"""

import requests
import json
import os
import sys
import argparse
from pathlib import Path

# Default MCP server URL
MCP_URL = "http://localhost:8001/call_tool"

def test_generate_mermaid(mcp_url=MCP_URL, diagram_type="flowchart"):
    """
    Test the generate_npx tool with different diagram types.

    Args:
        mcp_url: URL of the MCP server
        diagram_type: Type of diagram to generate (flowchart, sequence, class, er)

    Returns:
        Response from the MCP server
    """
    print(f"\n=== Testing Mermaid Diagram Generation: {diagram_type} ===")

    # Define different diagram types
    diagrams = {
        "flowchart": {
            "code": """
graph TD;
    A[Start] --> B[Process];
    B --> C{Decision};
    C -->|Yes| D[End];
    C -->|No| B;
            """,
            "name": "flowchart_test"
        },
        "sequence": {
            "code": """
sequenceDiagram
    participant User
    participant System
    User->>System: Request Data
    System->>User: Return Data
            """,
            "name": "sequence_test"
        },
        "class": {
            "code": """
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
            """,
            "name": "class_test"
        },
        "er": {
            "code": """
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE-ITEM : contains
            """,
            "name": "er_test"
        }
    }

    # Get the diagram data
    if diagram_type not in diagrams:
        print(f"Error: Unknown diagram type '{diagram_type}'")
        print(f"Available types: {', '.join(diagrams.keys())}")
        return None

    diagram_data = diagrams[diagram_type]

    # Prepare the request
    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "tool": "generate_npx",
        "params": {
            "code": diagram_data["code"].strip(),
            "name": diagram_data["name"],
            "theme": "default",
            "backgroundColor": "white"
        }
    }

    # Send the request
    try:
        print(f"Sending request to {mcp_url}...")
        response = requests.post(mcp_url, headers=headers, data=json.dumps(data))
        response.raise_for_status()
        result = response.json()

        # Print the result
        print("\nResponse:")
        print(json.dumps(result, indent=2))

        return result
    except requests.exceptions.RequestException as e:
        print(f"Error: {str(e)}")
        return None

def main():
    """Main function to run the test."""
    parser = argparse.ArgumentParser(description="Test the Mermaid diagram generation tool")
    parser.add_argument("--url", default=MCP_URL, help="URL of the MCP server")
    parser.add_argument("--type", default="flowchart", choices=["flowchart", "sequence", "class", "er", "all"],
                        help="Type of diagram to generate")

    args = parser.parse_args()

    if args.type == "all":
        for diagram_type in ["flowchart", "sequence", "class", "er"]:
            test_generate_mermaid(args.url, diagram_type)
    else:
        test_generate_mermaid(args.url, args.type)

if __name__ == "__main__":
    main()
