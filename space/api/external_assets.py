from ..schema import ExternalAsset, ExternalAssetList
from ._client import prune, request


async def list_external_assets(
    project_id: int | str,
    *,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> ExternalAssetList:
    return await request(
        "GET",
        f"/projects/{project_id}/external_assets",
        params=prune({"active": active, "page": page, "per_page": per_page}),
    )


async def get_external_asset(project_id: int | str, asset_id: int | str) -> ExternalAsset:
    return await request("GET", f"/projects/{project_id}/external_assets/{asset_id}")


async def create_external_asset(
    project_id: int | str,
    title: str,
    url: str,
    *,
    doc_type: str | None = None,
    icon: str | None = None,
    source_type: str | None = None,
    meta_text: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> ExternalAsset:
    """`source_type` is one of `internal_file`, `external_url`."""
    return await request(
        "POST",
        f"/projects/{project_id}/external_assets",
        json=prune(
            {
                "title": title,
                "url": url,
                "doc_type": doc_type,
                "icon": icon,
                "source_type": source_type,
                "meta_text": meta_text,
                "active": active,
                "position": position,
            }
        ),
    )


async def update_external_asset(
    project_id: int | str,
    asset_id: int | str,
    *,
    title: str | None = None,
    url: str | None = None,
    doc_type: str | None = None,
    icon: str | None = None,
    source_type: str | None = None,
    meta_text: str | None = None,
    active: bool | None = None,
    position: int | None = None,
) -> ExternalAsset:
    return await request(
        "PATCH",
        f"/projects/{project_id}/external_assets/{asset_id}",
        json=prune(
            {
                "title": title,
                "url": url,
                "doc_type": doc_type,
                "icon": icon,
                "source_type": source_type,
                "meta_text": meta_text,
                "active": active,
                "position": position,
            }
        ),
    )


async def delete_external_asset(project_id: int | str, asset_id: int | str) -> None:
    return await request("DELETE", f"/projects/{project_id}/external_assets/{asset_id}")
