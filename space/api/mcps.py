from ..schema import McpServer, McpServerList
from ._client import request


async def list_mcps() -> McpServerList:
    return await request("GET", "/mcps")


async def get_mcp(mcp_id: int | str) -> McpServer:
    return await request("GET", f"/mcps/{mcp_id}")
