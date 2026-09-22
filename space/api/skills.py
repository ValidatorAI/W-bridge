from ..schema import Skill, SkillList
from ._client import request


async def list_skills() -> SkillList:
    return await request("GET", "/skills")


async def get_skill(skill_id: int | str) -> Skill:
    return await request("GET", f"/skills/{skill_id}")
