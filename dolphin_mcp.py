#!/usr/bin/env python

import os
import sys
import json
import asyncio
import logging
import dotenv
from openai import AsyncOpenAI

# Suppress debug logs; only show critical errors
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger("dolphin_mcp")
logger.setLevel(logging.CRITICAL)

dotenv.load_dotenv(override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT")
OPENAI_MODEL = os.getenv("OPENAI_MODEL") or "gpt-4-turbo"

if not OPENAI_API_KEY:
    print("Error: No OPENAI_API_KEY found.")
    sys.exit(1)

openai_client = AsyncOpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_ENDPOINT if OPENAI_ENDPOINT else None
)

class MCPClient:
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

    def _process_message(self, message):
        # Basic JSON-RPC handling: store responses by ID, etc.
        if "jsonrpc" in message and "id" in message:
            # It's either a response or a request from server
            if "result" in message or "error" in message:
                # It's a response
                self.responses[message["id"]] = message
            else:
                # It's a server->client request (not implemented)
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
            # It's a notification from the server, we ignore
            pass

    async def start(self):
        # Expand any ~ in args
        expanded_args = []
        for a in self.args:
            if isinstance(a, str) and "~" in a:
                expanded_args.append(os.path.expanduser(a))
            else:
                expanded_args.append(a)

        env_vars = os.environ.copy()
        if self.env:
            env_vars.update(self.env)

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

    async def _perform_initialize(self):
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
                    # Send notifications/initialized
                    note = {"jsonrpc": "2.0", "method": "notifications/initialized"}
                    await self._send_message(note)
                    # Store server caps
                    init_result = resp["result"]
                    self.server_capabilities = init_result.get("capabilities", {})
                    return True
            await asyncio.sleep(0.05)
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

    async def call_tool(self, tool_name, arguments):
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

    async def _send_message(self, msg):
        if not self.process or self.process.stdin.is_closing():
            return
        line = json.dumps(msg) + "\n"
        self.process.stdin.write(line.encode())
        await self.process.stdin.drain()

    async def close(self):
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
            # Discard stderr so it doesn't spam
            _ = await self.process.stderr.read()
            self.process = None

async def load_mcp_config():
    try:
        with open("mcp_config.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: mcp_config.json not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("Error: Invalid JSON in mcp_config.json.")
        sys.exit(1)

async def run():
    if len(sys.argv) < 2:
        print("Usage: python dolphin_mcp.py 'your query'")
        sys.exit(1)

    user_query = " ".join(sys.argv[1:])
    config = await load_mcp_config()
    servers_cfg = config.get("mcpServers", {})
    if not servers_cfg:
        print("Error: No servers in config.")
        sys.exit(1)

    # Connect to each server
    servers = {}
    all_tools = []
    for server_name, conf in servers_cfg.items():
        client = MCPClient(
            server_name,
            conf.get("command"),
            conf.get("args", []),
            conf.get("env")
        )
        ok = await client.start()
        if not ok:
            print(f"Could not start server {server_name}")
            continue
        # Gather tools
        tools = await client.list_tools()
        for t in tools:
            input_schema = t.get("inputSchema") or {"type": "object", "properties": {}}
            openai_tool = {
                "type": "function",
                "function": {
                    "name": f"{server_name}_{t['name']}",
                    "description": t.get("description", ""),
                    "parameters": input_schema
                }
            }
            all_tools.append(openai_tool)
        servers[server_name] = client

    if not servers:
        print("No servers could be connected.")
        sys.exit(1)

    # Build initial conversation
    conversation = [
        {"role": "system", "content": "You are a helpful assistant with multiple specialized tools."},
        {"role": "user", "content": user_query}
    ]

    #
    # MAIN LOOP:
    # We'll keep calling the model until it no longer requests any new function calls.
    #
    while True:
        # Call the model (non-streaming)
        resp = await openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=conversation,
            tools=all_tools,
            tool_choice="auto"
        )
        assistant_msg = resp.choices[0].message

        # Add the assistant's text (if any) to the conversation
        assistant_text = assistant_msg.content or ""
        conversation.append({"role": "assistant", "content": assistant_text})

        # Check if there are function (tool) calls
        if hasattr(assistant_msg, "tool_calls") and assistant_msg.tool_calls:
            # For each requested function call, call the corresponding server method
            for tc in assistant_msg.tool_calls:
                func_name = tc.function.name
                func_args = json.loads(tc.function.arguments or "{}")
                parts = func_name.split("_", 1)
                if len(parts) == 2:
                    srv_name, tool_name = parts
                    print(f"View result from {tool_name} from {srv_name} {json.dumps(func_args)}")

                    if srv_name in servers:
                        result = await servers[srv_name].call_tool(tool_name, func_args)
                        # Print the server's JSON result
                        print(json.dumps(result, indent=2))

                        # Add a 'function' role message with the JSON result
                        conversation.append({
                            "role": "function",
                            "name": func_name,
                            "content": json.dumps(result)
                        })
                    else:
                        # If server not found
                        print(f"[No server named {srv_name} found!]")
                        conversation.append({
                            "role": "function",
                            "name": func_name,
                            "content": json.dumps({"error":"Unknown server"})
                        })

            # If any function calls occurred, loop again
            # so the model can incorporate these results
            continue
        else:
            # No tool calls => the assistant is done with function usage
            # Print final assistant text and exit
            print("\n" + assistant_text.strip() + "\n")
            break

    # Done - close servers
    for cli in servers.values():
        await cli.close()

if __name__ == "__main__":
    asyncio.run(run())
