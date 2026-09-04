import logging
from typing import Any, BinaryIO

import httpx

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


async def request(
    method: str,
    path: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    files: dict[str, FileUpload] | None = None,
) -> Any:
    response = await _get_client().request(
        method,
        f"/api{path}",
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


async def request_bytes(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
) -> bytes:
    response = await _get_client().request(
        method,
        f"/api{path}",
        params=params,
        headers=_auth_headers(),
    )
    response.raise_for_status()
    return response.content


async def aclose_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None
