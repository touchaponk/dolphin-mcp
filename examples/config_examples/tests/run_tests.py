#!/usr/bin/env python
"""
Test runner for the MCP configuration examples.
This script runs all the tests for the MCP configuration examples.
"""

import os
import sys
import unittest
import argparse

# Add parent directory to path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import test modules
from test_configs import TestConfigs
from test_queries import TestQueries
from test_functional import TestFunctional
from test_weather_news import TestWeatherNewsConfig
from test_github_filesystem import TestGitHubFilesystemConfig
from test_database import TestDatabaseConfig
from test_communication import TestCommunicationConfig
from test_browser_search import TestBrowserSearchConfig
from test_location import TestLocationConfig
from test_finance import TestFinanceConfig
from test_knowledge import TestKnowledgeConfig
from test_monitoring import TestMonitoringConfig
from test_developer import TestDeveloperConfig

def run_tests(test_type=None, verbose=False):
    """Run the tests."""
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Add tests based on the test type
    if test_type == "configs" or test_type is None:
        suite.addTest(unittest.makeSuite(TestConfigs))
    
    if test_type == "queries" or test_type is None:
        suite.addTest(unittest.makeSuite(TestQueries))
    
    if test_type == "functional" or test_type is None:
        suite.addTest(unittest.makeSuite(TestFunctional))
        suite.addTest(unittest.makeSuite(TestWeatherNewsConfig))
        suite.addTest(unittest.makeSuite(TestGitHubFilesystemConfig))
        suite.addTest(unittest.makeSuite(TestDatabaseConfig))
        suite.addTest(unittest.makeSuite(TestCommunicationConfig))
        suite.addTest(unittest.makeSuite(TestBrowserSearchConfig))
        suite.addTest(unittest.makeSuite(TestLocationConfig))
        suite.addTest(unittest.makeSuite(TestFinanceConfig))
        suite.addTest(unittest.makeSuite(TestKnowledgeConfig))
        suite.addTest(unittest.makeSuite(TestMonitoringConfig))
        suite.addTest(unittest.makeSuite(TestDeveloperConfig))
    
    # Run the tests
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    # Return the result
    return result.wasSuccessful()

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run tests for the MCP configuration examples.")
    parser.add_argument("--type", choices=["configs", "queries", "functional"], help="Type of tests to run")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    # Run the tests
    success = run_tests(args.type, args.verbose)
    
    # Exit with the appropriate status code
    sys.exit(0 if success else 1)
