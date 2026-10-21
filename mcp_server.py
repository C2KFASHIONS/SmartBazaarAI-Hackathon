"""Local Streamable HTTP MCP server powered by the official MCP Python SDK.
Run separately: python mcp_server.py. Local port 8000, endpoint /mcp.
"""
from mcp.server.fastmcp import FastMCP
from catalog import PRODUCTS, search_products

mcp = FastMCP("SmartBazaar AI Shopping Tools", host="127.0.0.1", port=8000, stateless_http=True, json_response=True)

@mcp.tool()
def search_fashion(query: str, max_price: int | None = None, color: str | None = None) -> dict:
    """Search demonstration fashion items using color, garment type, and price budget. All inventory is fictional."""
    matches, filters = search_products(query, max_price=max_price, color=color)
    return {"items": matches, "filters": filters, "count": len(matches), "currency": "INR", "data_source": "fictional demo catalog"}

@mcp.tool()
def list_fashion_catalog() -> list[dict]:
    """Return the fictional sample fashion catalog."""
    return PRODUCTS

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
