import httpx
import json
import logging

log = logging.getLogger("mcp")

MCP_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


def _parse_sse_json(response_text: str) -> dict:
    """Parse JSON from SSE response (lines like 'data: {...}')."""
    for line in response_text.strip().split("\n"):
        if line.startswith("data:"):
            data = line[5:].strip()
            if data:
                return json.loads(data)
    raise ValueError("No JSON data in SSE response")


class MCPClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0, headers=MCP_HEADERS)
        self._session_id: str | None = None

    async def _ensure_session(self) -> None:
        """Establish MCP session via initialize handshake if not already done."""
        if self._session_id is not None:
            return

        log.info("Establishing MCP session...")
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "civic-dashboard", "version": "1.0"},
            },
        }
        response = await self.client.post(self.base_url, json=payload)
        response.raise_for_status()

        session_id = response.headers.get("mcp-session-id")
        if not session_id:
            raise RuntimeError("MCP server did not return mcp-session-id")
        self._session_id = session_id.strip()
        log.info("MCP session established")

    def _session_headers(self) -> dict:
        if not self._session_id:
            raise RuntimeError("MCP session not initialized")
        return {"mcp-session-id": self._session_id}

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call an MCP tool and return the text content as a string."""
        await self._ensure_session()

        log.debug("Calling MCP tool %s", tool_name)
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        response = await self.client.post(
            self.base_url, json=payload, headers=self._session_headers()
        )
        response.raise_for_status()

        result = _parse_sse_json(response.text)
        if "result" in result and "content" in result["result"]:
            content = result["result"]["content"]
            if isinstance(content, list) and len(content) > 0:
                return content[0].get("text", "")
        return ""

    async def list_tools(self) -> list[dict]:
        """Fetch available tools from the MCP server."""
        await self._ensure_session()

        log.info("Listing MCP tools...")
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }

        response = await self.client.post(
            self.base_url, json=payload, headers=self._session_headers()
        )
        response.raise_for_status()

        result = _parse_sse_json(response.text)
        if "result" in result and "tools" in result["result"]:
            tools = result["result"]["tools"]
            log.info("MCP returned %d tools", len(tools))
            return tools
        return []

    async def close(self):
        await self.client.aclose()
