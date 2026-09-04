from typing import Any

from ..schema import ObsidianNote, ObsidianNoteList
from ._client import FileUpload, prune, request


def _body_kwargs(fields: dict[str, Any], file: FileUpload | None) -> dict[str, Any]:
    if file is None:
        return {"json": prune(fields)}
    return {"data": prune(fields), "files": {"file": file}}


async def list_obsidian_notes(
    project_id: int | str,
    *,
    active: bool | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> ObsidianNoteList:
    return await request(
        "GET",
        f"/projects/{project_id}/obsidian_notes",
        params=prune({"active": active, "page": page, "per_page": per_page}),
    )


async def get_obsidian_note(project_id: int | str, note_id: int | str) -> ObsidianNote:
    return await request("GET", f"/projects/{project_id}/obsidian_notes/{note_id}")


async def create_obsidian_note(
    project_id: int | str,
    *,
    title: str | None = None,
    tags: str | None = None,
    content: str | None = None,
    html_source_type: str | None = None,
    html_source_path: str | None = None,
    active: bool | None = None,
    position: int | None = None,
    file: FileUpload | None = None,
) -> ObsidianNote:
    """`html_source_type` is one of `internal_file`, `external_url`."""
    return await request(
        "POST",
        f"/projects/{project_id}/obsidian_notes",
        **_body_kwargs(
            {
                "title": title,
                "tags": tags,
                "content": content,
                "html_source_type": html_source_type,
                "html_source_path": html_source_path,
                "active": active,
                "position": position,
            },
            file,
        ),
    )


async def update_obsidian_note(
    project_id: int | str,
    note_id: int | str,
    *,
    title: str | None = None,
    tags: str | None = None,
    content: str | None = None,
    html_source_type: str | None = None,
    html_source_path: str | None = None,
    active: bool | None = None,
    position: int | None = None,
    file: FileUpload | None = None,
) -> ObsidianNote:
    return await request(
        "PATCH",
        f"/projects/{project_id}/obsidian_notes/{note_id}",
        **_body_kwargs(
            {
                "title": title,
                "tags": tags,
                "content": content,
                "html_source_type": html_source_type,
                "html_source_path": html_source_path,
                "active": active,
                "position": position,
            },
            file,
        ),
    )


async def delete_obsidian_note(project_id: int | str, note_id: int | str) -> None:
    return await request("DELETE", f"/projects/{project_id}/obsidian_notes/{note_id}")
