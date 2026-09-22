from ..schema import AiProfileSkill, AiProfileSkillList
from ._client import prune, request


async def list_ai_profile_skills(
    *,
    ai_profile_id: int | str | None = None,
    skill_id: int | str | None = None,
) -> AiProfileSkillList:
    return await request(
        "GET",
        "/ai_profile_skills",
        params=prune({"ai_profile_id": ai_profile_id, "skill_id": skill_id}),
    )


async def get_ai_profile_skill(ai_profile_skill_id: int | str) -> AiProfileSkill:
    return await request("GET", f"/ai_profile_skills/{ai_profile_skill_id}")
