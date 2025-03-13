"""
Ollama provider implementation for Dolphin MCP.
"""

from typing import Dict, List, Any

async def generate_with_ollama(conversation, model_cfg, all_functions):
    """
    Generate text using Ollama's API.
    
    Args:
        conversation: The conversation history
        model_cfg: Configuration for the model
        all_functions: Available functions for the model to call (not used by Ollama)
        
    Returns:
        Dict containing assistant_text and tool_calls
    """
    from ollama import chat, ResponseError

    model_name = model_cfg["model"]
    temperature = model_cfg.get("temperature", 0.7)
    top_k = model_cfg.get("top_k", None)
    repetition_penalty = model_cfg.get("repetition_penalty", None)
    max_tokens = model_cfg.get("max_tokens", 1024)

    try:
        response = chat(
            model=model_name,
            messages=conversation,
            temperature=temperature,
            top_k=top_k,
            repeat_penalty=repetition_penalty,
            max_tokens=max_tokens,
            stream=False
        )
        assistant_text = response.message.content or ""
        return {"assistant_text": assistant_text, "tool_calls": []}
    except ResponseError as e:
        return {"assistant_text": f"Ollama error: {str(e)}", "tool_calls": []}
    except Exception as e:
        return {"assistant_text": f"Unexpected Ollama error: {str(e)}", "tool_calls": []}
