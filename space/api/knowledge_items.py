from typing import Any

from ._client import prune, request


async def list_knowledge_items(
    project_id: int | str,
    *,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> dict[str, Any]:
    return await request(
        "GET",
        f"/projects/{project_id}/knowledge_items",
        params=prune({"active": active, "page": page, "per_page": per_page}),
    )


async def get_knowledge_item(project_id: int | str, item_id: int | str) -> dict[str, Any]:
    return await request("GET", f"/projects/{project_id}/knowledge_items/{item_id}")


async def create_knowledge_item(
    project_id: int | str,
    title: str,
    description: str,
    *,
    badge: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]:
    return await request(
        "POST",
        f"/projects/{project_id}/knowledge_items",
        json=prune(
            {
                "title": title,
                "description": description,
                "badge": badge,
                "active": active,
                "position": position,
            }
        ),
    )


async def update_knowledge_item(
    project_id: int | str,
    item_id: int | str,
    *,
    title: str | None = None,
    description: str | None = None,
    badge: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]:
    return await request(
        "PATCH",
        f"/projects/{project_id}/knowledge_items/{item_id}",
        json=prune(
            {
                "title": title,
                "description": description,
                "badge": badge,
                "active": active,
                "position": position,
            }
        ),
    )


async def delete_knowledge_item(project_id: int | str, item_id: int | str) -> None:
    return await request("DELETE", f"/projects/{project_id}/knowledge_items/{item_id}")
