#!/usr/bin/env python3
"""
Test script to reproduce and validate the fix for o4-mini reasoning model issue.
"""
import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Mock the OpenAI API to test our parameter filtering
class MockOpenAI:
    def __init__(self, api_key, base_url=None):
        self.api_key = api_key
        self.base_url = base_url
        
    class Chat:
        class Completions:
            @staticmethod
            async def create(**kwargs):
                # Check for invalid parameters that would cause the original error
                if 'max_tokens' in kwargs and kwargs['max_tokens'] is None:
                    # This would cause the original error for reasoning models
                    raise Exception("Invalid type for 'max_tokens': expected an unsupported value, but got null instead.")
                
                # For reasoning models, these parameters should not be present
                model_name = kwargs.get('model', '').lower()
                is_reasoning = any(pattern in model_name for pattern in ['o1', 'o3', 'o4'])
                
                if is_reasoning:
                    invalid_params = []
                    if 'max_tokens' in kwargs:
                        invalid_params.append('max_tokens')
                    if 'temperature' in kwargs:
                        invalid_params.append('temperature') 
                    if 'top_p' in kwargs:
                        invalid_params.append('top_p')
                    
                    if invalid_params:
                        raise Exception(f"Reasoning model {model_name} does not support parameters: {invalid_params}")
                
                # Mock successful response
                class MockResponse:
                    def __init__(self):
                        self.choices = [MockChoice()]
                        
                class MockChoice:
                    def __init__(self):
                        self.message = MockMessage()
                        
                class MockMessage:
                    def __init__(self):
                        self.content = "Test response"
                        self.tool_calls = None
                        
                return MockResponse()
    
    def __init__(self, *args, **kwargs):
        self.chat = self.Chat()

# Patch the OpenAI import
import src.dolphin_mcp.providers.openai as openai_provider
openai_provider.AsyncOpenAI = MockOpenAI

async def test_reasoning_model_fix():
    """Test that the fix properly handles reasoning models"""
    
    print("=== Testing Reasoning Model Parameter Filtering ===")
    
    # Test 1: o4-mini should not receive unsupported parameters
    print("\n1. Testing o4-mini (reasoning model)...")
    model_cfg = {
        "model": "o4-mini",
        "provider": "openai",
        "max_tokens": None,  # This should be filtered out
        "temperature": 0.7,  # This should be filtered out
        "top_p": 0.9,       # This should be filtered out
        "is_reasoning": False,  # Auto-detection should work
        "reasoning_effort": "medium"
    }
    
    conversation = [{"role": "user", "content": "What is 2+2?"}]
    all_functions = []
    
    try:
        result = await openai_provider.generate_with_openai(conversation, model_cfg, all_functions, stream=False)
        print("✅ o4-mini test passed - no parameter errors")
    except Exception as e:
        if "does not support parameters" in str(e) or "max_tokens" in str(e):
            print(f"❌ o4-mini test failed - parameters not filtered: {e}")
            return False
        else:
            print(f"❌ o4-mini test failed - unexpected error: {e}")
            return False
    
    # Test 2: Regular model should still receive all parameters
    print("\n2. Testing gpt-4o (regular model)...")
    model_cfg = {
        "model": "gpt-4o",
        "provider": "openai", 
        "max_tokens": 1000,
        "temperature": 0.7,
        "top_p": 0.9,
        "is_reasoning": False
    }
    
    try:
        result = await openai_provider.generate_with_openai(conversation, model_cfg, all_functions, stream=False)
        print("✅ gpt-4o test passed - all parameters accepted")
    except Exception as e:
        print(f"❌ gpt-4o test failed: {e}")
        return False
    
    # Test 3: Explicit is_reasoning flag should override detection
    print("\n3. Testing explicit is_reasoning flag...")
    model_cfg = {
        "model": "gpt-4o",  # Regular model name
        "provider": "openai",
        "max_tokens": None,
        "temperature": 0.7,
        "top_p": 0.9,
        "is_reasoning": True,  # Explicit flag
        "reasoning_effort": "medium"
    }
    
    try:
        result = await openai_provider.generate_with_openai(conversation, model_cfg, all_functions, stream=False)
        print("✅ Explicit is_reasoning flag test passed")
    except Exception as e:
        if "does not support parameters" in str(e):
            print(f"❌ Explicit is_reasoning flag test failed - parameters not filtered: {e}")
            return False
        else:
            print(f"❌ Explicit is_reasoning flag test failed - unexpected error: {e}")
            return False
    
    # Test 4: Test detection function directly
    print("\n4. Testing detection function...")
    test_cases = [
        ("o4-mini", False, True),
        ("o1-preview", False, True),
        ("o3-medium", False, True),
        ("gpt-4o", False, False),
        ("gpt-3.5-turbo", False, False),
        ("gpt-4o", True, True),  # Explicit flag
    ]
    
    for model_name, explicit_flag, expected in test_cases:
        result = openai_provider.is_reasoning_model(model_name, explicit_flag)
        if result == expected:
            print(f"✅ {model_name} (flag={explicit_flag}) -> {result} (expected {expected})")
        else:
            print(f"❌ {model_name} (flag={explicit_flag}) -> {result} (expected {expected})")
            return False
    
    print("\n🎉 All tests passed! The fix should resolve the o4-mini issue.")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_reasoning_model_fix())
    if not success:
        sys.exit(1)