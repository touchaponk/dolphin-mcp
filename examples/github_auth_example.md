# Example: Using GitHub Auth Provider with Dolphin MCP

This example demonstrates how to configure and use the GitHub authentication provider with Dolphin MCP.

## Example Configuration

Here's a sample MCP server configuration that uses GitHub authentication:

```json
{
  "mcpServers": {
    "github-api-server": {
      "url": "https://api.example-github-server.com/mcp/sse",
      "transport": "sse",
      "provider": "github",
      "client_id": "Iv1.a1b2c3d4e5f6g7h8",
      "client_secret": "1234567890abcdef1234567890abcdef12345678",
      "scopes": ["repo", "user:email", "issues:write"]
    },
    "github-public-server": {
      "url": "https://public-github-server.com/mcp/sse",
      "transport": "sse", 
      "provider": "github",
      "client_id": "Iv1.x9y8z7w6v5u4t3s2",
      "client_secret": "fedcba0987654321fedcba0987654321fedcba09",
      "scopes": ["public_repo", "user:email"]
    }
  }
}
```

## Setup Steps

1. **Create GitHub OAuth Apps**: Create OAuth applications in GitHub for each server configuration
2. **Initial Authentication**: Run the setup tool to authenticate and store credentials
3. **Use in Dolphin MCP**: Configure your MCP servers and let Dolphin MCP handle token injection

## Authentication Flow

When Dolphin MCP starts:

1. Reads server configurations from `mcp_config.json`
2. For servers with `provider: "github"`, initializes the GitHub auth provider
3. Loads stored credentials from `~/.dolphin/github_credentials.json`
4. Injects `Authorization: Bearer <token>` headers automatically
5. Connects to MCP servers with authenticated requests

## Benefits

- **Automatic Token Management**: No need to manually manage tokens in config files
- **Secure Storage**: Credentials stored securely in user's home directory
- **Dynamic Injection**: Tokens injected at runtime, not stored in config
- **Multiple Apps**: Support for different GitHub OAuth apps per server
- **Scope Management**: Fine-grained control over OAuth scopes per server