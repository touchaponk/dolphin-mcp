#!/usr/bin/env python
"""
Example script that uses Dolphin-MCP to query the dolphin database.
This demonstrates how to set up a configuration file and run queries
against the test SQLite database created by setup_dolphin_db.py.
"""

import os
import sys
import json
import subprocess
import argparse
import asyncio
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def ensure_database_exists():
    """Make sure the test database exists, create it if not."""
    db_path = os.path.expanduser("~/.dolphin/dolphin.db")
    if not os.path.exists(db_path):
        print("Database not found. Setting up test database...")
        setup_script = os.path.join(os.path.dirname(__file__), "setup_dolphin_db.py")
        subprocess.run([sys.executable, setup_script], check=True)
    return db_path

def create_config_file(db_path):
    """Create a temporary MCP config file for the SQLite server."""
    config = {
        "mcpServers": {
            "dolphin-db": {
                "command": "uvx" if shutil.which("uvx") else "python",
                "args": ["mcp-server-sqlite", "--db-path", db_path] if shutil.which("uvx") else ["-m", "mcp_server.sqlite", "--db-path", db_path]
            }
        }
    }
    
    config_path = os.path.join(os.path.dirname(__file__), "dolphin_db_config.json")
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    
    return config_path

def main():
    parser = argparse.ArgumentParser(description="Query the dolphin database using Dolphin-MCP")
    parser.add_argument("prompt", nargs="?", default="List all dolphin species in the database", 
                        help="The prompt to send to the AI model")
    args = parser.parse_args()
    
    # Ensure required tools are available
    try:
        import shutil
        if not shutil.which("mcp-server-sqlite") and not os.path.exists("mcp_server/sqlite.py"):
            print("Error: mcp-server-sqlite is not installed or not in PATH")
            print("Install it with: pip install mcp-server-sqlite")
            return 1
    except ImportError:
        print("Error: Required packages are not installed")
        print("Install them with: pip install -r requirements.txt")
        return 1
    
    # Make sure database exists
    db_path = ensure_database_exists()
    
    # Create config file
    config_path = create_config_file(db_path)
    
    # Import our main script
    try:
        from src.dolphin_mcp import main as dolphin_main
        
        # Run the query
        print(f"Querying dolphin database with prompt: '{args.prompt}'")
        print("=" * 80)
        
        # Set up arguments for the main function
        sys.argv = [
            "dolphin_mcp.py",
            args.prompt,
            "--config", config_path
        ]
        
        # Run the main function
        asyncio.run(dolphin_main())
        
    except ImportError:
        print("Error: Could not import dolphin_mcp.py")
        print("Make sure you're running this script from the project root directory")
        return 1
    except Exception as e:
        print(f"Error running query: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    import shutil  # Import here for the function scope
    sys.exit(main())
