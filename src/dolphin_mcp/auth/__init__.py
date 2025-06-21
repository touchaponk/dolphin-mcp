"""
Authentication module for Dolphin MCP.
Provides OAuth providers for MCP server authentication.
"""

from .factory import get_auth_provider
from .base import AuthProvider

__all__ = ["AuthProvider", "get_auth_provider"]