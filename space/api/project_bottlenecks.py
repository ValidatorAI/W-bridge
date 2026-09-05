from ..schema import ProjectBottleneck, ProjectBottleneckList
from ._client import prune, request


async def list_project_bottlenecks(
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
    active: bool | None = None,
    severity: str | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> ProjectBottleneckList:
    return await request(
        "GET",
        f"/projects/{project_id}/project_bottlenecks",
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
                "active": active,
                "severity": severity,
                "page": page,
                "per_page": per_page,
            }
        ),
    )


async def get_project_bottleneck(
    project_id: int | str, bottleneck_id: int | str
) -> ProjectBottleneck:
    return await request(
        "GET", f"/projects/{project_id}/project_bottlenecks/{bottleneck_id}"
    )


async def create_project_bottleneck(
    project_id: int | str,
    title: str,
    *,
    description: str | None = None,
    severity: str | None = None,
    position: int | None = None,
    resolved_at: str | None = None,
) -> ProjectBottleneck:
    return await request(
        "POST",
        f"/projects/{project_id}/project_bottlenecks",
        json=prune(
            {
                "title": title,
                "description": description,
                "severity": severity,
                "position": position,
                "resolved_at": resolved_at,
            }
        ),
    )


async def update_project_bottleneck(
    project_id: int | str,
    bottleneck_id: int | str,
    *,
    title: str | None = None,
    description: str | None = None,
    severity: str | None = None,
    position: int | None = None,
    resolved_at: str | None = None,
    resolved: bool | None = None,
) -> ProjectBottleneck:
    return await request(
        "PATCH",
        f"/projects/{project_id}/project_bottlenecks/{bottleneck_id}",
        json=prune(
            {
                "title": title,
                "description": description,
                "severity": severity,
                "position": position,
                "resolved_at": resolved_at,
                "resolved": resolved,
            }
        ),
    )


async def delete_project_bottleneck(
    project_id: int | str, bottleneck_id: int | str
) -> None:
    return await request(
        "DELETE", f"/projects/{project_id}/project_bottlenecks/{bottleneck_id}"
    )
