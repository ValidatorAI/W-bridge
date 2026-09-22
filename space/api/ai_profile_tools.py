from ..schema import AiProfileTool, AiProfileToolList
from ._client import prune, request


async def list_ai_profile_tools(
    *,
    ai_profile_id: int | str | None = None,
    tool_id: int | str | None = None,
) -> AiProfileToolList:
    return await request(
        "GET",
        "/ai_profile_tools",
        params=prune({"ai_profile_id": ai_profile_id, "tool_id": tool_id}),
    )


async def get_ai_profile_tool(ai_profile_tool_id: int | str) -> AiProfileTool:
    return await request("GET", f"/ai_profile_tools/{ai_profile_tool_id}")
