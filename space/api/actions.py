from ..schema import ActionAck
from ._client import request


async def send_action(
    project_id: int | str | None,
    room_id: int | str,
    user_id: int | str,
    action_type: str,
) -> ActionAck:
    """`action_type` is one of `typing_start`, `typing_stop` (`action` is reserved by Rails)."""
    path = (
        f"/projects/{project_id}/rooms/{room_id}/actions"
        if project_id is not None
        else f"/rooms/{room_id}/actions"
    )
    return await request(
        "POST",
        path,
        json={"user_id": user_id, "action_type": action_type},
    )
