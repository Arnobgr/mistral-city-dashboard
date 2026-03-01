import asyncio
import logging
import httpx
import json
import pytest

MCP_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}

logging.basicConfig(level=logging.DEBUG)


@pytest.mark.skip(reason="Manual MCP integration script - run with: python test_mcp_no_session.py")
async def test():
    async with httpx.AsyncClient(timeout=30.0, headers=MCP_HEADERS) as client:
        async def call(q):
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "search_datasets", "arguments": {"query": q, "page_size": 5}}
            }
            res = await client.post("https://mcp.data.gouv.fr/mcp", json=payload)
            print(f"Done {q}: {len(res.text)}")
            print(res.text[:100])

        await asyncio.gather(
            call("population Lyon INSEE"),
            call("démographie Lyon")
        )


if __name__ == "__main__":
    asyncio.run(test())