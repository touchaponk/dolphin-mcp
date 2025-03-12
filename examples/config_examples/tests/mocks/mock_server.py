#!/usr/bin/env python
"""
Mock MCP server for testing.
This script implements a mock MCP server that can be used for testing.
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mock-mcp-server")

class MockMCPServer:
    """Mock MCP server for testing."""
    
    def __init__(self, server_type):
        """Initialize the mock server."""
        self.server_type = server_type
        self.responses_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "responses")
        self.response_file = os.path.join(self.responses_dir, f"{server_type}_default.json")
        
        # Load the response file
        if not os.path.exists(self.response_file):
            logger.error(f"Response file not found: {self.response_file}")
            raise FileNotFoundError(f"Response file not found: {self.response_file}")
        
        with open(self.response_file, "r") as f:
            self.responses = json.load(f)
        
        logger.info(f"Loaded response file: {self.response_file}")
        logger.info(f"Server type: {server_type}")
    
    def run(self):
        """Run the mock server."""
        logger.info("Starting mock MCP server")
        
        # Send the initialize response
        if "initialize" in self.responses:
            print(json.dumps({"jsonrpc": "2.0", "result": self.responses["initialize"], "id": 1}))
            sys.stdout.flush()
        
        # Process requests
        for line in sys.stdin:
            try:
                request = json.loads(line)
                logger.info(f"Received request: {request}")
                
                # Process the request
                if "method" in request:
                    method = request["method"]
                    
                    if method == "list_tools" and "list_tools" in self.responses:
                        print(json.dumps({"jsonrpc": "2.0", "result": self.responses["list_tools"], "id": request["id"]}))
                    elif method == "call_tool" and "call_tool" in self.responses:
                        # Get the tool name from the params
                        tool_name = request["params"]["name"]
                        
                        # Check if we have a response for this tool
                        if tool_name in self.responses["call_tool"]:
                            print(json.dumps({"jsonrpc": "2.0", "result": self.responses["call_tool"][tool_name], "id": request["id"]}))
                        else:
                            # Return a generic response
                            print(json.dumps({
                                "jsonrpc": "2.0",
                                "result": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": f"Mock response for tool: {tool_name}"
                                        }
                                    ]
                                },
                                "id": request["id"]
                            }))
                    elif method == "list_resources" and "list_resources" in self.responses:
                        print(json.dumps({"jsonrpc": "2.0", "result": self.responses["list_resources"], "id": request["id"]}))
                    elif method == "list_resource_templates" and "list_resource_templates" in self.responses:
                        print(json.dumps({"jsonrpc": "2.0", "result": self.responses["list_resource_templates"], "id": request["id"]}))
                    elif method == "read_resource" and "read_resource" in self.responses:
                        print(json.dumps({"jsonrpc": "2.0", "result": self.responses["read_resource"], "id": request["id"]}))
                    else:
                        # Return an error for unknown methods
                        print(json.dumps({
                            "jsonrpc": "2.0",
                            "error": {
                                "code": -32601,
                                "message": f"Method not found: {method}"
                            },
                            "id": request["id"]
                        }))
                
                sys.stdout.flush()
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON: {line}")
            except Exception as e:
                logger.error(f"Error processing request: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Mock MCP server for testing.")
    parser.add_argument("--server-type", required=True, help="Type of server to mock (e.g., weather, github, etc.)")
    args = parser.parse_args()
    
    # Create and run the mock server
    server = MockMCPServer(args.server_type)
    server.run()

if __name__ == "__main__":
    main()
