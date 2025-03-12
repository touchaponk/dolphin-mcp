#!/usr/bin/env python
"""
Query script for the browser and search configuration.
This script demonstrates how to use the browser and search MCP servers together.
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
logger = logging.getLogger("browser-search-query")

def load_config(config_path):
    """Load the configuration file."""
    with open(config_path, "r") as f:
        return json.load(f)

def search_web(topic, results, config):
    """Search the web for a topic."""
    # In a real implementation, this would use the MCP client to call the search server
    logger.info(f"Searching for '{topic}' with {results} results")
    
    # Simulate the search results
    search_results = []
    for i in range(min(results, 5)):
        search_results.append({
            "title": f"Result {i + 1} for {topic}",
            "url": f"https://example.com/search/{topic.replace(' ', '-')}/{i + 1}",
            "snippet": f"This is a snippet for result {i + 1} about {topic}. It contains some information about the topic that might be useful.",
            "source": "Example Search Engine",
            "published_at": f"2025-03-{11 - i:02d}T10:00:00Z"
        })
    
    return search_results

def browse_url(url, config):
    """Browse a URL."""
    # In a real implementation, this would use the MCP client to call the browser server
    logger.info(f"Browsing URL: {url}")
    
    # Simulate the browser response
    browser_response = {
        "url": url,
        "title": f"Page Title for {url}",
        "content_length": 12345,
        "links": [
            f"{url}/page1",
            f"{url}/page2",
            f"{url}/page3"
        ],
        "images": [
            f"{url}/image1.jpg",
            f"{url}/image2.jpg"
        ],
        "status": "success"
    }
    
    return browser_response

def format_search_results(results):
    """Format the search results for display."""
    output = []
    output.append("Search Results:")
    
    for i, result in enumerate(results):
        output.append(f"\n  Result {i + 1}:")
        output.append(f"  Title: {result['title']}")
        output.append(f"  URL: {result['url']}")
        output.append(f"  Snippet: {result['snippet']}")
        output.append(f"  Source: {result['source']}")
        output.append(f"  Published: {result['published_at']}")
    
    return "\n".join(output)

def format_browser_response(response):
    """Format the browser response for display."""
    output = []
    output.append("\nBrowser Response:")
    output.append(f"  URL: {response['url']}")
    output.append(f"  Title: {response['title']}")
    output.append(f"  Content Length: {response['content_length']} bytes")
    output.append(f"  Status: {response['status']}")
    
    output.append("\n  Links:")
    for link in response['links']:
        output.append(f"    {link}")
    
    output.append("\n  Images:")
    for image in response['images']:
        output.append(f"    {image}")
    
    return "\n".join(output)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Search the web and browse URLs.")
    parser.add_argument("topic", nargs="?", default="artificial intelligence", help="Topic to search for")
    parser.add_argument("--results", type=int, default=3, help="Number of search results to return")
    parser.add_argument("--config", default="browser_search_config.json", help="Path to the configuration file")
    args = parser.parse_args()
    
    # Load the configuration
    config_path = args.config
    if not os.path.isabs(config_path):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_path)
    
    config = load_config(config_path)
    
    # Search the web and browse the first result
    search_results = search_web(args.topic, args.results, config)
    browser_response = browse_url(search_results[0]["url"], config)
    
    # Format and display the results
    print(format_search_results(search_results))
    print(format_browser_response(browser_response))

if __name__ == "__main__":
    main()
