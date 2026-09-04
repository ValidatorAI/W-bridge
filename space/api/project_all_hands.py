from typing import Any

from ._client import prune, request


async def list_all_hands_takeaways(
    project_id: int | str,
    *,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> dict[str, Any]:
    return await request(
        "GET",
        f"/projects/{project_id}/project_all_hands_takeaways",
        params=prune({"active": active, "page": page, "per_page": per_page}),
    )


async def get_all_hands_takeaway(project_id: int | str, takeaway_id: int | str) -> dict[str, Any]:
    return await request("GET", f"/projects/{project_id}/project_all_hands_takeaways/{takeaway_id}")


async def create_all_hands_takeaway(
    project_id: int | str,
    category: str,
    content: str,
    *,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]:
    return await request(
        "POST",
        f"/projects/{project_id}/project_all_hands_takeaways",
        json=prune(
            {
                "category": category,
                "content": content,
                "active": active,
                "position": position,
            }
        ),
    )


async def update_all_hands_takeaway(
    project_id: int | str,
    takeaway_id: int | str,
    *,
    category: str | None = None,
    content: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]:
    return await request(
        "PATCH",
        f"/projects/{project_id}/project_all_hands_takeaways/{takeaway_id}",
        json=prune(
            {
                "category": category,
                "content": content,
                "active": active,
                "position": position,
            }
        ),
    )


async def delete_all_hands_takeaway(project_id: int | str, takeaway_id: int | str) -> None:
    return await request(
        "DELETE", f"/projects/{project_id}/project_all_hands_takeaways/{takeaway_id}"
    )


async def list_all_hands_decisions(
    project_id: int | str,
    *,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> dict[str, Any]:
    return await request(
        "GET",
        f"/projects/{project_id}/project_all_hands_decisions",
        params=prune({"active": active, "page": page, "per_page": per_page}),
    )


async def get_all_hands_decision(project_id: int | str, decision_id: int | str) -> dict[str, Any]:
    return await request("GET", f"/projects/{project_id}/project_all_hands_decisions/{decision_id}")


async def create_all_hands_decision(
    project_id: int | str,
    title: str,
    *,
    basis: str | None = None,
    impact: str | None = None,
    badge: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]:
    return await request(
        "POST",
        f"/projects/{project_id}/project_all_hands_decisions",
        json=prune(
            {
                "title": title,
                "basis": basis,
                "impact": impact,
                "badge": badge,
                "active": active,
                "position": position,
            }
        ),
    )


async def update_all_hands_decision(
    project_id: int | str,
    decision_id: int | str,
    *,
    title: str | None = None,
    basis: str | None = None,
    impact: str | None = None,
    badge: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]:
    return await request(
        "PATCH",
        f"/projects/{project_id}/project_all_hands_decisions/{decision_id}",
        json=prune(
            {
                "title": title,
                "basis": basis,
                "impact": impact,
                "badge": badge,
                "active": active,
                "position": position,
            }
        ),
    )


async def delete_all_hands_decision(project_id: int | str, decision_id: int | str) -> None:
    return await request(
        "DELETE", f"/projects/{project_id}/project_all_hands_decisions/{decision_id}"
    )


async def list_all_hands_action_items(
    project_id: int | str,
    *,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> dict[str, Any]:
    return await request(
        "GET",
        f"/projects/{project_id}/project_all_hands_action_items",
        params=prune({"active": active, "page": page, "per_page": per_page}),
    )


async def get_all_hands_action_item(
    project_id: int | str, action_item_id: int | str
) -> dict[str, Any]:
    return await request(
        "GET", f"/projects/{project_id}/project_all_hands_action_items/{action_item_id}"
    )


async def create_all_hands_action_item(
    project_id: int | str,
    title: str,
    *,
    assignee_name: str | None = None,
    due_date: str | None = None,
    completed: bool | None = None,
    completed_at: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]:
    return await request(
        "POST",
        f"/projects/{project_id}/project_all_hands_action_items",
        json=prune(
            {
                "title": title,
                "assignee_name": assignee_name,
                "due_date": due_date,
                "completed": completed,
                "completed_at": completed_at,
                "active": active,
                "position": position,
            }
        ),
    )


async def update_all_hands_action_item(
    project_id: int | str,
    action_item_id: int | str,
    *,
    title: str | None = None,
    assignee_name: str | None = None,
    due_date: str | None = None,
    completed: bool | None = None,
    completed_at: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> dict[str, Any]:
    return await request(
        "PATCH",
        f"/projects/{project_id}/project_all_hands_action_items/{action_item_id}",
        json=prune(
            {
                "title": title,
                "assignee_name": assignee_name,
                "due_date": due_date,
                "completed": completed,
                "completed_at": completed_at,
                "active": active,
                "position": position,
            }
        ),
    )


async def delete_all_hands_action_item(project_id: int | str, action_item_id: int | str) -> None:
    return await request(
        "DELETE", f"/projects/{project_id}/project_all_hands_action_items/{action_item_id}"
    )
