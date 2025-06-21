# GitHub Authentication Setup Example

This example shows how to set up GitHub OAuth authentication for your MCP servers.

## Quick Start

1. **Create a GitHub OAuth App**:
   - Go to https://github.com/settings/applications/new
   - Set callback URL to: `http://localhost:8080/callback`
   - Copy your Client ID and Client Secret

2. **Run the setup tool**:
   ```bash
   python -m dolphin_mcp.auth.setup_github \
     --client-id "Iv1.your_client_id_here" \
     --client-secret "your_client_secret_here" \
     --scopes repo user:email
   ```

3. **Configure your MCP server**:
   ```json
   {
     "mcpServers": {
       "my-github-server": {
         "url": "https://api.myserver.com/mcp/sse",
         "transport": "sse",
         "provider": "github",
         "client_id": "Iv1.your_client_id_here",
         "client_secret": "your_client_secret_here",
         "scopes": ["repo", "user:email"]
       }
     }
   }
   ```

4. **Start Dolphin MCP**:
   The client will automatically inject GitHub tokens into your server requests!

## What Happens During Setup

1. A local callback server starts on `localhost:8080`
2. Your browser opens to GitHub's OAuth authorization page
3. You authorize the application
4. GitHub redirects back with an authorization code
5. The tool exchanges the code for an access token
6. Credentials are securely stored in `~/.dolphin/github_credentials.json`

## Authentication Headers

When your MCP server receives requests, they will automatically include:

```
Authorization: Bearer ghp_your_actual_access_token_here
User-Agent: dolphin-mcp
```

## Security Notes

- Never commit your `client_secret` to version control
- The credentials file should only be readable by your user
- GitHub access tokens don't expire but can be revoked
- Use minimal scopes required for your application