#!/usr/bin/env python
import argparse
import asyncio
import json
import logging
import os
import sys
import time
from typing import Dict, List, Any, Optional, Tuple, Union

from dotenv import load_dotenv
from jsonschema import validate
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import Tool as MCPTool
from openai import AsyncOpenAI

# Configure logging
def setup_logging(level=logging.INFO):
    """Set up logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('dolphin_mcp.log')
        ]
    )

# Create logger for this module
logger = logging.getLogger(__name__)

# Configuration schema for validation
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "mcpServers": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "required": ["command"],
                "properties": {
                    "command": {"type": "string"},
                    "args": {"type": "array", "items": {"type": "string"}},
                    "env": {
                        "type": "object",
                        "additionalProperties": {"type": "string"}
                    }
                }
            }
        }
    },
    "required": ["mcpServers"]
}

def load_and_validate_config(config_path):
    """Load and validate the MCP configuration."""
    try:
        with open(config_path, 'r') as file:
            config = json.load(file)
        
        # Validate against schema
        validate(instance=config, schema=CONFIG_SCHEMA)
        
        # Additional validation logic
        for server_name, server_config in config.get("mcpServers", {}).items():
            if not server_config.get("command"):
                raise ValueError(f"Server '{server_name}' is missing required 'command' field")
        
        return config
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {e}")

async def connect_to_mcp_server(server_name: str, config: Dict) -> Tuple[ClientSession, List[Dict]]:
    """Connect to an MCP server and get its tools."""
    logger.info(f"Connecting to MCP server '{server_name}'")
    server_config = config["mcpServers"].get(server_name)
    if not server_config:
        raise ValueError(f"Server '{server_name}' not found in configuration")
    
    command = server_config.get("command")
    args = server_config.get("args", [])
    logger.info(f"Using command: {command} with args: {args}")
    
    # Get the current environment and update it with any additional env vars
    current_env = os.environ.copy()
    if server_config.get("env"):
        current_env.update(server_config.get("env", {}))
    
    # Add MCP_DEBUG environment variable to enable debug logging
    current_env["MCP_DEBUG"] = "1"
    current_env["MCP_LOG_LEVEL"] = "DEBUG"
    
    # Create the StdioServerParameters
    params = StdioServerParameters(
        command=command,
        args=args,
        env=current_env,
        stdout_line_callback=lambda line: logger.debug(f"SERVER STDOUT: {line}"),
        stderr_line_callback=lambda line: logger.debug(f"SERVER STDERR: {line}"),
        debug=True,
        log_stderr=True
    )
    
    logger.debug("About to open stdio client")
    
    # Use async with instead of await
    try:
        logger.debug("Creating StdioServerParameters")
        
        # Connect to the MCP server
        read_stream, write_stream = await stdio_client(params).__aenter__()
        logger.debug("stdio_client connected. Creating ClientSession")
        session = ClientSession(read_stream, write_stream)
        
        # Initialize the session with a timeout
        try:
            logger.debug("About to initialize session with timeout")
            await asyncio.wait_for(session.initialize(), timeout=10)
            logger.debug("Session initialized successfully")
        except asyncio.TimeoutError:
            logger.error(f"Session initialization timed out after 10 seconds")
            raise
        except Exception as e:
            logger.error(f"Error during session initialization: {type(e).__name__}: {str(e)}")
            raise
        
        # Get tools from the MCP server
        logger.debug("Getting tools from MCP server")
        mcp_tools = await session.list_tools()
        logger.info(f"Got {len(mcp_tools)} tools from server '{server_name}'")
        
        # Convert MCP tools to OpenAI format
        openai_tools = [convert_mcp_tool_to_openai(tool) for tool in mcp_tools]
        
        return session, openai_tools
    except Exception as e:
        logger.error(f"Error in stdio_client: {type(e).__name__}: {str(e)}")
        raise

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
    # Set up logging
    setup_logging()
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MCP OpenAI Integration")
    parser.add_argument("prompt", help="The prompt to send to OpenAI")
    parser.add_argument("--config", default="mcp_config.json", help="Path to MCP config file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Set debug logging if requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    
    # Load environment variables
    load_dotenv(override=True)  # Force reload of environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    endpoint = os.getenv("OPENAI_ENDPOINT")
    model = os.getenv("OPENAI_MODEL", "gpt-4o")  # Default to gpt-4o if not specified
    
    if not api_key or not model:
        logger.error("OPENAI_API_KEY and OPENAI_MODEL must be set in .env file")
        sys.exit(1)
    
    # Load and validate MCP configuration
    try:
        config = load_and_validate_config(args.config)
        logger.info(f"Successfully loaded and validated configuration from {args.config}")
    except Exception as e:
        logger.error(f"Error loading or validating config file: {e}")
        sys.exit(1)
    
    # Connect to all MCP servers and collect tools
    sessions = {}
    all_tools = []
    connection_errors = []
    
    for server_name in config.get("mcpServers", {}):
        try:
            session, tools = await connect_to_mcp_server(server_name, config)
            # Store both session and tools to easily look up tools later
            sessions[server_name] = (session, tools)
            all_tools.extend(tools)
            logger.info(f"Successfully connected to server '{server_name}' with {len(tools)} tools")
        except Exception as e:
            error_msg = f"Could not connect to server '{server_name}': {str(e)}"
            logger.error(error_msg)
            connection_errors.append(f"{server_name}: {str(e)}")
            # Continue with other servers instead of raising an exception
    
    if not all_tools:
        # Only fail if we couldn't connect to ANY servers
        error_msgs = "\n".join(connection_errors)
        logger.error(f"No MCP tools were loaded. Errors:\n{error_msgs}")
        raise RuntimeError(f"No MCP tools were loaded. Errors:\n{error_msgs}")
    elif connection_errors:
        # Warn but continue if some servers failed
        logger.warning(f"Some MCP servers failed to connect. The system will operate with reduced functionality.")
        # Could also add this information to the first message to the model
        initial_message = f"{args.prompt}\n\nNote: Some requested capabilities are unavailable: {', '.join(connection_errors)}"
        messages = [{"role": "user", "content": initial_message}]
    else:
        messages = [{"role": "user", "content": args.prompt}]
    
    # Initialize OpenAI client
    client_kwargs = {"api_key": api_key}
    if endpoint:
        client_kwargs["base_url"] = endpoint
    
    logger.info(f"Using OpenAI API with model: {model}")
    if endpoint:
        logger.info(f"Using custom endpoint: {endpoint}")
    
    client = AsyncOpenAI(**client_kwargs)
    
    # Log the tools for debugging
    logger.debug(f"Tools being sent to OpenAI API: {json.dumps(all_tools, indent=2)}")
    
    # Stream the conversation
    first_message = True
    while True:
        # Call OpenAI API
        try:
            # Force the model to use the appropriate tool only for the first message
            tool_choice = "auto"
            if first_message:
                if "list_tables" in args.prompt.lower():
                    tool_choice = {
                        "type": "function",
                        "function": {"name": "list_tables"}
                    }
                elif "describe_table" in args.prompt.lower():
                    tool_choice = {
                        "type": "function",
                        "function": {"name": "describe_table"}
                    }
                elif "query_data" in args.prompt.lower() or "sql" in args.prompt.lower():
                    tool_choice = {
                        "type": "function",
                        "function": {"name": "query_data"}
                    }
                first_message = False
                
            logger.debug(f"Using tool_choice: {tool_choice}")
            
            stream = await client.chat.completions.create(
                model=model,
                messages=messages,
                tools=all_tools,
                stream=True,
                tool_choice=tool_choice
            )
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
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
                        logger.info(f"Model is calling function: {current_tool_call['function']['name']}")
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
                    logger.error(error_msg)
                    print(error_msg, file=sys.stderr)  # Keep console output for user visibility
                    messages.append({
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "name": function_name,
                        "content": error_msg
                    })
                    continue
                
                # Find the session that has this tool - improved logic for tool lookup
                server_name = None
                for srv_name, (session, tools) in sessions.items():
                    if any(t["function"]["name"] == function_name for t in tools):
                        server_name = srv_name
                        break
                
                if not server_name:
                    error_msg = f"Function {function_name} not found in any MCP server"
                    logger.error(error_msg)
                    print(error_msg, file=sys.stderr)  # Keep console output for user visibility
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
                    logger.info(f"Calling function {function_name} on server {server_name}")
                    result = await call_mcp_tool(session, function_name, function_args)
                    logger.info(f"Result from {function_name}: {result}")
                    print(f"Result from {function_name}: {result}", flush=True)  # Keep console output for user visibility
                    
                    # Add the tool response to the conversation
                    messages.append({
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "name": function_name,
                        "content": str(result)  # Ensure result is a string
                    })
                except Exception as e:
                    error_msg = f"Error calling {function_name}: {str(e)}"
                    logger.error(error_msg)
                    print(error_msg, file=sys.stderr)  # Keep console output for user visibility
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
    for server_name, (session, _) in sessions.items():
        try:
            logger.debug(f"Closing session for server '{server_name}'")
            await session.close()
            logger.debug(f"Session for server '{server_name}' closed successfully")
        except Exception as e:
            logger.warning(f"Error closing session for server '{server_name}': {e}")
            print(f"Warning: Error closing session for server '{server_name}': {e}", file=sys.stderr)
    
    logger.info("Conversation completed")
    print("Conversation completed.")

if __name__ == "__main__":
    asyncio.run(main())
