import asyncio
import logging
from mcp_client import MCPClient

logging.basicConfig(level=logging.DEBUG)

async def test():
    client = MCPClient("https://mcp.data.gouv.fr/mcp")
    
    # Establish session first
    await client._ensure_session()
    
    async def execute_one(q):
        try:
            print(f"Calling {q}")
            res = await client.call_tool("search_datasets", {"query": q, "page_size": 5})
            print(f"Done {q}: {len(res)} chars")
            return res
        except Exception as e:
            print(f"Exception for {q}: {repr(e)}")
            raise e

    print("Gathering...")
    results = await asyncio.gather(
        execute_one("population Lyon INSEE"),
        execute_one("démographie Lyon")
    )
    
    print("Gather finished!")
    await client.close()

asyncio.run(test())
