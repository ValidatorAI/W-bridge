from typing import Any

from ..schema import ApprovalRequest, ApprovalRequestList
from ._client import prune, request


def _approval_request_path(
    room_id: int | str,
    project_id: int | str | None = None,
    approval_request_id: int | str | None = None,
) -> str:
    base = (
        f"/projects/{project_id}/rooms/{room_id}/approval_requests"
        if project_id is not None
        else f"/rooms/{room_id}/approval_requests"
    )
    if approval_request_id is not None:
        base = f"{base}/{approval_request_id}"
    return base


async def list_approval_requests(
    project_id: int | str | None,
    room_id: int | str,
    *,
    page: int | None = None,
    per_page: int | None = None,
) -> ApprovalRequestList:
    return await request(
        "GET",
        _approval_request_path(room_id, project_id),
        params=prune({"page": page, "per_page": per_page}),
    )


async def get_approval_request(
    project_id: int | str | None,
    room_id: int | str,
    approval_request_id: int | str,
) -> ApprovalRequest:
    return await request(
        "GET",
        _approval_request_path(room_id, project_id, approval_request_id),
    )


async def create_approval_request(
    project_id: int | str | None,
    room_id: int | str,
    *,
    request_type: str | None = None,
    status: str | None = None,
    message_id: int | str | None = None,
    agent_id: int | str | None = None,
    requested_at: str | None = None,
    resolved_at: str | None = None,
    resolved_by_id: int | str | None = None,
    payload: dict[str, Any] | None = None,
) -> ApprovalRequest:
    return await request(
        "POST",
        _approval_request_path(room_id, project_id),
        json=prune(
            {
                "request_type": request_type,
                "status": status,
                "message_id": message_id,
                "agent_id": agent_id,
                "requested_at": requested_at,
                "resolved_at": resolved_at,
                "resolved_by_id": resolved_by_id,
                "payload": payload,
            }
        ),
    )


async def update_approval_request(
    project_id: int | str | None,
    room_id: int | str,
    approval_request_id: int | str,
    *,
    request_type: str | None = None,
    status: str | None = None,
    message_id: int | str | None = None,
    agent_id: int | str | None = None,
    requested_at: str | None = None,
    resolved_at: str | None = None,
    resolved_by_id: int | str | None = None,
    payload: dict[str, Any] | None = None,
) -> ApprovalRequest:
    return await request(
        "PATCH",
        _approval_request_path(room_id, project_id, approval_request_id),
        json=prune(
            {
                "request_type": request_type,
                "status": status,
                "message_id": message_id,
                "agent_id": agent_id,
                "requested_at": requested_at,
                "resolved_at": resolved_at,
                "resolved_by_id": resolved_by_id,
                "payload": payload,
            }
        ),
    )


async def delete_approval_request(
    project_id: int | str | None,
    room_id: int | str,
    approval_request_id: int | str,
) -> None:
    return await request(
        "DELETE",
        _approval_request_path(room_id, project_id, approval_request_id),
    )
