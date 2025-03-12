#!/usr/bin/env python
"""
Query script for the weather and news configuration.
This script demonstrates how to use the weather and news MCP servers together.
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
logger = logging.getLogger("weather-news-query")

def load_config(config_path):
    """Load the configuration file."""
    with open(config_path, "r") as f:
        return json.load(f)

def get_weather(city, config):
    """Get the weather for a city."""
    # In a real implementation, this would use the MCP client to call the weather server
    logger.info(f"Getting weather for {city}")
    
    # Simulate the weather data
    weather_data = {
        "location": city,
        "temperature": 22.5,
        "conditions": "Partly Cloudy",
        "humidity": 65,
        "wind_speed": 10,
        "forecast": [
            {"day": "Today", "high": 24, "low": 18, "conditions": "Partly Cloudy"},
            {"day": "Tomorrow", "high": 26, "low": 19, "conditions": "Sunny"},
            {"day": "Wednesday", "high": 25, "low": 17, "conditions": "Cloudy"}
        ]
    }
    
    return weather_data

def get_news(city, config):
    """Get the news for a city."""
    # In a real implementation, this would use the MCP client to call the news server
    logger.info(f"Getting news for {city}")
    
    # Simulate the news data
    news_data = {
        "location": city,
        "articles": [
            {
                "title": f"New Development Project Announced in {city}",
                "summary": f"A major development project has been announced in {city}, promising to create thousands of jobs.",
                "source": "City News",
                "published_at": "2025-03-11T10:00:00Z"
            },
            {
                "title": f"{city} Hosts International Conference",
                "summary": f"{city} is hosting an international conference on climate change this week.",
                "source": "Global News",
                "published_at": "2025-03-10T14:30:00Z"
            },
            {
                "title": f"Local Restaurant in {city} Wins Award",
                "summary": f"A local restaurant in {city} has won a prestigious culinary award.",
                "source": "Food & Dining",
                "published_at": "2025-03-09T18:15:00Z"
            }
        ]
    }
    
    return news_data

def format_weather(weather_data):
    """Format the weather data for display."""
    output = []
    output.append(f"Weather for {weather_data['location']}:")
    output.append(f"  Temperature: {weather_data['temperature']}°C")
    output.append(f"  Conditions: {weather_data['conditions']}")
    output.append(f"  Humidity: {weather_data['humidity']}%")
    output.append(f"  Wind Speed: {weather_data['wind_speed']} km/h")
    output.append("\nForecast:")
    
    for day in weather_data["forecast"]:
        output.append(f"  {day['day']}: {day['conditions']}, High: {day['high']}°C, Low: {day['low']}°C")
    
    return "\n".join(output)

def format_news(news_data):
    """Format the news data for display."""
    output = []
    output.append(f"\nNews for {news_data['location']}:")
    
    for article in news_data["articles"]:
        output.append(f"\n  {article['title']}")
        output.append(f"  {article['summary']}")
        output.append(f"  Source: {article['source']}")
        output.append(f"  Published: {article['published_at']}")
    
    return "\n".join(output)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Query weather and news for a city.")
    parser.add_argument("city", nargs="?", default="San Francisco", help="City to query")
    parser.add_argument("--config", default="weather_news_config.json", help="Path to the configuration file")
    args = parser.parse_args()
    
    # Load the configuration
    config_path = args.config
    if not os.path.isabs(config_path):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_path)
    
    config = load_config(config_path)
    
    # Get the weather and news
    weather_data = get_weather(args.city, config)
    news_data = get_news(args.city, config)
    
    # Format and display the results
    print(format_weather(weather_data))
    print(format_news(news_data))

if __name__ == "__main__":
    main()
