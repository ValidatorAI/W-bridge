from ..schema import Adr, AdrList
from ._client import prune, request


async def list_adrs(
    project_id: int | str,
    *,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> AdrList:
    return await request(
        "GET",
        f"/projects/{project_id}/adrs",
        params=prune({"active": active, "page": page, "per_page": per_page}),
    )


async def get_adr(project_id: int | str, adr_id: int | str) -> Adr:
    return await request("GET", f"/projects/{project_id}/adrs/{adr_id}")


async def create_adr(
    project_id: int | str,
    identifier: str,
    title: str,
    *,
    decision_date: str | None = None,
    status: str | None = None,
    file_path: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> Adr:
    """`status` is one of `proposed`, `accepted`, `deprecated`, `superseded`."""
    return await request(
        "POST",
        f"/projects/{project_id}/adrs",
        json=prune(
            {
                "identifier": identifier,
                "title": title,
                "decision_date": decision_date,
                "status": status,
                "file_path": file_path,
                "active": active,
                "position": position,
            }
        ),
    )


async def update_adr(
    project_id: int | str,
    adr_id: int | str,
    *,
    identifier: str | None = None,
    title: str | None = None,
    decision_date: str | None = None,
    status: str | None = None,
    file_path: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> Adr:
    return await request(
        "PATCH",
        f"/projects/{project_id}/adrs/{adr_id}",
        json=prune(
            {
                "identifier": identifier,
                "title": title,
                "decision_date": decision_date,
                "status": status,
                "file_path": file_path,
                "active": active,
                "position": position,
            }
        ),
    )


async def delete_adr(project_id: int | str, adr_id: int | str) -> None:
    return await request("DELETE", f"/projects/{project_id}/adrs/{adr_id}")
