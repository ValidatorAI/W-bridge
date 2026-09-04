from ..schema import CompanyStatusItem, CompanyStatusItemList
from ._client import prune, request


async def list_company_status_items(
    *,
    company_status_period_id: int | str | None = None,
    project_id: int | str | None = None,
    category: str | None = None,
    status: str | None = None,
    health: str | None = None,
    badge: str | None = None,
    owner_name: str | None = None,
    source_type: str | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> CompanyStatusItemList:
    return await request(
        "GET",
        "/company_status_items",
        params=prune(
            {
                "company_status_period_id": company_status_period_id,
                "project_id": project_id,
                "category": category,
                "status": status,
                "health": health,
                "badge": badge,
                "owner_name": owner_name,
                "source_type": source_type,
                "page": page,
                "per_page": per_page,
            }
        ),
    )


async def get_company_status_item(item_id: int | str) -> CompanyStatusItem:
    return await request("GET", f"/company_status_items/{item_id}")


async def list_company_status_items_by_period(
    company_status_period_id: int | str,
) -> CompanyStatusItemList:
    return await request(
        "GET",
        "/company_status_items/by_period",
        params={"company_status_period_id": company_status_period_id},
    )


async def filter_company_status_items(
    *,
    company_status_period_id: int | str | None = None,
    project_id: int | str | None = None,
    category: str | None = None,
    status: str | None = None,
    health: str | None = None,
    badge: str | None = None,
    owner_name: str | None = None,
    source_type: str | None = None,
    created_at_gt: str | None = None,
    created_at_lt: str | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> CompanyStatusItemList:
    return await request(
        "GET",
        "/company_status_items/advanced_filter",
        params=prune(
            {
                "company_status_period_id": company_status_period_id,
                "project_id": project_id,
                "category": category,
                "status": status,
                "health": health,
                "badge": badge,
                "owner_name": owner_name,
                "source_type": source_type,
                "created_at_gt": created_at_gt,
                "created_at_lt": created_at_lt,
                "page": page,
                "per_page": per_page,
            }
        ),
    )


async def create_company_status_item(
    company_status_period_id: int | str,
    title: str,
    category: str,
    *,
    status: str | None = None,
    health: str | None = None,
    badge: str | None = None,
    summary: str | None = None,
    details: str | None = None,
    owner_name: str | None = None,
    position: int | None = None,
    project_id: int | str | None = None,
) -> CompanyStatusItem:
    return await request(
        "POST",
        "/company_status_items",
        json=prune(
            {
                "company_status_period_id": company_status_period_id,
                "title": title,
                "category": category,
                "status": status,
                "health": health,
                "badge": badge,
                "summary": summary,
                "details": details,
                "owner_name": owner_name,
                "position": position,
                "project_id": project_id,
            }
        ),
    )


async def update_company_status_item(
    item_id: int | str,
    *,
    company_status_period_id: int | str | None = None,
    title: str | None = None,
    category: str | None = None,
    status: str | None = None,
    health: str | None = None,
    badge: str | None = None,
    summary: str | None = None,
    details: str | None = None,
    owner_name: str | None = None,
    position: int | None = None,
    project_id: int | str | None = None,
) -> CompanyStatusItem:
    return await request(
        "PATCH",
        f"/company_status_items/{item_id}",
        json=prune(
            {
                "company_status_period_id": company_status_period_id,
                "title": title,
                "category": category,
                "status": status,
                "health": health,
                "badge": badge,
                "summary": summary,
                "details": details,
                "owner_name": owner_name,
                "position": position,
                "project_id": project_id,
            }
        ),
    )


async def delete_company_status_item(item_id: int | str) -> None:
    return await request("DELETE", f"/company_status_items/{item_id}")
