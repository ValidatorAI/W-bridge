from ..schema import ProjectMilestone, ProjectMilestoneList
from ._client import prune, request


async def list_project_milestones(
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
    page: int | None = None,
    per_page: int | None = None,
) -> ProjectMilestoneList:
    return await request(
        "GET",
        f"/projects/{project_id}/project_milestones",
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
                "page": page,
                "per_page": per_page,
            }
        ),
    )


async def get_project_milestone(
    project_id: int | str, milestone_id: int | str
) -> ProjectMilestone:
    return await request(
        "GET", f"/projects/{project_id}/project_milestones/{milestone_id}"
    )


async def create_project_milestone(
    project_id: int | str,
    title: str,
    *,
    description: str | None = None,
    icon: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> ProjectMilestone:
    return await request(
        "POST",
        f"/projects/{project_id}/project_milestones",
        json=prune(
            {
                "title": title,
                "description": description,
                "icon": icon,
                "active": active,
                "position": position,
            }
        ),
    )


async def update_project_milestone(
    project_id: int | str,
    milestone_id: int | str,
    *,
    title: str | None = None,
    description: str | None = None,
    icon: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> ProjectMilestone:
    return await request(
        "PATCH",
        f"/projects/{project_id}/project_milestones/{milestone_id}",
        json=prune(
            {
                "title": title,
                "description": description,
                "icon": icon,
                "active": active,
                "position": position,
            }
        ),
    )


async def delete_project_milestone(
    project_id: int | str, milestone_id: int | str
) -> None:
    return await request(
        "DELETE", f"/projects/{project_id}/project_milestones/{milestone_id}"
    )
