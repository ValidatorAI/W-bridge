import logging
from typing import Any

from mcp.core import call_tool, list_tools

logger = logging.getLogger(__name__)

MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {
    "name": "w-bridge-mcp",
    "version": "1.0.0",
}
SERVER_CAPABILITIES = {
    "tools": {},
}


def _jsonrpc_error(code: int, message: str, req_id: Any = None, data: Any = None) -> dict[str, Any]:
    err: dict[str, Any] = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": err,
    }


def _jsonrpc_result(result: Any, req_id: Any) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": result,
    }


async def handle_mcp_request(payload: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return _jsonrpc_error(-32600, "Invalid Request: expected a JSON object")

    req_id = payload.get("id")
    method = payload.get("method")

    if not isinstance(method, str):
        return _jsonrpc_error(-32600, "Invalid Request: missing or invalid 'method'", req_id)

    params = payload.get("params") or {}
    if not isinstance(params, dict):
        return _jsonrpc_error(-32602, "Invalid params: params must be an object", req_id)

    # Notifications do not require a response if no id is provided
    is_notification = req_id is None

    if method == "initialize":
        result = {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": SERVER_CAPABILITIES,
            "serverInfo": SERVER_INFO,
        }
        return _jsonrpc_result(result, req_id)

    elif method in ("notifications/initialized", "initialized"):
        if is_notification:
            return None
        return _jsonrpc_result({}, req_id)

    elif method == "ping":
        return _jsonrpc_result({}, req_id)

    elif method == "tools/list":
        result = {
            "tools": list_tools(),
        }
        return _jsonrpc_result(result, req_id)

    elif method == "tools/call":
        tool_name = params.get("name")
        if not tool_name or not isinstance(tool_name, str):
            return _jsonrpc_error(-32602, "Invalid params: 'name' is required and must be a string", req_id)

        arguments = params.get("arguments")
        if arguments is not None and not isinstance(arguments, dict):
            return _jsonrpc_error(-32602, "Invalid params: 'arguments' must be an object", req_id)

        tool_result = await call_tool(tool_name, arguments, request_id=req_id)
        return _jsonrpc_result(tool_result, req_id)

    else:
        if is_notification:
            return None
        return _jsonrpc_error(-32601, f"Method not found: '{method}'", req_id)
