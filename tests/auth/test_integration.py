"""
Integration tests for auth provider with MCP client.
"""

import pytest
import json
import tempfile
from unittest.mock import patch, AsyncMock, MagicMock
from dolphin_mcp.auth.providers.github import GithubAuthProvider
from dolphin_mcp.auth.factory import get_auth_provider


class TestClientIntegration:
    """Test integration between auth providers and MCP client."""
    
    @pytest.mark.asyncio
    async def test_github_provider_integration(self, tmp_path):
        """Test GitHub provider integration with client."""
        # Setup test configuration
        config = {
            "provider": "github",
            "client_id": "test_client_id",
            "client_secret": "test_client_secret",
            "scopes": ["repo", "user:email"]
        }
        
        # Create provider
        provider = get_auth_provider("github", config)
        provider.storage_path = str(tmp_path / "github_credentials.json")
        
        # Store test credentials
        credentials = {
            "access_token": "test_access_token",
            "token_type": "bearer",
            "scope": "repo,user:email"
        }
        await provider.store_credentials(credentials)
        
        # Test header injection
        original_headers = {"Content-Type": "application/json"}
        auth_headers = await provider.inject_auth_headers(original_headers)
        
        assert auth_headers["Authorization"] == "Bearer test_access_token"
        assert auth_headers["User-Agent"] == "dolphin-mcp"
        assert auth_headers["Content-Type"] == "application/json"
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        valid_config = {
            "provider": "github",
            "client_id": "test_id",
            "client_secret": "test_secret"
        }
        provider = get_auth_provider("github", valid_config)
        assert isinstance(provider, GithubAuthProvider)
        
        # Invalid config - missing required fields
        with pytest.raises(ValueError) as exc_info:
            invalid_config = {
                "provider": "github",
                "client_id": "test_id"
                # missing client_secret
            }
            get_auth_provider("github", invalid_config)
        
        assert "Invalid GitHub provider configuration" in str(exc_info.value)
    
    def test_unsupported_provider_validation(self):
        """Test validation of unsupported providers."""
        config = {
            "provider": "unsupported",
            "client_id": "test",
            "client_secret": "test"
        }
        
        with pytest.raises(ValueError) as exc_info:
            get_auth_provider("unsupported", config)
        
        assert "Unknown provider type: unsupported" in str(exc_info.value)