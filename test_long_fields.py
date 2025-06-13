#!/usr/bin/env python3
"""
Test the long fields processing functionality.
"""
import sys
import os
import json
import tempfile

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dolphin_mcp.client import process_long_fields

def test_short_content():
    """Test that short content is not modified."""
    result = {
        "message": "Hello world",
        "status": "success",
        "data": ["item1", "item2"]
    }
    
    processed = process_long_fields(result)
    assert processed == result, "Short content should not be modified"
    print("✓ Short content test passed")

def test_long_content():
    """Test that long content gets replaced with file reference."""
    long_text = "x" * 6000  # Create string longer than 5000 chars
    result = {
        "message": "Hello world",
        "long_field": long_text,
        "status": "success"
    }
    
    processed = process_long_fields(result)
    
    # Check that the long field was replaced
    assert processed["message"] == "Hello world", "Short fields should remain unchanged"
    assert processed["status"] == "success", "Short fields should remain unchanged" 
    assert "<content_written_to_file:" in processed["long_field"], "Long field should contain file reference"
    assert ".json" in processed["long_field"], "File reference should contain .json extension"
    # Check that it starts with preview of content
    assert processed["long_field"].startswith("x" * 200), "Long field should start with preview of content"
    
    # Extract file path and verify file exists and contains original data
    file_path = processed["long_field"].split("<content_written_to_file:")[1].replace(">", "")
    assert os.path.exists(file_path), "Referenced file should exist"
    
    with open(file_path, 'r') as f:
        saved_data = json.load(f)
    
    assert saved_data == result, "Saved file should contain original data"
    
    # Clean up
    os.unlink(file_path)
    print("✓ Long content test passed")

def test_nested_long_content():
    """Test that nested long content is handled correctly."""
    long_text = "y" * 7000  # Create string longer than 5000 chars
    result = {
        "metadata": {
            "description": long_text,
            "author": "test"
        },
        "data": [
            {"text": "short"},
            {"text": long_text}
        ]
    }
    
    processed = process_long_fields(result)
    
    # Check that nested long fields were replaced
    assert "<content_written_to_file:" in processed["metadata"]["description"], "Nested long field should contain file reference"
    assert processed["metadata"]["author"] == "test", "Short nested field should remain unchanged"
    assert processed["data"][0]["text"] == "short", "Short list item should remain unchanged"
    assert "<content_written_to_file:" in processed["data"][1]["text"], "Long list item should contain file reference"
    # Check that it starts with preview of content
    assert processed["metadata"]["description"].startswith("y" * 200), "Long field should start with preview of content"
    
    # Extract file path and verify file exists
    file_path = processed["metadata"]["description"].split("<content_written_to_file:")[1].replace(">", "")
    assert os.path.exists(file_path), "Referenced file should exist"
    
    with open(file_path, 'r') as f:
        saved_data = json.load(f)
    
    assert saved_data == result, "Saved file should contain original data"
    
    # Clean up
    os.unlink(file_path)
    print("✓ Nested long content test passed")

def test_non_dict_input():
    """Test that non-dict inputs are handled correctly."""
    # Test string input
    short_string = "hello"
    assert process_long_fields(short_string) == short_string
    
    # Test list input
    short_list = ["a", "b", "c"]
    assert process_long_fields(short_list) == short_list
    
    # Test None input
    assert process_long_fields(None) is None
    
    print("✓ Non-dict input test passed")

def test_custom_max_length():
    """Test that custom max_length parameter works."""
    result = {
        "short": "x" * 50,
        "medium": "y" * 150
    }
    
    # With default max_length (5000), nothing should change
    processed_default = process_long_fields(result)
    assert processed_default == result
    
    # With max_length=100, medium field should be replaced
    processed_custom = process_long_fields(result, max_length=100)
    assert processed_custom["short"] == result["short"]
    assert "<content_written_to_file:" in processed_custom["medium"]
    # Check that it starts with preview of content
    assert processed_custom["medium"].startswith("y" * 150), "Long field should start with preview of content"
    
    # Clean up
    file_path = processed_custom["medium"].split("<content_written_to_file:")[1].replace(">", "")
    if os.path.exists(file_path):
        os.unlink(file_path)
    
    print("✓ Custom max_length test passed")

if __name__ == "__main__":
    print("Running long fields processing tests...")
    test_short_content()
    test_long_content()
    test_nested_long_content()
    test_non_dict_input()
    test_custom_max_length()
    print("All tests passed! ✓")