import asyncio
import inspect
import traceback
from typing import Any

from db.database import SessionLocal
from db.models import McpException
from mcp.tools import TOOL_DEFINITIONS, TOOL_HANDLERS


def list_tools() -> list[dict[str, Any]]:
    return TOOL_DEFINITIONS


def _persist_tool_exception(tool_name: str, exc: Exception) -> None:
    session = SessionLocal()
    try:
        record = McpException(
            tool_call_name=tool_name,
            exception=str(exc),
            stored_exception=traceback.format_exc(),
        )
        session.add(record)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


async def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    if name not in TOOL_HANDLERS:
        return {
            "content": [{"type": "text", "text": f"Tool '{name}' not found."}],
            "isError": True,
        }

    handler = TOOL_HANDLERS[name]
    args = arguments or {}

    try:
        if inspect.iscoroutinefunction(handler):
            result = await handler(**args)
        else:
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
        _persist_tool_exception(name, exc)
        return {
            "content": [{"type": "text", "text": f"Error executing tool '{name}': {str(exc)}"}],
            "isError": True,
        }

