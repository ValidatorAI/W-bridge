from typing import Any

from ._client import prune, request


async def list_knowledge_activities(
    project_id: int | str,
    *,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> dict[str, Any]:
    return await request(
        "GET",
        f"/projects/{project_id}/knowledge_activities",
        params=prune({"active": active, "page": page, "per_page": per_page}),
    )


async def get_knowledge_activity(project_id: int | str, activity_id: int | str) -> dict[str, Any]:
    return await request("GET", f"/projects/{project_id}/knowledge_activities/{activity_id}")


async def create_knowledge_activity(
    project_id: int | str,
    actor_name: str,
    action_text: str,
    *,
    actor_color: str | None = None,
    target_path: str | None = None,
    target_url: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]:
    return await request(
        "POST",
        f"/projects/{project_id}/knowledge_activities",
        json=prune(
            {
                "actor_name": actor_name,
                "action_text": action_text,
                "actor_color": actor_color,
                "target_path": target_path,
                "target_url": target_url,
                "active": active,
                "position": position,
            }
        ),
    )


async def update_knowledge_activity(
    project_id: int | str,
    activity_id: int | str,
    *,
    actor_name: str | None = None,
    action_text: str | None = None,
    actor_color: str | None = None,
    target_path: str | None = None,
    target_url: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]:
    return await request(
        "PATCH",
        f"/projects/{project_id}/knowledge_activities/{activity_id}",
        json=prune(
            {
                "actor_name": actor_name,
                "action_text": action_text,
                "actor_color": actor_color,
                "target_path": target_path,
                "target_url": target_url,
                "active": active,
                "position": position,
            }
        ),
    )


async def delete_knowledge_activity(project_id: int | str, activity_id: int | str) -> None:
    return await request("DELETE", f"/projects/{project_id}/knowledge_activities/{activity_id}")
