from ._client import request
from .types import Project


async def list_projects() -> list[Project]:
    return await request("GET", "/projects")


async def get_project(project: int | str) -> Project:
    """`project` may be the numeric id or the project slug."""
    return await request("GET", f"/projects/{project}")
