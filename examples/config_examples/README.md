# MCP Server Configuration Examples

This directory contains example configurations for various MCP server combinations. Each configuration demonstrates how to set up and use multiple MCP servers together to accomplish specific tasks.

## Configuration Files

Each configuration file is a JSON file that defines the MCP servers to be used. The configuration files follow this structure:

```json
{
  "mcpServers": {
    "server1": {
      "command": "command-to-run-server1",
      "args": ["arg1", "arg2"],
      "env": {
        "ENV_VAR1": "value1",
        "ENV_VAR2": "value2"
      }
    },
    "server2": {
      "command": "command-to-run-server2",
      "args": ["arg1", "arg2"],
      "env": {
        "ENV_VAR1": "value1",
        "ENV_VAR2": "value2"
      }
    }
  }
}
```

## Query Scripts

Each configuration file has a corresponding query script that demonstrates how to use the MCP servers defined in the configuration. The query scripts accept a `--config` parameter that allows you to specify a different configuration file.

```bash
python query_script.py [args] --config path/to/config.json
```

## Available Configurations

### Weather and News

- **Configuration File**: `weather_news_config.json`
- **Query Script**: `weather_news_query.py`
- **Description**: Demonstrates how to use weather and news MCP servers together to get weather information and news for a specific location.
- **Example Usage**:
  ```bash
  python weather_news_query.py "San Francisco" --config weather_news_config.json
  ```

### GitHub and Filesystem

- **Configuration File**: `github_filesystem_config.json`
- **Query Script**: `github_filesystem_query.py`
- **Description**: Demonstrates how to use GitHub and filesystem MCP servers together to clone a repository and list files.
- **Example Usage**:
  ```bash
  python github_filesystem_query.py "octocat/Hello-World" --local-dir "./repo" --config github_filesystem_config.json
  ```

### Database

- **Configuration File**: `database_config.json`
- **Query Script**: `database_query.py`
- **Description**: Demonstrates how to use multiple database MCP servers (SQLite, PostgreSQL, MySQL) together.
- **Example Usage**:
  ```bash
  python database_query.py --table "users" --limit 5 --config database_config.json
  ```

### Communication

- **Configuration File**: `communication_config.json`
- **Query Script**: `communication_query.py`
- **Description**: Demonstrates how to use email, calendar, and Slack MCP servers together to send emails, schedule meetings, and send Slack messages.
- **Example Usage**:
  ```bash
  python communication_query.py --meeting-topic "Project Update" --attendees "alice@example.com,bob@example.com" --channel "general" --config communication_config.json
  ```

### Browser and Search

- **Configuration File**: `browser_search_config.json`
- **Query Script**: `browser_search_query.py`
- **Description**: Demonstrates how to use browser and search MCP servers together to search the web and browse URLs.
- **Example Usage**:
  ```bash
  python browser_search_query.py "artificial intelligence" --results 3 --config browser_search_config.json
  ```

### Location

- **Configuration File**: `location_config.json`
- **Query Script**: `location_query.py`
- **Description**: Demonstrates how to use maps, timeserver, and weather MCP servers together to get directions, local time, and weather for locations.
- **Example Usage**:
  ```bash
  python location_query.py --origin "New York, NY" --destination "San Francisco, CA" --stops "Chicago, IL;Denver, CO" --config location_config.json
  ```

### Finance

- **Configuration File**: `finance_config.json`
- **Query Script**: `finance_query.py`
- **Description**: Demonstrates how to use cryptocurrency and stock market MCP servers together to get financial data.
- **Example Usage**:
  ```bash
  python finance_query.py --crypto "BTC,ETH,SOL" --stocks "AAPL,MSFT,GOOGL" --config finance_config.json
  ```

### Knowledge

- **Configuration File**: `knowledge_config.json`
- **Query Script**: `knowledge_query.py`
- **Description**: Demonstrates how to use the memory MCP server to store and retrieve facts.
- **Example Usage**:
  ```bash
  python knowledge_query.py --store "San Francisco is a city in California." --query "San Francisco" --limit 5 --config knowledge_config.json
  ```

### Monitoring

- **Configuration File**: `monitoring_config.json`
- **Query Script**: `monitoring_query.py`
- **Description**: Demonstrates how to use the Sentry MCP server to get issues and performance metrics.
- **Example Usage**:
  ```bash
  python monitoring_query.py --project "example-project" --status "unresolved" --limit 5 --config monitoring_config.json
  ```

### Developer

- **Configuration File**: `developer_config.json`
- **Query Script**: `developer_query.py`
- **Description**: Demonstrates how to use Docker and IDE MCP servers together to list containers and get project structure.
- **Example Usage**:
  ```bash
  python developer_query.py --project-path "./example-project" --running-only --config developer_config.json
  ```

## Running Tests

You can run tests for all configurations using the `run_tests.py` script in the `tests` directory:

```bash
cd examples/config_examples
python tests/run_tests.py
```

You can also run tests for specific configurations:

```bash
cd examples/config_examples
python tests/run_tests.py --type configs  # Run configuration tests
python tests/run_tests.py --type queries  # Run query tests
python tests/run_tests.py --type functional  # Run functional tests
