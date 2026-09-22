from ..schema import AiSetting, AiSettingList
from ._client import request


async def list_ai_settings() -> AiSettingList:
    return await request("GET", "/ai_settings")


async def get_ai_setting(ai_setting_id: int | str) -> AiSetting:
    return await request("GET", f"/ai_settings/{ai_setting_id}")
