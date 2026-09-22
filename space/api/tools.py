from ..schema import Tool, ToolList
from ._client import request


async def list_tools() -> ToolList:
    return await request("GET", "/tools")


async def get_tool(tool_id: int | str) -> Tool:
    return await request("GET", f"/tools/{tool_id}")
