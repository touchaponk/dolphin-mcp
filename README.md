# Dolphin MCP

A flexible Python client for interacting with any Model Context Protocol (MCP) servers using OpenAI's API.

## Overview

Dolphin MCP is a command-line tool that allows you to query and interact with MCP servers through natural language. It connects to any number of configured MCP servers, makes their tools available to OpenAI's language models, and provides a conversational interface for accessing and manipulating data from these servers.

The project demonstrates how to:
- Connect to multiple MCP servers simultaneously
- List and call tools provided by these servers
- Use OpenAI's function calling capabilities to interact with external data sources
- Process and present results in a user-friendly way

## Features

- Connect to any number of MCP servers simultaneously
- Automatically discover and use tools provided by MCP servers
- Integrate with any data source or service that has an MCP server implementation
- Natural language interface powered by OpenAI's API
- Conversational, step-by-step explanation of tool usage and results

## Prerequisites

Before installing Dolphin MCP, ensure you have the following prerequisites installed:

1. **Python 3.8+**
2. **SQLite** - A lightweight database used by the demo
3. **uv/uvx** - A fast Python package installer and resolver

### Setting up Prerequisites

#### Windows

1. **Python 3.8+**:
   - Download and install from [python.org](https://www.python.org/downloads/windows/)
   - Ensure you check "Add Python to PATH" during installation

2. **SQLite**:
   - Download the precompiled binaries from [SQLite website](https://www.sqlite.org/download.html)
   - Choose the "Precompiled Binaries for Windows" section and download the sqlite-tools zip file
   - Extract the files to a folder (e.g., `C:\sqlite`)
   - Add this folder to your PATH:
     - Open Control Panel > System > Advanced System Settings > Environment Variables
     - Edit the PATH variable and add the path to your SQLite folder
     - Verify installation by opening Command Prompt and typing `sqlite3 --version`

3. **uv/uvx**:
   - Open PowerShell as Administrator and run:
     ```
     curl -sSf https://install.ultraviolet.rs/windows | powershell
     ```
   - Restart your terminal and verify installation with `uv --version`

#### macOS

1. **Python 3.8+**:
   - Install using Homebrew:
     ```
     brew install python
     ```

2. **SQLite**:
   - SQLite comes pre-installed on macOS, but you can update it using Homebrew:
     ```
     brew install sqlite
     ```
   - Verify installation with `sqlite3 --version`

3. **uv/uvx**:
   - Install using Homebrew:
     ```
     brew install ultraviolet/uv/uv
     ```
   - Or use the official installer:
     ```
     curl -sSf https://install.ultraviolet.rs/mac | bash
     ```
   - Verify installation with `uv --version`

#### Linux (Ubuntu/Debian)

1. **Python 3.8+**:
   ```
   sudo apt update
   sudo apt install python3 python3-pip
   ```

2. **SQLite**:
   ```
   sudo apt update
   sudo apt install sqlite3
   ```
   - Verify installation with `sqlite3 --version`

3. **uv/uvx**:
   ```
   curl -sSf https://install.ultraviolet.rs/linux | bash
   ```
   - Verify installation with `uv --version`

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/cognitivecomputations/dolphin-mcp.git
   cd dolphin-mcp
   ```

2. Install dependencies using uv:
   ```
   uv pip install -r requirements.txt
   ```
   
   Alternatively, you can use pip:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables by copying the example file and adding your OpenAI API key:
   ```
   cp .env.example .env
   ```
   Then edit the `.env` file to add your OpenAI API key.

4. (Optional) Set up the demo dolphin database:
   ```
   python setup_db.py
   ```
   This creates a sample SQLite database with dolphin information that you can use to test the system.

## Configuration

The project uses two main configuration files:

1. `.env` - Contains OpenAI API configuration:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_MODEL=gpt-4o
   # OPENAI_ENDPOINT=https://api.openai.com/v1  # Uncomment and modify if using a custom endpoint
   ```

2. `mcp_config.json` - Defines MCP servers to connect to:
   ```json
   {
     "mcpServers": {
       "server1": {
         "command": "command-to-start-server",
         "args": ["arg1", "arg2"],
         "env": {
           "ENV_VAR1": "value1",
           "ENV_VAR2": "value2"
         }
       },
       "server2": {
         "command": "another-server-command",
         "args": ["--option", "value"]
       }
     }
   }
   ```

   You can add as many MCP servers as you need, and the client will connect to all of them and make their tools available.

## Usage

Run the script with your query as an argument:

```
python dolphin_mcp.py "Your query here"
```

The script will:
1. Connect to all configured MCP servers
2. List available tools from each server
3. Call the OpenAI API with your query and the available tools
4. Execute any tool calls requested by the model
5. Return the results in a conversational format

## Example Queries

Examples will depend on the MCP servers you have configured. With the demo dolphin database:

```
python dolphin_mcp.py "What dolphin species are endangered?"
```

Or with your own custom MCP servers:

```
python dolphin_mcp.py "Query relevant to your configured servers"
```

## Demo Database

If you run `setup_db.py`, it will create a sample SQLite database with information about dolphin species. This is provided as a demonstration of how the system works with a simple MCP server. The database includes:

- Information about various dolphin species
- Evolutionary relationships between species
- Conservation status and physical characteristics

This is just one example of what you can do with the Dolphin MCP client. You can connect it to any MCP server that provides tools for accessing different types of data or services.

## Requirements

- Python 3.8+
- OpenAI API key
- Dependencies listed in requirements.txt:
  - openai
  - mcp[cli]
  - python-dotenv
  - pytest (for testing)
  - pytest-asyncio (for testing)
  - pytest-mock (for testing)
  - uv
  - mcp-server-sqlite (for the demo)
  - jsonschema

## How It Works

1. The script loads configuration from `mcp_config.json` and connects to each configured MCP server.
2. It retrieves the list of available tools from each server and formats them for OpenAI's function calling API.
3. The user's query is sent to OpenAI along with the available tools.
4. If the model decides to call a tool, the script routes the call to the appropriate server and returns the result.
5. This process continues until the model has all the information it needs to provide a final response.

This architecture allows for great flexibility - you can add any MCP server that provides tools for accessing different data sources or services, and the client will automatically make those tools available to the language model.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your license information here]
