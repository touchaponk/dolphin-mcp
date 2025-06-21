"""
Configuration validation for auth providers.
"""

import jsonschema
from typing import Dict, Any


# GitHub provider configuration schema
GITHUB_PROVIDER_SCHEMA = {
    "type": "object",
    "properties": {
        "provider": {
            "type": "string",
            "enum": ["github"]
        },
        "client_id": {
            "type": "string",
            "description": "GitHub OAuth application client ID"
        },
        "client_secret": {
            "type": "string",
            "description": "GitHub OAuth application client secret"
        },
        "scopes": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "default": ["repo", "user:email"],
            "description": "OAuth scopes to request"
        },
        "redirect_uri": {
            "type": "string",
            "default": "http://localhost:8080/callback",
            "description": "OAuth redirect URI"
        }
    },
    "required": ["provider", "client_id", "client_secret"],
    "additionalProperties": True
}


def validate_github_config(config: Dict[str, Any]) -> None:
    """Validate GitHub provider configuration."""
    try:
        jsonschema.validate(config, GITHUB_PROVIDER_SCHEMA)
    except jsonschema.ValidationError as e:
        raise ValueError(f"Invalid GitHub provider configuration: {e.message}")


def validate_provider_config(provider_type: str, config: Dict[str, Any]) -> None:
    """Validate provider configuration based on type."""
    validators = {
        "github": validate_github_config
    }
    
    if provider_type not in validators:
        raise ValueError(f"Unknown provider type: {provider_type}")
    
    validators[provider_type](config)