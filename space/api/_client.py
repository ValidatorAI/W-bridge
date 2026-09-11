import logging
import traceback
from typing import Any, BinaryIO

import httpx
from db.exception_store import persist_api_exception

from helpers.environment import (
    OUTPUT_BASE_URL,
    OUTPUT_EVENTS_TOKEN,
    OUTPUT_HTTP_TIMEOUT,
)


logger = logging.getLogger(__name__)

FileUpload = tuple[str, BinaryIO | bytes, str] | tuple[str, BinaryIO | bytes]

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(base_url=OUTPUT_BASE_URL, timeout=OUTPUT_HTTP_TIMEOUT)
    return _client


def _auth_headers(extra_headers: dict[str, str] | None = None) -> dict[str, str]:
    headers: dict[str, str] = {"Authorization": f"Bearer {OUTPUT_EVENTS_TOKEN}"}
    if extra_headers:
        headers.update(extra_headers)
    return headers


def prune(values: dict[str, Any] | None) -> dict[str, Any] | None:
    """Drop keys whose value is None so unset optional params are not sent."""
    if values is None:
        return None
    pruned = {key: value for key, value in values.items() if value is not None}
    return pruned or None


def _status_code_from_http_error(exc: httpx.HTTPError) -> int | None:
    response = getattr(exc, "response", None)
    if response is None:
        return None
    return response.status_code


def _persist_space_api_exception(
    *,
    method: str,
    endpoint: str,
    params: dict[str, Any] | None,
    json_payload: dict[str, Any] | None,
    data_payload: dict[str, Any] | None,
    file_fields: list[str] | None,
    exc: httpx.HTTPError,
) -> None:
    persist_api_exception(
        service_name="space_api",
        method=method,
        endpoint=endpoint,
        status_code=_status_code_from_http_error(exc),
        error_type=type(exc).__name__,
        error_message=str(exc),
        stored_exception=traceback.format_exc(),
        request_context={
            "params": params,
            "json": json_payload,
            "data": data_payload,
            "file_fields": file_fields,
        },
    )


async def request(
    method: str,
    path: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    files: dict[str, FileUpload] | None = None,
) -> Any:
    endpoint = f"/api{path}"
    try:
        response = await _get_client().request(
            method,
            endpoint,
            json=json,
            params=params,
            data=data,
            files=files,
            headers=_auth_headers(),
        )
        response.raise_for_status()
        if response.status_code == 204 or not response.content:
            return None
        return response.json()
    except httpx.HTTPError as exc:
        _persist_space_api_exception(
            method=method,
            endpoint=endpoint,
            params=params,
            json_payload=json,
            data_payload=data,
            file_fields=sorted(files.keys()) if files else None,
            exc=exc,
        )
        raise


async def request_bytes(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
) -> bytes:
    endpoint = f"/api{path}"
    try:
        response = await _get_client().request(
            method,
            endpoint,
            params=params,
            headers=_auth_headers(),
        )
        response.raise_for_status()
        return response.content
    except httpx.HTTPError as exc:
        _persist_space_api_exception(
            method=method,
            endpoint=endpoint,
            params=params,
            json_payload=None,
            data_payload=None,
            file_fields=None,
            exc=exc,
        )
        raise


async def aclose_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None
