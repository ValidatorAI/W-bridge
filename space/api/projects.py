from typing import Any

from ._client import request


async def list_projects() -> list[dict[str, Any]]:
    return await request("GET", "/projects")


async def get_project(project: int | str) -> dict[str, Any]:
    """`project` may be the numeric id or the project slug."""
    return await request("GET", f"/projects/{project}")
