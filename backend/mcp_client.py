import asyncio
import httpx
import json
import logging

log = logging.getLogger("mcp")

MCP_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

# Retry configuration for transient upstream errors (502, 503, 504, timeouts)
MCP_MAX_RETRIES = 3
MCP_RETRY_BACKOFF_BASE = 1.0  # seconds


def _is_retryable(exc: BaseException) -> bool:
    """Return True if the exception indicates a transient error worth retrying."""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in (502, 503, 504)
    if isinstance(exc, (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout)):
        return True
    return False


def _parse_sse_json(response_text: str) -> dict:
    """Parse JSON from SSE response (lines like 'data: {...}')."""
    for line in response_text.strip().split("\n"):
        if line.startswith("data:"):
            data = line[5:].strip()
            if data:
                return json.loads(data)
    raise ValueError("No JSON data in SSE response")


class MCPClient:
    """MCP client for data.gouv.fr. Uses stateless Streamable HTTP - no session required."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0, headers=MCP_HEADERS)

    async def _post_with_retry(self, payload: dict) -> httpx.Response:
        """POST to MCP endpoint with retry on transient errors (502, 503, 504, timeouts)."""
        last_exc = None
        for attempt in range(MCP_MAX_RETRIES):
            try:
                response = await self.client.post(self.base_url, json=payload)
                response.raise_for_status()
                return response
            except Exception as e:
                last_exc = e
                if not _is_retryable(e) or attempt == MCP_MAX_RETRIES - 1:
                    raise
                delay = MCP_RETRY_BACKOFF_BASE * (2**attempt)
                log.warning(
                    "MCP call failed (attempt %d/%d): %s. Retrying in %.1fs...",
                    attempt + 1,
                    MCP_MAX_RETRIES,
                    e,
                    delay,
                )
                await asyncio.sleep(delay)
        raise last_exc

    async def call_tool(self, tool_name: str, arguments: dict) -> str:
        """Call an MCP tool and return the text content as a string."""
        log.debug("Calling MCP tool %s", tool_name)
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
        }

        response = await self._post_with_retry(payload)

        result = _parse_sse_json(response.text)
        if "result" in result and "content" in result["result"]:
            content = result["result"]["content"]
            if isinstance(content, list) and len(content) > 0:
                return content[0].get("text", "")
        return ""

    async def list_tools(self) -> list[dict]:
        """Fetch available tools from the MCP server."""
        log.info("Listing MCP tools...")
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }

        response = await self._post_with_retry(payload)

        result = _parse_sse_json(response.text)
        if "result" in result and "tools" in result["result"]:
            tools = result["result"]["tools"]
            log.info("MCP returned %d tools", len(tools))
            return tools
        return []

    async def close(self):
        await self.client.aclose()
