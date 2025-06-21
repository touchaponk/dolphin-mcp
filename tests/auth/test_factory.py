"""
Tests for auth factory.
"""

import pytest
from dolphin_mcp.auth.factory import get_auth_provider
from dolphin_mcp.auth.providers.github import GithubAuthProvider


class TestAuthFactory:
    """Test auth provider factory."""
    
    def test_get_github_provider(self):
        """Test getting GitHub provider from factory."""
        config = {
            "provider": "github",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret"
        }
        
        provider = get_auth_provider("github", config)
        
        assert isinstance(provider, GithubAuthProvider)
        assert provider.client_id == "test_client_id"
        assert provider.client_secret == "test_client_secret"
    
    def test_unsupported_provider(self):
        """Test error handling for unsupported providers."""
        config = {
            "provider": "unsupported",
            "client_id": "test", 
            "client_secret": "test"
        }
        
        with pytest.raises(ValueError) as exc_info:
            get_auth_provider("unsupported", config)
        
        assert "Unknown provider type: unsupported" in str(exc_info.value)