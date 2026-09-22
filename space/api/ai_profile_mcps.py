from ..schema import AiProfileMcp, AiProfileMcpList
from ._client import prune, request


async def list_ai_profile_mcps(
    *,
    ai_profile_id: int | str | None = None,
    mcp_id: int | str | None = None,
) -> AiProfileMcpList:
    return await request(
        "GET",
        "/ai_profile_mcps",
        params=prune({"ai_profile_id": ai_profile_id, "mcp_id": mcp_id}),
    )


async def get_ai_profile_mcp(ai_profile_mcp_id: int | str) -> AiProfileMcp:
    return await request("GET", f"/ai_profile_mcps/{ai_profile_mcp_id}")
