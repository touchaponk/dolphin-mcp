#!/usr/bin/env python
"""
Query script for the developer configuration.
This script demonstrates how to use the Docker and IDE MCP servers together.
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
logger = logging.getLogger("developer-query")

def load_config(config_path):
    """Load the configuration file."""
    with open(config_path, "r") as f:
        return json.load(f)

def list_containers(running_only, config):
    """List Docker containers."""
    # In a real implementation, this would use the MCP client to call the Docker server
    logger.info(f"Listing {'running ' if running_only else ''}Docker containers")
    
    # Simulate the container list
    containers = []
    for i in range(5):
        status = "running" if i < 3 else "exited"
        
        if running_only and status != "running":
            continue
        
        containers.append({
            "id": f"container_{i + 1}",
            "name": f"example-service-{i + 1}",
            "image": f"example/service-{i + 1}:latest",
            "status": status,
            "created": f"2025-03-{10 - i:02d}T10:00:00Z",
            "ports": [f"808{i}:808{i}"] if status == "running" else []
        })
    
    return containers

def get_project_structure(project_path, config):
    """Get the project structure from the IDE."""
    # In a real implementation, this would use the MCP client to call the IDE server
    logger.info(f"Getting project structure for {project_path}")
    
    # Simulate the project structure
    structure = {
        "name": os.path.basename(project_path),
        "path": project_path,
        "type": "directory",
        "children": [
            {
                "name": "src",
                "path": f"{project_path}/src",
                "type": "directory",
                "children": [
                    {
                        "name": "main.py",
                        "path": f"{project_path}/src/main.py",
                        "type": "file",
                        "size": 1024,
                        "modified": "2025-03-11T10:00:00Z"
                    },
                    {
                        "name": "utils.py",
                        "path": f"{project_path}/src/utils.py",
                        "type": "file",
                        "size": 2048,
                        "modified": "2025-03-10T14:30:00Z"
                    }
                ]
            },
            {
                "name": "tests",
                "path": f"{project_path}/tests",
                "type": "directory",
                "children": [
                    {
                        "name": "test_main.py",
                        "path": f"{project_path}/tests/test_main.py",
                        "type": "file",
                        "size": 512,
                        "modified": "2025-03-09T15:45:00Z"
                    }
                ]
            },
            {
                "name": "README.md",
                "path": f"{project_path}/README.md",
                "type": "file",
                "size": 256,
                "modified": "2025-03-08T09:15:00Z"
            }
        ]
    }
    
    return structure

def format_containers(containers):
    """Format the container list for display."""
    output = []
    output.append("Docker Containers:")
    
    if not containers:
        output.append("  No containers found.")
        return "\n".join(output)
    
    for i, container in enumerate(containers):
        output.append(f"\n  Container {i + 1}:")
        output.append(f"    ID: {container['id']}")
        output.append(f"    Name: {container['name']}")
        output.append(f"    Image: {container['image']}")
        output.append(f"    Status: {container['status']}")
        output.append(f"    Created: {container['created']}")
        
        if container['ports']:
            output.append(f"    Ports: {', '.join(container['ports'])}")
    
    return "\n".join(output)

def format_project_structure(structure, indent=0):
    """Format the project structure for display."""
    output = []
    
    if indent == 0:
        output.append("Project Structure:")
    
    # Add the current item
    prefix = "  " * indent
    if structure["type"] == "directory":
        output.append(f"{prefix}{structure['name']}/ (Directory)")
    else:
        output.append(f"{prefix}{structure['name']} (File, {structure['size']} bytes, Modified: {structure['modified']})")
    
    # Add children if any
    if structure["type"] == "directory" and "children" in structure:
        for child in structure["children"]:
            output.extend(format_project_structure(child, indent + 1))
    
    return output

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Query developer tools.")
    parser.add_argument("--project-path", default="./example-project", help="Project path to get structure for")
    parser.add_argument("--running-only", action="store_true", help="List only running Docker containers")
    parser.add_argument("--config", default="developer_config.json", help="Path to the configuration file")
    args = parser.parse_args()
    
    # Load the configuration
    config_path = args.config
    if not os.path.isabs(config_path):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_path)
    
    config = load_config(config_path)
    
    # List containers and get project structure
    containers = list_containers(args.running_only, config)
    project_structure = get_project_structure(args.project_path, config)
    
    # Format and display the results
    print(format_containers(containers))
    print("\n" + "\n".join(format_project_structure(project_structure)))

if __name__ == "__main__":
    main()
