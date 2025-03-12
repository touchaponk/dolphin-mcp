#!/usr/bin/env python

import os
import sys
import json
import asyncio
import logging
import dotenv

from typing import Any, Dict, List, Optional

# ================
# Provider imports
# ================
import openai
from openai import OpenAI, APIError, RateLimitError  # to catch exceptions
from anthropic import Anthropic, AsyncAnthropic, APIError as AnthropicAPIError
import ollama

# ================
# Logging
# ================
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger("dolphin_mcp")
logger.setLevel(logging.CRITICAL)

# ================
# Load .env
# ================
dotenv.load_dotenv(override=True)

def parse_arguments():
    """
    Extract optional '--model <model_name>' from sys.argv,
    treat the rest as a user query.
    """
    args = sys.argv[1:]
    chosen_model = None
    user_query_parts = []
    i = 0
    while i < len(args):
        if args[i] == "--model":
            if i + 1 < len(args):
                chosen_model = args[i+1]
                i += 2
            else:
                print("Error: --model requires an argument")
                sys.exit(1)
        else:
            user_query_parts.append(args[i])
            i += 1

    user_query = " ".join(user_query_parts)
    return chosen_model, user_query

async def load_mcp_config() -> dict:
    try:
        with open("mcp_config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: mcp_config.json not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in mcp_config.json.")
        sys.exit(1)


class MCPClient:
    """Implementation for a single MCP server."""
    def __init__(self, server_name, command, args=None, env=None):
        self.server_name = server_name
        self.command = command
        self.args = args or []
        self.env = env
        self.process = None
        self.tools = []
        self.request_id = 0
        self.protocol_version = "2024-11-05"
        self.receive_task = None
        self.responses = {}
        self.server_capabilities = {}

    async def _receive_loop(self):
        """Continuously reads JSON-RPC messages from the server."""
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
        """Stores responses by ID, handles notifications, etc."""
        if "jsonrpc" in message and "id" in message:
            # It's either a response or a server->client request
            if "result" in message or "error" in message:
                self.responses[message["id"]] = message
            else:
                # A request from server, not implemented
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
            # It's a notification from the server
            pass

    async def start(self):
        """Start the MCP server and initialize."""
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
                env=env_vars
            )
            self.receive_task = asyncio.create_task(self._receive_loop())
            return await self._perform_initialize()
        except Exception:
            return False

    async def _perform_initialize(self):
        """Send 'initialize' and wait for response."""
        self.request_id += 1
        req_id = self.request_id
        req = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "initialize",
            "params": {
                "protocolVersion": self.protocol_version,
                "capabilities": {
                    "sampling": {}
                },
                "clientInfo": {
                    "name": "DolphinMCPClient",
                    "version": "1.0.0"
                }
            }
        }
        await self._send_message(req)

        start = asyncio.get_event_loop().time()
        while asyncio.get_event_loop().time() - start < 5:
            if req_id in self.responses:
                resp = self.responses[req_id]
                del self.responses[req_id]
                if "error" in resp:
                    return False
                if "result" in resp:
                    # Then send 'notifications/initialized'
                    note = {"jsonrpc": "2.0", "method": "notifications/initialized"}
                    await self._send_message(note)
                    init_result = resp["result"]
                    self.server_capabilities = init_result.get("capabilities", {})
                    return True
            await asyncio.sleep(0.05)
        return False

    async def list_tools(self):
        """Request and return the list of tools from the server."""
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
        while asyncio.get_event_loop().time() - start < 5:
            if rid in self.responses:
                resp = self.responses[rid]
                del self.responses[rid]
                if "error" in resp:
                    return []
                if "result" in resp and "tools" in resp["result"]:
                    self.tools = resp["result"]["tools"]
                    return self.tools
            await asyncio.sleep(0.05)
        return []

    async def call_tool(self, tool_name: str, arguments: dict):
        """Call a tool on the server."""
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
        while asyncio.get_event_loop().time() - start < 10:
            if rid in self.responses:
                resp = self.responses[rid]
                del self.responses[rid]
                if "error" in resp:
                    return {"error": resp["error"]}
                if "result" in resp:
                    return resp["result"]
            await asyncio.sleep(0.05)
        return {"error": "Timeout waiting for tool result"}

    async def _send_message(self, msg: dict):
        """Send JSON-RPC message to server."""
        if not self.process or self.process.stdin.is_closing():
            return
        line = json.dumps(msg) + "\n"
        self.process.stdin.write(line.encode())
        await self.process.stdin.drain()

    async def close(self):
        """Close the server process."""
        if self.receive_task and not self.receive_task.done():
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass
        if self.process:
            self.process.stdin.close()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=2)
            except asyncio.TimeoutError:
                self.process.terminate()
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=2)
                except asyncio.TimeoutError:
                    self.process.kill()
                    await self.process.wait()
            _ = await self.process.stderr.read()
            self.process = None

#
# Generation for each provider
#
async def generate_with_openai(conversation, model_cfg, all_functions):
    """
    Use openai>=1.0.0 library, with synchronous calls via run_in_executor.
    We pass `functions=all_functions, function_call='auto'` so the model can choose to call them.
    """
    api_key = model_cfg.get("apiKey") or os.getenv("OPENAI_API_KEY")
    if "apiBase" in model_cfg:
        client = OpenAI(api_key=api_key, base_url=model_cfg["apiBase"])
    else:
        client = OpenAI(api_key=api_key)

    model_name = model_cfg["model"]
    temperature = model_cfg.get("temperature", None)
    top_p = model_cfg.get("top_p", None)
    max_tokens = model_cfg.get("max_tokens", None)

    loop = asyncio.get_event_loop()

    def do_openai_sync():
        return client.chat.completions.create(
            model=model_name,
            messages=conversation,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            functions=all_functions,       # <--- Pass in the function definitions
            function_call="auto"           # <--- Let the model decide
        )

    try:
        resp = await loop.run_in_executor(None, do_openai_sync)
        choice = resp.choices[0]
        assistant_text = choice.message.content or ""
        tool_calls = []
        if choice.message.function_call:
            fc = choice.message.function_call
            tool_calls.append({
                "id": "call_openai",
                "function": {
                    "name": fc.name or "unknown_function",
                    "arguments": fc.arguments or "{}"
                }
            })
        return {"assistant_text": assistant_text, "tool_calls": tool_calls}

    except APIError as e:
        return {"assistant_text": f"OpenAI API error: {str(e)}", "tool_calls": []}
    except RateLimitError as e:
        return {"assistant_text": f"OpenAI rate limit: {str(e)}", "tool_calls": []}
    except Exception as e:
        return {"assistant_text": f"Unexpected OpenAI error: {str(e)}", "tool_calls": []}


async def generate_with_anthropic(conversation, model_cfg, all_functions):
    """
    Anthropics library doesn't currently support 'functions' the way OpenAI does.
    We skip them for now.
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
        return {"assistant_text": f"Unexpected Anthropics error: {str(e)}", "tool_calls": []}


async def generate_with_ollama(conversation, model_cfg, all_functions):
    """
    The ollama library does not support function calling in the same manner as OpenAI.
    We'll skip them here too.
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


async def generate_text(conversation, model_cfg, all_functions):
    """
    Depending on the provider, call the correct function.
    For OpenAI, pass all_functions in as 'functions=' so the model can do function calling.
    """
    provider = model_cfg.get("provider", "").lower()
    if provider == "openai":
        return await generate_with_openai(conversation, model_cfg, all_functions)
    elif provider == "anthropic":
        return await generate_with_anthropic(conversation, model_cfg, all_functions)
    elif provider == "ollama":
        return await generate_with_ollama(conversation, model_cfg, all_functions)
    else:
        return {"assistant_text": f"Unsupported provider '{provider}'", "tool_calls": []}


async def run():
    chosen_model_name, user_query = parse_arguments()
    if not user_query:
        print("Usage: python dolphin_mcp.py [--model <name>] 'your question'")
        sys.exit(1)

    config = await load_mcp_config()
    servers_cfg = config.get("mcpServers", {})
    models_cfg = config.get("models", [])

    if not servers_cfg:
        print("Error: No servers in config.")
        sys.exit(1)

    # 1) Choose a model
    selected_model = None
    if chosen_model_name:
        for m in models_cfg:
            if m.get("model") == chosen_model_name:
                selected_model = m
                break
        if not selected_model:
            print(f"Error: Model '{chosen_model_name}' not found in config.")
            sys.exit(1)
    else:
        # fallback to default
        for m in models_cfg:
            if m.get("default"):
                selected_model = m
                break
        if not selected_model and models_cfg:
            selected_model = models_cfg[0]

    if not selected_model:
        print("No model available in config.")
        sys.exit(1)

    # 2) Start MCP servers
    servers = {}
    # We'll store "all_functions" in the shape the new openai library wants:
    # each item is { "name": ..., "description":..., "parameters": {...} }
    # We'll accumulate them from each server's tools
    all_functions = []
    
    for server_name, conf in servers_cfg.items():
        client = MCPClient(
            server_name=server_name,
            command=conf.get("command"),
            args=conf.get("args", []),
            env=conf.get("env", {})
        )
        ok = await client.start()
        if not ok:
            print(f"Could not start server {server_name}")
            continue
        tools = await client.list_tools()

        # Convert each tool into an OpenAI function definition
        for t in tools:
            input_schema = t.get("inputSchema") or {"type": "object", "properties": {}}
            fn_def = {
                "name": f"{server_name}_{t['name']}",
                "description": t.get("description", ""),
                "parameters": input_schema
            }
            all_functions.append(fn_def)

        servers[server_name] = client

    if not servers:
        print("No MCP servers could be connected.")
        sys.exit(1)

    # 3) Build conversation
    system_msg = selected_model.get("systemMessage","")
    conversation = []
    if system_msg:
        conversation.append({"role":"system","content":system_msg})
    else:
        conversation.append({"role":"system","content":"You are a helpful assistant."})

    conversation.append({"role": "user", "content": user_query})

    # 4) Conversation loop
    while True:
        # Now pass all_functions to generate_text
        gen_result = await generate_text(conversation, selected_model, all_functions)
        assistant_text = gen_result["assistant_text"]
        tool_calls = gen_result.get("tool_calls", [])

        # Add the assistant message
        conversation.append({"role":"assistant","content":assistant_text})

        if not tool_calls:
            # No further function calls => done
            print("\n" + assistant_text.strip() + "\n")
            break

        # If there are function calls, we handle them
        for tc in tool_calls:
            func_name = tc["function"]["name"]
            func_args_str = tc["function"].get("arguments","{}")
            try:
                func_args = json.loads(func_args_str)
            except:
                func_args = {}

            parts = func_name.split("_",1)
            if len(parts) != 2:
                # can't parse "server_tool"
                conversation.append({
                    "role":"function",
                    "name": func_name,
                    "content": json.dumps({"error":"Invalid function name format"})
                })
                continue

            srv_name, tool_name = parts
            print(f"View result from {tool_name} from {srv_name} {json.dumps(func_args)}")

            if srv_name not in servers:
                print(f"[No server named {srv_name} connected!]")
                conversation.append({
                    "role":"function",
                    "name": func_name,
                    "content": json.dumps({"error":f"Unknown server: {srv_name}"})
                })
                continue

            result = await servers[srv_name].call_tool(tool_name, func_args)
            print(json.dumps(result, indent=2))

            # Insert a "function" role message so the model sees the tool's output
            conversation.append({
                "role":"function",
                "name": func_name,
                "content": json.dumps(result)
            })

        # Loop again so the model can incorporate these function messages

    # 5) Close servers
    for cli in servers.values():
        await cli.close()

if __name__ == "__main__":
    asyncio.run(run())
