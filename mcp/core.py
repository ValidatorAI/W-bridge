import asyncio
import inspect
import logging
import time
import traceback
from typing import Any

from db.exception_store import persist_mcp_call_log
from db.database import SessionLocal
from db.models import McpException
from mcp.tools import TOOL_DEFINITIONS, TOOL_HANDLERS

logger = logging.getLogger(__name__)

_SENSITIVE_KEY_PARTS = {
    "authorization",
    "cookie",
    "password",
    "secret",
    "token",
}
_RESULT_PREVIEW_LIMIT = 2000


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


def _is_sensitive_key(key: str) -> bool:
    lower = key.lower()
    return any(part in lower for part in _SENSITIVE_KEY_PARTS)


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            key_str = str(key)
            if _is_sensitive_key(key_str):
                sanitized[key_str] = "***"
            else:
                sanitized[key_str] = _sanitize_value(item)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_value(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_value(item) for item in value]
    return value


def _result_preview(text: str) -> tuple[str, int]:
    text_size = len(text)
    if text_size <= _RESULT_PREVIEW_LIMIT:
        return text, text_size
    return f"{text[:_RESULT_PREVIEW_LIMIT]}...(truncated)", text_size


async def call_tool(
    name: str,
    arguments: dict[str, Any] | None = None,
    request_id: Any | None = None,
) -> dict[str, Any]:
    started_at = time.perf_counter()
    jsonrpc_id = None if request_id is None else str(request_id)
    args = arguments or {}
    sanitized_args = _sanitize_value(args)

    is_error = True
    error_message: str | None = None
    preview_text = ""

    if name not in TOOL_HANDLERS:
        error_message = f"Tool '{name}' not found."
        preview_text = error_message
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        persist_mcp_call_log(
            jsonrpc_id=jsonrpc_id,
            tool_call_name=name,
            params_sanitized=sanitized_args,
            is_error=True,
            error_message=error_message,
            result_preview=error_message,
            result_size=len(error_message),
            duration_ms=elapsed_ms,
        )
        logger.warning("MCP tool not found: %s", name)
        return {
            "content": [{"type": "text", "text": error_message}],
            "isError": True,
        }

    handler = TOOL_HANDLERS[name]

    try:
        logger.info("MCP tool call started: tool=%s request_id=%s", name, jsonrpc_id)
        if inspect.iscoroutinefunction(handler):
            result = await handler(**args)
        else:
            result = handler(**args)

        if isinstance(result, str):
            text_result = result
        else:
            text_result = str(result)

        preview_text = text_result
        is_error = False
        logger.info("MCP tool call finished: tool=%s request_id=%s", name, jsonrpc_id)

        return {
            "content": [{"type": "text", "text": text_result}],
            "isError": False,
        }
    except Exception as exc:
        error_message = str(exc)
        preview_text = f"Error executing tool '{name}': {error_message}"
        _persist_tool_exception(name, exc)
        logger.exception("MCP tool call failed: tool=%s request_id=%s", name, jsonrpc_id)
        return {
            "content": [{"type": "text", "text": preview_text}],
            "isError": True,
        }
    finally:
        preview, size = _result_preview(preview_text)
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        persist_mcp_call_log(
            jsonrpc_id=jsonrpc_id,
            tool_call_name=name,
            params_sanitized=sanitized_args,
            is_error=is_error,
            error_message=error_message,
            result_preview=preview,
            result_size=size,
            duration_ms=elapsed_ms,
        )

