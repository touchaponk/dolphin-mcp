#!/usr/bin/env python
"""
Functional test for the weather and news configuration.
This script tests the weather_news_config.json configuration with mock MCP servers.
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

class TestWeatherNewsConfig(BaseMCPTest):
    """Test case for the weather and news configuration."""
    
    def setUp(self):
        """Set up the test case."""
        super().setUp()
        self.config_name = "weather_news_config.json"
        self.query_script = "weather_news_query.py"
        
        # Load the configuration
        self.config = self.load_config(self.config_name)
    
    def test_config_structure(self):
        """Test that the configuration has the expected structure."""
        self.assertIn("mcpServers", self.config, "Configuration missing mcpServers key")
        
        # Check that the configuration has the expected servers
        expected_servers = ["weather", "news"]
        for server in expected_servers:
            self.assertTrue(self.server_exists(server, self.config), f"Configuration missing {server} server")
    
    def test_mock_servers(self):
        """Test that the mock servers can be started."""
        # Start the weather server
        weather_server = self.start_mock_server(
            sys.executable,
            [os.path.join(self.config_dir, "tests", "mocks", "mock_server.py"), "--server-type", "weather"]
        )
        self.assertIsNotNone(weather_server, "Failed to start weather server")
        
        # Start the news server
        news_server = self.start_mock_server(
            sys.executable,
            [os.path.join(self.config_dir, "tests", "mocks", "mock_server.py"), "--server-type", "brave_search"]
        )
        self.assertIsNotNone(news_server, "Failed to start news server")
    
    def test_query_execution(self):
        """Test that the query script can be executed with mock servers."""
        # Create a temporary configuration file that uses the mock servers
        temp_config = {
            "mcpServers": {
                "weather": {
                    "command": sys.executable,
                    "args": [os.path.join(self.config_dir, "tests", "mocks", "mock_server.py"), "--server-type", "weather"],
                    "env": {}
                },
                "brave-search": {
                    "command": sys.executable,
                    "args": [os.path.join(self.config_dir, "tests", "mocks", "mock_server.py"), "--server-type", "brave_search"],
                    "env": {}
                }
            }
        }
        
        temp_config_path = os.path.join(self.config_dir, "tests", "temp_weather_news_config.json")
        with open(temp_config_path, "w") as f:
            json.dump(temp_config, f)
        
        try:
            # Make the query script executable
            query_script_path = os.path.join(self.config_dir, self.query_script)
            os.chmod(query_script_path, 0o755)
            
            # Execute the query script with the temporary configuration
            result = subprocess.run(
                [sys.executable, query_script_path, "San Francisco", "--config", temp_config_path],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Check that the script executed successfully
            self.assertEqual(result.returncode, 0, f"Query script failed with error: {result.stderr}")
            
            # Check that the output contains expected content
            self.assertIn("weather", result.stdout.lower(), "Output does not contain weather information")
            self.assertIn("news", result.stdout.lower(), "Output does not contain news information")
            
            print("Weather and news query executed successfully.")
            print("Output excerpt:")
            print("\n".join(result.stdout.split("\n")[:10]) + "\n...")
            
        except subprocess.CalledProcessError as e:
            self.fail(f"Error executing query: {e}")
        finally:
            # Clean up the temporary configuration file
            if os.path.exists(temp_config_path):
                os.remove(temp_config_path)

if __name__ == "__main__":
    unittest.main()
