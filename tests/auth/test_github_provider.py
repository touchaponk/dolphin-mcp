"""
Tests for GitHub authentication provider.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, AsyncMock
from dolphin_mcp.auth.providers.github import GithubAuthProvider


@pytest.fixture
def github_config():
    """Test configuration for GitHub provider."""
    return {
        "client_id": "test_client_id",
        "client_secret": "test_client_secret",
        "scopes": ["repo", "user:email"],
        "redirect_uri": "http://localhost:8080/callback"
    }


@pytest.fixture
def github_provider(github_config, tmp_path):
    """Create GitHub provider with temporary storage."""
    provider = GithubAuthProvider(github_config)
    provider.storage_path = str(tmp_path / "github_credentials.json")
    return provider


class TestGithubAuthProvider:
    """Test GitHub authentication provider."""
    
    def test_initialization(self, github_config):
        """Test provider initialization."""
        provider = GithubAuthProvider(github_config)
        
        assert provider.client_id == "test_client_id"
        assert provider.client_secret == "test_client_secret"
        assert provider.scopes == ["repo", "user:email"]
        assert provider.redirect_uri == "http://localhost:8080/callback"
        assert provider.authorize_url == "https://github.com/login/oauth/authorize"
        assert provider.token_url == "https://github.com/login/oauth/access_token"
    
    def test_initialization_default_scopes(self):
        """Test provider initialization with default scopes."""
        config = {
            "client_id": "test_client_id",
            "client_secret": "test_client_secret"
        }
        provider = GithubAuthProvider(config)
        
        assert provider.scopes == ["repo", "user:email"]
    
    @pytest.mark.asyncio
    async def test_get_authorize_url(self, github_provider):
        """Test authorization URL generation."""
        url = await github_provider.get_authorize_url()
        
        assert "https://github.com/login/oauth/authorize" in url
        assert "client_id=test_client_id" in url
        assert "redirect_uri=http%3A%2F%2Flocalhost%3A8080%2Fcallback" in url
        assert "scope=repo+user%3Aemail" in url
        assert "response_type=code" in url
    
    @pytest.mark.asyncio
    async def test_get_authorize_url_with_state(self, github_provider):
        """Test authorization URL generation with state."""
        url = await github_provider.get_authorize_url(state="test_state")
        
        assert "state=test_state" in url
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_handle_callback_success(self, mock_post, github_provider):
        """Test successful OAuth callback handling."""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "token_type": "bearer",
            "scope": "repo,user:email"
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        result = await github_provider.handle_callback("test_code")
        
        assert result["access_token"] == "test_access_token"
        assert result["token_type"] == "bearer"
        assert result["scope"] == "repo,user:email"
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_handle_callback_error(self, mock_post, github_provider):
        """Test OAuth callback error handling."""
        # Mock error response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "error": "invalid_grant",
            "error_description": "The provided authorization grant is invalid"
        }
        mock_post.return_value.__aenter__.return_value = mock_response
        
        with pytest.raises(Exception) as exc_info:
            await github_provider.handle_callback("invalid_code")
        
        assert "GitHub OAuth error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_credentials(self, github_provider):
        """Test credential storage and retrieval."""
        credentials = {
            "access_token": "test_access_token",
            "token_type": "bearer",
            "scope": "repo,user:email"
        }
        
        # Store credentials
        await github_provider.store_credentials(credentials)
        
        # Retrieve credentials
        stored_creds = await github_provider.get_stored_credentials()
        
        assert stored_creds["access_token"] == "test_access_token"
        assert stored_creds["token_type"] == "bearer"
        assert stored_creds["scope"] == "repo,user:email"
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_user_credentials(self, github_provider):
        """Test user-specific credential storage and retrieval."""
        credentials = {
            "access_token": "user_access_token",
            "token_type": "bearer",
            "scope": "repo,user:email"
        }
        
        # Store credentials for specific user
        await github_provider.store_credentials(credentials, user_id="test_user")
        
        # Retrieve credentials for specific user
        stored_creds = await github_provider.get_stored_credentials(user_id="test_user")
        
        assert stored_creds["access_token"] == "user_access_token"
        
        # Ensure default credentials are empty
        default_creds = await github_provider.get_stored_credentials()
        assert default_creds is None
    
    @pytest.mark.asyncio
    async def test_inject_auth_headers(self, github_provider):
        """Test authentication header injection."""
        # Store credentials first
        credentials = {
            "access_token": "test_access_token",
            "token_type": "bearer"
        }
        await github_provider.store_credentials(credentials)
        
        # Test header injection
        original_headers = {"Content-Type": "application/json"}
        auth_headers = await github_provider.inject_auth_headers(original_headers)
        
        assert auth_headers["Content-Type"] == "application/json"
        assert auth_headers["Authorization"] == "Bearer test_access_token"
        assert auth_headers["User-Agent"] == "dolphin-mcp"
        
        # Ensure original headers weren't modified
        assert "Authorization" not in original_headers
    
    @pytest.mark.asyncio
    async def test_inject_auth_headers_no_credentials(self, github_provider):
        """Test header injection with no stored credentials."""
        original_headers = {"Content-Type": "application/json"}
        auth_headers = await github_provider.inject_auth_headers(original_headers)
        
        # Should return original headers unchanged
        assert auth_headers == original_headers
        assert "Authorization" not in auth_headers
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, github_provider):
        """Test token refresh (GitHub doesn't actually support refresh tokens)."""
        # Store credentials first
        credentials = {
            "access_token": "test_access_token",
            "token_type": "bearer"
        }
        await github_provider.store_credentials(credentials)
        
        # Test refresh (should return existing credentials)
        refreshed = await github_provider.refresh_token("dummy_refresh_token")
        
        assert refreshed["access_token"] == "test_access_token"