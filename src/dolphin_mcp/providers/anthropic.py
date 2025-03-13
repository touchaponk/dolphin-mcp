"""
Anthropic provider implementation for Dolphin MCP.
"""

import os
from typing import Dict, List, Any

async def generate_with_anthropic(conversation, model_cfg, all_functions):
    """
    Generate text using Anthropic's API.
    
    Args:
        conversation: The conversation history
        model_cfg: Configuration for the model
        all_functions: Available functions for the model to call (not used by Anthropic)
        
    Returns:
        Dict containing assistant_text and tool_calls
    """
    from anthropic import AsyncAnthropic, APIError as AnthropicAPIError

    anthro_api_key = model_cfg.get("apiKey", os.getenv("ANTHROPIC_API_KEY"))
    client = AsyncAnthropic(api_key=anthro_api_key)

    model_name = model_cfg["model"]
    temperature = model_cfg.get("temperature", 0.7)
    top_k = model_cfg.get("top_k", None)
    top_p = model_cfg.get("top_p", None)
    max_tokens = model_cfg.get("max_tokens", 1024)

    try:
        create_resp = await client.messages.create(
            model=model_name,
            messages=conversation,
            max_tokens=max_tokens,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p
        )
        assistant_text = create_resp.content or ""
        return {"assistant_text": assistant_text, "tool_calls": []}

    except AnthropicAPIError as e:
        return {"assistant_text": f"Anthropic error: {str(e)}", "tool_calls": []}
    except Exception as e:
        return {"assistant_text": f"Unexpected Anthropic error: {str(e)}", "tool_calls": []}
