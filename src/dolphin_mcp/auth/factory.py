"""
Authentication provider factory.
"""

from typing import Dict, Any
from .base import AuthProvider
from .providers.github import GithubAuthProvider
from .validation import validate_provider_config


def get_auth_provider(provider_type: str, config: Dict[str, Any]) -> AuthProvider:
    """Factory function to create auth provider instances."""
    
    # Validate configuration first
    validate_provider_config(provider_type, config)
    
    provider_map = {
        "github": GithubAuthProvider,
    }
    
    if provider_type not in provider_map:
        raise ValueError(f"Unsupported auth provider: {provider_type}. Supported: {list(provider_map.keys())}")
    
    provider_class = provider_map[provider_type]
    return provider_class(config)