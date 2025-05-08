# msazure.py

import os
import json
from typing import Dict, List, Any, AsyncGenerator, Optional, Union
import aiohttp
from dotenv import load_dotenv
    

def load_env():
    """Load environment variables from .env file"""
    load_dotenv()

    required_keys = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_API_ENDPOINT",
        "AZURE_OPENAI_DEPLOYMENT_ID",
        "AZURE_OPENAI_API_VERSION"
    ]
    for key in required_keys:
        if key not in os.environ:
            raise ValueError(f"Required environment variable {key} is not set.")

async def generate_with_msazure_openai_stream(model_cfg: Dict, conversation: List[Dict], 
                                            formatted_functions: List[Dict],
                                            temperature: Optional[float] = None,
                                            top_p: Optional[float] = None,
                                            max_tokens: Optional[int] = None) -> AsyncGenerator:
    """Streaming generation with Azure OpenAI"""
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    api_base = os.environ.get("AZURE_OPENAI_API_ENDPOINT")
    if api_base is None:
        raise ValueError("AZURE_OPENAI_API_ENDPOINT environment variable is not set.")
    deployment_id = os.environ.get("AZURE_OPENAI_DEPLOYMENT_ID")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION")

    url = f"{api_base}/openai/deployments/{deployment_id}/chat/completions?api-version={api_version}"
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    payload = {
        "messages": conversation,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "tools": [{"type": "function", "function": f} for f in formatted_functions],
        "tool_choice": "auto",
        "stream": True
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                yield {"assistant_text": f"Azure OpenAI API error: {error_text}", "tool_calls": [], "is_chunk": False}
                return

            async for line in response.content:
                if line:
                    decoded_line = line.decode('utf-8').strip()
                    if decoded_line.startswith("data: "):
                        data = decoded_line[6:]
                        if data == "[DONE]":
                            break
                        chunk = json.loads(data)
                        delta = chunk["choices"][0]["delta"]
                        content = delta.get("content", "")
                        if content:
                            yield {"assistant_text": content, "tool_calls": [], "is_chunk": True, "token": True}

async def generate_with_msazure_openai_sync(model_cfg: Dict, conversation: List[Dict], 
                                          formatted_functions: List[Dict],
                                          temperature: Optional[float] = None,
                                          top_p: Optional[float] = None,
                                          max_tokens: Optional[int] = None) -> Dict:
    """Non-streaming generation with Azure OpenAI"""
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    api_base = os.environ.get("AZURE_OPENAI_API_ENDPOINT")
    if api_base is None:
        raise ValueError("AZURE_OPENAI_API_ENDPOINT environment variable is not set.")
    deployment_id = os.environ.get("AZURE_OPENAI_DEPLOYMENT_ID")
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION")

    url = f"{api_base}/openai/deployments/{deployment_id}/chat/completions?api-version={api_version}"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    payload = {
        "messages": conversation,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "tools": [{"type": "function", "function": f} for f in formatted_functions],
        "tool_choice": "auto",
        "stream": False
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status != 200:
                error_text = await response.text()
                return {"assistant_text": f"Azure OpenAI API error: {error_text}", "tool_calls": []}
            data = await response.json()
            choice = data["choices"][0]
            assistant_text = choice["message"].get("content", "")
            tool_calls = choice["message"].get("tool_calls", [])
            return {"assistant_text": assistant_text, "tool_calls": tool_calls}

async def generate_with_msazure_openai(conversation: List[Dict], model_cfg: Dict, 
                                     all_functions: List[Dict], stream: bool = False) -> Union[Dict, AsyncGenerator]:
    """Dispatcher for Azure OpenAI generation"""
    temperature = model_cfg.get("temperature", 0.7)
    top_p = model_cfg.get("top_p", 0.95)
    max_tokens = model_cfg.get("max_tokens", 1000)

    formatted_functions = [
        {
            "name": func["name"],
            "description": func["description"],
            "parameters": func["parameters"]
        } for func in all_functions
    ]

    if stream:
        return generate_with_msazure_openai_stream(
            model_cfg, conversation, formatted_functions,
            temperature, top_p, max_tokens
        )
    else:
        return await generate_with_msazure_openai_sync(
            model_cfg, conversation, formatted_functions,
            temperature, top_p, max_tokens
        )

