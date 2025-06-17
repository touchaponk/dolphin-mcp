"""
OpenAI provider implementation for Dolphin MCP.
"""

import os
import json
from typing import Dict, List, Any, AsyncGenerator, Optional, Union

from openai import AsyncOpenAI, APIError, RateLimitError

async def generate_with_openai_stream(client: AsyncOpenAI, model_name: str, conversation: List[Dict],
                                    formatted_functions: List[Dict], temperature: Optional[float] = None,
                                    top_p: Optional[float] = None, max_tokens: Optional[int] = None,
                                    is_reasoning: bool = False, reasoning_effort: Optional[str] = "medium") -> AsyncGenerator:
    """Internal function for streaming generation"""
    try:
        # Use Response API for all models
        input_text = _convert_messages_to_input(conversation)
        
        # Build tools parameter for Response API
        tools = []
        if formatted_functions:
            for func in formatted_functions:
                tools.append({
                    "type": "function",
                    "name": func["name"],
                    "description": func["description"],
                    "parameters": func["parameters"]
                })
        
        response = await client.responses.create(
            model=model_name,
            input=input_text,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_tokens,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
            include=["reasoning.encrypted_content"],  # Include reasoning in response
            stream=True
        )
        
        # Handle Response API streaming format
        current_tool_calls = []
        current_content = ""
        current_reasoning = ""

        async for chunk in response:
            # The Response API streaming format is different from Chat Completions
            # We need to handle ResponseStreamEvent format
            assistant_text_chunk = ""
            reasoning_chunk = ""
            
            # Extract content from Response API stream chunk
            if hasattr(chunk, 'text') and chunk.text:
                if hasattr(chunk.text, 'delta'):
                    assistant_text_chunk = chunk.text.delta or ""
                elif hasattr(chunk.text, 'content'):
                    assistant_text_chunk = chunk.text.content or ""
            
            # Extract reasoning from Response API stream chunk
            if hasattr(chunk, 'reasoning') and chunk.reasoning:
                if hasattr(chunk.reasoning, 'delta'):
                    reasoning_chunk = chunk.reasoning.delta or ""
                elif hasattr(chunk.reasoning, 'encrypted_content'):
                    reasoning_chunk = chunk.reasoning.encrypted_content or ""
            
            # Yield text chunks
            if assistant_text_chunk:
                yield {"assistant_text": assistant_text_chunk, "tool_calls": [], "is_chunk": True, "token": True, "reasoning": ""}
                current_content += assistant_text_chunk
            
            # Yield reasoning chunks
            if reasoning_chunk:
                yield {"assistant_text": "", "tool_calls": [], "is_chunk": True, "token": False, "reasoning": reasoning_chunk}
                current_reasoning += reasoning_chunk
            
            # Handle tool calls (if supported by Response API)
            if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                # Similar logic to Chat Completions API tool call handling
                # This part might need adjustment based on actual Response API format
                pass
            
            # Check if this is the final chunk
            if hasattr(chunk, 'done') and chunk.done:
                yield {
                    "assistant_text": current_content,
                    "tool_calls": current_tool_calls,
                    "is_chunk": False,
                    "reasoning": current_reasoning
                }

    except Exception as e:
        yield {"assistant_text": f"OpenAI error: {str(e)}", "tool_calls": [], "is_chunk": False, "reasoning": ""}

def _convert_messages_to_input(conversation: List[Dict]) -> str:
    """Convert OpenAI messages format to single input string for Response API."""
    input_parts = []
    for message in conversation:
        role = message.get("role", "")
        content = message.get("content", "")
        if role and content:
            input_parts.append(f"{role}: {content}")
    return "\n\n".join(input_parts)

async def generate_with_openai_sync(client: AsyncOpenAI, model_name: str, conversation: List[Dict], 
                                  formatted_functions: List[Dict], temperature: Optional[float] = None,
                                  top_p: Optional[float] = None, max_tokens: Optional[int] = None,
                                  is_reasoning: bool = False, reasoning_effort: Optional[str] = "medium") -> Dict:
    """Internal function for non-streaming generation"""
    try:
        # Use Response API for all models
        input_text = _convert_messages_to_input(conversation)
        
        # Build tools parameter for Response API
        tools = []
        if formatted_functions:
            for func in formatted_functions:
                tools.append({
                    "type": "function",
                    "name": func["name"],
                    "description": func["description"],
                    "parameters": func["parameters"]
                })
        
        response = await client.responses.create(
            model=model_name,
            input=input_text,
            temperature=temperature,
            top_p=top_p,
            max_output_tokens=max_tokens,
            tools=tools if tools else None,
            tool_choice="auto" if tools else None,
            include=["reasoning.encrypted_content"],  # Include reasoning in response
            stream=False
        )

        # Handle Response API response format
        assistant_text = ""
        tool_calls = []
        reasoning = ""
        
        # Extract content from Response API format
        if hasattr(response, 'text') and response.text:
            if hasattr(response.text, 'content'):
                assistant_text = response.text.content or ""
            else:
                assistant_text = str(response.text)
        # Ensure assistant_text is a string
        if not isinstance(assistant_text, str):
            assistant_text = str(assistant_text) if assistant_text else ""
        
        # Extract reasoning from Response API format
        if hasattr(response, 'reasoning') and response.reasoning:
            # Try different possible structures for reasoning
            if hasattr(response.reasoning, 'encrypted_content'):
                reasoning = response.reasoning.encrypted_content or ""
            elif hasattr(response.reasoning, 'content'):
                reasoning = response.reasoning.content or ""
            else:
                reasoning = str(response.reasoning)
            # Ensure reasoning is a string
            if not isinstance(reasoning, str):
                reasoning = str(reasoning) if reasoning else ""
        
        # Extract tool calls from Response API format
        if hasattr(response, 'tool_calls') and response.tool_calls:
            for tc in response.tool_calls:
                if hasattr(tc, 'type') and tc.type == 'function':
                    tool_call = {
                        "id": getattr(tc, 'id', ''),
                        "function": {
                            "name": tc.function.name if hasattr(tc, 'function') else '',
                            "arguments": tc.function.arguments if hasattr(tc, 'function') and hasattr(tc.function, 'arguments') else "{}"
                        }
                    }
                    # Ensure arguments is valid JSON
                    try:
                        json.loads(tool_call["function"]["arguments"])
                    except json.JSONDecodeError:
                        tool_call["function"]["arguments"] = "{}"
                    tool_calls.append(tool_call)
        
        return {"assistant_text": assistant_text, "tool_calls": tool_calls, "reasoning": reasoning}

    except APIError as e:
        return {"assistant_text": f"OpenAI API error: {str(e)}", "tool_calls": [], "reasoning": ""}
    except RateLimitError as e:
        return {"assistant_text": f"OpenAI rate limit: {str(e)}", "tool_calls": [], "reasoning": ""}
    except Exception as e:
        return {"assistant_text": f"Unexpected OpenAI error: {str(e)}", "tool_calls": [], "reasoning": ""}

async def generate_with_openai(conversation: List[Dict], model_cfg: Dict, 
                             all_functions: List[Dict], stream: bool = False) -> Union[Dict, AsyncGenerator]:
    """
    Generate text using OpenAI's API.
    
    Args:
        conversation: The conversation history
        model_cfg: Configuration for the model
        all_functions: Available functions for the model to call
        stream: Whether to stream the response
        
    Returns:
        If stream=False: Dict containing assistant_text and tool_calls
        If stream=True: AsyncGenerator yielding chunks of assistant text and tool calls
    """
    api_key = model_cfg.get("apiKey") or os.getenv("OPENAI_API_KEY")
    if "apiBase" in model_cfg:
        client = AsyncOpenAI(api_key=api_key, base_url=model_cfg["apiBase"])
    else:
        client = AsyncOpenAI(api_key=api_key)

    model_name = model_cfg["model"]
    temperature = model_cfg.get("temperature", None)
    top_p = model_cfg.get("top_p", None)
    max_tokens = model_cfg.get("max_tokens", None)
    is_reasoning = model_cfg.get("is_reasoning", False)
    reasoning_effort = model_cfg.get("reasoning_effort", None)

    # Format functions for OpenAI API
    formatted_functions = []
    for func in all_functions:
        formatted_func = {
            "name": func["name"],
            "description": func["description"],
            "parameters": func["parameters"]
        }
        formatted_functions.append(formatted_func)

    if stream:
        return generate_with_openai_stream(
            client, model_name, conversation, formatted_functions,
            temperature, top_p, max_tokens, is_reasoning, reasoning_effort
        )
    else:
        return await generate_with_openai_sync(
            client, model_name, conversation, formatted_functions,
            temperature, top_p, max_tokens, is_reasoning, reasoning_effort
        )
