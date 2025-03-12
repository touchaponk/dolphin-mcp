#!/usr/bin/env python
"""
Query script for the monitoring configuration.
This script demonstrates how to use the Sentry MCP server.
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
logger = logging.getLogger("monitoring-query")

def load_config(config_path):
    """Load the configuration file."""
    with open(config_path, "r") as f:
        return json.load(f)

def get_issues(project, status, limit, config):
    """Get issues from Sentry."""
    # In a real implementation, this would use the MCP client to call the Sentry server
    logger.info(f"Getting {status} issues for project {project} with limit {limit}")
    
    # Simulate the issues
    issues = []
    for i in range(min(limit, 5)):
        issues.append({
            "id": f"ISSUE-{i + 1}",
            "title": f"Error in module_{i + 1}.py: {status.title()} Exception",
            "status": status,
            "level": "error" if i % 2 == 0 else "warning",
            "events": 10 * (i + 1),
            "users_affected": 5 * (i + 1),
            "first_seen": f"2025-03-{10 - i:02d}T10:00:00Z",
            "last_seen": "2025-03-11T10:00:00Z",
            "url": f"https://sentry.io/organizations/example/issues/{i + 1}/"
        })
    
    return issues

def get_performance(project, transaction, limit, config):
    """Get performance metrics from Sentry."""
    # In a real implementation, this would use the MCP client to call the Sentry server
    logger.info(f"Getting performance metrics for project {project}, transaction {transaction} with limit {limit}")
    
    # Simulate the performance metrics
    metrics = []
    for i in range(min(limit, 5)):
        metrics.append({
            "id": f"METRIC-{i + 1}",
            "transaction": transaction or f"/api/endpoint_{i + 1}",
            "avg_duration": 100 + (i * 50),  # milliseconds
            "p50": 90 + (i * 40),
            "p95": 150 + (i * 60),
            "p99": 200 + (i * 80),
            "throughput": 1000 - (i * 100),
            "failure_rate": 0.01 * (i + 1),
            "timestamp": f"2025-03-{11 - i:02d}T10:00:00Z"
        })
    
    return metrics

def format_issues(issues):
    """Format the issues for display."""
    output = []
    output.append("Sentry Issues:")
    
    if not issues:
        output.append("  No issues found.")
        return "\n".join(output)
    
    for i, issue in enumerate(issues):
        output.append(f"\n  Issue {i + 1}:")
        output.append(f"    ID: {issue['id']}")
        output.append(f"    Title: {issue['title']}")
        output.append(f"    Status: {issue['status']}")
        output.append(f"    Level: {issue['level']}")
        output.append(f"    Events: {issue['events']}")
        output.append(f"    Users Affected: {issue['users_affected']}")
        output.append(f"    First Seen: {issue['first_seen']}")
        output.append(f"    Last Seen: {issue['last_seen']}")
        output.append(f"    URL: {issue['url']}")
    
    return "\n".join(output)

def format_performance(metrics):
    """Format the performance metrics for display."""
    output = []
    output.append("\nSentry Performance Metrics:")
    
    if not metrics:
        output.append("  No metrics found.")
        return "\n".join(output)
    
    for i, metric in enumerate(metrics):
        output.append(f"\n  Metric {i + 1}:")
        output.append(f"    ID: {metric['id']}")
        output.append(f"    Transaction: {metric['transaction']}")
        output.append(f"    Avg Duration: {metric['avg_duration']} ms")
        output.append(f"    p50: {metric['p50']} ms")
        output.append(f"    p95: {metric['p95']} ms")
        output.append(f"    p99: {metric['p99']} ms")
        output.append(f"    Throughput: {metric['throughput']} req/min")
        output.append(f"    Failure Rate: {metric['failure_rate']:.2%}")
        output.append(f"    Timestamp: {metric['timestamp']}")
    
    return "\n".join(output)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Query Sentry for monitoring data.")
    parser.add_argument("--project", default="example-project", help="Sentry project to query")
    parser.add_argument("--status", default="unresolved", choices=["unresolved", "resolved", "ignored"], help="Issue status to filter by")
    parser.add_argument("--transaction", help="Transaction name to filter performance metrics by")
    parser.add_argument("--limit", type=int, default=5, help="Limit the number of results")
    parser.add_argument("--config", default="monitoring_config.json", help="Path to the configuration file")
    args = parser.parse_args()
    
    # Load the configuration
    config_path = args.config
    if not os.path.isabs(config_path):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_path)
    
    config = load_config(config_path)
    
    # Get issues and performance metrics
    issues = get_issues(args.project, args.status, args.limit, config)
    performance = get_performance(args.project, args.transaction, args.limit, config)
    
    # Format and display the results
    print(format_issues(issues))
    print(format_performance(performance))

if __name__ == "__main__":
    main()
