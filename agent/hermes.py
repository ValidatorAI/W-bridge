from collections.abc import AsyncIterator
from typing import Any

import httpx
from hermpers.environment import API_SERVER_KEY, BASE_URI, HERMES_HTTP_TIMEOUT


# --- Configuration ---------------------------------------------------
REQUEST_TIMEOUT = HERMES_HTTP_TIMEOUT


def _normalize_profile(profile: str | None) -> str:
    if profile is None:
        return "default"
    cleaned = profile.strip().strip("/")
    return cleaned or "default"


def _build_url(path: str, profile: str | None = None) -> str:
    normalized_path = path if path.startswith("/") else f"/{path}"
    if normalized_path.startswith("/p/"):
        routed_path = normalized_path
    else:
        routed_path = f"/p/{_normalize_profile(profile)}{normalized_path}"
    return f"{BASE_URI}{routed_path}"



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
    profile: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    url = _build_url(path, profile)
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
    profile: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> AsyncIterator[str]:
    url = _build_url(path, profile)
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
    profile: str | None = None,
) -> dict[str, Any]:
    return await _request(
        "POST",
        "/v1/chat/completions",
        json=payload,
        session_id=session_id,
        session_key=session_key,
        profile=profile,
    )


async def responses_create(
    payload: dict[str, Any],
    *,
    session_id: str | None = None,
    session_key: str | None = None,
    profile: str | None = None,
) -> dict[str, Any]:
    return await _request(
        "POST",
        "/v1/responses",
        json=payload,
        session_id=session_id,
        session_key=session_key,
        profile=profile,
    )


async def responses_get(response_id: str, *, profile: str | None = None) -> dict[str, Any]:
    return await _request("GET", f"/v1/responses/{response_id}", profile=profile)


async def responses_delete(response_id: str, *, profile: str | None = None) -> dict[str, Any]:
    return await _request("DELETE", f"/v1/responses/{response_id}", profile=profile)


async def models_list(*, profile: str | None = None) -> dict[str, Any]:
    return await _request("GET", "/v1/models", profile=profile)


async def capabilities_get(*, profile: str | None = None) -> dict[str, Any]:
    return await _request("GET", "/v1/capabilities", profile=profile)


async def skills_list(*, profile: str | None = None) -> dict[str, Any]:
    return await _request("GET", "/v1/skills", profile=profile)


async def toolsets_list(*, profile: str | None = None) -> dict[str, Any]:
    return await _request("GET", "/v1/toolsets", profile=profile)


# ----------------------------- Runs API -----------------------------
async def runs_create(
    payload: dict[str, Any],
    *,
    session_id: str | None = None,
    session_key: str | None = None,
    profile: str | None = None,
) -> dict[str, Any]:
    return await _request(
        "POST",
        "/v1/runs",
        json=payload,
        session_id=session_id,
        session_key=session_key,
        profile=profile,
    )


async def runs_get(run_id: str, *, profile: str | None = None) -> dict[str, Any]:
    return await _request("GET", f"/v1/runs/{run_id}", profile=profile)


async def runs_stop(run_id: str, *, profile: str | None = None) -> dict[str, Any]:
    return await _request("POST", f"/v1/runs/{run_id}/stop", json={}, profile=profile)


async def runs_approval(run_id: str, payload: dict[str, Any], *, profile: str | None = None) -> dict[str, Any]:
    return await _request("POST", f"/v1/runs/{run_id}/approval", json=payload, profile=profile)


async def runs_events_stream(
    run_id: str,
    *,
    session_id: str | None = None,
    session_key: str | None = None,
    profile: str | None = None,
) -> AsyncIterator[str]:
    async for line in _stream_sse(
        "GET",
        f"/v1/runs/{run_id}/events",
        session_id=session_id,
        session_key=session_key,
        profile=profile,
    ):
        yield line


# ----------------------------- Health -----------------------------
async def health_get(*, profile: str | None = None) -> dict[str, Any]:
    return await _request("GET", "/health", profile=profile)


async def health_v1_get(*, profile: str | None = None) -> dict[str, Any]:
    return await _request("GET", "/v1/health", profile=profile)


async def health_detailed_get(*, profile: str | None = None) -> dict[str, Any]:
    return await _request("GET", "/health/detailed", profile=profile)


# ----------------------------- Sessions API -----------------------------
async def sessions_list(
    *,
    limit: int | None = None,
    offset: int | None = None,
    source: str | None = None,
    include_children: bool | None = None,
    profile: str | None = None,
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
        profile=profile,
    )


async def sessions_create(
    payload: dict[str, Any] | None = None,
    *,
    profile: str | None = None,
) -> dict[str, Any]:
    return await _request("POST", "/api/sessions", json=payload or {}, profile=profile)


async def sessions_get(session_id: str, *, profile: str | None = None) -> dict[str, Any]:
    return await _request("GET", f"/api/sessions/{session_id}", profile=profile)


async def sessions_update(
    session_id: str,
    payload: dict[str, Any],
    *,
    profile: str | None = None,
) -> dict[str, Any]:
    return await _request("PATCH", f"/api/sessions/{session_id}", json=payload, profile=profile)


async def sessions_delete(session_id: str, *, profile: str | None = None) -> dict[str, Any]:
    return await _request("DELETE", f"/api/sessions/{session_id}", profile=profile)


async def sessions_messages(session_id: str, *, profile: str | None = None) -> dict[str, Any]:
    return await _request("GET", f"/api/sessions/{session_id}/messages", profile=profile)


async def sessions_fork(
    session_id: str,
    payload: dict[str, Any] | None = None,
    *,
    profile: str | None = None,
) -> dict[str, Any]:
    return await _request("POST", f"/api/sessions/{session_id}/fork", json=payload or {}, profile=profile)


async def sessions_chat(
    session_id: str,
    payload: dict[str, Any],
    *,
    profile: str | None = None,
) -> dict[str, Any]:
    return await _request("POST", f"/api/sessions/{session_id}/chat", json=payload, profile=profile)


async def sessions_chat_stream(
    session_id: str,
    payload: dict[str, Any],
    *,
    session_key: str | None = None,
    profile: str | None = None,
) -> AsyncIterator[str]:
    async for line in _stream_sse(
        "POST",
        f"/api/sessions/{session_id}/chat/stream",
        json=payload,
        session_key=session_key,
        profile=profile,
    ):
        yield line


# ----------------------------- Jobs API -----------------------------
async def jobs_list(*, profile: str | None = None) -> dict[str, Any]:
    return await _request("GET", "/api/jobs", profile=profile)


async def jobs_create(payload: dict[str, Any], *, profile: str | None = None) -> dict[str, Any]:
    return await _request("POST", "/api/jobs", json=payload, profile=profile)


async def jobs_get(job_id: str, *, profile: str | None = None) -> dict[str, Any]:
    return await _request("GET", f"/api/jobs/{job_id}", profile=profile)


async def jobs_update(
    job_id: str,
    payload: dict[str, Any],
    *,
    profile: str | None = None,
) -> dict[str, Any]:
    return await _request("PATCH", f"/api/jobs/{job_id}", json=payload, profile=profile)


async def jobs_delete(job_id: str, *, profile: str | None = None) -> dict[str, Any]:
    return await _request("DELETE", f"/api/jobs/{job_id}", profile=profile)


async def jobs_pause(job_id: str, *, profile: str | None = None) -> dict[str, Any]:
    return await _request("POST", f"/api/jobs/{job_id}/pause", json={}, profile=profile)


async def jobs_resume(job_id: str, *, profile: str | None = None) -> dict[str, Any]:
    return await _request("POST", f"/api/jobs/{job_id}/resume", json={}, profile=profile)


async def jobs_run(job_id: str, *, profile: str | None = None) -> dict[str, Any]:
    return await _request("POST", f"/api/jobs/{job_id}/run", json={}, profile=profile)


# ----------------------------- Hermes-specific helpers -----------------------------
async def model_options_get(*, refresh: bool = False, profile: str | None = None) -> dict[str, Any]:
    params = {"refresh": 1} if refresh else None
    return await _request("GET", "/api/model/options", params=params, profile=profile)

async def create_new_hermes_session(
    payload: dict[str, Any] | None = None,
    *,
    profile: str | None = None,
) -> dict[str, Any]:
    """Create a new Hermes session with POST /api/sessions."""
    return await sessions_create(payload or {}, profile=profile)

