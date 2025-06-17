"""
Core client functionality for Dolphin MCP.
"""
import traceback
import os
import sys
import json
import asyncio
import logging
import tempfile
from typing import Any, Dict, List, Optional, Union, AsyncGenerator

from mcp.client.sse import sse_client
from mcp import ClientSession

from .utils import load_config_from_file # Renamed import
from .providers.openai import generate_with_openai
from .providers.msazureopenai import generate_with_msazure_openai
from .providers.anthropic import generate_with_anthropic
from .providers.ollama import generate_with_ollama
from .providers.lmstudio import generate_with_lmstudio
from .reasoning import MultiStepReasoner, ReasoningConfig

logger = logging.getLogger("dolphin_mcp")
logging.getLogger(__name__).setLevel(logging.DEBUG)  # Set default logging level to DEBUG

class SSEMCPClient:
    """Implementation for a SSE-based MCP server."""

    def __init__(self, server_name: str, url: str, headers: Optional[Dict[str, str]] = None):
        self.server_name = server_name
        self.url = url
        self.headers = headers or {}
        self.tools = []
        self._streams_context = None
        self._session_context = None
        self.session = None

    async def start(self):
        try:
            logger.debug(f"Starting SSE MCP server {self.server_name} at {self.url} with headers: {self.headers}")
            self._streams_context = sse_client(url=self.url, headers=self.headers)
            streams = await self._streams_context.__aenter__()

            self._session_context = ClientSession(*streams)
            self.session = await self._session_context.__aenter__()

            # Initialize
            await self.session.initialize()
            return True
        except Exception as e:
            logger.error(f"Server {self.server_name}: SSE connection error: {str(e)}")
            # print stack
            traceback.print_exc()
            return False

    async def list_tools(self):
        if not self.session:
            return []
        try:
            response = await self.session.list_tools()
            # 将 pydantic 模型转换为字典格式
            self.tools = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    # "inputSchema": tool.inputSchema.model_dump() if tool.inputSchema else None
                    "inputSchema": tool.inputSchema
                }
                for tool in response.tools
            ]
            return self.tools
        except Exception as e:
            logger.error(f"Server {self.server_name}: List tools error: {str(e)}")
            return []

    async def call_tool(self, tool_name: str, arguments: dict):
        if not self.session:
            return {"error": "Not connected"}
        try:
            response = await self.session.call_tool(tool_name, arguments)
            # 将 pydantic 模型转换为字典格式
            return response.model_dump() if hasattr(response, 'model_dump') else response
        except Exception as e:
            logger.error(f"Server {self.server_name}: Tool call error: {str(e)}")
            return {"error": str(e)}

    async def stop(self):
        if self.session:
            await self._session_context.__aexit__(None, None, None)
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)


class MCPClient:
    """Implementation for a single MCP server."""
    def __init__(self, server_name, command, args=None, env=None, cwd=None, tool_timeout=None):
        self.server_name = server_name
        self.command = command
        self.args = args or []
        self.env = env
        self.tool_timeout = tool_timeout if tool_timeout is not None else 3600
        self.process = None
        self.tools = []
        self.request_id = 0
        self.protocol_version = "2024-11-05"
        self.receive_task = None
        self.responses = {}
        self.server_capabilities = {}
        self._shutdown = False
        self._cleanup_lock = asyncio.Lock()
        self.cwd = cwd

    async def _receive_loop(self):
        if not self.process or self.process.stdout.at_eof():
            return
        try:
            while not self.process.stdout.at_eof():
                line = await self.process.stdout.readline()
                if not line:
                    break
                try:
                    message = json.loads(line.decode().strip())
                    self._process_message(message)
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass

    def _process_message(self, message: dict):
        if "jsonrpc" in message and "id" in message:
            if "result" in message or "error" in message:
                self.responses[message["id"]] = message
            else:
                # request from server, not implemented
                resp = {
                    "jsonrpc": "2.0",
                    "id": message["id"],
                    "error": {
                        "code": -32601,
                        "message": f"Method {message.get('method')} not implemented in client"
                    }
                }
                asyncio.create_task(self._send_message(resp))
        elif "jsonrpc" in message and "method" in message and "id" not in message:
            # notification from server
            pass

    async def start(self):
        logger.debug(f"Starting MCP server {self.server_name} with command: {self.command} {self.args}")
        expanded_args = []
        for a in self.args:
            if isinstance(a, str) and "~" in a:
                expanded_args.append(os.path.expanduser(a))
            else:
                expanded_args.append(a)

        env_vars = os.environ.copy()
        if self.env:
            env_vars.update(self.env)

        try:
            self.process = await asyncio.create_subprocess_exec(
                self.command,
                *expanded_args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env_vars,
                cwd=self.cwd,
                limit=1 << 20 # Set a larger buffer size for stdout
            )
            self.receive_task = asyncio.create_task(self._receive_loop())
            # Print subprocess stdout to current process stdout
            async def _print_stdout(proc):
                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    logger.debug(f"[{self.server_name} STDOUT]", line.decode().rstrip(), file=sys.stdout)
                    await asyncio.sleep(0.01)  # Throttle to avoid busy loop
            asyncio.create_task(_print_stdout(self.process))
            # Print subprocess stderr to current process stderr
            async def _print_stderr(proc):
                while True:
                    line = await proc.stderr.readline()
                    if not line:
                        break
                    logger.error(f"[{self.server_name} STDERR]", line.decode().rstrip(), file=sys.stderr)
                    await asyncio.sleep(0.01)  # Throttle to avoid busy loop
            asyncio.create_task(_print_stderr(self.process))
            return await self._perform_initialize()
        except Exception as e:
            logger.error(f"Server {self.server_name}: Failed to start process: {str(e)}")
            return False

    async def _perform_initialize(self):
        self.request_id += 1
        req_id = self.request_id
        req = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "initialize",
            "params": {
                "protocolVersion": self.protocol_version,
                "capabilities": {"sampling": {}},
                "clientInfo": {
                    "name": "DolphinMCPClient",
                    "version": "1.0.0"
                }
            }
        }
        await self._send_message(req)

        start = asyncio.get_event_loop().time()
        timeout = 10  # Increased timeout to 10 seconds
        while asyncio.get_event_loop().time() - start < timeout:
            if req_id in self.responses:
                resp = self.responses[req_id]
                del self.responses[req_id]
                if "error" in resp:
                    logger.error(f"Server {self.server_name}: Initialize error: {resp['error']}")
                    return False
                if "result" in resp:
                    elapsed = asyncio.get_event_loop().time() - start
                    logger.info(f"Server {self.server_name}: Initialized in {elapsed:.2f}s")
                    note = {"jsonrpc": "2.0", "method": "notifications/initialized"}
                    await self._send_message(note)
                    init_result = resp["result"]
                    self.server_capabilities = init_result.get("capabilities", {})
                    return True
            await asyncio.sleep(0.05)
        logger.error(f"Server {self.server_name}: Initialize timed out after {timeout}s")
        return False

    async def list_tools(self):
        if not self.process:
            return []
        self.request_id += 1
        rid = self.request_id
        req = {
            "jsonrpc": "2.0",
            "id": rid,
            "method": "tools/list",
            "params": {}
        }
        await self._send_message(req)

        start = asyncio.get_event_loop().time()
        timeout = 10  # Increased timeout to 10 seconds
        while asyncio.get_event_loop().time() - start < timeout:
            if rid in self.responses:
                resp = self.responses[rid]
                del self.responses[rid]
                if "error" in resp:
                    logger.error(f"Server {self.server_name}: List tools error: {resp['error']}")
                    return []
                if "result" in resp and "tools" in resp["result"]:
                    elapsed = asyncio.get_event_loop().time() - start
                    logger.info(f"Server {self.server_name}: Listed {len(resp['result']['tools'])} tools in {elapsed:.2f}s")
                    self.tools = resp["result"]["tools"]
                    return self.tools
            await asyncio.sleep(0.05)
        logger.error(f"Server {self.server_name}: List tools timed out after {timeout}s")
        return []
    
    async def call_tool(self, tool_name: str, arguments: dict):
        if not self.process:
            return {"error": "Not started"}
        self.request_id += 1
        rid = self.request_id
        req = {
            "jsonrpc": "2.0",
            "id": rid,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        await self._send_message(req)

        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < self.tool_timeout:
            if rid in self.responses:
                resp = self.responses[rid]
                del self.responses[rid]
                if "error" in resp:
                    logger.error(f"Server {self.server_name}: Tool {tool_name} error: {resp['error']}")
                    return {"error": resp["error"]}
                if "result" in resp:
                    elapsed = asyncio.get_event_loop().time() - start
                    logger.info(f"Server {self.server_name}: Tool {tool_name} completed in {elapsed:.2f}s")
                    return resp["result"]
            await asyncio.sleep(0.01)  # Reduced sleep interval for more responsive streaming
            if asyncio.get_event_loop().time() - start > 5:  # Log warning after 5 seconds
                logger.warning(f"Server {self.server_name}: Tool {tool_name} taking longer than 5s...")
        logger.error(f"Server {self.server_name}: Tool {tool_name} timed out after {self.tool_timeout}s")
        return {"error": f"Timeout waiting for tool result after {self.tool_timeout}s"}

    async def _send_message(self, message: dict):
        if not self.process or self._shutdown:
            logger.error(f"Server {self.server_name}: Cannot send message - process not running or shutting down")
            return False
        try:
            data = json.dumps(message) + "\n"
            self.process.stdin.write(data.encode())
            await self.process.stdin.drain()
            return True
        except Exception as e:
            logger.error(f"Server {self.server_name}: Error sending message: {str(e)}")
            return False

    async def stop(self):
        async with self._cleanup_lock:
            if self._shutdown:
                return
            self._shutdown = True

            if self.receive_task and not self.receive_task.done():
                self.receive_task.cancel()
                try:
                    await self.receive_task
                except asyncio.CancelledError:
                    pass

            if self.process:
                try:
                    # Try to send a shutdown notification first
                    try:
                        note = {"jsonrpc": "2.0", "method": "shutdown"}
                        await self._send_message(note)
                        # Give a small window for the process to react
                        await asyncio.sleep(0.5)
                    except:
                        pass

                    # Close stdin before terminating to prevent pipe errors
                    if self.process.stdin:
                        self.process.stdin.close()

                    # Try graceful shutdown first
                    self.process.terminate()
                    try:
                        # Use a shorter timeout to make cleanup faster
                        await asyncio.wait_for(self.process.wait(), timeout=1.0)
                    except asyncio.TimeoutError:
                        # Force kill if graceful shutdown fails
                        logger.warning(f"Server {self.server_name}: Force killing process after timeout")
                        self.process.kill()
                        try:
                            await asyncio.wait_for(self.process.wait(), timeout=1.0)
                        except asyncio.TimeoutError:
                            logger.error(f"Server {self.server_name}: Process did not respond to SIGKILL")
                except Exception as e:
                    logger.error(f"Server {self.server_name}: Error during process cleanup: {str(e)}")
                finally:
                    # Make sure we clear the reference
                    self.process = None

    # Alias close to stop for backward compatibility
    async def close(self):
        await self.stop()

    # Add async context manager support
    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

async def generate_text(conversation: List[Dict], model_cfg: Dict,
all_functions: List[Dict], stream: bool = False) -> Union[Dict, AsyncGenerator]:
    """
    Generate text using the specified provider.

    Args:
        conversation: The conversation history
        model_cfg: Configuration for the model
        all_functions: Available functions for the model to call
        stream: Whether to stream the response

    Returns:
        If stream=False: Dict containing assistant_text and tool_calls
        If stream=True: AsyncGenerator yielding chunks of assistant text and tool calls
    """
    provider = model_cfg.get("provider", "").lower()

    if provider == "openai":
        if stream:
            return generate_with_openai(conversation, model_cfg, all_functions, stream=True)
        else:
            return await generate_with_openai(conversation, model_cfg, all_functions, stream=False)

    if provider == "msazureopenai":
        try:
            if stream:
                return generate_with_msazure_openai(conversation, model_cfg, all_functions, stream=True)
            else:
                return await generate_with_msazure_openai(conversation, model_cfg, all_functions, stream=False)
        except Exception as e:
            traceback.print_exc()
            raise e


    # For non-streaming providers, wrap the response in an async generator if streaming is requested
    if stream:
        async def wrap_response():
            if provider == "anthropic":
                result = await generate_with_anthropic(conversation, model_cfg, all_functions)
            elif provider == "ollama":
                result = await generate_with_ollama(conversation, model_cfg, all_functions)
            elif provider == "lmstudio":
                result = await generate_with_lmstudio(conversation, model_cfg, all_functions)
            else:
                result = {"assistant_text": f"Unsupported provider '{provider}'", "tool_calls": []}
            yield result
        return wrap_response()

    # Non-streaming path
    if provider == "anthropic":
        return await generate_with_anthropic(conversation, model_cfg, all_functions)
    elif provider == "ollama":
        return await generate_with_ollama(conversation, model_cfg, all_functions)
    elif provider == "lmstudio":
        return await generate_with_lmstudio(conversation, model_cfg, all_functions)
    else:
        return {"assistant_text": f"Unsupported provider '{provider}'", "tool_calls": []}

async def log_messages_to_file(messages: List[Dict], functions: List[Dict], log_path: str):
    """
    Log messages and function definitions to a JSONL file.

    Args:
        messages: List of messages to log
        functions: List of function definitions
        log_path: Path to the log file
    """
    try:
        # Create directory if it doesn't exist
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Append to file
        with open(log_path, "a") as f:
            f.write(json.dumps({
                "messages": messages,
                "functions": functions
            }) + "\n")
    except Exception as e:
        logger.error(f"Error logging messages to {log_path}: {str(e)}")

def process_long_fields(tool_result: Any, max_length: int = 15000) -> Any:
    """
    Process tool result and replace long string fields with file references.
    
    Args:
        result: The tool result (can be dict, list, or any JSON-serializable value)
        max_length: Maximum length for string fields before writing to file
        
    Returns:
        Modified result with long fields replaced by file references
    """
    if not isinstance(tool_result, (dict, list)):
        return tool_result
    
    result_is_content_text = False
    result = tool_result
     # extract result.content[0].text as JSON if available
    if isinstance(result, dict) and "content" in result and isinstance(result["content"], list):
        if len(result["content"]) > 0 and isinstance(result["content"][0], dict) and "text" in result["content"][0]:
            try:
                logger.info("Extracting content.text as JSON")
                result = json.loads(result["content"][0]["text"])
                result_is_content_text = True
            except json.JSONDecodeError:
                logger.error("Failed to decode content.text as JSON, using original result")
    
    
    # First check if any field is too long by recursively traversing
    long_field_found = False
    
    def check_for_long_fields(obj: Any) -> bool:
        if isinstance(obj, str) and len(obj) > max_length:
            return True
        elif isinstance(obj, dict):
            return any(check_for_long_fields(v) for v in obj.values())
        elif isinstance(obj, list):
            return any(check_for_long_fields(item) for item in obj)
        return False
    
    long_field_found = check_for_long_fields(result)
    
    if not long_field_found:
        return tool_result
    
    # If we found long fields, write the original result to a temp file
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(result, f, indent=2)
            temp_file_path = f.name
        
        logger.info(f"Tool response contains long fields, full response written to: {temp_file_path}")
        
        # Now create a modified version with long fields replaced
        def replace_long_fields(obj: Any) -> Any:
            if isinstance(obj, str) and len(obj) > max_length:
                preview = obj[:200] + "..." if len(obj) > 200 else obj
                logger.info(f"Field too long, replacing with file reference: {preview}...<content_written_to_file:{temp_file_path}>")
                return f"{preview}\n\n<content_written_to_file:{temp_file_path}>"
            elif isinstance(obj, dict):
                return {k: replace_long_fields(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_long_fields(item) for item in obj]
            return obj
        
        result = replace_long_fields(result)
        if result_is_content_text:
            # If we extracted content.text as JSON, we need to wrap it back
            tool_result["content"][0]["text"] = json.dumps(result, indent=0, ensure_ascii=False)
        else:
            tool_result = result
        return tool_result
        
    except Exception as e:
        logger.error(f"Error processing long fields: {str(e)}")
        return tool_result

async def process_tool_call(tc: Dict, servers: Dict[str, MCPClient], quiet_mode: bool) -> Optional[Dict]:
    """Process a single tool call and return the result"""
    func_name = tc["function"]["name"]
    func_args_str = tc["function"].get("arguments", "{}")
    try:
        func_args = json.loads(func_args_str)
    except:
        func_args = {}

    parts = func_name.split("_", 1)
    if len(parts) != 2:
        return {
            "role": "tool",
            "tool_call_id": tc["id"],
            "name": func_name,
            "content": json.dumps({"error": "Invalid function name format"})
        }

    srv_name, tool_name = parts
    if not quiet_mode:
        print(f"\nView result from {tool_name} from {srv_name} {json.dumps(func_args)}")
    else:
        print(f"\nProcessing tool call...{tool_name}")

    if srv_name not in servers:
        return {
            "role": "tool",
            "tool_call_id": tc["id"],
            "name": func_name,
            "content": json.dumps({"error": f"Unknown server: {srv_name}"})
        }

    # Get the tool's schema
    tool_schema = None
    for tool in servers[srv_name].tools:
        if tool["name"] == tool_name:
            tool_schema = tool.get("inputSchema", {})
            break

    if tool_schema:
        # Ensure required parameters are present
        required_params = tool_schema.get("required", [])
        for param in required_params:
            if param not in func_args:
                return {
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "name": func_name,
                    "content": json.dumps({"error": f"Missing required parameter: {param}"})
                }

    result = await servers[srv_name].call_tool(tool_name, func_args)
    if not quiet_mode:
        print(json.dumps(result, indent=2))

    # Process the result to handle long fields
    processed_result = process_long_fields(result)

    return {
        "role": "tool",
        "tool_call_id": tc["id"],
        "name": func_name,
        "content": json.dumps(processed_result)
    }


class MCPAgent:
    @classmethod
    async def create(cls,
                     model_name: Optional[str] = None,
                     provider_config: dict = None, # New parameter
                     mcp_server_config: Optional[dict] = None, # Renamed from config
                     mcp_server_config_path: str = "mcp_config.json", # Renamed from config_path
                     quiet_mode: bool = False,
                     log_messages_path: Optional[str] = None,
                     stream: bool = False,
                     reasoning_config: Optional[ReasoningConfig] = None) -> "MCPAgent":
        """
        Create an instance of the MCPAgent using MCPAgent.create(...)
        async class method so that the initialization can be awaited.

        Args:
            model_name: Name of the model to use (optional)
            provider_config: Provider configuration dictionary (required)
            mcp_server_config: MCP server configuration dict (optional, if not provided will load from mcp_server_config_path)
            mcp_server_config_path: Path to the MCP server configuration file (default: mcp_config.json)
            quiet_mode: Whether to suppress intermediate output (default: False)
            log_messages_path: Path to log messages in JSONL format (optional)
            stream: Whether to stream the response (default: False)
            reasoning_config: Configuration for multi-step reasoning (optional)

        Returns:
            An instance of MCPAgent 
        """
        if provider_config is None:
            # This should ideally be handled by loading a default or raising an error earlier,
            # but for now, let's ensure it's not None.
            # In practice, run_interaction loads it.
            raise ValueError("provider_config cannot be None")

        obj = cls()
        await obj._initialize(
            model_name=model_name,
            provider_config=provider_config,
            mcp_server_config=mcp_server_config,
            mcp_server_config_path=mcp_server_config_path,
            quiet_mode=quiet_mode,
            log_messages_path=log_messages_path,
            stream=stream,
            reasoning_config=reasoning_config
        )
        return obj
    
    def __init__(self):
        pass

    async def _initialize(self,
                          model_name: Optional[str] = None,
                          provider_config: dict = None, # New parameter
                          mcp_server_config: Optional[dict] = None, # Renamed from config
                          mcp_server_config_path: str = "mcp_config.json", # Renamed from config_path
                          quiet_mode: bool = False,
                          log_messages_path: Optional[str] = None,
                          stream: bool = False,
                          reasoning_config: Optional[ReasoningConfig] = None) -> Union[str, AsyncGenerator[str, None]]:

        self.stream = stream
        self.log_messages_path = log_messages_path
        self.quiet_mode = quiet_mode
        
        # Initialize the reasoning system
        self.reasoning_config = reasoning_config or ReasoningConfig()
        self.reasoner = MultiStepReasoner(self.reasoning_config)

        # 1) Load MCP Server config if not provided directly
        if mcp_server_config is None:
            mcp_server_config = await load_config_from_file(mcp_server_config_path)

        servers_cfg = mcp_server_config.get("mcpServers", {})
        models_cfg = provider_config.get("models", []) # Get models from provider_config

        # 2) Choose a model
        self.chosen_model = None
        if model_name:
            for m in models_cfg:
                if m.get("model") == model_name or m.get("title") == model_name:
                    self.chosen_model = m
                    break
            if not self.chosen_model: # If specific model not found, try default
                for m in models_cfg:
                    if m.get("default"):
                        self.chosen_model = m
                        break
        else: # If no model_name specified, pick default
            for m in models_cfg:
                if m.get("default"):
                    self.chosen_model = m
                    break
            if not self.chosen_model and models_cfg: # If no default, pick first
                self.chosen_model = models_cfg[0]

        if not self.chosen_model:
            error_msg = "No suitable model found in provider_config."
            if stream:
                async def error_gen():
                    yield error_msg
                return error_gen()
            return error_msg

        # 3) Start servers
        self.servers = {}
        self.all_functions = []
        tool_timeout = provider_config.get("tool_timeout")
        for server_name, conf in servers_cfg.items():
            # Check if server is disabled
            if conf.get("disabled", False):
                if not quiet_mode:
                    print(f"[SKIP] {server_name} (disabled)")
                continue
                
            # Determine transport type
            transport = conf.get("transport", "stdio")  # Default to stdio for backward compatibility
            
            if transport == "sse" or ("url" in conf and transport != "stdio"):
                # SSE server
                if "url" not in conf:
                    if not quiet_mode:
                        print(f"[WARN] Server {server_name} has transport 'sse' but no URL specified")
                    continue
                client = SSEMCPClient(
                    server_name=server_name, 
                    url=conf["url"],
                    headers=conf.get("headers")
                )
            else:
                # Local process-based server (stdio transport)
                client = MCPClient(
                    server_name=server_name,
                    command=conf.get("command"),
                    args=conf.get("args", []),
                    env=conf.get("env", {}),
                    cwd=conf.get("cwd", None),
                    tool_timeout=tool_timeout 
                )
            ok = await client.start()
            if not ok:
                if not quiet_mode:
                    print(f"[WARN] Could not start server {server_name}")
                continue
            else:
                print(f"[OK] {server_name}")

            # gather tools
            tools = await client.list_tools()
            for t in tools:
                input_schema = t.get("inputSchema") or {"type": "object", "properties": {}}
                fn_def = {
                    "name": f"{server_name}_{t['name']}",
                    "description": t.get("description", ""),
                    "parameters": input_schema
                }
                self.all_functions.append(fn_def)

            self.servers[server_name] = client

        if not self.servers:
            error_msg = "No MCP servers could be started."
            if stream:
                async def error_gen():
                    yield error_msg
                return error_gen()
            return error_msg

        self.conversation = []

        # 4) Build conversation
        # Get system message - either from systemMessageFile, systemMessage, or default
        system_msg = "You are a helpful assistant."
        if "systemMessageFile" in self.chosen_model:
            try:
                with open(self.chosen_model["systemMessageFile"], "r", encoding="utf-8") as f:
                    system_msg = f.read()
            except Exception as e:
                logger.warning(f"Failed to read system message file: {e}")
                # Fall back to direct systemMessage if available
                self.conversation.append({"role": "system", "content": self.chosen_model.get("systemMessage", system_msg)})
        else:
            self.conversation.append({"role": "system", "content": self.chosen_model.get("systemMessage", system_msg)})
        if "systemMessageFiles" in self.chosen_model:
            for file in self.chosen_model["systemMessageFiles"]:
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        system_msg = f.read()
                        self.conversation.append({"role": "system", "content": "File: " + file + "\n" + system_msg})
                except Exception as e:
                    logger.warning(f"Failed to read system message file: {e}")

    async def cleanup(self):
        """Clean up servers and log messages"""
        if self.log_messages_path:
            await log_messages_to_file(self.conversation, self.all_functions, self.log_messages_path)
        for cli in self.servers.values():
            await cli.stop()
        self.servers.clear()

    async def prompt_with_reasoning(self, user_query: str, guidelines: str = "") -> str:
        """
        Prompt using the multi-step reasoning approach with planning and execution.
        
        Args:
            user_query: The user's query
            guidelines: Optional answer guidelines
            
        Returns:
            The final answer from the reasoning process
        """
        if not self.quiet_mode:
            self.reasoning_config.reasoning_trace("Planning...")
        
        # Generate initial plan
        initial_plan = await self.reasoner.generate_plan(
            user_query, guidelines, generate_text, self.chosen_model, self.all_functions
        )
        
        if not self.quiet_mode:
            log_planning = f"""
<plan>
{initial_plan}
</plan>
"""
            self.reasoning_config.reasoning_trace(log_planning)
            self.reasoning_config.reasoning_trace("Starting execution...")
        
        # Execute the reasoning loop
        success, result = await self.reasoner.execute_reasoning_loop(
            user_query, guidelines, initial_plan,
            generate_text, self.chosen_model, self.all_functions,
            process_tool_call, self.servers, self.quiet_mode
        )
        
        if success:
            if not self.quiet_mode:
                self.reasoning_config.reasoning_trace("\n====== ✅ FINAL ANSWER FOUND ======")
            return result
        else:
            if not self.quiet_mode:
                self.reasoning_config.reasoning_trace(f"\n====== ❌ ERROR OR MAX ITERATIONS ======\n{result}")
            return result

    async def prompt(self, user_query, use_reasoning: bool = None, guidelines: str = ""):
        """
        Prompt the specified model along with the configured MCP servers.

        Args:
            user_query: The user's query
            use_reasoning: Whether to use multi-step reasoning. If None, uses config default.
            guidelines: Answer guidelines (used with reasoning mode)

        Returns:
            If self.stream=False: The final text response
            If self.stream=True: AsyncGenerator yielding chunks of the response
        """
        # Determine if we should use reasoning mode
        should_use_reasoning = use_reasoning if use_reasoning is not None else self.reasoning_config.enable_planning
        
        if should_use_reasoning and not self.stream:
            # Use the new multi-step reasoning approach
            return await self.prompt_with_reasoning(user_query, guidelines)
        else:
            # Use the original simple approach
            return await self._prompt_original(user_query)
    
    async def _prompt_original(self, user_query):
        """
        Original prompt method that uses simple tool-call loop.
        
        Args:
            user_query: The user's query

        Returns:
            If self.stream=False: The final text response
            If self.stream=True: AsyncGenerator yielding chunks of the response
        """        
        self.conversation.append({"role": "user", "content": user_query})

        if self.stream:
            async def stream_response():
                try:
                    while True:  # Main conversation loop
                        generator = await generate_text(self.conversation, self.chosen_model, self.all_functions, stream=True)
                        accumulated_text = ""
                        tool_calls_processed = False
                        
                        async for chunk in await generator:
                            if chunk.get("is_chunk", False):
                                # Immediately yield each token without accumulation
                                if chunk.get("token", False):
                                    yield chunk["assistant_text"]
                                accumulated_text += chunk["assistant_text"]
                            else:
                                # This is the final chunk with tool calls
                                if accumulated_text != chunk["assistant_text"]:
                                    # If there's any remaining text, yield it
                                    remaining = chunk["assistant_text"][len(accumulated_text):]
                                    if remaining:
                                        yield remaining
                                
                                # Process any tool calls from the final chunk
                                tool_calls = chunk.get("tool_calls", [])
                                if tool_calls:
                                    # Add type field to each tool call
                                    for tc in tool_calls:
                                        tc["type"] = "function"
                                    # Add the assistant's message with tool calls
                                    assistant_message = {
                                        "role": "assistant",
                                        "content": chunk["assistant_text"],
                                        "tool_calls": tool_calls
                                    }
                                    self.conversation.append(assistant_message)
                                    
                                    # Process each tool call
                                    for tc in tool_calls:
                                        if tc.get("function", {}).get("name"):
                                            result = await process_tool_call(tc, self.servers, self.quiet_mode)
                                            if result:
                                                self.conversation.append(result)
                                                tool_calls_processed = True
                        
                        # Break the loop if no tool calls were processed
                        if not tool_calls_processed:
                            break
                        
                finally:
                    pass
            return stream_response()
        else:
            try:
                final_text = ""
                while True:
                    gen_result = await generate_text(self.conversation, self.chosen_model, self.all_functions, stream=False)
                    
                    assistant_text = gen_result["assistant_text"]
                    final_text = assistant_text
                    tool_calls = gen_result.get("tool_calls", [])

                    # Add the assistant's message
                    assistant_message = {"role": "assistant", "content": assistant_text}
                    if tool_calls:
                        # Add type field to each tool call
                        for tc in tool_calls:
                            tc["type"] = "function"
                        assistant_message["tool_calls"] = tool_calls
                    self.conversation.append(assistant_message)
                    logger.info(f"Added assistant message: {json.dumps(assistant_message, indent=2)}")

                    if not tool_calls:
                        break

                    for tc in tool_calls:
                        result = await process_tool_call(tc, self.servers, self.quiet_mode)
                        if result:
                            self.conversation.append(result)
                            logger.info(f"Added tool result: {json.dumps(result, indent=2)}")

            finally:
                return final_text
            
async def run_interaction(
    user_query: str,
    model_name: Optional[str] = None,
    provider_config: Optional[dict] = None, # New parameter for provider config
    provider_config_path: str = "config.yml", # New parameter for provider config
    mcp_server_config: Optional[dict] = None, # Renamed from config
    mcp_server_config_path: str = "mcp_config.json", # Renamed from config_path
    quiet_mode: bool = False,
    log_messages_path: Optional[str] = None,
    stream: bool = False,
    reasoning_config: Optional[ReasoningConfig] = None,
    use_reasoning: Optional[bool] = None,
    guidelines: str = ""
) -> Union[str, AsyncGenerator[str, None]]:
    """
    Run an interaction with the MCP servers.

    Args:
        user_query: The user's query
        model_name: Name of the model to use (optional)
        provider_config: Provider server configuration dict
        provider_config_path: Path to the provider configuration file (default: config.yml)
        mcp_server_config: MCP server configuration dict (optional, if not provided will load from mcp_server_config_path)
        mcp_server_config_path: Path to the MCP server configuration file (default: mcp_config.json)
        quiet_mode: Whether to suppress intermediate output (default: False)
        log_messages_path: Path to log messages in JSONL format (optional)
        stream: Whether to stream the response (default: False)
        reasoning_config: Configuration for multi-step reasoning (optional)
        use_reasoning: Whether to use multi-step reasoning (optional, overrides config default)
        guidelines: Answer guidelines for reasoning mode (optional)

    Returns:
        If stream=False: The final text response
        If stream=True: AsyncGenerator yielding chunks of the response
    """
    if provider_config is None:
        provider_config = await load_config_from_file(provider_config_path)
    agent = await MCPAgent.create(
        model_name=model_name,
        provider_config=provider_config, # Pass loaded provider_config
        mcp_server_config=mcp_server_config, # Pass mcp_server_config
        mcp_server_config_path=mcp_server_config_path, # Pass mcp_server_config_path
        quiet_mode=quiet_mode,
        log_messages_path=log_messages_path,
        stream=stream,
        reasoning_config=reasoning_config
    )
    response = await agent.prompt(user_query, use_reasoning=use_reasoning, guidelines=guidelines)
    await agent.cleanup()
    return response
