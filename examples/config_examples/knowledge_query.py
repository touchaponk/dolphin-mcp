#!/usr/bin/env python
"""
Query script for the knowledge configuration.
This script demonstrates how to use the memory MCP server.
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
logger = logging.getLogger("knowledge-query")

def load_config(config_path):
    """Load the configuration file."""
    with open(config_path, "r") as f:
        return json.load(f)

def store_fact(fact, config):
    """Store a fact in the memory server."""
    # In a real implementation, this would use the MCP client to call the memory server
    logger.info(f"Storing fact: {fact}")
    
    # Simulate the storage response
    storage_response = {
        "success": True,
        "fact_id": "12345",
        "timestamp": "2025-03-11T10:00:00Z",
        "fact": fact
    }
    
    return storage_response

def retrieve_facts(query, limit, config):
    """Retrieve facts from the memory server."""
    # In a real implementation, this would use the MCP client to call the memory server
    logger.info(f"Retrieving facts for query: {query} with limit {limit}")
    
    # Simulate the retrieval response
    facts = []
    
    if "weather" in query.lower():
        facts.append({
            "fact_id": "12345",
            "fact": "The weather in San Francisco is usually mild with temperatures between 50°F and 70°F.",
            "timestamp": "2025-03-10T10:00:00Z",
            "relevance": 0.95
        })
        facts.append({
            "fact_id": "12346",
            "fact": "San Francisco often experiences fog, especially in the summer months.",
            "timestamp": "2025-03-09T14:30:00Z",
            "relevance": 0.85
        })
    elif "population" in query.lower():
        facts.append({
            "fact_id": "23456",
            "fact": "The population of San Francisco is approximately 815,000 as of 2025.",
            "timestamp": "2025-03-08T09:15:00Z",
            "relevance": 0.98
        })
        facts.append({
            "fact_id": "23457",
            "fact": "San Francisco is the 17th most populous city in the United States.",
            "timestamp": "2025-03-07T16:45:00Z",
            "relevance": 0.75
        })
    else:
        facts.append({
            "fact_id": "34567",
            "fact": f"No specific facts found for query: {query}. Please try a different query.",
            "timestamp": "2025-03-11T10:05:00Z",
            "relevance": 0.5
        })
    
    # Limit the number of facts
    facts = facts[:min(limit, len(facts))]
    
    return facts

def format_storage_response(response):
    """Format the storage response for display."""
    output = []
    output.append("Fact Stored:")
    output.append(f"  Fact ID: {response['fact_id']}")
    output.append(f"  Timestamp: {response['timestamp']}")
    output.append(f"  Fact: {response['fact']}")
    
    return "\n".join(output)

def format_retrieval_response(facts):
    """Format the retrieval response for display."""
    output = []
    output.append("\nFacts Retrieved:")
    
    if not facts:
        output.append("  No facts found.")
        return "\n".join(output)
    
    for i, fact in enumerate(facts):
        output.append(f"\n  Fact {i + 1}:")
        output.append(f"    Fact ID: {fact['fact_id']}")
        output.append(f"    Timestamp: {fact['timestamp']}")
        output.append(f"    Relevance: {fact['relevance']:.2f}")
        output.append(f"    Fact: {fact['fact']}")
    
    return "\n".join(output)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Query the knowledge base.")
    parser.add_argument("--store", help="Fact to store in the knowledge base")
    parser.add_argument("--query", default="weather in San Francisco", help="Query to retrieve facts from the knowledge base")
    parser.add_argument("--limit", type=int, default=5, help="Limit the number of facts to retrieve")
    parser.add_argument("--config", default="knowledge_config.json", help="Path to the configuration file")
    args = parser.parse_args()
    
    # Load the configuration
    config_path = args.config
    if not os.path.isabs(config_path):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_path)
    
    config = load_config(config_path)
    
    # Store a fact if provided
    if args.store:
        storage_response = store_fact(args.store, config)
        print(format_storage_response(storage_response))
    
    # Retrieve facts
    facts = retrieve_facts(args.query, args.limit, config)
    print(format_retrieval_response(facts))

if __name__ == "__main__":
    main()
