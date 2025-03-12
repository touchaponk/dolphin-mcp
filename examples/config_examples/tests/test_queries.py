#!/usr/bin/env python
"""
Tests for MCP query scripts.
This script tests that the query scripts are valid and can be executed.
"""

import os
import sys
import json
import unittest
import importlib.util
from pathlib import Path

# Add parent directory to path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from test_base import BaseMCPTest

class TestQueries(BaseMCPTest):
    """Test case for query scripts."""
    
    def setUp(self):
        """Set up the test case."""
        super().setUp()
        
        # Get the list of query scripts
        self.query_scripts = [
            f for f in os.listdir(self.config_dir)
            if f.endswith("_query.py") and os.path.isfile(os.path.join(self.config_dir, f))
        ]
    
    def test_query_scripts_exist(self):
        """Test that the query scripts exist."""
        # Check that we have at least one query script
        self.assertGreater(len(self.query_scripts), 0, "No query scripts found")
        
        # Check that we have all the expected query scripts
        expected_queries = [
            "weather_news_query.py",
            "github_filesystem_query.py",
            "database_query.py",
            "communication_query.py",
            "browser_search_query.py",
            "location_query.py",
            "finance_query.py",
            "knowledge_query.py",
            "monitoring_query.py",
            "developer_query.py"
        ]
        
        for query in expected_queries:
            self.assertIn(query, self.query_scripts, f"Expected query script not found: {query}")
    
    def test_query_scripts_executable(self):
        """Test that the query scripts are executable."""
        for query_script in self.query_scripts:
            query_script_path = os.path.join(self.config_dir, query_script)
            
            # Check that the script is executable
            self.assertTrue(os.access(query_script_path, os.X_OK), f"Query script not executable: {query_script}")
    
    def test_query_scripts_importable(self):
        """Test that the query scripts can be imported."""
        for query_script in self.query_scripts:
            query_script_path = os.path.join(self.config_dir, query_script)
            
            try:
                # Import the script as a module
                spec = importlib.util.spec_from_file_location("module", query_script_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            except Exception as e:
                self.fail(f"Error importing query script {query_script}: {e}")
    
    def test_query_scripts_have_config(self):
        """Test that each query script has a corresponding configuration file."""
        for query_script in self.query_scripts:
            config_file = query_script.replace("_query.py", "_config.json")
            config_path = os.path.join(self.config_dir, config_file)
            
            self.assertTrue(os.path.isfile(config_path), f"Configuration file not found for query script: {query_script}")
    
    def test_weather_news_query(self):
        """Test the weather and news query script."""
        self._test_query_script("weather_news_query.py")
    
    def test_github_filesystem_query(self):
        """Test the GitHub and filesystem query script."""
        self._test_query_script("github_filesystem_query.py")
    
    def test_database_query(self):
        """Test the database query script."""
        self._test_query_script("database_query.py")
    
    def test_communication_query(self):
        """Test the communication query script."""
        self._test_query_script("communication_query.py")
    
    def test_browser_search_query(self):
        """Test the browser and search query script."""
        self._test_query_script("browser_search_query.py")
    
    def test_location_query(self):
        """Test the location query script."""
        self._test_query_script("location_query.py")
    
    def test_finance_query(self):
        """Test the finance query script."""
        self._test_query_script("finance_query.py")
    
    def test_knowledge_query(self):
        """Test the knowledge query script."""
        self._test_query_script("knowledge_query.py")
    
    def test_monitoring_query(self):
        """Test the monitoring query script."""
        self._test_query_script("monitoring_query.py")
    
    def test_developer_query(self):
        """Test the developer query script."""
        self._test_query_script("developer_query.py")
    
    def _test_query_script(self, query_script):
        """Test a query script."""
        query_script_path = os.path.join(self.config_dir, query_script)
        
        # Check that the script exists
        self.assertTrue(os.path.isfile(query_script_path), f"Query script not found: {query_script}")
        
        # Check that the script is executable
        self.assertTrue(os.access(query_script_path, os.X_OK), f"Query script not executable: {query_script}")
        
        try:
            # Import the script as a module
            spec = importlib.util.spec_from_file_location("module", query_script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check that the module has a main function
            self.assertTrue(hasattr(module, "main"), f"Query script missing main function: {query_script}")
        except Exception as e:
            self.fail(f"Error importing query script {query_script}: {e}")

if __name__ == "__main__":
    unittest.main()
