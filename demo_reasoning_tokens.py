#!/usr/bin/env python3
"""
Demo script showing how to access reasoning tokens from reasoning models.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock

# Mock the OpenAI provider for demonstration
async def demo_reasoning_tokens():
    """Demonstrate how reasoning tokens work."""
    
    print("=== Reasoning Tokens Demo ===")
    print("\nThis demo shows how to access reasoning tokens from models like o1-mini")
    
    # Import the provider
    import sys
    import os
    sys.path.insert(0, os.path.join("/home/runner/work/amity-dolphin-mcp/amity-dolphin-mcp", "src"))
    
    from dolphin_mcp.providers.openai import generate_with_openai_sync, generate_with_openai_stream
    
    # Demo 1: Non-streaming with reasoning
    print("\n1. Non-streaming response with reasoning tokens:")
    print("-" * 50)
    
    # Mock client
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "The capital of France is Paris."
    mock_choice.message.tool_calls = None
    mock_choice.message.reasoning = """Let me think about this step by step:

1. The question asks for the capital of France
2. France is a country in Western Europe
3. The capital city is the primary city where the government is located
4. Paris has been the capital of France for centuries
5. Therefore, the answer is Paris."""
    
    mock_response.choices = [mock_choice]
    mock_client.chat.completions.create.return_value = mock_response
    
    result = await generate_with_openai_sync(
        mock_client, "o1-mini", [], [], is_reasoning=True
    )
    
    print(f"Assistant Response: {result['assistant_text']}")
    print(f"\nReasoning Process:")
    print(result['reasoning'])
    print(f"\nTool Calls: {result['tool_calls']}")
    
    # Demo 2: Streaming with reasoning tokens
    print("\n\n2. Streaming response with reasoning tokens:")
    print("-" * 50)
    
    # Mock streaming chunks
    chunks = []
    
    # Reasoning chunks
    chunk1 = MagicMock()
    chunk1.choices = [MagicMock()]
    chunk1.choices[0].delta.content = None
    chunk1.choices[0].delta.reasoning = "I need to think about this question..."
    chunk1.choices[0].finish_reason = None
    chunks.append(chunk1)
    
    chunk2 = MagicMock()
    chunk2.choices = [MagicMock()]
    chunk2.choices[0].delta.content = None
    chunk2.choices[0].delta.reasoning = " The user is asking about capitals."
    chunk2.choices[0].finish_reason = None
    chunks.append(chunk2)
    
    # Content chunk
    chunk3 = MagicMock()
    chunk3.choices = [MagicMock()]
    chunk3.choices[0].delta.content = "The capital of France is Paris."
    chunk3.choices[0].delta.reasoning = None
    chunk3.choices[0].finish_reason = None
    chunks.append(chunk3)
    
    # Final chunk
    chunk4 = MagicMock()
    chunk4.choices = [MagicMock()]
    chunk4.choices[0].delta.content = None
    chunk4.choices[0].delta.reasoning = None
    chunk4.choices[0].finish_reason = "stop"
    chunks.append(chunk4)
    
    mock_stream = AsyncMock()
    mock_stream.__aiter__.return_value = iter(chunks)
    mock_client.chat.completions.create.return_value = mock_stream
    
    print("Streaming chunks:")
    async for chunk in generate_with_openai_stream(mock_client, "o1-mini", [], []):
        if chunk.get("is_chunk"):
            if chunk.get("reasoning"):
                print(f"  [REASONING] {chunk['reasoning']}")
            if chunk.get("assistant_text") and chunk.get("token"):
                print(f"  [CONTENT] {chunk['assistant_text']}")
        else:
            # Final chunk
            print(f"\nFinal Response:")
            print(f"  Content: {chunk['assistant_text']}")
            print(f"  Full Reasoning: {chunk['reasoning']}")
    
    # Demo 3: Show response structure
    print("\n\n3. Response Structure:")
    print("-" * 50)
    
    example_response = {
        "assistant_text": "The answer to your question.",
        "tool_calls": [],
        "reasoning": "Here's how I thought through this problem..."
    }
    
    print("New response structure:")
    print(json.dumps(example_response, indent=2))
    
    print("\nBackward compatibility:")
    print("- Existing code using result['assistant_text'] still works")
    print("- Existing code using result.get('tool_calls', []) still works") 
    print("- New reasoning access: result.get('reasoning', '')")
    
    print("\n4. Usage in Practice:")
    print("-" * 50)
    print("""
# For reasoning models like o1-mini:
model_cfg = {
    "provider": "openai",
    "model": "o1-mini", 
    "is_reasoning": True,
    "reasoning_effort": "medium"  # or "high"
}

# Non-streaming
result = await generate_with_openai(conversation, model_cfg, functions, stream=False)
reasoning = result.get('reasoning', '')  # Access reasoning tokens

# Streaming  
async for chunk in generate_with_openai(conversation, model_cfg, functions, stream=True):
    if chunk.get('reasoning'):
        print(f"Reasoning: {chunk['reasoning']}")
    if chunk.get('assistant_text'):
        print(f"Content: {chunk['assistant_text']}")
""")

async def main():
    await demo_reasoning_tokens()

if __name__ == "__main__":
    asyncio.run(main())