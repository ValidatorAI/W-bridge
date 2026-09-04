from ..schema import ProjectUser, ProjectUserList
from ._client import prune, request


async def list_project_users(
    project_id: int | str,
    *,
    page: int | None = None,
    per_page: int | None = None,
) -> ProjectUserList:
    return await request(
        "GET",
        f"/projects/{project_id}/users",
        params=prune({"page": page, "per_page": per_page}),
    )


async def get_project_user(project_id: int | str, user_id: int | str) -> ProjectUser:
    return await request("GET", f"/projects/{project_id}/users/{user_id}")
