from ..schema import CompanyStatusPeriod, CompanyStatusPeriodList
from ._client import prune, request


async def list_company_status_periods() -> CompanyStatusPeriodList:
    return await request("GET", "/company_status_periods")


async def get_company_status_period(period_id: int | str) -> CompanyStatusPeriod:
    return await request("GET", f"/company_status_periods/{period_id}")


async def get_current_company_status_period() -> CompanyStatusPeriod:
    return await request("GET", "/company_status_periods/current")


async def get_company_status_period_by_slug(slug: str) -> CompanyStatusPeriod:
    return await request("GET", f"/company_status_periods/by_slug/{slug}")


async def get_company_status_period_by_name(name: str) -> CompanyStatusPeriod:
    return await request("GET", "/company_status_periods/by_name", params={"name": name})


async def create_company_status_period(
    name: str,
    *,
    slug: str | None = None,
    current: bool | None = None,
    starts_on: str | None = None,
    ends_on: str | None = None,
    position: int | None = None,
) -> CompanyStatusPeriod:
    return await request(
        "POST",
        "/company_status_periods",
        json=prune(
            {
                "name": name,
                "slug": slug,
                "current": current,
                "starts_on": starts_on,
                "ends_on": ends_on,
                "position": position,
            }
        ),
    )


async def update_company_status_period(
    period_id: int | str,
    *,
    name: str | None = None,
    slug: str | None = None,
    current: bool | None = None,
    starts_on: str | None = None,
    ends_on: str | None = None,
    position: int | None = None,
) -> CompanyStatusPeriod:
    return await request(
        "PATCH",
        f"/company_status_periods/{period_id}",
        json=prune(
            {
                "name": name,
                "slug": slug,
                "current": current,
                "starts_on": starts_on,
                "ends_on": ends_on,
                "position": position,
            }
        ),
    )


async def delete_company_status_period(period_id: int | str) -> None:
    return await request("DELETE", f"/company_status_periods/{period_id}")
