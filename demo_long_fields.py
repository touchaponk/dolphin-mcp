#!/usr/bin/env python3
"""
Integration test showing the tool response write-to-file feature in action.
"""
import sys
import os
import json
import tempfile

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dolphin_mcp.client import process_long_fields

def demo_long_field_handling():
    """Demonstrate how the long field handling works in practice."""
    print("=== Tool Response Write-to-File Feature Demo ===\n")
    
    # Simulate a tool response with both short and long content
    # This could be from a file-reading tool, web scraping tool, etc.
    very_long_content = """
This is a simulated very long response that might come from an MCP tool.
""" + "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 200  # Make it definitely > 5000 chars
    
    mock_tool_response = {
        "status": "success",
        "summary": "File contents retrieved successfully",
        "file_info": {
            "name": "large_document.txt", 
            "size": len(very_long_content),
            "type": "text"
        },
        "content": very_long_content,
        "metadata": {
            "encoding": "utf-8",
            "last_modified": "2024-01-01T00:00:00Z"
        }
    }
    
    print(f"Original response size: {len(json.dumps(mock_tool_response))} characters")
    print(f"Content field size: {len(mock_tool_response['content'])} characters")
    print()
    
    # Process the response
    processed_response = process_long_fields(mock_tool_response)
    
    print("After processing:")
    print(f"Processed response size: {len(json.dumps(processed_response))} characters")
    print()
    
    # Show the processed response
    print("Processed response:")
    print(json.dumps(processed_response, indent=2))
    print()
    
    # Verify the file was created and contains the original data
    content_field = processed_response["content"]
    if content_field.startswith("<content_written_to_file:"):
        file_path = content_field.replace("<content_written_to_file:", "").replace(">", "")
        print(f"Full response saved to: {file_path}")
        
        with open(file_path, 'r') as f:
            saved_data = json.load(f)
        
        print(f"Saved file size: {os.path.getsize(file_path)} bytes")
        print(f"Original content preserved: {saved_data['content'] == mock_tool_response['content']}")
        
        # Clean up
        os.unlink(file_path)
        print(f"Cleaned up temporary file: {file_path}")
    
    print("\n=== Demo completed successfully! ===")

def demo_nested_long_fields():
    """Demonstrate handling of nested long fields."""
    print("\n=== Nested Long Fields Demo ===\n")
    
    # Create a response with multiple long fields in different places
    long_text_1 = "A" * 6000
    long_text_2 = "B" * 7000
    
    nested_response = {
        "results": [
            {
                "id": 1,
                "title": "Short title",
                "description": long_text_1,
                "tags": ["tag1", "tag2"]
            },
            {
                "id": 2, 
                "title": "Another short title",
                "body": long_text_2,
                "summary": "This is a short summary"
            }
        ],
        "metadata": {
            "total": 2,
            "notes": "This response contains multiple long fields"
        }
    }
    
    print(f"Original nested response size: {len(json.dumps(nested_response))} characters")
    
    processed = process_long_fields(nested_response)
    
    print(f"Processed nested response size: {len(json.dumps(processed))} characters")
    print()
    print("Processed nested response:")
    print(json.dumps(processed, indent=2))
    
    # Clean up any temp files
    for result in processed["results"]:
        for key, value in result.items():
            if isinstance(value, str) and value.startswith("<content_written_to_file:"):
                file_path = value.replace("<content_written_to_file:", "").replace(">", "")
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    print(f"Cleaned up: {file_path}")
    
    print("\n=== Nested demo completed! ===")

if __name__ == "__main__":
    demo_long_field_handling()
    demo_nested_long_fields()