import traceback
from typing import Any

from db.database import SessionLocal
from db.models import ApiException, McpCallLog


def persist_api_exception(
    *,
    service_name: str,
    method: str | None = None,
    endpoint: str | None = None,
    status_code: int | None = None,
    error_type: str,
    error_message: str,
    stored_exception: str | None = None,
    request_context: dict[str, Any] | None = None,
) -> None:
    session = SessionLocal()
    try:
        record = ApiException(
            service_name=service_name,
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            error_type=error_type,
            error_message=error_message,
            stored_exception=stored_exception or traceback.format_exc(),
            request_context=request_context,
        )
        session.add(record)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def persist_mcp_call_log(
    *,
    jsonrpc_id: str | None,
    tool_call_name: str,
    params_sanitized: dict[str, Any] | None,
    is_error: bool,
    error_message: str | None,
    result_preview: str | None,
    result_size: int | None,
    duration_ms: int | None,
) -> None:
    session = SessionLocal()
    try:
        record = McpCallLog(
            jsonrpc_id=jsonrpc_id,
            tool_call_name=tool_call_name,
            params_sanitized=params_sanitized,
            is_error=is_error,
            error_message=error_message,
            result_preview=result_preview,
            result_size=result_size,
            duration_ms=duration_ms,
        )
        session.add(record)
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()
