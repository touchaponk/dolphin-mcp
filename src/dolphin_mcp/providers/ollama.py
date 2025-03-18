"""
Ollama provider implementation for Dolphin MCP.
"""

from typing import Dict, List, Any



tool_name_mapping: Dict[str, str] = {}


def sanitize_tool_name(name: str) -> str:
        """Sanitize tool name for OpenAI compatibility"""
        # Replace any characters that might cause issues
        return name.replace("-", "_").replace(" ", "_").lower()

def convert_mcp_tools_to_openai_format(mcp_tools: List[Any]) -> List[Dict[str, Any]]:
        """Convert MCP tool format to OpenAI tool format"""
        openai_tools = []
        
#        print(f"Input mcp_tools type: {type(mcp_tools)}")
#        print(f"Input mcp_tools: {mcp_tools}")
        
        # Extract tools from the response
        if hasattr(mcp_tools, 'tools'):
            tools_list = mcp_tools.tools
#            print("Found ListToolsResult, extracting tools attribute")
        elif isinstance(mcp_tools, dict):
            tools_list = mcp_tools.get('tools', [])
#            print("Found dict, extracting 'tools' key")
        else:
            tools_list = mcp_tools
#            print("Using mcp_tools directly as list")
            
#        print(f"Tools list type: {type(tools_list)}")
#        print(f"Tools list: {tools_list}")
        
        # Process each tool in the list
        if isinstance(tools_list, list):
            #print(f"Processing {len(tools_list)} tools")
            for tool in tools_list:
                #print(f"Processing tool: {tool}, type: {type(tool)}")
                if "name" in tool.keys() and "description" in tool.keys():
                    #openai_name = sanitize_tool_name(tool["name"])
                    openai_name = tool["name"]
                    tool_name_mapping[openai_name] = tool["name"]
#                    print(f"Tool has required attributes. Name: {tool["name"]}")
                    
                    tool_schema = {
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    if "parameters" in tool.keys():
                        tool_schema = tool['parameters']
                    
                    
                    openai_tool = {
                        "type": "function",
                        "function": {
                            "name": openai_name,
                            "description": tool["description"],
                            "parameters": tool_schema
                        }
                    }
                    #print(openai_tool)
                    openai_tools.append(openai_tool)
                    #print(f"Converted tool {tool["name"]} to OpenAI format")
                else:
                    print(f"Tool missing required attributes: has name = {'name' in tool.keys()}, has description = {'description' in tool.keys()}")
                    a=1
        else:
#            print(f"Tools list is not a list, it's a {type(tools_list)}")
            b=2
        
        return openai_tools





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
    from ollama import chat, Client,ResponseError

    #print("DEBUG: Starting text generation with OLLAMA")

    model_name = model_cfg["model"]
    
    
    #converted_all_functions = convert_mcp_tools_ollama_structure(all_functions)    
    converted_all_functions =   convert_mcp_tools_to_openai_format(mcp_tools=all_functions) 
    
 #   print("converted all funcitons : ")
 #   print(converted_all_functions)
    
    
    #options = {
    #    "functions": list(all_functions.values()),  # Pass the tools as part of the request
    #    # Add other options if needed
    #}
    
    # Prepare options dictionary for Ollama
    options = {}
    client=""
    keep_alive_seconds="0"
    if "temperature" in model_cfg:
        options["temperature"] = model_cfg.get("temperature", 0.7)
    if "top_k" in model_cfg:
        options["top_k"] = model_cfg.get("top_k")
    if "repetition_penalty" in model_cfg:
        options["repeat_penalty"] = model_cfg.get("repetition_penalty")
    if "max_tokens" in model_cfg:
        options["num_predict"] = model_cfg.get("max_tokens", 1024)
    if  "client" in model_cfg:
        client = Client(model_cfg.get("client","http://localhost:11434"))
    if  "keep_alive_seconds" in model_cfg:
        keep_alive_seconds=model_cfg.get("keep_alive_seconds")+"s"



    try:
        if client == "":
            response = chat(
                keep_alive=keep_alive_seconds,
                model=model_name,
                messages=conversation,
                options=options,
                stream=False,
                tools=converted_all_functions
            )
        else:
            response = client.chat(
                model=model_name,
                keep_alive=keep_alive_seconds,
                messages=conversation,
                options=options,
                stream=False,
                tools=converted_all_functions
            )
        assistant_text = response.message.content or ""
        tool_calls =[]
        if response.message.tool_calls is not None:
            for tool in response.message.tool_calls:
                #print("tool") 
                #print(tool)
                #print("coisas da funcao")
                #print(tool.function.name)
                #print("arguments")
                #print(tool.function.arguments)
                
                tool_obj={
                    "id": "call_ollama",
                    "function": {
                        "name": tool.function.name or "unknown_function",
                        "arguments": tool.function.arguments or "{}"
                    }

                }
                #print(tool_obj)

                tool_calls.append(tool_obj)
        #if response.message.tool.callsfunction_call:
        #    fc = response.message.function_call
        #    tool_calls = [{
        #        "id": "call_ollama",
        #        "function": {
        #            "name": fc.name or "unknown_function",
        #            "arguments": fc.arguments or "{}"
        #        }
        #    }]

        #print("response")
        #print(response)
        return {"assistant_text": assistant_text, "tool_calls": tool_calls}
    except ResponseError as e:
        return {"assistant_text": f"Ollama error: {str(e)}", "tool_calls": []}
    except Exception as e:
        return {"assistant_text": f"Unexpected Ollama error: {str(e)}", "tool_calls": []}
