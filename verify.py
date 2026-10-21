"""Run after starting main.py and mcp_server.py in separate terminals."""
import asyncio
import json
from urllib.request import Request, urlopen
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


def check_web():
    data = json.dumps({"message": "blue kurti under 1000"}).encode()
    req = Request("http://127.0.0.1:5001/api/search", data=data, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=8) as r:
        result = json.load(r)
    assert result["products"][0]["name"] == "Blue Embroidered Kurti", result
    print("PASS Flask product search")


async def check_mcp():
    async with streamable_http_client("http://127.0.0.1:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            assert "search_fashion" in [t.name for t in tools.tools]
            result = await session.call_tool("search_fashion", {"query": "blue kurti under 1000"})
            assert not result.isError, result
            print("PASS MCP Streamable HTTP search_fashion")
            print("MCP output:", result.content[0].text[:500])


if __name__ == "__main__":
    check_web()
    asyncio.run(check_mcp())
