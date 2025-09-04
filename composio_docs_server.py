# composio_docs_server.py
import requests
from fastmcp import FastMCP

# Create the MCP server
mcp = FastMCP("composio-docs-server")

@mcp.tool()
def get_composio_docs(section: str = None) -> dict:
    """Retrieve the latest Composio MCP documentation"""
    base_url = "https://docs.composio.dev/docs/mcp-developers"
    url = f"{base_url}#{section}" if section else base_url
    resp = requests.get(url)
    resp.raise_for_status()
    return {"content": resp.text}

if __name__ == "__main__":
    mcp.run()
