from ..schema import ProjectTodo, ProjectTodoList
from ._client import prune, request


async def list_project_todos(
    project_id: int | str,
    *,
    created_at_gt: str | None = None,
    created_at_gte: str | None = None,
    created_at_lt: str | None = None,
    created_at_lte: str | None = None,
    from_: str | None = None,
    starts_at: str | None = None,
    start_date: str | None = None,
    to: str | None = None,
    ends_at: str | None = None,
    end_date: str | None = None,
    completed: bool | None = None,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> ProjectTodoList:
    return await request(
        "GET",
        f"/projects/{project_id}/project_todos",
        params=prune(
            {
                "created_at_gt": created_at_gt,
                "created_at_gte": created_at_gte,
                "created_at_lt": created_at_lt,
                "created_at_lte": created_at_lte,
                "from": from_,
                "starts_at": starts_at,
                "start_date": start_date,
                "to": to,
                "ends_at": ends_at,
                "end_date": end_date,
                "completed": completed,
                "active": active,
                "page": page,
                "per_page": per_page,
            }
        ),
    )


async def get_project_todo(
    project_id: int | str, todo_id: int | str
) -> ProjectTodo:
    return await request(
        "GET", f"/projects/{project_id}/project_todos/{todo_id}"
    )


async def create_project_todo(
    project_id: int | str,
    title: str,
    *,
    meta_text: str | None = None,
    completed: bool | None = None,
    completed_at: str | None = None,
    position: int | None = None,
) -> ProjectTodo:
    return await request(
        "POST",
        f"/projects/{project_id}/project_todos",
        json=prune(
            {
                "title": title,
                "meta_text": meta_text,
                "completed": completed,
                "completed_at": completed_at,
                "position": position,
            }
        ),
    )


async def update_project_todo(
    project_id: int | str,
    todo_id: int | str,
    *,
    title: str | None = None,
    meta_text: str | None = None,
    completed: bool | None = None,
    completed_at: str | None = None,
    position: int | None = None,
) -> ProjectTodo:
    return await request(
        "PATCH",
        f"/projects/{project_id}/project_todos/{todo_id}",
        json=prune(
            {
                "title": title,
                "meta_text": meta_text,
                "completed": completed,
                "completed_at": completed_at,
                "position": position,
            }
        ),
    )


async def delete_project_todo(
    project_id: int | str, todo_id: int | str
) -> None:
    return await request(
        "DELETE", f"/projects/{project_id}/project_todos/{todo_id}"
    )
