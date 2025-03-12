#!/usr/bin/env python
"""
Functional tests for MCP configuration examples.
This script tests that the configurations and query scripts work together.
"""

import os
import sys
import json
import unittest
import subprocess
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_base import BaseMCPTest

class TestFunctional(BaseMCPTest):
    """Test case for functional tests."""
    
    def setUp(self):
        """Set up the test case."""
        super().setUp()
        
        # Get the list of configuration files
        self.config_files = [
            f for f in os.listdir(self.config_dir)
            if f.endswith("_config.json") and os.path.isfile(os.path.join(self.config_dir, f))
        ]
    
    def test_config_files_exist(self):
        """Test that the configuration files exist."""
        # Check that we have at least one configuration file
        self.assertGreater(len(self.config_files), 0, "No configuration files found")
        
        # Check that each configuration file has a corresponding query script
        for config_file in self.config_files:
            query_script = config_file.replace("_config.json", "_query.py")
            self.assertTrue(
                os.path.isfile(os.path.join(self.config_dir, query_script)),
                f"Query script not found for configuration: {config_file}"
            )
    
    def test_config_files_valid(self):
        """Test that the configuration files are valid."""
        for config_file in self.config_files:
            # Load the configuration
            config_path = os.path.join(self.config_dir, config_file)
            with open(config_path, "r") as f:
                config = json.load(f)
            
            # Check that the configuration has the expected structure
            self.assertIn("mcpServers", config, f"Configuration missing mcpServers key: {config_file}")
            self.assertIsInstance(config["mcpServers"], dict, f"mcpServers is not a dictionary: {config_file}")
            
            # Check that each server has the expected structure
            for server_name, server_config in config["mcpServers"].items():
                self.assertIn("command", server_config, f"Server missing command key: {server_name} in {config_file}")
                self.assertIn("args", server_config, f"Server missing args key: {server_name} in {config_file}")
                self.assertIn("env", server_config, f"Server missing env key: {server_name} in {config_file}")
    
    def test_query_scripts_executable(self):
        """Test that the query scripts are executable."""
        for config_file in self.config_files:
            query_script = config_file.replace("_config.json", "_query.py")
            query_script_path = os.path.join(self.config_dir, query_script)
            
            # Check that the script is executable
            self.assertTrue(os.access(query_script_path, os.X_OK), f"Query script not executable: {query_script}")
            
            # Check that the script can be imported
            try:
                # Add the config directory to the path
                sys.path.insert(0, self.config_dir)
                
                # Import the script
                module_name = query_script.replace(".py", "")
                __import__(module_name)
                
                # Remove the config directory from the path
                sys.path.pop(0)
            except ImportError as e:
                self.fail(f"Error importing query script {query_script}: {e}")
            except Exception as e:
                self.fail(f"Error in query script {query_script}: {e}")

if __name__ == "__main__":
    unittest.main()
