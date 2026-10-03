import unittest

from fastapi.testclient import TestClient

from main import app


class TestKnowledgeMCP(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_knowledge_mcp_hello_only(self):
        response = self.client.post(
            "/knowledge-mcp",
            json={
                "jsonrpc": "2.0",
                "id": 900,
                "method": "initialize",
                "params": {},
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["jsonrpc"], "2.0")
        self.assertEqual(data["id"], 900)
        self.assertEqual(data["result"]["serverInfo"]["name"], "w-bridge-knowledge-mcp")

        list_response = self.client.post(
            "/knowledge-mcp",
            json={
                "jsonrpc": "2.0",
                "id": 901,
                "method": "tools/list",
                "params": {},
            },
        )
        self.assertEqual(list_response.status_code, 200)
        tools = list_response.json()["result"]["tools"]
        self.assertEqual([tool["name"] for tool in tools], ["hello"])

        call_response = self.client.post(
            "/knowledge-mcp",
            json={
                "jsonrpc": "2.0",
                "id": 902,
                "method": "tools/call",
                "params": {"name": "hello", "arguments": {"name": "Knowledge"}},
            },
        )
        self.assertEqual(call_response.status_code, 200)
        call_data = call_response.json()
        self.assertFalse(call_data["result"]["isError"])
        self.assertEqual(call_data["result"]["content"], [{"type": "text", "text": "Hello, Knowledge!"}])

        forbidden_response = self.client.post(
            "/knowledge-mcp",
            json={
                "jsonrpc": "2.0",
                "id": 903,
                "method": "tools/call",
                "params": {"name": "unknown_tool", "arguments": {}},
            },
        )
        self.assertEqual(forbidden_response.status_code, 200)
        self.assertTrue(forbidden_response.json()["result"]["isError"])
