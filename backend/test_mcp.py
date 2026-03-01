import asyncio
import logging
import pytest
from mcp_client import MCPClient

logging.basicConfig(level=logging.DEBUG)


@pytest.mark.skip(reason="Manual MCP integration script - run with: python test_mcp.py")
async def test():
    client = MCPClient("https://mcp.data.gouv.fr/mcp")
    try:
        r1 = await client.call_tool("search_datasets", {"query": "population Lyon INSEE", "page_size": 5})
        print("R1 chars:", len(r1))
        print("R1 text:", r1[:100])
    except Exception as e:
        print("R1 Exception", repr(e))

    try:
        r2 = await client.call_tool("search_datasets", {"query": "démographie Lyon", "page_size": 5})
        print("R2 chars:", len(r2))
        print("R2 text:", r2[:100])
    except Exception as e:
        print("R2 Exception", repr(e))
    
    await client.close()


if __name__ == "__main__":
    asyncio.run(test())
