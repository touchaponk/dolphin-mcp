"""
Base authentication provider interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


class AuthProvider(ABC):
    """Base class for authentication providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the auth provider with configuration."""
        self.config = config
        self.client_id = config.get("client_id")
        self.client_secret = config.get("client_secret")
        self.redirect_uri = config.get("redirect_uri", "http://localhost:8080/callback")
        self.scopes = config.get("scopes", [])
    
    @abstractmethod
    async def get_authorize_url(self, state: Optional[str] = None) -> str:
        """Generate OAuth authorization URL."""
        pass
    
    @abstractmethod
    async def handle_callback(self, code: str, state: Optional[str] = None) -> Dict[str, Any]:
        """Handle OAuth callback and exchange code for tokens."""
        pass
    
    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token."""
        pass
    
    @abstractmethod
    async def get_stored_credentials(self, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve stored credentials for a user."""
        pass
    
    @abstractmethod
    async def store_credentials(self, credentials: Dict[str, Any], user_id: Optional[str] = None) -> None:
        """Store credentials for a user."""
        pass
    
    @abstractmethod
    async def inject_auth_headers(self, headers: Dict[str, str], user_id: Optional[str] = None) -> Dict[str, str]:
        """Inject authentication headers with valid tokens."""
        pass