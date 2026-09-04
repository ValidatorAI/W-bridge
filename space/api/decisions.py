from ._client import prune, request
from .types import ApprovalRequest


async def create_decision(
    project_id: int | str,
    room_id: int | str,
    user_id: int | str,
    approval_request_id: int | str,
    decision: str,
    *,
    note: str | None = None,
) -> ApprovalRequest:
    """`decision` is one of `approve`, `confirm`, `deny`, `cancel`."""
    return await request(
        "POST",
        f"/projects/{project_id}/rooms/{room_id}/decisions",
        json=prune(
            {
                "user_id": user_id,
                "approval_request_id": approval_request_id,
                "decision": decision,
                "note": note,
            }
        ),
    )
