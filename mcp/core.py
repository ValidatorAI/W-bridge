from typing import Any

from mcp.tools import TOOL_DEFINITIONS, TOOL_HANDLERS, hello


def list_tools() -> list[dict[str, Any]]:
    return TOOL_DEFINITIONS


def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    if name not in TOOL_HANDLERS:
        return {
            "content": [{"type": "text", "text": f"Tool '{name}' not found."}],
            "isError": True,
        }

    handler = TOOL_HANDLERS[name]
    args = arguments or {}

    try:
        result = handler(**args)
        if isinstance(result, str):
            text_result = result
        else:
            text_result = str(result)

        return {
            "content": [{"type": "text", "text": text_result}],
            "isError": False,
        }
    except Exception as exc:
        return {
            "content": [{"type": "text", "text": f"Error executing tool '{name}': {str(exc)}"}],
            "isError": True,
        }

