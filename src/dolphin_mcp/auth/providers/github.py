"""
GitHub OAuth authentication provider.
"""

import os
import json
import logging
from typing import Dict, Optional, Any
from urllib.parse import urlencode
import aiohttp
import aiofiles

from ..base import AuthProvider

logger = logging.getLogger(__name__)


class GithubAuthProvider(AuthProvider):
    """GitHub OAuth 2.0 authentication provider."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize GitHub auth provider."""
        super().__init__(config)
        
        # GitHub OAuth endpoints
        self.authorize_url = "https://github.com/login/oauth/authorize"
        self.token_url = "https://github.com/login/oauth/access_token"
        
        # Default scopes if none provided
        if not self.scopes:
            self.scopes = ["repo", "user:email"]
        
        # Credentials storage path
        self.storage_path = os.path.expanduser("~/.dolphin/github_credentials.json")
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
    
    async def get_authorize_url(self, state: Optional[str] = None) -> str:
        """Generate GitHub OAuth authorization URL."""
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "response_type": "code"
        }
        
        if state:
            params["state"] = state
        
        url = f"{self.authorize_url}?{urlencode(params)}"
        logger.debug(f"Generated GitHub authorize URL: {url}")
        return url
    
    async def handle_callback(self, code: str, state: Optional[str] = None) -> Dict[str, Any]:
        """Handle OAuth callback and exchange code for tokens."""
        logger.debug("Handling GitHub OAuth callback")
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": self.redirect_uri
        }
        
        headers = {
            "Accept": "application/json",
            "User-Agent": "dolphin-mcp"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.token_url, data=data, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"GitHub token exchange failed: {response.status} {error_text}")
                
                token_data = await response.json()
                
                if "error" in token_data:
                    raise Exception(f"GitHub OAuth error: {token_data['error_description']}")
                
                logger.debug("Successfully exchanged code for tokens")
                return token_data
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        # GitHub doesn't support refresh tokens in the traditional OAuth2 sense
        # Access tokens don't expire, so we just return the existing credentials
        logger.debug("GitHub tokens don't need refreshing (they don't expire)")
        credentials = await self.get_stored_credentials()
        if credentials:
            return credentials
        else:
            raise Exception("No stored credentials found to refresh")
    
    async def get_stored_credentials(self, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve stored credentials for a user."""
        try:
            if os.path.exists(self.storage_path):
                async with aiofiles.open(self.storage_path, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
                    
                    # If user_id is specified, get user-specific credentials
                    if user_id:
                        return data.get("users", {}).get(user_id)
                    else:
                        # Return default user credentials
                        return data.get("default")
            return None
        except Exception as e:
            logger.error(f"Error reading stored credentials: {e}")
            return None
    
    async def store_credentials(self, credentials: Dict[str, Any], user_id: Optional[str] = None) -> None:
        """Store credentials for a user."""
        try:
            # Load existing data or create new structure
            data = {}
            if os.path.exists(self.storage_path):
                async with aiofiles.open(self.storage_path, 'r') as f:
                    content = await f.read()
                    data = json.loads(content)
            
            # Ensure structure exists
            if "users" not in data:
                data["users"] = {}
            
            # Store credentials
            if user_id:
                data["users"][user_id] = credentials
            else:
                data["default"] = credentials
            
            # Write back to file
            async with aiofiles.open(self.storage_path, 'w') as f:
                await f.write(json.dumps(data, indent=2))
            
            logger.debug(f"Stored GitHub credentials for user: {user_id or 'default'}")
            
        except Exception as e:
            logger.error(f"Error storing credentials: {e}")
            raise
    
    async def inject_auth_headers(self, headers: Dict[str, str], user_id: Optional[str] = None) -> Dict[str, str]:
        """Inject authentication headers with valid tokens."""
        credentials = await self.get_stored_credentials(user_id)
        
        if not credentials or "access_token" not in credentials:
            logger.warning(f"No valid GitHub credentials found for user: {user_id or 'default'}")
            return headers
        
        # Create new headers dict to avoid modifying original
        auth_headers = headers.copy()
        auth_headers["Authorization"] = f"Bearer {credentials['access_token']}"
        auth_headers["User-Agent"] = "dolphin-mcp"
        
        logger.debug("Injected GitHub auth headers")
        return auth_headers