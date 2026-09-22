from ..schema import AiProfile, AiProfileList
from ._client import request


async def list_ai_profiles() -> AiProfileList:
    return await request("GET", "/ai_profiles")


async def get_ai_profile(ai_profile_id: int | str) -> AiProfile:
    return await request("GET", f"/ai_profiles/{ai_profile_id}")
