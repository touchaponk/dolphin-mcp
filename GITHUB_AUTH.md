# GitHub OAuth Authentication for Dolphin MCP

This guide explains how to set up and use GitHub OAuth authentication with Dolphin MCP servers.

## Overview

The GitHub authentication provider allows MCP servers to automatically receive GitHub OAuth tokens, enabling seamless integration with GitHub's API without manually managing credentials in configuration files.

## Setup

### 1. Create a GitHub OAuth Application

1. Go to [GitHub Settings > Developer settings > OAuth Apps](https://github.com/settings/applications/new)
2. Click "New OAuth App"
3. Fill in the application details:
   - **Application name**: Your application name (e.g., "My MCP App")
   - **Homepage URL**: Your application's homepage URL
   - **Authorization callback URL**: `http://localhost:8080/callback`
4. Click "Register application"
5. Note down the **Client ID** and **Client Secret**

### 2. Configure Authentication

Add the GitHub provider configuration to your MCP server configuration:

```json
{
  "mcpServers": {
    "github-server": {
      "url": "https://api.example.com/mcp/sse",
      "transport": "sse",
      "provider": "github",
      "client_id": "your_github_client_id",
      "client_secret": "your_github_client_secret",
      "scopes": ["repo", "user:email"]
    }
  }
}
```

### 3. Initial Authentication

Run the setup tool to authenticate and store credentials:

```bash
python -m dolphin_mcp.auth.setup_github \
  --client-id your_github_client_id \
  --client-secret your_github_client_secret \
  --scopes repo user:email
```

This will:
1. Start a local callback server
2. Open your browser to GitHub's OAuth authorization page
3. Handle the callback and exchange the code for tokens
4. Store the credentials securely in `~/.dolphin/github_credentials.json`

## Configuration Options

### Required Fields

- `provider`: Must be set to `"github"`
- `client_id`: Your GitHub OAuth application's client ID
- `client_secret`: Your GitHub OAuth application's client secret

### Optional Fields

- `scopes`: Array of OAuth scopes to request (default: `["repo", "user:email"]`)
- `redirect_uri`: OAuth callback URL (default: `"http://localhost:8080/callback"`)

### Available Scopes

Common GitHub OAuth scopes include:

- `repo`: Full access to repositories
- `repo:status`: Access to commit status
- `public_repo`: Access to public repositories only
- `user`: Access to user profile information
- `user:email`: Access to user email addresses
- `read:org`: Read access to organization membership
- `write:org`: Write access to organization membership

See [GitHub's OAuth scopes documentation](https://docs.github.com/en/developers/apps/building-oauth-apps/scopes-for-oauth-apps) for a complete list.

## Example Configuration

Here's a complete example of an MCP server configuration with GitHub authentication:

```json
{
  "mcpServers": {
    "github-issues": {
      "url": "https://github-mcp-server.example.com/sse",
      "transport": "sse",
      "provider": "github",
      "client_id": "Iv1.a1b2c3d4e5f6g7h8",
      "client_secret": "1234567890abcdef1234567890abcdef12345678",
      "scopes": ["repo", "issues:write", "user:email"],
      "redirect_uri": "http://localhost:8080/callback"
    },
    "github-repos": {
      "url": "https://github-repo-server.example.com/sse", 
      "transport": "sse",
      "provider": "github",
      "client_id": "Iv1.a1b2c3d4e5f6g7h8",
      "client_secret": "1234567890abcdef1234567890abcdef12345678",
      "scopes": ["public_repo", "user:email"]
    }
  }
}
```

## How It Works

1. **Configuration**: When Dolphin MCP starts, it reads the server configurations
2. **Authentication Check**: For servers with `provider: "github"`, it looks for stored credentials
3. **Token Injection**: Valid GitHub access tokens are automatically injected into request headers as `Authorization: Bearer <token>`
4. **Automatic Headers**: Additional headers like `User-Agent: dolphin-mcp` are also added

## Token Management

- **Storage**: Credentials are stored in `~/.dolphin/github_credentials.json`
- **User-specific**: Multiple users can have separate credentials (feature for future enhancement)
- **No Refresh**: GitHub access tokens don't expire, so no refresh mechanism is needed
- **Security**: Ensure the credentials file has appropriate permissions (readable only by the user)

## Troubleshooting

### Authentication Failed

If authentication fails, check:

1. **Client ID/Secret**: Ensure they're correct and copied exactly from GitHub
2. **Callback URL**: Must match exactly what's configured in your GitHub OAuth app
3. **Network**: Ensure you can reach GitHub's OAuth endpoints
4. **Firewall**: Port 8080 must be accessible for the callback server

### Missing Permissions

If API calls fail with permission errors:

1. **Scopes**: Ensure you've requested the necessary scopes for your use case
2. **Re-authentication**: Run the setup tool again with additional scopes
3. **Repository Access**: For private repositories, ensure the OAuth app has access

### Server Connection Issues

If the MCP server can't authenticate:

1. **Credentials**: Check that `~/.dolphin/github_credentials.json` exists and is readable
2. **Token Validity**: GitHub tokens don't expire, but they can be revoked
3. **Server Config**: Ensure the server configuration includes all required fields

## Security Considerations

1. **Keep Secrets Safe**: Never commit client secrets to version control
2. **Limit Scopes**: Only request the minimum scopes needed for your application
3. **Secure Storage**: Protect the credentials file with appropriate file permissions
4. **Regular Rotation**: Consider regenerating client secrets periodically
5. **Monitor Usage**: Review OAuth application usage in GitHub settings

## Advanced Usage

### Multiple GitHub Apps

You can use different GitHub OAuth applications for different servers by providing different client IDs and secrets:

```json
{
  "mcpServers": {
    "public-server": {
      "provider": "github",
      "client_id": "public_app_client_id",
      "client_secret": "public_app_secret",
      "scopes": ["public_repo"]
    },
    "private-server": {
      "provider": "github", 
      "client_id": "private_app_client_id",
      "client_secret": "private_app_secret",
      "scopes": ["repo", "user", "admin:org"]
    }
  }
}
```

### Programmatic Setup

For automated deployments, you can set up authentication programmatically:

```python
from dolphin_mcp.auth.providers.github import GithubAuthProvider

config = {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "scopes": ["repo", "user:email"]
}

provider = GithubAuthProvider(config)
# Store pre-obtained tokens
await provider.store_credentials({
    "access_token": "your_access_token",
    "token_type": "bearer",
    "scope": "repo,user:email"
})
```