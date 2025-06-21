"""
OAuth callback server utilities.
"""

import asyncio
import logging
from typing import Dict, Optional, Callable
from urllib.parse import parse_qs, urlparse
from aiohttp import web, ClientSession
import aiohttp

logger = logging.getLogger(__name__)


class OAuthCallbackServer:
    """Simple HTTP server to handle OAuth callbacks."""
    
    def __init__(self, host: str = "localhost", port: int = 8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.callback_future = None
        
        # Setup routes
        self.app.router.add_get("/callback", self.handle_callback)
        self.app.router.add_get("/", self.handle_root)
    
    async def handle_root(self, request):
        """Handle root path."""
        return web.Response(text="OAuth Callback Server - Waiting for authentication...")
    
    async def handle_callback(self, request):
        """Handle OAuth callback."""
        query_params = dict(request.query)
        
        if "error" in query_params:
            error = query_params.get("error", "unknown_error")
            error_description = query_params.get("error_description", "No description provided")
            
            logger.error(f"OAuth error: {error} - {error_description}")
            
            if self.callback_future and not self.callback_future.done():
                self.callback_future.set_exception(Exception(f"OAuth error: {error} - {error_description}"))
            
            return web.Response(text=f"Authentication failed: {error_description}", status=400)
        
        if "code" in query_params:
            code = query_params["code"]
            state = query_params.get("state")
            
            logger.debug(f"Received OAuth callback with code: {code[:10]}...")
            
            if self.callback_future and not self.callback_future.done():
                self.callback_future.set_result({"code": code, "state": state})
            
            return web.Response(text="Authentication successful! You can close this window.")
        
        return web.Response(text="Invalid callback - missing code parameter", status=400)
    
    async def start(self):
        """Start the callback server."""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        
        logger.info(f"OAuth callback server started at http://{self.host}:{self.port}")
    
    async def stop(self):
        """Stop the callback server."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        
        logger.info("OAuth callback server stopped")
    
    async def wait_for_callback(self, timeout: int = 300) -> Dict[str, str]:
        """Wait for OAuth callback."""
        self.callback_future = asyncio.Future()
        
        try:
            result = await asyncio.wait_for(self.callback_future, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            raise Exception(f"OAuth callback timeout after {timeout} seconds")
        finally:
            self.callback_future = None


async def run_oauth_flow(auth_provider, state: Optional[str] = None, timeout: int = 300) -> Dict[str, str]:
    """Run complete OAuth flow with callback server."""
    server = OAuthCallbackServer()
    
    try:
        # Start callback server
        await server.start()
        
        # Get authorization URL
        auth_url = await auth_provider.get_authorize_url(state)
        
        print(f"\nPlease open the following URL in your browser to authenticate:")
        print(f"{auth_url}\n")
        print("Waiting for authentication callback...")
        
        # Wait for callback
        callback_data = await server.wait_for_callback(timeout)
        
        # Exchange code for tokens
        tokens = await auth_provider.handle_callback(callback_data["code"], callback_data.get("state"))
        
        # Store credentials
        await auth_provider.store_credentials(tokens)
        
        print("Authentication successful! Credentials stored.")
        return tokens
        
    finally:
        await server.stop()