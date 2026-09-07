import asyncio
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app
from mcp.core import call_tool, list_tools
from mcp.tools import hello


class TestMCP(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_hello_tool_function(self):
        self.assertEqual(hello(), "Hello, World!")
        self.assertEqual(hello("Developer"), "Hello, Developer!")

    def test_list_tools_contains_hello(self):
        tools = list_tools()
        self.assertTrue(any(tool["name"] == "hello" for tool in tools))
        hello_tool = next(tool for tool in tools if tool["name"] == "hello")
        self.assertIn("inputSchema", hello_tool)
        self.assertIn("properties", hello_tool["inputSchema"])

    def test_call_tool_hello(self):
        res = asyncio.run(call_tool("hello", {"name": "Alice"}))
        self.assertFalse(res["isError"])
        self.assertEqual(res["content"], [{"type": "text", "text": "Hello, Alice!"}])

        res_default = asyncio.run(call_tool("hello", {}))
        self.assertFalse(res_default["isError"])
        self.assertEqual(res_default["content"], [{"type": "text", "text": "Hello, World!"}])

        res_unknown = asyncio.run(call_tool("unknown_tool", {}))
        self.assertTrue(res_unknown["isError"])

    def test_mcp_initialize(self):
        response = self.client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {},
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["id"], 1)
        self.assertEqual(data["result"]["protocolVersion"], "2024-11-05")
        self.assertIn("tools", data["result"]["capabilities"])
        self.assertEqual(data["result"]["serverInfo"]["name"], "w-bridge-mcp")

    def test_mcp_ping(self):
        response = self.client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "ping",
                "params": {},
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["id"], 2)
        self.assertEqual(data["result"], {})

    def test_mcp_tools_list(self):
        response = self.client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/list",
                "params": {},
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["id"], 3)
        tools = data["result"]["tools"]
        tool_names = {tool["name"] for tool in tools}
        expected_tools = [
            "hello",
            # Company Home
            "decisions_waiting",
            "blockers",
            "outcomes_review",
            "mentions",
            "material_changes",
            "ai_confirm",
            "knowledge_proposals",
            "add_decisions_waiting",
            "edit_decisions_waiting",
            "add_blockers",
            "edit_blockers",
            "add_outcomes_review",
            "edit_outcomes_review",
            "add_mentions",
            "edit_mentions",
            "add_material_changes",
            "edit_material_changes",
            "add_ai_confirm",
            "edit_ai_confirm",
            "add_knowledge_proposals",
            "edit_knowledge_proposals",
            # Company Status
            "company_status_period",
            "priorities",
            "progress",
            "risks",
            "dependencies",
            "changes",
            "decisions",
            "learnings",
            # Project Overview
            "project_milestones",
            # Project Status
            "project_bottlenecks",
            "project_todos",
            "project_knowledge_items",
            # Project All Hands
            "ProjectAllHandsTakeaway",
            "ProjectAllHandsActionItem",
            "ProjectAllHandsDecision",
            # Project Knowledge
            "external_knowledge_assets",
            "knowledge_activity_log",
            "tree_based_project_directory_data",
            "knowledge_summary_items",
            "ProjectObsidianNote",
            # Room Tools
            "add_message",
            "add_loading_message",
            "edit_loading_message",
            "delete_loading_message",
            "add_action_message",
            "add_decision_message",
        ]
        for name in expected_tools:
            self.assertIn(name, tool_names)

    def test_mcp_tools_call_categories(self):
        sample_tools = [
            ("decisions_waiting", {}),
            ("blockers", {}),
            ("add_blockers", {"title": "A blocker", "project_id": 1}),
            ("edit_blockers", {"attention_item_id": 10, "title": "Updated blocker"}),
            ("add_decisions_waiting", {"title": "A pending decision"}),
            ("edit_decisions_waiting", {"attention_item_id": 11, "status": "resolved"}),
            ("add_outcomes_review", {"title": "Outcome to review"}),
            ("edit_outcomes_review", {"attention_item_id": 12}),
            ("add_mentions", {"title": "A mention"}),
            ("edit_mentions", {"attention_item_id": 13}),
            ("add_material_changes", {"title": "A material change"}),
            ("edit_material_changes", {"attention_item_id": 14}),
            ("add_ai_confirm", {"title": "Needs AI confirmation"}),
            ("edit_ai_confirm", {"attention_item_id": 15}),
            ("add_knowledge_proposals", {"title": "Propose knowledge"}),
            ("edit_knowledge_proposals", {"attention_item_id": 16}),
            ("company_status_period", {}),
            ("priorities", {}),
            ("project_milestones", {"project_id": 1}),
            ("project_bottlenecks", {"project_id": 1}),
            ("ProjectAllHandsTakeaway", {"project_id": 1}),
            ("external_knowledge_assets", {"project_id": 1}),
            ("ProjectObsidianNote", {"project_id": 1}),
            ("add_message", {"project_id": 1, "room_id": 2, "user_id": 3, "body": "hi"}),
            ("add_loading_message", {"project_id": 1, "room_id": 2, "user_id": 3}),
            ("edit_loading_message", {"message_id": 4}),
            ("delete_loading_message", {"message_id": 4}),
            ("add_action_message", {"project_id": 1, "room_id": 2, "user_id": 3}),
            ("add_decision_message", {"project_id": 1, "room_id": 2, "user_id": 3, "approval_request_id": 5}),
        ]

        with (
            patch("mcp.tools.list_attention_items", return_value={"attention_items": []}),
            patch("mcp.tools.create_attention_item", return_value={"id": 1, "title": "Item"}),
            patch("mcp.tools.update_attention_item", return_value={"id": 10, "title": "Updated item"}),
            patch("mcp.tools.list_company_status_periods", return_value={"company_status_periods": []}),
            patch("mcp.tools.list_company_status_items", return_value={"company_status_items": []}),
            patch("mcp.tools.list_project_milestones", return_value={"project_milestones": []}),
            patch("mcp.tools.list_project_bottlenecks", return_value={"project_bottlenecks": []}),
            patch("mcp.tools.list_all_hands_takeaways", return_value={"project_all_hands_takeaways": []}),
            patch("mcp.tools.list_external_assets", return_value={"external_assets": []}),
            patch("mcp.tools.list_obsidian_notes", return_value={"obsidian_notes": []}),
            patch("mcp.tools.create_message", return_value={"id": 1}),
            patch("mcp.tools.update_message_by_id", return_value={"id": 4}),
            patch("mcp.tools.delete_message_by_id", return_value=None),
            patch("mcp.tools.send_action", return_value={"status": "ok"}),
            patch("mcp.tools.create_decision", return_value={"id": 5}),
        ):
            for name, arguments in sample_tools:
                response = self.client.post(
                    "/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "id": 100,
                        "method": "tools/call",
                        "params": {"name": name, "arguments": arguments},
                    },
                )
                self.assertEqual(response.status_code, 200, f"Tool {name} failed")
                data = response.json()
                self.assertFalse(data["result"]["isError"], f"Tool {name} returned error: {data['result']}")
                self.assertIn("content", data["result"])
                self.assertTrue(len(data["result"]["content"]) > 0)

    def test_mcp_tools_call_hello(self):
        response = self.client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "hello",
                    "arguments": {"name": "Bob"},
                },
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["id"], 4)
        self.assertFalse(data["result"]["isError"])
        self.assertEqual(data["result"]["content"], [{"type": "text", "text": "Hello, Bob!"}])

    def test_mcp_invalid_method(self):
        response = self.client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 5,
                "method": "non_existent_method",
                "params": {},
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["id"], 5)
        self.assertIn("error", data)
        self.assertEqual(data["error"]["code"], -32601)

    def test_mcp_invalid_json(self):
        response = self.client.post(
            "/mcp",
            content="not a valid json",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data["error"]["code"], -32700)

    def test_mcp_tools_call_with_project_name_resolution(self):
        with (
            patch("mcp.tools.project_name_fuzzy_match", return_value={"id": 42, "name": "Acme"}) as fuzzy_mock,
            patch("mcp.tools.list_project_milestones", return_value={"project_milestones": []}) as api_mock,
        ):
            response = self.client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 200,
                    "method": "tools/call",
                    "params": {"name": "project_milestones", "arguments": {"project_name": "Acme"}},
                },
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertFalse(data["result"]["isError"])
            fuzzy_mock.assert_awaited_once_with("Acme")
            api_mock.assert_awaited_once_with(42, active=None, page=None, per_page=None)

    def test_mcp_loading_message_prefixes_body(self):
        with patch("mcp.tools.create_message", return_value={"id": 7}) as api_mock:
            response = self.client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 201,
                    "method": "tools/call",
                    "params": {
                        "name": "add_loading_message",
                        "arguments": {"project_id": 1, "room_id": 2, "user_id": 3, "body": "working"},
                    },
                },
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertFalse(data["result"]["isError"])
            api_mock.assert_awaited_once()
            _, _, kwargs = api_mock.mock_calls[0]
            self.assertTrue(kwargs["body"].startswith(":spin:"))

    def test_add_message_without_project(self):
        with patch("mcp.tools.create_message", return_value={"id": 9}) as api_mock:
            response = self.client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 300,
                    "method": "tools/call",
                    "params": {
                        "name": "add_message",
                        "arguments": {"room_id": 2, "user_id": 3, "body": "hi from private room"},
                    },
                },
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertFalse(data["result"]["isError"])
            api_mock.assert_awaited_once_with(None, 2, 3, body="hi from private room", attachment=None)

    def test_add_loading_message_without_project(self):
        with patch("mcp.tools.create_message", return_value={"id": 10}) as api_mock:
            response = self.client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 301,
                    "method": "tools/call",
                    "params": {
                        "name": "add_loading_message",
                        "arguments": {"room_id": 2, "user_id": 3, "body": "working privately"},
                    },
                },
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertFalse(data["result"]["isError"])
            api_mock.assert_awaited_once()
            _, _, kwargs = api_mock.mock_calls[0]
            self.assertEqual(kwargs.get("project_id"), None)
            self.assertTrue(kwargs["body"].startswith(":spin:"))


if __name__ == "__main__":
    unittest.main()
