#!/usr/bin/env python3
"""
Test to verify the OpenAI Response API tool format fix.
"""

import sys
import os
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dolphin_mcp.providers.openai import generate_with_openai_sync, generate_with_openai_stream


@pytest.mark.asyncio
async def test_response_api_tool_format_fix():
    """Test that tools are formatted correctly for Response API."""
    
    # Mock OpenAI client  
    mock_client = AsyncMock()
    
    # Mock formatted functions (the format that was causing the issue)
    formatted_functions = [{
        "name": "github_add_issue_comment",
        "description": "Add a comment to a specific issue in a GitHub repository.",
        "parameters": {
            "type": "object",
            "properties": {
                "issue_number": {"type": "integer", "description": "Issue number"},
                "comment": {"type": "string", "description": "Comment text"}
            },
            "required": ["issue_number", "comment"]
        }
    }]
    
    # Mock a successful response
    mock_response = MagicMock()
    mock_text = MagicMock()
    mock_text.content = "Comment added successfully!"
    mock_response.text = mock_text
    mock_response.reasoning = None
    mock_response.tool_calls = None
    
    mock_client.responses.create.return_value = mock_response
    
    # Call the function with tools
    result = await generate_with_openai_sync(
        mock_client, "gpt-4", [{"role": "user", "content": "Add a comment"}], formatted_functions
    )
    
    # Verify the call was made
    mock_client.responses.create.assert_called_once()
    call_args = mock_client.responses.create.call_args
    tools_param = call_args[1]['tools']
    
    # Verify the new flattened format
    assert len(tools_param) == 1
    tool = tools_param[0]
    
    # Check that the format is now flattened (name at top level)
    assert tool["type"] == "function"  
    assert tool["name"] == "github_add_issue_comment"  # Name should be at top level
    assert tool["description"] == "Add a comment to a specific issue in a GitHub repository."
    assert "parameters" in tool
    assert tool["parameters"]["type"] == "object"
    
    # Verify that the old nested format is NOT used
    assert "function" not in tool  # Should NOT have nested function object
    
    # Verify the response is still processed correctly
    assert result["assistant_text"] == "Comment added successfully!"
    assert result["tool_calls"] == []


@pytest.mark.asyncio 
async def test_streaming_response_api_tool_format_fix():
    """Test that tools are formatted correctly for streaming Response API."""
    
    # Mock OpenAI client
    mock_client = AsyncMock()
    
    # Mock formatted functions
    formatted_functions = [{
        "name": "test_function", 
        "description": "Test function",
        "parameters": {"type": "object", "properties": {}}
    }]
    
    # Create mock streaming chunks
    mock_chunks = []
    chunk = MagicMock()
    chunk.text = MagicMock()
    chunk.text.delta = "Test response"
    chunk.reasoning = None 
    chunk.done = True
    mock_chunks.append(chunk)
    
    # Mock the async iteration
    mock_response = AsyncMock()
    mock_response.__aiter__.return_value = iter(mock_chunks)
    mock_client.responses.create.return_value = mock_response
    
    # Call the streaming function
    chunks_received = []
    async for chunk in generate_with_openai_stream(
        mock_client, "gpt-4", [{"role": "user", "content": "test"}], formatted_functions
    ):
        chunks_received.append(chunk)
    
    # Verify the call was made with correct tool format
    mock_client.responses.create.assert_called_once()
    call_args = mock_client.responses.create.call_args
    tools_param = call_args[1]['tools']
    
    # Verify the new flattened format
    assert len(tools_param) == 1
    tool = tools_param[0]
    
    # Check that the format is now flattened 
    assert tool["type"] == "function"
    assert tool["name"] == "test_function"  # Name should be at top level
    assert tool["description"] == "Test function"
    assert "parameters" in tool
    
    # Verify that the old nested format is NOT used
    assert "function" not in tool  # Should NOT have nested function object


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])