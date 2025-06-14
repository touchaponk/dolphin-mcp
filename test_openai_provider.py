#!/usr/bin/env python3
"""
Test the OpenAI provider fix by creating a simple scenario that would trigger the original issue.
"""
import asyncio
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import the OpenAI provider directly
from dolphin_mcp.providers.openai import generate_with_openai

class MockOpenAI:
    """Mock OpenAI client to simulate the original API error"""
    
    def __init__(self, api_key, base_url=None):
        self.api_key = api_key
        self.base_url = base_url
        
    class ChatCompletions:
        @staticmethod
        async def create(**kwargs):
            # Simulate the original error that would occur
            if 'max_tokens' in kwargs and kwargs['max_tokens'] is None:
                raise Exception("Error code: 400 - {'error': {'message': \"Invalid type for 'max_tokens': expected an unsupported value, but got null instead.\", 'type': 'invalid_request_error', 'param': 'max_tokens', 'code': 'invalid_type'}}")
            
            # For reasoning models, check if unsupported parameters are present
            model_name = kwargs.get('model', '').lower()
            if any(pattern in model_name for pattern in ['o1', 'o3', 'o4']):
                unsupported = []
                if 'max_tokens' in kwargs:
                    unsupported.append('max_tokens')
                if 'temperature' in kwargs:
                    unsupported.append('temperature')
                if 'top_p' in kwargs:
                    unsupported.append('top_p')
                
                if unsupported:
                    raise Exception(f"Reasoning model {model_name} does not support: {unsupported}")
            
            # Mock successful response
            class MockResponse:
                def __init__(self):
                    self.choices = [MockChoice()]
                    
            class MockChoice:
                def __init__(self):
                    self.message = MockMessage()
                    
            class MockMessage:
                def __init__(self):
                    self.content = "Mock response"
                    self.tool_calls = None
                    
            return MockResponse()
    
    def __init__(self, api_key, base_url=None):
        self.api_key = api_key
        self.base_url = base_url
        self.chat = type('Chat', (), {'completions': self.ChatCompletions()})()

async def test_original_issue_scenario():
    """Test the exact scenario that would cause the original issue"""
    
    # Monkey patch the OpenAI client
    import dolphin_mcp.providers.openai as openai_module
    original_openai = openai_module.AsyncOpenAI
    openai_module.AsyncOpenAI = MockOpenAI
    
    try:
        print("=== Testing Original Issue Scenario ===")
        
        # This is the exact configuration that would cause the original issue
        model_cfg = {
            "model": "o4-mini",
            "provider": "openai",
            "apiKey": "test-key",
            "max_tokens": None,      # This would cause the original error
            "temperature": 0.7,     # This would also cause issues for reasoning models
            "top_p": 0.9,          # This would also cause issues for reasoning models
            "is_reasoning": False,  # Let auto-detection work
            "reasoning_effort": "medium"
        }
        
        conversation = [
            {"role": "user", "content": "What is 2+2?"}
        ]
        
        all_functions = []
        
        print("Testing with the fixed implementation...")
        result = await generate_with_openai(conversation, model_cfg, all_functions, stream=False)
        
        print("✅ SUCCESS! No parameter errors occurred")
        print(f"Result: {result}")
        
        # Also test streaming
        print("\nTesting streaming mode...")
        result_gen = await generate_with_openai(conversation, model_cfg, all_functions, stream=True)
        
        chunks = []
        async for chunk in result_gen:
            chunks.append(chunk)
        
        print("✅ SUCCESS! Streaming mode also works")
        print(f"Streaming chunks: {len(chunks)}")
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        if "max_tokens" in error_msg and ("null" in error_msg or "unsupported" in error_msg):
            print(f"❌ FAILED: Original issue still present: {error_msg}")
            return False
        else:
            print(f"❌ FAILED: Unexpected error: {error_msg}")
            return False
    finally:
        # Restore original OpenAI
        openai_module.AsyncOpenAI = original_openai

async def test_backward_compatibility():
    """Test that regular models still work as before"""
    
    import dolphin_mcp.providers.openai as openai_module
    original_openai = openai_module.AsyncOpenAI
    openai_module.AsyncOpenAI = MockOpenAI
    
    try:
        print("\n=== Testing Backward Compatibility ===")
        
        # Test with a regular model that should accept all parameters
        model_cfg = {
            "model": "gpt-4o",
            "provider": "openai", 
            "apiKey": "test-key",
            "max_tokens": 1000,
            "temperature": 0.7,
            "top_p": 0.9,
            "is_reasoning": False
        }
        
        conversation = [
            {"role": "user", "content": "What is 2+2?"}
        ]
        
        all_functions = []
        
        print("Testing regular model (gpt-4o) with all parameters...")
        result = await generate_with_openai(conversation, model_cfg, all_functions, stream=False)
        
        print("✅ SUCCESS! Regular model works with all parameters")
        print(f"Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Backward compatibility broken: {e}")
        return False
    finally:
        openai_module.AsyncOpenAI = original_openai

async def main():
    print("Testing OpenAI Reasoning Model Fix - Integration Test")
    print("=" * 60)
    
    success = True
    success &= await test_original_issue_scenario()
    success &= await test_backward_compatibility()
    
    if success:
        print("\n🎉 All integration tests passed!")
        print("The fix successfully resolves the o4-mini issue while maintaining backward compatibility.")
    else:
        print("\n❌ Some integration tests failed!")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)