import unittest
from unittest.mock import AsyncMock, patch

from space.api import (
    get_ai_profile,
    get_ai_profile_mcp,
    get_ai_profile_skill,
    get_ai_profile_tool,
    get_ai_setting,
    get_mcp,
    get_skill,
    get_tool,
    list_ai_profiles,
    list_ai_profile_mcps,
    list_ai_profile_skills,
    list_ai_profile_tools,
    list_ai_settings,
    list_mcps,
    list_skills,
    list_tools,
)


class TestAiConfigAPI(unittest.IsolatedAsyncioTestCase):
    async def test_list_ai_profiles_calls_expected_endpoint(self) -> None:
        with patch("space.api.ai_profiles.request", new_callable=AsyncMock) as mock_request:
            await list_ai_profiles()
            mock_request.assert_awaited_once_with("GET", "/ai_profiles")

    async def test_get_ai_profile_calls_expected_endpoint(self) -> None:
        with patch("space.api.ai_profiles.request", new_callable=AsyncMock) as mock_request:
            await get_ai_profile(9)
            mock_request.assert_awaited_once_with("GET", "/ai_profiles/9")

    async def test_list_ai_settings_calls_expected_endpoint(self) -> None:
        with patch("space.api.ai_settings.request", new_callable=AsyncMock) as mock_request:
            await list_ai_settings()
            mock_request.assert_awaited_once_with("GET", "/ai_settings")

    async def test_get_ai_setting_calls_expected_endpoint(self) -> None:
        with patch("space.api.ai_settings.request", new_callable=AsyncMock) as mock_request:
            await get_ai_setting(3)
            mock_request.assert_awaited_once_with("GET", "/ai_settings/3")

    async def test_list_mcps_calls_expected_endpoint(self) -> None:
        with patch("space.api.mcps.request", new_callable=AsyncMock) as mock_request:
            await list_mcps()
            mock_request.assert_awaited_once_with("GET", "/mcps")

    async def test_get_mcp_calls_expected_endpoint(self) -> None:
        with patch("space.api.mcps.request", new_callable=AsyncMock) as mock_request:
            await get_mcp(4)
            mock_request.assert_awaited_once_with("GET", "/mcps/4")

    async def test_list_tools_calls_expected_endpoint(self) -> None:
        with patch("space.api.tools.request", new_callable=AsyncMock) as mock_request:
            await list_tools()
            mock_request.assert_awaited_once_with("GET", "/tools")

    async def test_get_tool_calls_expected_endpoint(self) -> None:
        with patch("space.api.tools.request", new_callable=AsyncMock) as mock_request:
            await get_tool(8)
            mock_request.assert_awaited_once_with("GET", "/tools/8")

    async def test_list_skills_calls_expected_endpoint(self) -> None:
        with patch("space.api.skills.request", new_callable=AsyncMock) as mock_request:
            await list_skills()
            mock_request.assert_awaited_once_with("GET", "/skills")

    async def test_get_skill_calls_expected_endpoint(self) -> None:
        with patch("space.api.skills.request", new_callable=AsyncMock) as mock_request:
            await get_skill(10)
            mock_request.assert_awaited_once_with("GET", "/skills/10")

    async def test_list_ai_profile_tools_calls_expected_endpoint_without_filters(self) -> None:
        with patch("space.api.ai_profile_tools.request", new_callable=AsyncMock) as mock_request:
            await list_ai_profile_tools()
            mock_request.assert_awaited_once_with("GET", "/ai_profile_tools", params=None)

    async def test_list_ai_profile_tools_calls_expected_endpoint_with_filters(self) -> None:
        with patch("space.api.ai_profile_tools.request", new_callable=AsyncMock) as mock_request:
            await list_ai_profile_tools(ai_profile_id=11, tool_id=12)
            mock_request.assert_awaited_once_with(
                "GET",
                "/ai_profile_tools",
                params={"ai_profile_id": 11, "tool_id": 12},
            )

    async def test_get_ai_profile_tool_calls_expected_endpoint(self) -> None:
        with patch("space.api.ai_profile_tools.request", new_callable=AsyncMock) as mock_request:
            await get_ai_profile_tool(13)
            mock_request.assert_awaited_once_with("GET", "/ai_profile_tools/13")

    async def test_list_ai_profile_skills_calls_expected_endpoint_without_filters(self) -> None:
        with patch(
            "space.api.ai_profile_skills.request", new_callable=AsyncMock
        ) as mock_request:
            await list_ai_profile_skills()
            mock_request.assert_awaited_once_with("GET", "/ai_profile_skills", params=None)

    async def test_list_ai_profile_skills_calls_expected_endpoint_with_filters(self) -> None:
        with patch(
            "space.api.ai_profile_skills.request", new_callable=AsyncMock
        ) as mock_request:
            await list_ai_profile_skills(ai_profile_id=21, skill_id=22)
            mock_request.assert_awaited_once_with(
                "GET",
                "/ai_profile_skills",
                params={"ai_profile_id": 21, "skill_id": 22},
            )

    async def test_get_ai_profile_skill_calls_expected_endpoint(self) -> None:
        with patch(
            "space.api.ai_profile_skills.request", new_callable=AsyncMock
        ) as mock_request:
            await get_ai_profile_skill(23)
            mock_request.assert_awaited_once_with("GET", "/ai_profile_skills/23")

    async def test_list_ai_profile_mcps_calls_expected_endpoint_without_filters(self) -> None:
        with patch("space.api.ai_profile_mcps.request", new_callable=AsyncMock) as mock_request:
            await list_ai_profile_mcps()
            mock_request.assert_awaited_once_with("GET", "/ai_profile_mcps", params=None)

    async def test_list_ai_profile_mcps_calls_expected_endpoint_with_filters(self) -> None:
        with patch("space.api.ai_profile_mcps.request", new_callable=AsyncMock) as mock_request:
            await list_ai_profile_mcps(ai_profile_id=31, mcp_id=32)
            mock_request.assert_awaited_once_with(
                "GET",
                "/ai_profile_mcps",
                params={"ai_profile_id": 31, "mcp_id": 32},
            )

    async def test_get_ai_profile_mcp_calls_expected_endpoint(self) -> None:
        with patch("space.api.ai_profile_mcps.request", new_callable=AsyncMock) as mock_request:
            await get_ai_profile_mcp(33)
            mock_request.assert_awaited_once_with("GET", "/ai_profile_mcps/33")


if __name__ == "__main__":
    unittest.main()
