#!/usr/bin/env python
"""
Query script for the GitHub and filesystem configuration.
This script demonstrates how to use the GitHub and filesystem MCP servers together.
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
logger = logging.getLogger("github-filesystem-query")

def load_config(config_path):
    """Load the configuration file."""
    with open(config_path, "r") as f:
        return json.load(f)

def clone_repository(repo, local_dir, config):
    """Clone a GitHub repository."""
    # In a real implementation, this would use the MCP client to call the GitHub server
    logger.info(f"Cloning repository {repo} to {local_dir}")
    
    # Simulate the repository data
    repo_data = {
        "name": repo,
        "url": f"https://github.com/{repo}",
        "description": "A sample repository",
        "stars": 1000,
        "forks": 500,
        "issues": 50,
        "pull_requests": 10,
        "last_commit": "2025-03-10T15:30:00Z",
        "files": [
            "README.md",
            "LICENSE",
            "src/main.py",
            "src/utils.py",
            "tests/test_main.py",
            "tests/test_utils.py"
        ]
    }
    
    return repo_data

def list_files(local_dir, config):
    """List files in a directory."""
    # In a real implementation, this would use the MCP client to call the filesystem server
    logger.info(f"Listing files in {local_dir}")
    
    # Simulate the file list
    file_list = [
        {
            "name": "README.md",
            "type": "file",
            "size": 1024,
            "modified": "2025-03-11T10:00:00Z"
        },
        {
            "name": "LICENSE",
            "type": "file",
            "size": 512,
            "modified": "2025-03-11T10:00:00Z"
        },
        {
            "name": "src",
            "type": "directory",
            "modified": "2025-03-11T10:00:00Z"
        },
        {
            "name": "tests",
            "type": "directory",
            "modified": "2025-03-11T10:00:00Z"
        }
    ]
    
    return file_list

def format_repository(repo_data):
    """Format the repository data for display."""
    output = []
    output.append(f"Repository: {repo_data['name']}")
    output.append(f"URL: {repo_data['url']}")
    output.append(f"Description: {repo_data['description']}")
    output.append(f"Stars: {repo_data['stars']}")
    output.append(f"Forks: {repo_data['forks']}")
    output.append(f"Issues: {repo_data['issues']}")
    output.append(f"Pull Requests: {repo_data['pull_requests']}")
    output.append(f"Last Commit: {repo_data['last_commit']}")
    output.append("\nFiles:")
    
    for file in repo_data["files"]:
        output.append(f"  {file}")
    
    return "\n".join(output)

def format_files(file_list):
    """Format the file list for display."""
    output = []
    output.append("\nLocal Files:")
    
    for file in file_list:
        if file["type"] == "directory":
            output.append(f"  {file['name']}/ (Directory, Modified: {file['modified']})")
        else:
            output.append(f"  {file['name']} (File, Size: {file['size']} bytes, Modified: {file['modified']})")
    
    return "\n".join(output)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Query GitHub and filesystem.")
    parser.add_argument("repo", nargs="?", default="octocat/Hello-World", help="GitHub repository to clone")
    parser.add_argument("--local-dir", default="./repo", help="Local directory to clone to")
    parser.add_argument("--config", default="github_filesystem_config.json", help="Path to the configuration file")
    args = parser.parse_args()
    
    # Load the configuration
    config_path = args.config
    if not os.path.isabs(config_path):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_path)
    
    config = load_config(config_path)
    
    # Clone the repository and list files
    repo_data = clone_repository(args.repo, args.local_dir, config)
    file_list = list_files(args.local_dir, config)
    
    # Format and display the results
    print(format_repository(repo_data))
    print(format_files(file_list))

if __name__ == "__main__":
    main()
