from ..schema import Task, TaskList
from ._client import prune, request


async def list_tasks(
    *,
    room_id: int | str | None = None,
    project_id: int | str | None = None,
    grand_parent_id: int | str | None = None,
    added_to_kanban: bool | None = None,
    runned: bool | None = None,
) -> TaskList:
    return await request(
        "GET",
        "/tasks",
        params=prune(
            {
                "room_id": room_id,
                "project_id": project_id,
                "grand_parent_id": grand_parent_id,
                "added_to_kanban": added_to_kanban,
                "runned": runned,
            }
        ),
    )


async def get_task(task_id: int | str) -> Task:
    return await request("GET", f"/tasks/{task_id}")


async def get_all_children_tasks(task_id: int | str) -> TaskList:
    return await request("GET", f"/tasks/{task_id}/children")


async def get_all_parent_tasks(task_id: int | str) -> TaskList:
    return await request("GET", f"/tasks/{task_id}/parents")


async def get_task_children(task_id: int | str) -> TaskList:
    return await get_all_children_tasks(task_id)


async def get_task_parents(task_id: int | str) -> TaskList:
    return await get_all_parent_tasks(task_id)


async def create_task(
    description: str,
    *,
    adder_profile: str | None = None,
    token_used: int | None = None,
    token_budget: int | None = None,
    usd_usage: float | None = None,
    usd_used: float | None = None,
    usd_budget: float | None = None,
    room_id: int | str | None = None,
    project_id: int | str | None = None,
    assigneee_profile: str | None = None,
    added_to_kanban: bool | None = None,
    runned: bool | None = None,
    parent_task_id: int | str | None = None,
    grand_parent_id: int | str | None = None,
    importance: int | None = None,
    level: int | None = None,
) -> Task:
    return await request(
        "POST",
        "/tasks",
        json=prune(
            {
                "adder_profile": adder_profile,
                "token_used": token_used,
                "token_budget": token_budget,
                "usd_usage": usd_usage,
                "usd_used": usd_used,
                "usd_budget": usd_budget,
                "room_id": room_id,
                "project_id": project_id,
                "description": description,
                "assigneee_profile": assigneee_profile,
                "added_to_kanban": added_to_kanban,
                "runned": runned,
                "parent_task_id": parent_task_id,
                "grand_parent_id": grand_parent_id,
                "importance": importance,
                "level": level,
            }
        ),
    )


async def update_task(
    task_id: int | str,
    *,
    adder_profile: str | None = None,
    token_used: int | None = None,
    token_budget: int | None = None,
    usd_usage: float | None = None,
    usd_used: float | None = None,
    usd_budget: float | None = None,
    room_id: int | str | None = None,
    project_id: int | str | None = None,
    description: str | None = None,
    assigneee_profile: str | None = None,
    added_to_kanban: bool | None = None,
    runned: bool | None = None,
    parent_task_id: int | str | None = None,
    grand_parent_id: int | str | None = None,
    importance: int | None = None,
    level: int | None = None,
) -> Task:
    return await request(
        "PATCH",
        f"/tasks/{task_id}",
        json=prune(
            {
                "adder_profile": adder_profile,
                "token_used": token_used,
                "token_budget": token_budget,
                "usd_usage": usd_usage,
                "usd_used": usd_used,
                "usd_budget": usd_budget,
                "room_id": room_id,
                "project_id": project_id,
                "description": description,
                "assigneee_profile": assigneee_profile,
                "added_to_kanban": added_to_kanban,
                "runned": runned,
                "parent_task_id": parent_task_id,
                "grand_parent_id": grand_parent_id,
                "importance": importance,
                "level": level,
            }
        ),
    )


async def delete_task(task_id: int | str) -> None:
    return await request("DELETE", f"/tasks/{task_id}")


async def task_cost(
    task_id: int | str,
    *,
    token_used: int | None = None,
    usd_used: float | None = None,
) -> Task:
    return await request(
        "PATCH",
        "/tasks/task_cost",
        json=prune(
            {
                "task_id": task_id,
                "token_used": token_used,
                "usd_used": usd_used,
            }
        ),
    )


async def update_task_cost(
    task_id: int | str,
    *,
    token_used: int | None = None,
    usd_used: float | None = None,
) -> Task:
    return await task_cost(task_id=task_id, token_used=token_used, usd_used=usd_used)
