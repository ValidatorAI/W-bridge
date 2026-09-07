import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from mcp import helpers


class TestFuzzyMatchHelpers(unittest.TestCase):
    def test_project_name_fuzzy_match(self):
        async def _run():
            with patch("mcp.helpers.list_projects", AsyncMock(return_value=[
                {"id": 1, "name": "Alpha Project"},
                {"id": 2, "name": "Beta Launch"},
            ])):
                match = await helpers.project_name_fuzzy_match("alp")
                self.assertIsNotNone(match)
                self.assertEqual(match["id"], 1)
                self.assertEqual(match["name"], "Alpha Project")

        asyncio.run(_run())

    def test_room_name_fuzzy(self):
        async def _run():
            with patch("mcp.helpers.search_rooms", AsyncMock(return_value=[
                {"id": 10, "name": "Design Review"},
                {"id": 11, "name": "Ops Standup"},
            ])):
                match = await helpers.room_name_fuzzy(3, "design")
                self.assertIsNotNone(match)
                self.assertEqual(match["id"], 10)
                self.assertEqual(match["name"], "Design Review")

        asyncio.run(_run())

    def test_username_fuzzy_match(self):
        async def _run():
            with patch("mcp.helpers.list_project_users", AsyncMock(return_value={
                "project_users": [
                    {"id": 1, "name": "Alicia Stone"},
                    {"id": 2, "name": "Miguel Lee"},
                ]
            })):
                match = await helpers.username_fuzzy_match(7, "alicia")
                self.assertIsNotNone(match)
                self.assertEqual(match["id"], 1)
                self.assertEqual(match["name"], "Alicia Stone")

        asyncio.run(_run())

    def test_bot_name_fuzzy_match(self):
        async def _run():
            with patch("mcp.helpers.SessionLocal") as session_factory:
                session = session_factory.return_value
                session.__enter__.return_value.query.return_value.filter.return_value.all.return_value = [
                    type("Bot", (), {"id": 5, "name": "Hera Bot", "profile_name": "default", "active": True})(),
                    type("Bot", (), {"id": 6, "name": "Ops Helper", "profile_name": "default", "active": True})(),
                ]
                match = await helpers.bot_name_fuzzy_match("hera")
                self.assertIsNotNone(match)
                self.assertEqual(match["id"], 5)
                self.assertEqual(match["name"], "Hera Bot")

        asyncio.run(_run())

    def test_no_match_returns_none(self):
        async def _run():
            with patch("mcp.helpers.list_projects", AsyncMock(return_value=[
                {"id": 1, "name": "Alpha Project"},
            ])):
                match = await helpers.project_name_fuzzy_match("totally unrelated xyz")
                self.assertIsNone(match)

        asyncio.run(_run())


if __name__ == "__main__":
    unittest.main()
