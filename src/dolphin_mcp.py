#!/usr/bin/env python
import argparse
import asyncio
import json
import os
import sys
from typing import Dict, List, Any, Optional, Tuple, Union
from mcp.types import Tool as MCPTool
from dotenv import load_dotenv
from openai import AsyncOpenAI
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool as MCPTool

async def connect_to_mcp_server(server_name: str, config: Dict) -> Tuple[ClientSession, List[Dict]]:
    """Connect to an MCP server and get its tools."""
    server_config = config["mcpServers"].get(server_name)
    if not server_config:
        raise ValueError(f"Server '{server_name}' not found in configuration")

    command = server_config.get("command")
    args = server_config.get("args", [])
    env = server_config.get("env", {})

    # Create the server parameters directly where used
    read_stream, write_stream = await stdio_client(StdioServerParameters(
        command=command,
        args=args,
        env=env
    ))
    session = ClientSession(read_stream, write_stream)
    await session.initialize()
    
    # Get tools from the MCP server
    mcp_tools = await session.list_tools()
    openai_tools = [convert_mcp_tool_to_openai(tool) for tool in mcp_tools]
    
    return session, openai_tools

def convert_mcp_tool_to_openai(mcp_tool: MCPTool) -> Dict:
    """
    Convert an MCP tool to OpenAI function format.
    
    Args:
        mcp_tool: The MCP tool to convert
        
    Returns:
        A dictionary representing the tool in OpenAI function format
    """
    parameters = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    for arg in mcp_tool.arguments:
        parameter_type = "string"  # Default type
        
        # Map MCP types to JSON Schema types
        if hasattr(arg, 'schema') and arg.schema:
            if 'type' in arg.schema:
                parameter_type = arg.schema['type']
        
        parameters["properties"][arg.name] = {
            "type": parameter_type,
            "description": arg.description or ""
        }
        
        if arg.required:
            parameters["required"].append(arg.name)
    
    return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": mcp_tool.description or "",
            "parameters": parameters
        }
    }

async def call_mcp_tool(session: ClientSession, tool_name: str, arguments: Dict) -> str:
    """Call an MCP tool and return the result."""
    result = await session.call_tool(tool_name, arguments)
    return str(result)

async def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MCP OpenAI Integration")
    parser.add_argument("prompt", help="The prompt to send to OpenAI")
    parser.add_argument("--config", default="mcp_config.json", help="Path to MCP config file")
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    endpoint = os.getenv("OPENAI_ENDPOINT")
    model = os.getenv("OPENAI_MODEL")
    
    if not api_key or not model:
        print("Error: OPENAI_API_KEY and OPENAI_MODEL must be set in .env file", file=sys.stderr)
        sys.exit(1)
    
    # Load MCP configuration
    try:
        with open(args.config, 'r') as file:
            config = json.load(file)
    except Exception as e:
        print(f"Error loading config file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Connect to all MCP servers and collect tools
    sessions = {}
    all_tools = []
    
    for server_name in config.get("mcpServers", {}):
        try:
            session, tools = await connect_to_mcp_server(server_name, config)
            # Store both session and tools to easily look up tools later
            sessions[server_name] = (session, tools)
            all_tools.extend(tools)
        except Exception as e:
            print(f"Warning: Could not connect to server '{server_name}': {e}", file=sys.stderr)
    
    if not all_tools:
        print("Warning: No tools were loaded from MCP servers", file=sys.stderr)
    
    # Initialize OpenAI client
    client_kwargs = {"api_key": api_key}
    if endpoint:
        client_kwargs["base_url"] = endpoint
    
    client = AsyncOpenAI(**client_kwargs)
    
    # Create initial message
    messages = [{"role": "user", "content": args.prompt}]
    
    # Stream the conversation
    while True:
        # Call OpenAI API
        try:
            stream = await client.chat.completions.create(
                model=model,
                messages=messages,
                tools=all_tools,
                stream=True
            )
        except Exception as e:
            print(f"Error calling OpenAI API: {e}", file=sys.stderr)
            break
        
        # Initialize variables to collect the response
        assistant_message = {"role": "assistant", "content": ""}
        tool_calls = []
        current_tool_call = None
        
        # Process the stream
        async for chunk in stream:
            delta = chunk.choices[0].delta
            
            # Handle regular content
            if delta.content:
                assistant_message["content"] += delta.content
                print(delta.content, end="", flush=True)
            
            # Handle tool calls
            if delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    index = tool_call_delta.index
                    
                    # Initialize a new tool call if needed
                    if index >= len(tool_calls):
                        tool_calls.append({
                            "id": "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""}
                        })
                    
                    current_tool_call = tool_calls[index]
                    
                    # Update tool call ID
                    if tool_call_delta.id:
                        current_tool_call["id"] += tool_call_delta.id
                    
                    # Update function name
                    if tool_call_delta.function and tool_call_delta.function.name:
                        current_tool_call["function"]["name"] += tool_call_delta.function.name
                        print(f"\nCalling function: {current_tool_call['function']['name']}", flush=True)
                    
                    # Update function arguments with proper error handling
                    if tool_call_delta.function and tool_call_delta.function.arguments:
                        current_tool_call["function"]["arguments"] += tool_call_delta.function.arguments
        
        # Add the assistant message to the conversation
        if tool_calls:
            assistant_message["tool_calls"] = tool_calls
        
        messages.append(assistant_message)
        
        # If there are tool calls, process them
        if tool_calls:
            print("\n", flush=True)
            
            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                function_args = {}
                try:
                    function_args = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError as e:
                    error_msg = f"Error parsing arguments for {function_name}: {e}"
                    print(error_msg, file=sys.stderr)
                    messages.append({
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "name": function_name,
                        "content": error_msg
                    })
                    continue
                
                # Find the server that has this tool - improved logic for tool lookup
                server_name = None
                for srv_name, (session, tools) in sessions.items():
                    if any(t["function"]["name"] == function_name for t in tools):
                        server_name = srv_name
                        break
                
                if not server_name:
                    error_msg = f"Function {function_name} not found in any MCP server"
                    print(error_msg, file=sys.stderr)
                    messages.append({
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "name": function_name,
                        "content": error_msg
                    })
                    continue
                
                try:
                    # Get session from the stored tuple (session, tools)
                    session = sessions[server_name][0]
                    result = await call_mcp_tool(session, function_name, function_args)
                    print(f"Result from {function_name}: {result}", flush=True)
                    
                    # Add the tool response to the conversation
                    messages.append({
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "name": function_name,
                        "content": str(result)  # Ensure result is a string
                    })
                except Exception as e:
                    error_msg = f"Error calling {function_name}: {str(e)}"
                    print(error_msg, file=sys.stderr)
                    messages.append({
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "name": function_name,
                        "content": error_msg
                    })
            
            # Continue the conversation
            continue
        
        # If there are no tool calls, we're done
        break
    
    # Clean up - ensure proper session closure
    for session, _ in sessions.values():
        try:
            await session.close()
        except Exception as e:
            print(f"Warning: Error closing session: {e}", file=sys.stderr)

if __name__ == "__main__":
    asyncio.run(main())
