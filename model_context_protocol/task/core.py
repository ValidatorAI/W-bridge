import inspect
from typing import Any

from .tools import TOOL_DEFINITIONS, TOOL_HANDLERS


def list_tools() -> list[dict[str, Any]]:
    return TOOL_DEFINITIONS


async def call_tool(
    name: str,
    arguments: dict[str, Any] | None = None,
    request_id: Any | None = None,
) -> dict[str, Any]:
    args = arguments or {}

    if name not in TOOL_HANDLERS:
        return {
            "content": [{"type": "text", "text": f"Tool '{name}' not found."}],
            "isError": True,
        }

    handler = TOOL_HANDLERS[name]
    if inspect.iscoroutinefunction(handler):
        result = await handler(**args)
    else:
        result = handler(**args)

    return {
        "content": [{"type": "text", "text": str(result)}],
        "isError": False,
    }


__all__ = ["call_tool", "list_tools"]
