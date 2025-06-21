#!/usr/bin/env python3
"""
GitHub OAuth setup tool for Dolphin MCP.
"""

import asyncio
import argparse
import json
import logging
import sys
from typing import Dict, Any

from dolphin_mcp.auth.providers.github import GithubAuthProvider
from dolphin_mcp.auth.oauth_server import run_oauth_flow

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_github_auth(client_id: str, client_secret: str, scopes: list = None) -> None:
    """Setup GitHub authentication."""
    
    if scopes is None:
        scopes = ["repo", "user:email"]
    
    config = {
        "client_id": client_id,
        "client_secret": client_secret,
        "scopes": scopes,
        "redirect_uri": "http://localhost:8080/callback"
    }
    
    provider = GithubAuthProvider(config)
    
    try:
        tokens = await run_oauth_flow(provider)
        print(f"\nGitHub authentication setup complete!")
        print(f"Access token: {tokens['access_token'][:10]}...")
        print(f"Token type: {tokens.get('token_type', 'bearer')}")
        print(f"Scope: {tokens.get('scope', 'N/A')}")
        
    except Exception as e:
        print(f"Authentication failed: {e}")
        sys.exit(1)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Setup GitHub OAuth for Dolphin MCP")
    parser.add_argument("--client-id", required=True, help="GitHub OAuth client ID")
    parser.add_argument("--client-secret", required=True, help="GitHub OAuth client secret")
    parser.add_argument("--scopes", nargs="*", default=["repo", "user:email"], 
                       help="OAuth scopes (default: repo user:email)")
    
    args = parser.parse_args()
    
    print("Setting up GitHub OAuth authentication for Dolphin MCP...")
    print(f"Client ID: {args.client_id}")
    print(f"Scopes: {' '.join(args.scopes)}")
    
    asyncio.run(setup_github_auth(args.client_id, args.client_secret, args.scopes))


if __name__ == "__main__":
    main()