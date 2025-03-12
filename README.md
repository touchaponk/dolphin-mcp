# Dolphin-MCP

![License](https://img.shields.io/github/license/cognitivecomputations/dolphin-mcp)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)

Dolphin-MCP is a Python utility that connects OpenAI's language models with Model Context Protocol (MCP) servers. It enables seamless integration between AI models and MCP-compatible context providers, allowing your applications to leverage both technologies with minimal effort.

## Features

- 🔄 Bi-directional integration between OpenAI API and MCP servers
- 🧰 Exposes MCP tools as functions to OpenAI models
- 📊 Real-time streaming of model responses
- 🔌 Support for multiple MCP servers
- 🛠️ Handles tool execution and context management automatically

## Installation

```bash
# Clone this repository
git clone https://github.com/cognitivecomputations/dolphin-mcp.git
cd dolphin-mcp

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

1. Create a `.env` file with your OpenAI credentials:

```bash
cp .env.example .env
# Edit .env with your API key
```

2. Set up your MCP configuration in `mcp_config.json`:

```json
{
  "mcpServers": {
    "dolphin-db": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "~/.dolphin/dolphin.db"]
    }
  }
}
```

3. Set up the dolphin database:

```bash
python examples/setup_dolphin_db.py
```

Test the database

```bash
sqlite3 ~/.dolphin/dolphin.db "SELECT common_name FROM dolphin_species WHERE conservation_status LIKE '%End
angered%'"
```

4. Run a query:

```bash
python src/dolphin_mcp.py "What tables are in my database?"
```

You can also use the example script which sets everything up for you:

```bash
python examples/dolphin_query.py "List all endangered dolphin species"
```

## How It Works

1. **Configuration Loading**: Dolphin-MCP loads your MCP server configurations from a JSON file.
2. **Server Connection**: It connects to all defined MCP servers using the MCP client interface and collects their available tools.
3. **Model Integration**: Your prompt is sent to the OpenAI API along with all available MCP tools.
4. **Function Execution**: When the AI model calls a function, Dolphin-MCP:
   - Locates the appropriate MCP server session
   - Executes the tool call with provided arguments
   - Returns the result to the model
5. **Response Streaming**: All responses are streamed to your console in real-time.
6. **Session Cleanup**: All MCP server sessions are properly closed when the program exits.

## Usage Examples

### Basic Query

```bash
python src/dolphin_mcp.py "What tables are in my database?"
```

### Dolphin Database Queries

The project includes a sample dolphin species database with detailed information about 20 different dolphin species and their evolutionary relationships:

```bash
# List all dolphin species
python examples/dolphin_query.py "List all dolphin species in the database"

# Find endangered species
python examples/dolphin_query.py "Which dolphin species are endangered and what's their population status?"

# Analyze evolutionary relationships
python examples/dolphin_query.py "Explain the evolutionary relationship between Orcas and Bottlenose dolphins"

# Compare different habitats
python examples/dolphin_query.py "Compare river dolphins to oceanic dolphins in terms of size and habitat"
```

### Custom Configuration

```bash
python src/dolphin_mcp.py "Describe the schema of my database" --config custom_config.json
```

## Configuration Options

### MCP Server Configuration

The `mcp_config.json` file defines available MCP servers:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "executable",
      "args": ["--flag", "value"],
      "env": {
        "ENV_VAR": "value"
      }
    }
  }
}
```

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_MODEL`: Model to use (default: varies by configuration)
- `OPENAI_ENDPOINT`: Custom API endpoint (optional)

## Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/dolphin_mcp_test.py -v
```

### Dolphin Database

The project includes a SQLite database with information about dolphin species that's used for demonstration purposes:

- **Location**: `~/.dolphin/dolphin.db`
- **Tables**:
  - `dolphin_species`: Contains information about 20 dolphin species including names, habitats, physical characteristics, lifespan, conservation status, and evolutionary ancestry.
  - `evolutionary_relationships`: Maps the relationships between different dolphin species including relationship type and estimated time of divergence.

### Project Structure

```
dolphin-mcp/
├── src/                # Main source code
│   └── dolphin_mcp.py  # Main integration script
├── tests/              # Test suite
├── examples/           # Usage examples
│   ├── dolphin_query.py       # Example query script
│   ├── setup_dolphin_db.py    # Database setup script
│   ├── simple_query.py        # Simple example
│   ├── dolphin_db_config.json # Sample config for dolphin DB
│   └── config_examples/       # Advanced configuration examples
│       ├── weather_news_config.json     # Weather and news configuration
│       ├── github_filesystem_config.json # GitHub and filesystem configuration
│       ├── database_config.json         # Database configuration
│       └── ... (more configuration examples)
├── .env.example        # Template for environment variables
├── requirements.txt    # Dependencies
└── README.md           # Project documentation
```

### Configuration Examples

The `examples/config_examples/` directory contains a comprehensive set of example configurations for various MCP server combinations. Each configuration demonstrates how to set up and use multiple MCP servers together to accomplish specific tasks:

- **Weather and News**: Get weather information and news for specific locations
- **GitHub and Filesystem**: Clone repositories and interact with the filesystem
- **Database**: Work with multiple database types (SQLite, PostgreSQL, MySQL)
- **Communication**: Send emails, schedule meetings, and send Slack messages
- **Browser and Search**: Search the web and browse URLs
- **Location**: Get directions, local time, and weather for locations
- **Finance**: Retrieve cryptocurrency and stock market data
- **Knowledge**: Store and retrieve facts using a memory server
- **Monitoring**: Get issues and performance metrics from Sentry
- **Developer**: Work with Docker containers and IDE project structures

Each configuration has a corresponding query script that demonstrates how to use the MCP servers. For more details, see the README in the `examples/config_examples/` directory.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Dependencies

Dolphin-MCP relies on the following key dependencies:

- **openai**: Client library for the OpenAI API
- **mcp[cli]**: Model Context Protocol client library with CLI support
- **mcp-server-sqlite**: SQLite MCP server implementation
- **python-dotenv**: For loading environment variables from .env files
- **uv**: Fast Python package installer and resolver
- **jsonschema**: JSON Schema validation library

Testing dependencies include pytest, pytest-asyncio, and pytest-mock.

## Troubleshooting

### Common Issues

1. **API Key Issues**
   - **Symptom**: "Authentication error" or "Invalid API key"
   - **Solution**: Ensure your OpenAI API key is correctly set in the .env file or as an environment variable

2. **MCP Server Connection Failures**
   - **Symptom**: "Failed to connect to MCP server" or "Server not responding"
   - **Solution**: Verify the server command and arguments in your configuration file. Ensure the required executables are installed and in your PATH.

3. **Database Path Issues**
   - **Symptom**: "Database not found" or "Unable to open database"
   - **Solution**: The SQLite database path (~/.dolphin/dolphin.db) is relative to your home directory. Ensure this directory exists and is writable.

4. **Tool Execution Errors**
   - **Symptom**: "Tool execution failed" or "Invalid arguments"
   - **Solution**: Check the arguments being passed to the MCP tool. Ensure they match the expected schema.

5. **Streaming Response Issues**
   - **Symptom**: No output or incomplete responses
   - **Solution**: Ensure you're using a compatible OpenAI model that supports function calling and streaming.

## Getting Help

If you encounter issues not covered in the troubleshooting section:

1. **GitHub Issues**: Check existing issues or create a new one on the [GitHub repository](https://github.com/cognitivecomputations/dolphin-mcp/issues)
2. **Discussions**: Join the discussion on the [GitHub Discussions](https://github.com/cognitivecomputations/dolphin-mcp/discussions) page
3. **MCP Documentation**: Refer to the [Model Context Protocol documentation](https://modelcontextprotocol.io) for protocol-specific questions

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Model Context Protocol (MCP)](https://modelcontextprotocol.io) for providing the protocol specification
- [OpenAI](https://openai.com) for their robust API and function calling capabilities
