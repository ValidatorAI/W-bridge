import unittest
from fastapi.testclient import TestClient

from main import app
from mcp.core import call_tool, hello, list_tools


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
        res = call_tool("hello", {"name": "Alice"})
        self.assertFalse(res["isError"])
        self.assertEqual(res["content"], [{"type": "text", "text": "Hello, Alice!"}])

        res_default = call_tool("hello", {})
        self.assertFalse(res_default["isError"])
        self.assertEqual(res_default["content"], [{"type": "text", "text": "Hello, World!"}])

        res_unknown = call_tool("unknown_tool", {})
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
            "decisions_waiting",
            "blockers",
            "company_status_period",
            "priorities",
            "project_milestones",
            "project_bottlenecks",
            "ProjectAllHandsTakeaway",
            "external_knowledge_assets",
            "ProjectObsidianNote",
            "add_message",
            "add_loading_message",
            "edit_loading_message",
            "delete_loading_message",
            "add_action_message",
            "add_decision_message",
        ]
        for name in sample_tools:
            response = self.client.post(
                "/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 100,
                    "method": "tools/call",
                    "params": {"name": name, "arguments": {}},
                },
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertFalse(data["result"]["isError"])
            self.assertIn("Dummy result", data["result"]["content"][0]["text"])

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


if __name__ == "__main__":
    unittest.main()
