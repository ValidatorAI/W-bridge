from typing import Any

from ..schema import Message, MessageList
from ._client import FileUpload, prune, request, request_bytes


def _body_kwargs(fields: dict[str, Any], attachment: FileUpload | None) -> dict[str, Any]:
    if attachment is None:
        return {"json": prune(fields)}
    return {"data": prune(fields), "files": {"attachment": attachment}}


def _room_message_path(
    room_id: int | str,
    project_id: int | str | None = None,
    message_id: int | str | None = None,
    suffix: str = "",
) -> str:
    base = (
        f"/projects/{project_id}/rooms/{room_id}/messages"
        if project_id is not None
        else f"/rooms/{room_id}/messages"
    )
    if message_id is not None:
        base = f"{base}/{message_id}"
    if suffix:
        base = f"{base}/{suffix}"
    return base


async def list_messages(
    project_id: int | str | None,
    room_id: int | str,
    *,
    page: int | None = None,
    per_page: int | None = None,
) -> MessageList:
    return await request(
        "GET",
        _room_message_path(room_id, project_id),
        params=prune({"page": page, "per_page": per_page}),
    )


async def create_message(
    project_id: int | str | None,
    room_id: int | str,
    user_id: int | str,
    *,
    body: str | None = None,
    attachment: FileUpload | None = None,
) -> Message:
    """At least one of `body` or `attachment` is required."""
    return await request(
        "POST",
        _room_message_path(room_id, project_id),
        **_body_kwargs({"user_id": user_id, "body": body}, attachment),
    )


async def get_message(
    project_id: int | str | None,
    room_id: int | str,
    message_id: int | str,
) -> Message:
    return await request("GET", _room_message_path(room_id, project_id, message_id))


async def update_message(
    project_id: int | str | None,
    room_id: int | str,
    message_id: int | str,
    *,
    body: str | None = None,
    attachment: FileUpload | None = None,
) -> Message:
    """At least one of `body` or `attachment` is required."""
    return await request(
        "PATCH",
        _room_message_path(room_id, project_id, message_id),
        **_body_kwargs({"body": body}, attachment),
    )


async def delete_message(
    project_id: int | str | None,
    room_id: int | str,
    message_id: int | str,
) -> None:
    return await request("DELETE", _room_message_path(room_id, project_id, message_id))


async def download_message_attachment(
    project_id: int | str | None,
    room_id: int | str,
    message_id: int | str,
    *,
    disposition: str | None = None,
) -> bytes:
    return await request_bytes(
        "GET",
        _room_message_path(room_id, project_id, message_id, "attachment"),
        params=prune({"disposition": disposition}),
    )


async def get_message_by_id(message_id: int | str) -> Message:
    return await request("GET", f"/messages/{message_id}")


async def update_message_by_id(
    message_id: int | str,
    *,
    body: str | None = None,
    attachment: FileUpload | None = None,
) -> Message:
    """At least one of `body` or `attachment` is required."""
    return await request(
        "PATCH",
        f"/messages/{message_id}",
        **_body_kwargs({"body": body}, attachment),
    )


async def delete_message_by_id(message_id: int | str) -> None:
    return await request("DELETE", f"/messages/{message_id}")


async def download_attachment_by_id(
    message_id: int | str,
    *,
    disposition: str | None = None,
) -> bytes:
    return await request_bytes(
        "GET",
        f"/messages/{message_id}/attachment",
        params=prune({"disposition": disposition}),
    )
