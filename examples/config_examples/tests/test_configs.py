#!/usr/bin/env python
"""
Tests for MCP configuration files.
This script tests that the configuration files are valid.
"""

import os
import sys
import json
import unittest
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_base import BaseMCPTest

class TestConfigs(BaseMCPTest):
    """Test case for configuration files."""
    
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
        
        # Check that we have all the expected configuration files
        expected_configs = [
            "weather_news_config.json",
            "github_filesystem_config.json",
            "database_config.json",
            "communication_config.json",
            "browser_search_config.json",
            "location_config.json",
            "finance_config.json",
            "knowledge_config.json",
            "monitoring_config.json",
            "developer_config.json"
        ]
        
        for config in expected_configs:
            self.assertIn(config, self.config_files, f"Expected configuration file not found: {config}")
    
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
                
                # Add env if it doesn't exist
                if "env" not in server_config:
                    server_config["env"] = {}
    
    def test_weather_news_config(self):
        """Test the weather and news configuration."""
        config = self.load_config("weather_news_config.json")
        self.assertTrue(self.server_exists("weather", config), "Weather server not found in weather_news_config.json")
        self.assertTrue(self.server_exists("news", config), "News server not found in weather_news_config.json")
    
    def test_github_filesystem_config(self):
        """Test the GitHub and filesystem configuration."""
        config = self.load_config("github_filesystem_config.json")
        self.assertTrue(self.server_exists("github", config), "GitHub server not found in github_filesystem_config.json")
        self.assertTrue(self.server_exists("filesystem", config), "Filesystem server not found in github_filesystem_config.json")
    
    def test_database_config(self):
        """Test the database configuration."""
        config = self.load_config("database_config.json")
        self.assertTrue(self.server_exists("sqlite", config), "SQLite server not found in database_config.json")
        self.assertTrue(self.server_exists("postgres", config), "PostgreSQL server not found in database_config.json")
        self.assertTrue(self.server_exists("mysql", config), "MySQL server not found in database_config.json")
    
    def test_communication_config(self):
        """Test the communication configuration."""
        config = self.load_config("communication_config.json")
        self.assertTrue(self.server_exists("email", config), "Email server not found in communication_config.json")
        self.assertTrue(self.server_exists("calendar", config), "Calendar server not found in communication_config.json")
        self.assertTrue(self.server_exists("slack", config), "Slack server not found in communication_config.json")
    
    def test_browser_search_config(self):
        """Test the browser and search configuration."""
        config = self.load_config("browser_search_config.json")
        self.assertTrue(self.server_exists("browser", config), "Browser server not found in browser_search_config.json")
        self.assertTrue(self.server_exists("search", config), "Search server not found in browser_search_config.json")
    
    def test_location_config(self):
        """Test the location configuration."""
        config = self.load_config("location_config.json")
        self.assertTrue(self.server_exists("maps", config), "Maps server not found in location_config.json")
        self.assertTrue(self.server_exists("timeserver", config), "Timeserver not found in location_config.json")
        self.assertTrue(self.server_exists("weather", config), "Weather server not found in location_config.json")
    
    def test_finance_config(self):
        """Test the finance configuration."""
        config = self.load_config("finance_config.json")
        self.assertTrue(self.server_exists("stocks", config), "Stocks server not found in finance_config.json")
        self.assertTrue(self.server_exists("crypto", config), "Crypto server not found in finance_config.json")
        self.assertTrue(self.server_exists("news", config), "News server not found in finance_config.json")
    
    def test_knowledge_config(self):
        """Test the knowledge configuration."""
        config = self.load_config("knowledge_config.json")
        self.assertTrue(self.server_exists("memory", config), "Memory server not found in knowledge_config.json")
        self.assertTrue(self.server_exists("filesystem", config), "Filesystem server not found in knowledge_config.json")
        self.assertTrue(self.server_exists("search", config), "Search server not found in knowledge_config.json")
    
    def test_monitoring_config(self):
        """Test the monitoring configuration."""
        config = self.load_config("monitoring_config.json")
        self.assertTrue(self.server_exists("errors", config), "Errors server not found in monitoring_config.json")
        self.assertTrue(self.server_exists("performance", config), "Performance server not found in monitoring_config.json")
        self.assertTrue(self.server_exists("security", config), "Security server not found in monitoring_config.json")
    
    def test_developer_config(self):
        """Test the developer configuration."""
        config = self.load_config("developer_config.json")
        self.assertTrue(self.server_exists("packages", config), "Packages server not found in developer_config.json")
        self.assertTrue(self.server_exists("docker", config), "Docker server not found in developer_config.json")
        self.assertTrue(self.server_exists("openapi", config), "OpenAPI server not found in developer_config.json")

if __name__ == "__main__":
    unittest.main()
