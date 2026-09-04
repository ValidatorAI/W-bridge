from typing import Any

from ..schema import DirectoryItem, DirectoryItemList
from ._client import FileUpload, prune, request


def _body_kwargs(fields: dict[str, Any], file: FileUpload | None) -> dict[str, Any]:
    if file is None:
        return {"json": prune(fields)}
    return {"data": prune(fields), "files": {"file": file}}


async def list_directory_items(
    project_id: int | str,
    *,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> DirectoryItemList:
    return await request(
        "GET",
        f"/projects/{project_id}/directory_items",
        params=prune({"active": active, "page": page, "per_page": per_page}),
    )


async def get_directory_item(project_id: int | str, item_id: int | str) -> DirectoryItem:
    return await request("GET", f"/projects/{project_id}/directory_items/{item_id}")


async def create_directory_item(
    project_id: int | str,
    *,
    name: str | None = None,
    item_type: str | None = None,
    file_path: str | None = None,
    parent_id: int | str | None = None,
    content: str | None = None,
    active: bool | None = None,
    position: int | None = None,
    file: FileUpload | None = None,
) -> DirectoryItem:
    """`item_type` is one of `file`, `directory`; `file` is saved under the project storage dir."""
    return await request(
        "POST",
        f"/projects/{project_id}/directory_items",
        **_body_kwargs(
            {
                "name": name,
                "item_type": item_type,
                "file_path": file_path,
                "parent_id": parent_id,
                "content": content,
                "active": active,
                "position": position,
            },
            file,
        ),
    )


async def update_directory_item(
    project_id: int | str,
    item_id: int | str,
    *,
    name: str | None = None,
    item_type: str | None = None,
    file_path: str | None = None,
    parent_id: int | str | None = None,
    content: str | None = None,
    active: bool | None = None,
    position: int | None = None,
    file: FileUpload | None = None,
) -> DirectoryItem:
    return await request(
        "PATCH",
        f"/projects/{project_id}/directory_items/{item_id}",
        **_body_kwargs(
            {
                "name": name,
                "item_type": item_type,
                "file_path": file_path,
                "parent_id": parent_id,
                "content": content,
                "active": active,
                "position": position,
            },
            file,
        ),
    )


async def delete_directory_item(project_id: int | str, item_id: int | str) -> None:
    return await request("DELETE", f"/projects/{project_id}/directory_items/{item_id}")
