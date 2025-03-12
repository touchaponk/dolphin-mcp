#!/usr/bin/env python
"""
Query script for the database configuration.
This script demonstrates how to use multiple database MCP servers together.
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
logger = logging.getLogger("database-query")

def load_config(config_path):
    """Load the configuration file."""
    with open(config_path, "r") as f:
        return json.load(f)

def query_sqlite(table, limit, config):
    """Query a SQLite database."""
    # In a real implementation, this would use the MCP client to call the SQLite server
    logger.info(f"Querying SQLite table {table} with limit {limit}")
    
    # Simulate the query results
    results = []
    for i in range(min(limit, 10)):
        results.append({
            "id": i + 1,
            "name": f"Item {i + 1}",
            "description": f"Description for item {i + 1}",
            "created_at": f"2025-03-{11 - i:02d}T10:00:00Z"
        })
    
    return results

def query_postgres(table, limit, config):
    """Query a PostgreSQL database."""
    # In a real implementation, this would use the MCP client to call the PostgreSQL server
    logger.info(f"Querying PostgreSQL table {table} with limit {limit}")
    
    # Simulate the query results
    results = []
    for i in range(min(limit, 10)):
        results.append({
            "id": i + 1,
            "name": f"Product {i + 1}",
            "price": 10.0 * (i + 1),
            "stock": 100 - (i * 10),
            "category": "Electronics" if i % 2 == 0 else "Home Goods"
        })
    
    return results

def query_mysql(table, limit, config):
    """Query a MySQL database."""
    # In a real implementation, this would use the MCP client to call the MySQL server
    logger.info(f"Querying MySQL table {table} with limit {limit}")
    
    # Simulate the query results
    results = []
    for i in range(min(limit, 10)):
        results.append({
            "id": i + 1,
            "username": f"user{i + 1}",
            "email": f"user{i + 1}@example.com",
            "active": i % 3 != 0,
            "last_login": f"2025-03-{11 - i:02d}T15:30:00Z"
        })
    
    return results

def format_sqlite_results(results):
    """Format the SQLite query results for display."""
    output = []
    output.append("SQLite Query Results:")
    
    for row in results:
        output.append(f"\n  ID: {row['id']}")
        output.append(f"  Name: {row['name']}")
        output.append(f"  Description: {row['description']}")
        output.append(f"  Created At: {row['created_at']}")
    
    return "\n".join(output)

def format_postgres_results(results):
    """Format the PostgreSQL query results for display."""
    output = []
    output.append("\nPostgreSQL Query Results:")
    
    for row in results:
        output.append(f"\n  ID: {row['id']}")
        output.append(f"  Name: {row['name']}")
        output.append(f"  Price: ${row['price']:.2f}")
        output.append(f"  Stock: {row['stock']}")
        output.append(f"  Category: {row['category']}")
    
    return "\n".join(output)

def format_mysql_results(results):
    """Format the MySQL query results for display."""
    output = []
    output.append("\nMySQL Query Results:")
    
    for row in results:
        output.append(f"\n  ID: {row['id']}")
        output.append(f"  Username: {row['username']}")
        output.append(f"  Email: {row['email']}")
        output.append(f"  Active: {row['active']}")
        output.append(f"  Last Login: {row['last_login']}")
    
    return "\n".join(output)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Query multiple databases.")
    parser.add_argument("--table", default="items", help="Table to query")
    parser.add_argument("--limit", type=int, default=5, help="Limit the number of results")
    parser.add_argument("--config", default="database_config.json", help="Path to the configuration file")
    args = parser.parse_args()
    
    # Load the configuration
    config_path = args.config
    if not os.path.isabs(config_path):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_path)
    
    config = load_config(config_path)
    
    # Query the databases
    sqlite_results = query_sqlite(args.table, args.limit, config)
    postgres_results = query_postgres(args.table, args.limit, config)
    mysql_results = query_mysql(args.table, args.limit, config)
    
    # Format and display the results
    print(format_sqlite_results(sqlite_results))
    print(format_postgres_results(postgres_results))
    print(format_mysql_results(mysql_results))

if __name__ == "__main__":
    main()
