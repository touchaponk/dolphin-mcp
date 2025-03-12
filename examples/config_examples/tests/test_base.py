#!/usr/bin/env python
"""
Base test class for MCP configuration examples.
This module provides a base test class that all test classes can inherit from.
"""

import os
import sys
import json
import unittest
import subprocess
from pathlib import Path

class BaseMCPTest(unittest.TestCase):
    """Base test class for MCP configuration examples."""
    
    def setUp(self):
        """Set up the test case."""
        # Get the directory containing the configuration files
        self.config_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Initialize the list of mock servers
        self.mock_servers = []
        
        # Server name mappings
        self.server_mappings = {
            "weather": ["weather", "openweathermap"],
            "news": ["news", "brave-search", "fetch"],
            "github": ["github"],
            "filesystem": ["filesystem"],
            "sqlite": ["sqlite"],
            "postgres": ["postgres", "postgresql"],
            "mysql": ["mysql", "mariadb"],
            "email": ["email", "gmail"],
            "calendar": ["calendar"],
            "slack": ["slack"],
            "browser": ["browser", "puppeteer"],
            "search": ["search", "brave-search", "fetch"],
            "maps": ["maps", "google-maps"],
            "timeserver": ["timeserver", "time"],
            "stocks": ["stocks", "alpha-vantage"],
            "crypto": ["crypto", "coincap"],
            "memory": ["memory"],
            "errors": ["errors", "sentry"],
            "performance": ["performance", "grafana"],
            "security": ["security", "virustotal", "shodan"],
            "packages": ["packages", "package-version"]
        }
    
    def tearDown(self):
        """Tear down the test case."""
        # Terminate any mock servers that were started
        for server in self.mock_servers:
            if server.poll() is None:  # Check if the server is still running
                server.terminate()
    
    def load_config(self, config_name):
        """Load a configuration file."""
        config_path = os.path.join(self.config_dir, config_name)
        with open(config_path, "r") as f:
            return json.load(f)
    
    def start_mock_server(self, command, args):
        """Start a mock MCP server."""
        try:
            # Start the server
            server = subprocess.Popen(
                [command] + args,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            # Add the server to the list of mock servers
            self.mock_servers.append(server)
            
            # Wait for the server to start up
            # The server should send an initialize response
            line = server.stdout.readline()
            if not line:
                # Check if the server has terminated
                if server.poll() is not None:
                    stderr = server.stderr.read()
                    raise RuntimeError(f"Server failed to start: {stderr}")
                
                # Server is still running but didn't send an initialize response
                raise RuntimeError("Server didn't send an initialize response")
            
            # Parse the initialize response
            try:
                response = json.loads(line)
                if "result" not in response or "id" not in response or response["id"] != 1:
                    raise RuntimeError(f"Invalid initialize response: {response}")
            except json.JSONDecodeError:
                raise RuntimeError(f"Invalid JSON in initialize response: {line}")
            
            return server
        except Exception as e:
            self.fail(f"Error starting mock server: {e}")
            return None
    
    def server_exists(self, server_name, config):
        """Check if a server exists in the configuration."""
        if server_name in config["mcpServers"]:
            return True
        
        # Check for alternative names
        if server_name in self.server_mappings:
            for alt_name in self.server_mappings[server_name]:
                if alt_name in config["mcpServers"]:
                    return True
        
        return False
    
    def get_server_name(self, server_name, config):
        """Get the actual server name from the configuration."""
        if server_name in config["mcpServers"]:
            return server_name
        
        # Check for alternative names
        if server_name in self.server_mappings:
            for alt_name in self.server_mappings[server_name]:
                if alt_name in config["mcpServers"]:
                    return alt_name
        
        return server_name
