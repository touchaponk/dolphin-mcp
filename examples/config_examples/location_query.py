#!/usr/bin/env python
"""
Query script for the location configuration.
This script demonstrates how to use the maps, timeserver, and weather MCP servers together.
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
logger = logging.getLogger("location-query")

def load_config(config_path):
    """Load the configuration file."""
    with open(config_path, "r") as f:
        return json.load(f)

def get_directions(origin, destination, stops, config):
    """Get directions from origin to destination with optional stops."""
    # In a real implementation, this would use the MCP client to call the maps server
    logger.info(f"Getting directions from {origin} to {destination} with stops at {stops}")
    
    # Simulate the directions
    directions = {
        "origin": origin,
        "destination": destination,
        "stops": stops,
        "distance": 1234.5,
        "duration": 7200,  # seconds
        "steps": [
            {
                "instruction": f"Start from {origin}",
                "distance": 0,
                "duration": 0
            }
        ]
    }
    
    # Add steps for each stop
    total_distance = 0
    total_duration = 0
    
    for stop in stops:
        distance = 300 + (total_distance * 0.1)  # Simulate increasing distances
        duration = 1800 + (total_duration * 0.1)  # Simulate increasing durations
        
        total_distance += distance
        total_duration += duration
        
        directions["steps"].append({
            "instruction": f"Continue to {stop}",
            "distance": distance,
            "duration": duration
        })
    
    # Add final step to destination
    final_distance = 400 + (total_distance * 0.1)
    final_duration = 2400 + (total_duration * 0.1)
    
    directions["steps"].append({
        "instruction": f"Arrive at {destination}",
        "distance": final_distance,
        "duration": final_duration
    })
    
    # Update total distance and duration
    directions["distance"] = total_distance + final_distance
    directions["duration"] = total_duration + final_duration
    
    return directions

def get_local_time(location, config):
    """Get the local time for a location."""
    # In a real implementation, this would use the MCP client to call the timeserver
    logger.info(f"Getting local time for {location}")
    
    # Simulate the time data
    time_data = {
        "location": location,
        "timezone": "America/Los_Angeles" if "San Francisco" in location else "America/New_York",
        "local_time": "2025-03-11T19:30:00Z" if "San Francisco" in location else "2025-03-11T22:30:00Z",
        "utc_offset": "-07:00" if "San Francisco" in location else "-04:00"
    }
    
    return time_data

def get_weather(location, config):
    """Get the weather for a location."""
    # In a real implementation, this would use the MCP client to call the weather server
    logger.info(f"Getting weather for {location}")
    
    # Simulate the weather data
    weather_data = {
        "location": location,
        "temperature": 18.5 if "San Francisco" in location else 12.3,
        "conditions": "Partly Cloudy" if "San Francisco" in location else "Rainy",
        "humidity": 65 if "San Francisco" in location else 80,
        "wind_speed": 10 if "San Francisco" in location else 15
    }
    
    return weather_data

def format_directions(directions):
    """Format the directions for display."""
    output = []
    output.append("Directions:")
    output.append(f"  From: {directions['origin']}")
    output.append(f"  To: {directions['destination']}")
    
    if directions["stops"]:
        output.append(f"  Stops: {', '.join(directions['stops'])}")
    
    output.append(f"  Total Distance: {directions['distance']:.1f} km")
    output.append(f"  Total Duration: {directions['duration'] // 3600} hours {(directions['duration'] % 3600) // 60} minutes")
    
    output.append("\n  Steps:")
    for i, step in enumerate(directions["steps"]):
        output.append(f"    {i + 1}. {step['instruction']}")
        if i > 0:  # Skip distance/duration for the starting point
            output.append(f"       Distance: {step['distance']:.1f} km")
            output.append(f"       Duration: {step['duration'] // 3600} hours {(step['duration'] % 3600) // 60} minutes")
    
    return "\n".join(output)

def format_time(time_data):
    """Format the time data for display."""
    output = []
    output.append(f"\nLocal Time in {time_data['location']}:")
    output.append(f"  Timezone: {time_data['timezone']}")
    output.append(f"  Local Time: {time_data['local_time']}")
    output.append(f"  UTC Offset: {time_data['utc_offset']}")
    
    return "\n".join(output)

def format_weather(weather_data):
    """Format the weather data for display."""
    output = []
    output.append(f"\nWeather in {weather_data['location']}:")
    output.append(f"  Temperature: {weather_data['temperature']}°C")
    output.append(f"  Conditions: {weather_data['conditions']}")
    output.append(f"  Humidity: {weather_data['humidity']}%")
    output.append(f"  Wind Speed: {weather_data['wind_speed']} km/h")
    
    return "\n".join(output)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Query location-based services.")
    parser.add_argument("--origin", default="New York, NY", help="Origin location")
    parser.add_argument("--destination", default="San Francisco, CA", help="Destination location")
    parser.add_argument("--stops", default="Chicago, IL;Denver, CO", help="Semicolon-separated list of stops")
    parser.add_argument("--config", default="location_config.json", help="Path to the configuration file")
    args = parser.parse_args()
    
    # Load the configuration
    config_path = args.config
    if not os.path.isabs(config_path):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config_path)
    
    config = load_config(config_path)
    
    # Parse the stops
    stops = args.stops.split(";") if args.stops else []
    
    # Get directions, local time, and weather
    directions = get_directions(args.origin, args.destination, stops, config)
    origin_time = get_local_time(args.origin, config)
    destination_time = get_local_time(args.destination, config)
    origin_weather = get_weather(args.origin, config)
    destination_weather = get_weather(args.destination, config)
    
    # Format and display the results
    print(format_directions(directions))
    print(format_time(origin_time))
    print(format_time(destination_time))
    print(format_weather(origin_weather))
    print(format_weather(destination_weather))

if __name__ == "__main__":
    main()
