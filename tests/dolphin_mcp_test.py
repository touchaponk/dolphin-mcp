#!/usr/bin/env python
import asyncio
import json
import os
import pytest
import tempfile
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from io import StringIO

# Add path to import the script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the script
from src import dolphin_mcp

# Mock classes and functions
class MockStream:
    """Mock for AsyncOpenAI stream responses"""
    def __init__(self, responses):
        self.responses = responses
        self.index = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.index >= len(self.responses):
            raise StopAsyncIteration
        response = self.responses[self.index]
        self.index += 1
        return response

# Mock of MCPTool type
class MockMCPTool:
    def __init__(self, name, description, arguments):
        self.name = name
        self.description = description
        self.arguments = arguments

# Mock of ClientSession
class MockClientSession:
    def __init__(self, tools=None, tool_results=None):
        self.tools = tools or []
        self.tool_results = tool_results or {}
    
    async def initialize(self):
        return True
    
    async def list_tools(self):
        return self.tools
    
    async def call_tool(self, name, arguments):
        if name in self.tool_results:
            return self.tool_results[name]
        return f"Result for {name} with {json.dumps(arguments)}"
    
    async def close(self):
        return True

@pytest.fixture
def mock_config():
    return {
        "mcpServers": {
            "sqlite": {
                "command": "mcp-server-sqlite",
                "args": ["--db-path", "test.db"]
            }
        }
    }

@pytest.fixture
def mock_env_vars():
    os.environ["OPENAI_API_KEY"] = "test_api_key"
    os.environ["OPENAI_MODEL"] = "gpt-4"
    os.environ["OPENAI_ENDPOINT"] = "https://api.test.openai.com/v1"
    yield
    os.environ.pop("OPENAI_API_KEY", None)
    os.environ.pop("OPENAI_MODEL", None)
    os.environ.pop("OPENAI_ENDPOINT", None)

@pytest.mark.asyncio
async def test_convert_mcp_tool_to_openai():
    """Test conversion from MCP tool to OpenAI function format"""
    # Create a mock MCP tool
    mock_tool = MockMCPTool(
        name="query_sqlite",
        description="Run an SQL query on SQLite database",
        arguments=[
            MagicMock(
                name="query", 
                description="SQL query to run", 
                required=True,
                schema={"type": "string"}
            )
        ]
    )
    
    # Convert to OpenAI format
    result = dolphin_mcp.convert_mcp_tool_to_openai(mock_tool)
    
    # Verify conversion
    assert result["type"] == "function"
    assert result["function"]["name"] == "query_sqlite"
    assert result["function"]["description"] == "Run an SQL query on SQLite database"
    assert "query" in result["function"]["parameters"]["properties"]
    assert "query" in result["function"]["parameters"]["required"]

@pytest.mark.asyncio
async def test_connect_to_mcp_server(mocker):
    """Test MCP server connection"""
    # Mock config
    config = {
        "mcpServers": {
            "sqlite": {
                "command": "mcp-server-sqlite",
                "args": ["--db-path", "test.db"]
            }
        }
    }
    
    # Mock ClientSession
    mock_session = MockClientSession(
        tools=[
            MockMCPTool(
                name="query_sqlite",
                description="Run SQL query",
                arguments=[
                    MagicMock(name="query", description="SQL query", required=True)
                ]
            )
        ]
    )
    
    # Mock stdio_client to return streams
    mock_stdio = mocker.patch("mcp.client.stdio.stdio_client")
    mock_stdio.return_value = (AsyncMock(), AsyncMock())
    
    # Mock ClientSession instantiation
    mocker.patch("mcp.ClientSession", return_value=mock_session)
    
    # Call function
    session, tools = await dolphin_mcp.connect_to_mcp_server("sqlite", config)
    
    # Verify
    assert session == mock_session
    assert len(tools) == 1
    assert tools[0]["function"]["name"] == "query_sqlite"

@pytest.mark.asyncio
async def test_main_with_no_tool_calls(mocker, mock_env_vars, mock_config):
    """Test main function with a simple response (no tool calls)"""
    # Create temp config file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
        json.dump(mock_config, tmp)
        config_path = tmp.name
    
    try:
        # Mock arguments
        test_args = ["dolphin_mcp.py", "What is the schema of my database?", "--config", config_path]
        mocker.patch("sys.argv", test_args)
        
        # Mock connect_to_mcp_server
        mock_connect = mocker.patch("src.dolphin_mcp.connect_to_mcp_server")
        mock_connect.return_value = (
            MockClientSession(),
            [{"type": "function", "function": {"name": "query_sqlite"}}]
        )
        
        # Mock OpenAI client
        mock_openai = mocker.patch("openai.AsyncOpenAI")
        mock_client = mock_openai.return_value
        
        # Create mock response without tool calls
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].delta = MagicMock()
        mock_response.choices[0].delta.content = "This is the database schema"
        mock_response.choices[0].delta.tool_calls = None
        
        # Set up mock stream
        mock_client.chat.completions.create.return_value = MockStream([mock_response])
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        # Run main
        with patch("asyncio.run") as mock_run:
            mock_run.side_effect = lambda x: asyncio.get_event_loop().run_until_complete(x)
            dolphin_mcp.main()
        
        # Restore stdout
        sys.stdout = sys.__stdout__
        
        # Verify output
        assert "This is the database schema" in captured_output.getvalue()
        
        # Verify OpenAI was called correctly
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        assert call_args["model"] == "gpt-4"
        assert call_args["stream"] is True
        assert len(call_args["messages"]) == 1
        assert call_args["messages"][0]["content"] == "What is the schema of my database?"
    
    finally:
        # Clean up temp file
        os.unlink(config_path)

@pytest.mark.asyncio
async def test_main_with_tool_calls(mocker, mock_env_vars, mock_config):
    """Test main function with tool calls from the model"""
    # Create temp config file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as tmp:
        json.dump(mock_config, tmp)
        config_path = tmp.name
    
    try:
        # Mock arguments
        test_args = ["dolphin_mcp.py", "Show me all users in the database", "--config", config_path]
        mocker.patch("sys.argv", test_args)
        
        # Create session with tool result
        mock_session = MockClientSession(
            tool_results={"query_sqlite": "User1, User2, User3"}
        )
        
        # Mock connect_to_mcp_server
        mock_connect = mocker.patch("src.dolphin_mcp.connect_to_mcp_server")
        mock_connect.return_value = (
            mock_session,
            [{"type": "function", "function": {"name": "query_sqlite"}}]
        )
        
        # Mock OpenAI client
        mock_openai = mocker.patch("openai.AsyncOpenAI")
        mock_client = mock_openai.return_value
        
        # Create mock responses with tool calls
        # First response - model requests to call a tool
        tool_call_response = MagicMock()
        tool_call_response.choices = [MagicMock()]
        tool_call_response.choices[0].delta = MagicMock()
        tool_call_response.choices[0].delta.content = ""
        
        tool_call = MagicMock()
        tool_call.index = 0
        tool_call.id = "call_abc123"
        tool_call.function = MagicMock()
        tool_call.function.name = "query_sqlite"
        tool_call.function.arguments = '{"query": "SELECT * FROM users"}'
        
        tool_call_response.choices[0].delta.tool_calls = [tool_call]
        
        # Second response - model gives final response after tool call
        final_response = MagicMock()
        final_response.choices = [MagicMock()]
        final_response.choices[0].delta = MagicMock()
        final_response.choices[0].delta.content = "Here are the users: User1, User2, User3"
        final_response.choices[0].delta.tool_calls = None
        
        # Set up mock streams for both API calls
        mock_client.chat.completions.create.side_effect = [
            MockStream([tool_call_response]),
            MockStream([final_response])
        ]
        
        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output
        
        # Run main
        with patch("asyncio.run") as mock_run:
            mock_run.side_effect = lambda x: asyncio.get_event_loop().run_until_complete(x)
            dolphin_mcp.main()
        
        # Restore stdout
        sys.stdout = sys.__stdout__
        
        # Verify output
        output = captured_output.getvalue()
        assert "query_sqlite" in output
        assert "Here are the users: User1, User2, User3" in output
        
        # Verify OpenAI was called twice (initial request + after tool call)
        assert mock_client.chat.completions.create.call_count == 2
        
    finally:
        # Clean up temp file
        os.unlink(config_path)

if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
