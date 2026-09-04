from typing import Any

from ._client import prune, request


async def list_attention_items(
    *,
    id: int | str | None = None,
    category: str | None = None,
    title: str | None = None,
    meta_text: str | None = None,
    due_at: str | None = None,
    overdue: bool | None = None,
    status: str | None = None,
    project_id: int | str | None = None,
    room_id: int | str | None = None,
    user_id: int | str | None = None,
    source_id: int | str | None = None,
    source_type: str | None = None,
    target_id: int | str | None = None,
    target_type: str | None = None,
    action_label: str | None = None,
    ai_confirm: bool | None = None,
    created_at_gt: str | None = None,
    created_at_lt: str | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> dict[str, Any]:
    return await request(
        "GET",
        "/attention_items",
        params=prune(
            {
                "id": id,
                "category": category,
                "title": title,
                "meta_text": meta_text,
                "due_at": due_at,
                "overdue": overdue,
                "status": status,
                "project_id": project_id,
                "room_id": room_id,
                "user_id": user_id,
                "source_id": source_id,
                "source_type": source_type,
                "target_id": target_id,
                "target_type": target_type,
                "action_label": action_label,
                "ai_confirm": ai_confirm,
                "created_at_gt": created_at_gt,
                "created_at_lt": created_at_lt,
                "page": page,
                "per_page": per_page,
            }
        ),
    )


async def get_attention_item(attention_item_id: int | str) -> dict[str, Any]:
    return await request("GET", f"/attention_items/{attention_item_id}")


async def create_attention_item(
    title: str,
    category: str,
    *,
    meta_text: str | None = None,
    due_at: str | None = None,
    status: str | None = None,
    overdue: bool | None = None,
    project_id: int | str | None = None,
    room_id: int | str | None = None,
    user_id: int | str | None = None,
    source_id: int | str | None = None,
    source_type: str | None = None,
    target_id: int | str | None = None,
    target_type: str | None = None,
    action_label: str | None = None,
    ai_confirm: bool | None = None,
) -> dict[str, Any]:
    return await request(
        "POST",
        "/attention_items",
        json=prune(
            {
                "title": title,
                "category": category,
                "meta_text": meta_text,
                "due_at": due_at,
                "status": status,
                "overdue": overdue,
                "project_id": project_id,
                "room_id": room_id,
                "user_id": user_id,
                "source_id": source_id,
                "source_type": source_type,
                "target_id": target_id,
                "target_type": target_type,
                "action_label": action_label,
                "ai_confirm": ai_confirm,
            }
        ),
    )


async def update_attention_item(
    attention_item_id: int | str,
    *,
    title: str | None = None,
    category: str | None = None,
    meta_text: str | None = None,
    due_at: str | None = None,
    status: str | None = None,
    overdue: bool | None = None,
    project_id: int | str | None = None,
    room_id: int | str | None = None,
    user_id: int | str | None = None,
    source_id: int | str | None = None,
    source_type: str | None = None,
    target_id: int | str | None = None,
    target_type: str | None = None,
    action_label: str | None = None,
    ai_confirm: bool | None = None,
) -> dict[str, Any]:
    return await request(
        "PATCH",
        f"/attention_items/{attention_item_id}",
        json=prune(
            {
                "title": title,
                "category": category,
                "meta_text": meta_text,
                "due_at": due_at,
                "status": status,
                "overdue": overdue,
                "project_id": project_id,
                "room_id": room_id,
                "user_id": user_id,
                "source_id": source_id,
                "source_type": source_type,
                "target_id": target_id,
                "target_type": target_type,
                "action_label": action_label,
                "ai_confirm": ai_confirm,
            }
        ),
    )


async def delete_attention_item(attention_item_id: int | str) -> None:
    return await request("DELETE", f"/attention_items/{attention_item_id}")
