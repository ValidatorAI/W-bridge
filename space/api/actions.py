from typing import Any

from ._client import request


async def send_action(
    project_id: int | str,
    room_id: int | str,
    user_id: int | str,
    action_type: str,
) -> dict[str, Any]:
    """`action_type` is one of `typing_start`, `typing_stop` (`action` is reserved by Rails)."""
    return await request(
        "POST",
        f"/projects/{project_id}/rooms/{room_id}/actions",
        json={"user_id": user_id, "action_type": action_type},
    )
