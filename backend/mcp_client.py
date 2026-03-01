import httpx
from typing import Optional
import json

class MCPClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call an MCP tool and return the text content as a string."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = await self.client.post(
            f"{self.base_url}/mcp",
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        if "result" in result and "content" in result["result"]:
            content = result["result"]["content"]
            if isinstance(content, list) and len(content) > 0:
                return content[0].get("text", "")
        return ""

    async def list_tools(self) -> list[dict]:
        """Fetch available tools from the MCP server."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        }
        
        response = await self.client.post(
            f"{self.base_url}/mcp",
            json=payload
        )
        response.raise_for_status()
        
        result = response.json()
        if "result" in result and "tools" in result["result"]:
            return result["result"]["tools"]
        return []

    async def close(self):
        await self.client.aclose()
