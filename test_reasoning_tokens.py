#!/usr/bin/env python3
"""
Unit tests for reasoning token extraction functionality.
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

class TestReasoningTokens:
    """Test class for reasoning token extraction functionality."""

    @pytest.mark.asyncio
    async def test_sync_reasoning_extraction(self):
        """Test reasoning token extraction in non-streaming mode."""
        
        # Mock OpenAI client and response for Response API
        mock_client = AsyncMock()
        mock_response = MagicMock()
        
        # Mock the Response API response structure with proper values
        mock_text = MagicMock()
        mock_text.content = "The answer is 42."
        mock_response.text = mock_text
        
        mock_reasoning = MagicMock()
        mock_reasoning.encrypted_content = "Let me think about this step by step. The answer to the ultimate question of life, the universe, and everything is 42."
        mock_response.reasoning = mock_reasoning
        
        mock_response.tool_calls = None
        
        mock_client.responses.create.return_value = mock_response
        
        # Call the function
        result = await generate_with_openai_sync(
            mock_client, "o1-mini", [], [], is_reasoning=True
        )
        
        # Verify the result
        assert "assistant_text" in result
        assert "tool_calls" in result
        assert "reasoning" in result
        assert result["assistant_text"] == "The answer is 42."
        assert result["reasoning"] == "Let me think about this step by step. The answer to the ultimate question of life, the universe, and everything is 42."
        assert result["tool_calls"] == []

    @pytest.mark.asyncio
    async def test_sync_without_reasoning(self):
        """Test that non-reasoning models work normally."""
        
        # Mock OpenAI client and response without reasoning
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Regular response"
        mock_choice.message.tool_calls = None
        # Explicitly set reasoning to None to simulate no reasoning field
        mock_choice.message.reasoning = None
        
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Call the function
        result = await generate_with_openai_sync(
            mock_client, "gpt-4", [], [], is_reasoning=False
        )
        
        # Verify the result
        assert "assistant_text" in result
        assert "tool_calls" in result
        assert "reasoning" in result
        assert result["assistant_text"] == "Regular response"
        assert result["reasoning"] == ""  # Should be empty string when no reasoning
        assert result["tool_calls"] == []

    @pytest.mark.asyncio
    async def test_streaming_reasoning_extraction(self):
        """Test reasoning token extraction in streaming mode."""
        
        # Mock OpenAI client
        mock_client = AsyncMock()
        
        # Create mock streaming chunks
        mock_chunks = []
        
        # Chunk 1: Reasoning content
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock()]
        chunk1.choices[0].delta.content = None
        chunk1.choices[0].delta.reasoning = "Let me think step by step..."
        chunk1.choices[0].finish_reason = None
        mock_chunks.append(chunk1)
        
        # Chunk 2: More reasoning
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock()]
        chunk2.choices[0].delta.content = None
        chunk2.choices[0].delta.reasoning = " This is a complex problem."
        chunk2.choices[0].finish_reason = None
        mock_chunks.append(chunk2)
        
        # Chunk 3: Content
        chunk3 = MagicMock()
        chunk3.choices = [MagicMock()]
        chunk3.choices[0].delta.content = "The answer is 42."
        chunk3.choices[0].delta.reasoning = None
        chunk3.choices[0].finish_reason = None
        mock_chunks.append(chunk3)
        
        # Final chunk
        chunk4 = MagicMock()
        chunk4.choices = [MagicMock()]
        chunk4.choices[0].delta.content = None
        chunk4.choices[0].delta.reasoning = None
        chunk4.choices[0].finish_reason = "stop"
        mock_chunks.append(chunk4)
        
        # Mock the async iteration
        mock_response = AsyncMock()
        mock_response.__aiter__.return_value = iter(mock_chunks)
        mock_client.chat.completions.create.return_value = mock_response
        
        # Call the streaming function
        chunks_received = []
        async for chunk in generate_with_openai_stream(
            mock_client, "o1-mini", [], []
        ):
            chunks_received.append(chunk)
        
        # Verify the chunks
        assert len(chunks_received) > 0
        
        # Find reasoning chunks
        reasoning_chunks = [c for c in chunks_received if c.get("reasoning") and c.get("is_chunk")]
        content_chunks = [c for c in chunks_received if c.get("assistant_text") and c.get("token")]
        final_chunks = [c for c in chunks_received if not c.get("is_chunk")]
        
        # Verify we got reasoning chunks
        assert len(reasoning_chunks) >= 2
        assert reasoning_chunks[0]["reasoning"] == "Let me think step by step..."
        assert reasoning_chunks[1]["reasoning"] == " This is a complex problem."
        
        # Verify we got content chunks
        assert len(content_chunks) >= 1
        assert content_chunks[0]["assistant_text"] == "The answer is 42."
        
        # Verify final chunk includes accumulated reasoning
        assert len(final_chunks) == 1
        assert "reasoning" in final_chunks[0]
        assert "Let me think step by step... This is a complex problem." in final_chunks[0]["reasoning"]

    @pytest.mark.asyncio
    async def test_uses_response_api_for_reasoning(self):
        """Test that Response API is used when is_reasoning=True."""
        
        # Mock OpenAI client and response for Response API
        mock_client = AsyncMock()
        mock_response = MagicMock()
        
        # Mock the Response API response structure with proper values
        mock_text = MagicMock()
        mock_text.content = "Response API result"
        mock_response.text = mock_text
        
        mock_reasoning = MagicMock()
        mock_reasoning.encrypted_content = "Response API reasoning"
        mock_response.reasoning = mock_reasoning
        
        mock_response.tool_calls = None
        
        mock_client.responses.create.return_value = mock_response
        
        # Call the function with is_reasoning=True
        result = await generate_with_openai_sync(
            mock_client, "o1-mini", [{"role": "user", "content": "test"}], [], is_reasoning=True
        )
        
        # Verify that responses.create was called, not chat.completions.create
        mock_client.responses.create.assert_called_once()
        mock_client.chat.completions.create.assert_not_called()
        
        # Verify the Response API was called with correct parameters
        call_args = mock_client.responses.create.call_args
        assert call_args[1]['model'] == 'o1-mini'
        assert call_args[1]['input'] == 'user: test'  # Converted from messages format
        assert call_args[1]['include'] == ['reasoning.encrypted_content']
        assert call_args[1]['stream'] is False
        
        # Verify the result structure
        assert result["assistant_text"] == "Response API result"
        assert result["reasoning"] == "Response API reasoning"

    @pytest.mark.asyncio
    async def test_uses_chat_completions_for_non_reasoning(self):
        """Test that Chat Completions API is used when is_reasoning=False."""
        
        # Mock OpenAI client and response for Chat Completions API
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Chat completion result"
        mock_choice.message.tool_calls = None
        mock_choice.message.reasoning = None
        
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Call the function with is_reasoning=False
        result = await generate_with_openai_sync(
            mock_client, "gpt-4", [{"role": "user", "content": "test"}], [], is_reasoning=False
        )
        
        # Verify that chat.completions.create was called, not responses.create
        mock_client.chat.completions.create.assert_called_once()
        mock_client.responses.create.assert_not_called()
        
        # Verify the Chat Completions API was called with correct parameters
        call_args = mock_client.chat.completions.create.call_args
        assert call_args[1]['model'] == 'gpt-4'
        assert call_args[1]['messages'] == [{"role": "user", "content": "test"}]
        assert call_args[1]['stream'] is False
        
        # Verify the result structure
        assert result["assistant_text"] == "Chat completion result"

    @pytest.mark.asyncio
    async def test_backward_compatibility(self):
        """Test that existing code continues to work with the new response structure."""
        
        # Mock a response that includes reasoning using Chat Completions API
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Test response"
        mock_choice.message.tool_calls = None
        mock_choice.message.reasoning = "Some reasoning"
        
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        # Call without explicit is_reasoning parameter (defaults to False)
        result = await generate_with_openai_sync(
            mock_client, "o1-mini", [], []
        )
        
        # Test that existing code patterns still work
        assistant_text = result["assistant_text"]  # Should not raise KeyError
        tool_calls = result.get("tool_calls", [])  # Should work
        reasoning = result.get("reasoning", "")  # Should work and return reasoning
        
        assert assistant_text == "Test response"
        assert tool_calls == []
        assert reasoning == "Some reasoning"
        """Test that existing code continues to work with the new response structure."""
        
        # Mock a response that includes reasoning
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "Test response"
        mock_choice.message.tool_calls = None
        mock_choice.message.reasoning = "Some reasoning"
        
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response
        
        result = await generate_with_openai_sync(
            mock_client, "o1-mini", [], []
        )
        
        # Test that existing code patterns still work
        assistant_text = result["assistant_text"]  # Should not raise KeyError
        tool_calls = result.get("tool_calls", [])  # Should work
        reasoning = result.get("reasoning", "")  # Should work and return reasoning
        
        assert assistant_text == "Test response"
        assert tool_calls == []
        assert reasoning == "Some reasoning"


def test_response_structure():
    """Test the response structure contains all expected fields."""
    
    # Test the expected structure
    expected_fields = {"assistant_text", "tool_calls", "reasoning"}
    
    # Mock response
    mock_response = {
        "assistant_text": "Test",
        "tool_calls": [],
        "reasoning": "Test reasoning"
    }
    
    # Verify all expected fields are present
    assert set(mock_response.keys()) == expected_fields
    
    # Test backward compatibility - old code should still work
    text = mock_response["assistant_text"]
    tools = mock_response.get("tool_calls", [])
    reasoning = mock_response.get("reasoning", "")
    
    assert text == "Test"
    assert tools == []
    assert reasoning == "Test reasoning"

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])