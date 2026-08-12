import os
from collections.abc import AsyncIterator
from typing import Any

import httpx


# --- Configuration ---------------------------------------------------
# Point this at wherever your Hermes Agent instance is running.
# Examples:
#   Local:  "http://localhost:8642/v1"
#   Remote: "https://your-hermes-host.example.com/v1"
BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8642/v1").rstrip("/")

_base_uri_from_url = BASE_URL[:-3] if BASE_URL.endswith("/v1") else BASE_URL
BASE_URI = os.environ.get("BASE_URI", _base_uri_from_url).rstrip("/")

# Hermes needs an API key to authenticate with your underlying model provider.
API_KEY = os.environ.get("API_KEY", "your_api_key_here")
API_SERVER_KEY = os.environ.get("API_SERVER_KEY", API_KEY)

# Model name as configured/expected by your Hermes setup.
MODEL = os.environ.get("MODEL", "deepseek-v4-flash")

REQUEST_TIMEOUT = float(os.environ.get("HERMES_HTTP_TIMEOUT", "60"))



def _auth_headers(
    *,
    session_id: str | None = None,
    session_key: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, str]:
    headers: dict[str, str] = {
        "Authorization": f"Bearer {API_SERVER_KEY}",
        "Content-Type": "application/json",
    }
    if session_id:
        headers["X-Hermes-Session-Id"] = session_id
    if session_key:
        headers["X-Hermes-Session-Key"] = session_key
    if extra_headers:
        headers.update(extra_headers)
    return headers


def _clean_query(params: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in params.items() if v is not None}


async def _request(
    method: str,
    path: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    session_id: str | None = None,
    session_key: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    url = f"{BASE_URI}{path}"
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as http_client:
        response = await http_client.request(
            method,
            url,
            json=json,
            params=params,
            headers=_auth_headers(
                session_id=session_id,
                session_key=session_key,
                extra_headers=extra_headers,
            ),
        )
        response.raise_for_status()
        if not response.content:
            return {"status": "ok"}
        return response.json()


async def _stream_sse(
    method: str,
    path: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    session_id: str | None = None,
    session_key: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> AsyncIterator[str]:
    url = f"{BASE_URI}{path}"
    headers = _auth_headers(
        session_id=session_id,
        session_key=session_key,
        extra_headers=extra_headers,
    )
    headers["Accept"] = "text/event-stream"

    async with httpx.AsyncClient(timeout=None) as http_client:
        async with http_client.stream(
            method,
            url,
            json=json,
            params=params,
            headers=headers,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    yield line


# ----------------------------- Core OpenAI-compatible APIs -----------------------------
async def chat_completions(
    payload: dict[str, Any],
    *,
    session_id: str | None = None,
    session_key: str | None = None,
) -> dict[str, Any]:
    return await _request(
        "POST",
        "/v1/chat/completions",
        json=payload,
        session_id=session_id,
        session_key=session_key,
    )


async def responses_create(
    payload: dict[str, Any],
    *,
    session_id: str | None = None,
    session_key: str | None = None,
) -> dict[str, Any]:
    return await _request(
        "POST",
        "/v1/responses",
        json=payload,
        session_id=session_id,
        session_key=session_key,
    )


async def responses_get(response_id: str) -> dict[str, Any]:
    return await _request("GET", f"/v1/responses/{response_id}")


async def responses_delete(response_id: str) -> dict[str, Any]:
    return await _request("DELETE", f"/v1/responses/{response_id}")


async def models_list() -> dict[str, Any]:
    return await _request("GET", "/v1/models")


async def capabilities_get() -> dict[str, Any]:
    return await _request("GET", "/v1/capabilities")


async def skills_list() -> dict[str, Any]:
    return await _request("GET", "/v1/skills")


async def toolsets_list() -> dict[str, Any]:
    return await _request("GET", "/v1/toolsets")


# ----------------------------- Runs API -----------------------------
async def runs_create(
    payload: dict[str, Any],
    *,
    session_id: str | None = None,
    session_key: str | None = None,
) -> dict[str, Any]:
    return await _request(
        "POST",
        "/v1/runs",
        json=payload,
        session_id=session_id,
        session_key=session_key,
    )


async def runs_get(run_id: str) -> dict[str, Any]:
    return await _request("GET", f"/v1/runs/{run_id}")


async def runs_stop(run_id: str) -> dict[str, Any]:
    return await _request("POST", f"/v1/runs/{run_id}/stop", json={})


async def runs_approval(run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return await _request("POST", f"/v1/runs/{run_id}/approval", json=payload)


async def runs_events_stream(
    run_id: str,
    *,
    session_id: str | None = None,
    session_key: str | None = None,
) -> AsyncIterator[str]:
    async for line in _stream_sse(
        "GET",
        f"/v1/runs/{run_id}/events",
        session_id=session_id,
        session_key=session_key,
    ):
        yield line


# ----------------------------- Health -----------------------------
async def health_get() -> dict[str, Any]:
    return await _request("GET", "/health")


async def health_v1_get() -> dict[str, Any]:
    return await _request("GET", "/v1/health")


async def health_detailed_get() -> dict[str, Any]:
    return await _request("GET", "/health/detailed")


# ----------------------------- Sessions API -----------------------------
async def sessions_list(
    *,
    limit: int | None = None,
    offset: int | None = None,
    source: str | None = None,
    include_children: bool | None = None,
) -> dict[str, Any]:
    return await _request(
        "GET",
        "/api/sessions",
        params=_clean_query(
            {
                "limit": limit,
                "offset": offset,
                "source": source,
                "include_children": include_children,
            }
        ),
    )


async def sessions_create(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return await _request("POST", "/api/sessions", json=payload or {})


async def sessions_get(session_id: str) -> dict[str, Any]:
    return await _request("GET", f"/api/sessions/{session_id}")


async def sessions_update(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return await _request("PATCH", f"/api/sessions/{session_id}", json=payload)


async def sessions_delete(session_id: str) -> dict[str, Any]:
    return await _request("DELETE", f"/api/sessions/{session_id}")


async def sessions_messages(session_id: str) -> dict[str, Any]:
    return await _request("GET", f"/api/sessions/{session_id}/messages")


async def sessions_fork(session_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return await _request("POST", f"/api/sessions/{session_id}/fork", json=payload or {})


async def sessions_chat(session_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return await _request("POST", f"/api/sessions/{session_id}/chat", json=payload)


async def sessions_chat_stream(
    session_id: str,
    payload: dict[str, Any],
    *,
    session_key: str | None = None,
) -> AsyncIterator[str]:
    async for line in _stream_sse(
        "POST",
        f"/api/sessions/{session_id}/chat/stream",
        json=payload,
        session_key=session_key,
    ):
        yield line


# ----------------------------- Jobs API -----------------------------
async def jobs_list() -> dict[str, Any]:
    return await _request("GET", "/api/jobs")


async def jobs_create(payload: dict[str, Any]) -> dict[str, Any]:
    return await _request("POST", "/api/jobs", json=payload)


async def jobs_get(job_id: str) -> dict[str, Any]:
    return await _request("GET", f"/api/jobs/{job_id}")


async def jobs_update(job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    return await _request("PATCH", f"/api/jobs/{job_id}", json=payload)


async def jobs_delete(job_id: str) -> dict[str, Any]:
    return await _request("DELETE", f"/api/jobs/{job_id}")


async def jobs_pause(job_id: str) -> dict[str, Any]:
    return await _request("POST", f"/api/jobs/{job_id}/pause", json={})


async def jobs_resume(job_id: str) -> dict[str, Any]:
    return await _request("POST", f"/api/jobs/{job_id}/resume", json={})


async def jobs_run(job_id: str) -> dict[str, Any]:
    return await _request("POST", f"/api/jobs/{job_id}/run", json={})


# ----------------------------- Hermes-specific helpers -----------------------------
async def model_options_get(*, refresh: bool = False) -> dict[str, Any]:
    params = {"refresh": 1} if refresh else None
    return await _request("GET", "/api/model/options", params=params)

async def create_new_hermes_session(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create a new Hermes session with POST /api/sessions."""
    return await sessions_create(payload or {})

