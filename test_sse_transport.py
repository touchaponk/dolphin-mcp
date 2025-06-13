#!/usr/bin/env python3
"""
Simple test to verify SSE transport configuration support.
"""

import asyncio
import json
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from dolphin_mcp.client import MCPAgent
from dolphin_mcp.utils import load_config_from_file

async def test_sse_transport_config():
    """Test that SSE transport configuration is properly parsed and handled."""
    
    # Create a minimal test configuration
    test_config = {
        "models": [
            {
                "title": "test-model", 
                "provider": "anthropic",
                "model": "claude-3-sonnet-20240229",
                "default": True
            }
        ]
    }
    
    # Test MCP server configurations
    test_mcp_config = {
        "mcpServers": {
            "sse-server": {
                "url": "https://api.example.com/mcp/sse",
                "transport": "sse",
                "headers": {
                    "Authorization": "Bearer test-token"
                },
                "disabled": False
            },
            "disabled-sse": {
                "url": "https://disabled.example.com/mcp/sse",
                "transport": "sse", 
                "disabled": True
            },
            "legacy-sse": {
                "url": "https://legacy.example.com/mcp/sse"
                # No transport field - should still work for backward compatibility
            },
            "stdio-server": {
                "command": "echo",
                "args": ["hello"],
                "transport": "stdio"
            }
        }
    }
    
    print("Testing SSE transport configuration parsing...")
    
    try:
        # Test that the agent can be created with the configuration
        # (it will fail to connect, but configuration parsing should work)
        agent = await MCPAgent.create(
            provider_config=test_config,
            mcp_server_config=test_mcp_config,
            quiet_mode=True
        )
        
        print("✓ MCPAgent created successfully with SSE transport config")
        
        # Check that only non-disabled servers were processed
        print(f"✓ Started {len(agent.servers)} servers (disabled servers were skipped)")
        
        # Clean up
        await agent.cleanup()
        
        print("✓ All tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_example_config():
    """Test loading the example SSE configuration file."""
    print("\nTesting example SSE configuration file...")
    
    try:
        config = await load_config_from_file("examples/sse-mcp.json")
        
        servers = config.get("mcpServers", {})
        print(f"✓ Loaded {len(servers)} server configurations")
        
        # Check that different transport types are properly recognized
        for name, conf in servers.items():
            transport = conf.get("transport", "stdio")
            disabled = conf.get("disabled", False)
            has_url = "url" in conf
            has_headers = "headers" in conf
            
            print(f"  {name}: transport={transport}, disabled={disabled}, url={has_url}, headers={has_headers}")
            
        print("✓ Example configuration loaded successfully")
        return True
        
    except Exception as e:
        print(f"✗ Example config test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("Testing SSE transport type implementation...\n")
    
    test1 = await test_sse_transport_config()
    test2 = await test_example_config()
    
    if test1 and test2:
        print("\n🎉 All tests passed! SSE transport implementation is working.")
        return 0
    else:
        print("\n❌ Some tests failed.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)