"""MCP tools for Company and Project management."""

import asyncio
import json
import mimetypes
import os
from typing import Any, Callable

import httpx

from mcp.helpers import (
    bot_name_fuzzy_match,
    project_name_fuzzy_match,
    room_name_fuzzy,
    username_fuzzy_match,
)
from space.api import (
    create_adr,
    create_all_hands_action_item,
    create_all_hands_decision,
    create_all_hands_takeaway,
    create_attention_item,
    create_company_status_item,
    create_company_status_period,
    create_decision,
    create_directory_item,
    create_external_asset,
    create_knowledge_activity,
    create_knowledge_item,
    create_message,
    create_obsidian_note,
    create_project_bottleneck,
    create_project_milestone,
    create_project_todo,
    delete_adr,
    delete_all_hands_action_item,
    delete_all_hands_decision,
    delete_all_hands_takeaway,
    delete_attention_item,
    delete_company_status_item,
    delete_company_status_period,
    delete_directory_item,
    delete_external_asset,
    delete_knowledge_activity,
    delete_knowledge_item,
    delete_message,
    delete_message_by_id,
    delete_obsidian_note,
    delete_project_bottleneck,
    delete_project_milestone,
    delete_project_todo,
    filter_company_status_items,
    get_adr,
    get_all_hands_action_item,
    get_all_hands_decision,
    get_all_hands_takeaway,
    get_attention_item,
    get_company_status_item,
    get_company_status_period,
    get_company_status_period_by_name,
    get_company_status_period_by_slug,
    get_current_company_status_period,
    get_directory_item,
    get_external_asset,
    get_knowledge_activity,
    get_knowledge_item,
    get_obsidian_note,
    get_project_bottleneck,
    get_project_milestone,
    get_project_todo,
    list_adrs,
    list_all_hands_action_items,
    list_all_hands_decisions,
    list_all_hands_takeaways,
    list_attention_items,
    list_company_status_items,
    list_company_status_periods,
    list_directory_items,
    list_external_assets,
    list_knowledge_activities,
    list_knowledge_items,
    list_obsidian_notes,
    list_project_bottlenecks,
    list_project_milestones,
    list_project_todos,
    send_action,
    update_adr,
    update_all_hands_action_item,
    update_all_hands_decision,
    update_all_hands_takeaway,
    update_attention_item,
    update_company_status_item,
    update_company_status_period,
    update_directory_item,
    update_external_asset,
    update_knowledge_activity,
    update_knowledge_item,
    update_message,
    update_message_by_id,
    update_obsidian_note,
    update_project_bottleneck,
    update_project_milestone,
    update_project_todo,
)
from space.api._client import FileUpload


# ============================================================================
# Shared helpers
# ============================================================================

_LOADING_PREFIX = ":spin:"


def _format_result(result: Any) -> str:
    """Serialize an API response for MCP text content."""
    if result is None:
        return "Success"
    try:
        return json.dumps(result, indent=2, default=str)
    except TypeError:
        return str(result)


def _coerce_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes", "on")
    return bool(value)


async def _resolve_project_id(
    project_id: Any = None, project_name: str | None = None
) -> Any:
    if project_id is not None:
        return project_id
    if project_name:
        project = await project_name_fuzzy_match(project_name)
        if project is None:
            raise ValueError(f"Project not found: {project_name}")
        return project.get("id") or project.get("slug")
    return None


async def _resolve_room_id(
    project_id: Any, room_id: Any = None, room_name: str | None = None
) -> Any:
    if room_id is not None:
        return room_id
    if room_name:
        if project_id is None:
            raise ValueError("room_name resolution requires project_id or project_name.")
        room = await room_name_fuzzy(project_id, room_name)
        if room is None:
            raise ValueError(f"Room not found: {room_name}")
        return room.get("id")
    raise ValueError("Either room_id or room_name is required.")


async def _resolve_user_id(
    project_id: Any, user_id: Any = None, user_name: str | None = None
) -> Any:
    if user_id is not None:
        return user_id
    if user_name:
        if project_id is None:
            raise ValueError("user_name resolution requires project_id or project_name.")
        user = await username_fuzzy_match(project_id, user_name)
        if user is None:
            raise ValueError(f"User not found: {user_name}")
        return user.get("id")
    raise ValueError("Either user_id or user_name is required.")


async def _resolve_bot_id(
    project_id: Any, bot_id: Any = None, bot_name: str | None = None
) -> Any:
    if bot_id is not None:
        return bot_id
    if bot_name:
        if project_id is None:
            raise ValueError("bot_name resolution requires project_id or project_name.")
        bot = await bot_name_fuzzy_match(project_id, bot_name)
        if bot is None:
            raise ValueError(f"Bot not found: {bot_name}")
        return bot.get("id")
    raise ValueError("Either bot_id or bot_name is required.")


async def _resolve_sender_id(
    project_id: Any,
    user_id: Any = None,
    user_name: str | None = None,
    bot_id: Any = None,
    bot_name: str | None = None,
) -> Any:
    if user_id is not None or user_name:
        return await _resolve_user_id(project_id, user_id, user_name)
    if bot_id is not None or bot_name:
        return await _resolve_bot_id(project_id, bot_id, bot_name)
    raise ValueError("Either user_id/user_name or bot_id/bot_name is required.")


async def _resolve_attachment(
    attachment_path: str | None = None, attachment_url: str | None = None
) -> FileUpload | None:
    if attachment_path and attachment_url:
        raise ValueError("Provide either attachment_path or attachment_url, not both.")
    if attachment_path:
        if not os.path.isfile(attachment_path):
            raise ValueError(f"Attachment file not found: {attachment_path}")
        filename = os.path.basename(attachment_path)
        content_type, _ = mimetypes.guess_type(attachment_path)
        content_type = content_type or "application/octet-stream"

        def _read() -> bytes:
            with open(attachment_path, "rb") as f:
                return f.read()

        content = await asyncio.to_thread(_read)
        return (filename, content, content_type)
    if attachment_url:
        async with httpx.AsyncClient() as client:
            response = await client.get(attachment_url)
            response.raise_for_status()
        filename = attachment_url.split("/")[-1] or "attachment"
        content_type = response.headers.get("content-type") or "application/octet-stream"
        return (filename, response.content, content_type)
    return None


def _paginated_list(result: Any) -> list[dict[str, Any]]:
    """Return the list payload from a paginated response, or the raw list."""
    if isinstance(result, dict):
        for key in (
            "attention_items",
            "company_status_items",
            "company_status_periods",
            "project_milestones",
            "project_bottlenecks",
            "project_todos",
            "knowledge_items",
            "external_assets",
            "knowledge_activities",
            "directory_items",
            "obsidian_notes",
            "project_all_hands_takeaways",
            "project_all_hands_decisions",
            "project_all_hands_action_items",
        ):
            if key in result:
                return result[key]
    if isinstance(result, list):
        return result
    return [result] if result is not None else []


def _build_directory_tree(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build a parent/child tree from a flat list of directory items."""
    nodes = {
        item["id"]: {**item, "children": []}
        for item in items
        if isinstance(item, dict) and "id" in item
    }
    roots: list[dict[str, Any]] = []
    for node in nodes.values():
        parent_id = node.get("parent_id")
        if parent_id and parent_id in nodes:
            nodes[parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


# ============================================================================
# Example / Baseline
# ============================================================================

def hello(name: str = "World", **kwargs: Any) -> str:
    return f"Hello, {name}!"


# ============================================================================
# 1. Company Home
# ============================================================================

async def _list_attention_items_by_category(
    category: str,
    project_id: Any = None,
    project_name: str | None = None,
    room_id: Any = None,
    room_name: str | None = None,
    user_id: Any = None,
    user_name: str | None = None,
    status: str | None = None,
    overdue: Any = None,
    ai_confirm: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = None
    if project_id is not None or project_name:
        resolved_project_id = await _resolve_project_id(project_id, project_name)
    resolved_room_id = None
    if resolved_project_id is not None and (room_id is not None or room_name):
        resolved_room_id = await _resolve_room_id(resolved_project_id, room_id, room_name)
    resolved_user_id = None
    if resolved_project_id is not None and (user_id is not None or user_name):
        resolved_user_id = await _resolve_user_id(resolved_project_id, user_id, user_name)

    result = await list_attention_items(
        category=category,
        project_id=resolved_project_id,
        room_id=resolved_room_id,
        user_id=resolved_user_id,
        status=status,
        overdue=_coerce_bool(overdue),
        ai_confirm=_coerce_bool(ai_confirm),
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def decisions_waiting(**kwargs: Any) -> str:
    return await _list_attention_items_by_category("decisions_waiting", **kwargs)


async def blockers(**kwargs: Any) -> str:
    return await _list_attention_items_by_category("blockers", **kwargs)


async def outcomes_review(**kwargs: Any) -> str:
    return await _list_attention_items_by_category("outcomes_review", **kwargs)


async def mentions(**kwargs: Any) -> str:
    return await _list_attention_items_by_category("mentions", **kwargs)


async def material_changes(**kwargs: Any) -> str:
    return await _list_attention_items_by_category("material_changes", **kwargs)


async def ai_confirm(**kwargs: Any) -> str:
    return await _list_attention_items_by_category("ai_confirm", **kwargs)


async def knowledge_proposals(**kwargs: Any) -> str:
    return await _list_attention_items_by_category("knowledge_proposals", **kwargs)


async def _add_attention_item(
    category: str,
    title: str,
    project_id: Any = None,
    project_name: str | None = None,
    room_id: Any = None,
    room_name: str | None = None,
    user_id: Any = None,
    user_name: str | None = None,
    meta_text: str | None = None,
    due_at: str | None = None,
    status: str | None = None,
    overdue: Any = None,
    source_id: int | str | None = None,
    source_type: str | None = None,
    target_id: int | str | None = None,
    target_type: str | None = None,
    action_label: str | None = None,
    ai_confirm: Any = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = None
    if project_id is not None or project_name:
        resolved_project_id = await _resolve_project_id(project_id, project_name)
    resolved_room_id = None
    if resolved_project_id is not None and (room_id is not None or room_name):
        resolved_room_id = await _resolve_room_id(resolved_project_id, room_id, room_name)
    resolved_user_id = None
    if resolved_project_id is not None and (user_id is not None or user_name):
        resolved_user_id = await _resolve_user_id(resolved_project_id, user_id, user_name)

    result = await create_attention_item(
        title,
        category,
        meta_text=meta_text,
        due_at=due_at,
        status=status,
        overdue=_coerce_bool(overdue),
        project_id=resolved_project_id,
        room_id=resolved_room_id,
        user_id=resolved_user_id,
        source_id=source_id,
        source_type=source_type,
        target_id=target_id,
        target_type=target_type,
        action_label=action_label,
        ai_confirm=_coerce_bool(ai_confirm),
    )
    return _format_result(result)


async def _edit_attention_item(
    category: str,
    attention_item_id: int | str,
    project_id: Any = None,
    project_name: str | None = None,
    room_id: Any = None,
    room_name: str | None = None,
    user_id: Any = None,
    user_name: str | None = None,
    title: str | None = None,
    meta_text: str | None = None,
    due_at: str | None = None,
    status: str | None = None,
    overdue: Any = None,
    source_id: int | str | None = None,
    source_type: str | None = None,
    target_id: int | str | None = None,
    target_type: str | None = None,
    action_label: str | None = None,
    ai_confirm: Any = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = None
    if project_id is not None or project_name:
        resolved_project_id = await _resolve_project_id(project_id, project_name)
    resolved_room_id = None
    if resolved_project_id is not None and (room_id is not None or room_name):
        resolved_room_id = await _resolve_room_id(resolved_project_id, room_id, room_name)
    resolved_user_id = None
    if resolved_project_id is not None and (user_id is not None or user_name):
        resolved_user_id = await _resolve_user_id(resolved_project_id, user_id, user_name)

    result = await update_attention_item(
        attention_item_id,
        category=category,
        title=title,
        meta_text=meta_text,
        due_at=due_at,
        status=status,
        overdue=_coerce_bool(overdue),
        project_id=resolved_project_id,
        room_id=resolved_room_id,
        user_id=resolved_user_id,
        source_id=source_id,
        source_type=source_type,
        target_id=target_id,
        target_type=target_type,
        action_label=action_label,
        ai_confirm=_coerce_bool(ai_confirm),
    )
    return _format_result(result)


async def add_decisions_waiting(title: str, **kwargs: Any) -> str:
    return await _add_attention_item("decisions_waiting", title, **kwargs)


async def edit_decisions_waiting(attention_item_id: int | str, **kwargs: Any) -> str:
    return await _edit_attention_item("decisions_waiting", attention_item_id, **kwargs)


async def add_blockers(title: str, **kwargs: Any) -> str:
    return await _add_attention_item("blockers", title, **kwargs)


async def edit_blockers(attention_item_id: int | str, **kwargs: Any) -> str:
    return await _edit_attention_item("blockers", attention_item_id, **kwargs)


async def add_outcomes_review(title: str, **kwargs: Any) -> str:
    return await _add_attention_item("outcomes_review", title, **kwargs)


async def edit_outcomes_review(attention_item_id: int | str, **kwargs: Any) -> str:
    return await _edit_attention_item("outcomes_review", attention_item_id, **kwargs)


async def add_mentions(title: str, **kwargs: Any) -> str:
    return await _add_attention_item("mentions", title, **kwargs)


async def edit_mentions(attention_item_id: int | str, **kwargs: Any) -> str:
    return await _edit_attention_item("mentions", attention_item_id, **kwargs)


async def add_material_changes(title: str, **kwargs: Any) -> str:
    return await _add_attention_item("material_changes", title, **kwargs)


async def edit_material_changes(attention_item_id: int | str, **kwargs: Any) -> str:
    return await _edit_attention_item("material_changes", attention_item_id, **kwargs)


async def add_ai_confirm(title: str, **kwargs: Any) -> str:
    return await _add_attention_item("ai_confirm", title, **kwargs)


async def edit_ai_confirm(attention_item_id: int | str, **kwargs: Any) -> str:
    return await _edit_attention_item("ai_confirm", attention_item_id, **kwargs)


async def add_knowledge_proposals(title: str, **kwargs: Any) -> str:
    return await _add_attention_item("knowledge_proposals", title, **kwargs)


async def edit_knowledge_proposals(attention_item_id: int | str, **kwargs: Any) -> str:
    return await _edit_attention_item("knowledge_proposals", attention_item_id, **kwargs)


# ============================================================================
# 2. Company Status
# ============================================================================

async def company_status_period(
    period_id: Any = None,
    name: str | None = None,
    slug: str | None = None,
    current: Any = None,
    starts_on: str | None = None,
    ends_on: str | None = None,
    position: int | None = None,
    delete: Any = None,
    **kwargs: Any,
) -> str:
    delete = _coerce_bool(delete)
    if delete and period_id is not None:
        await delete_company_status_period(period_id)
        return _format_result(None)
    if period_id is not None:
        if any(field is not None for field in (name, slug, current, starts_on, ends_on, position)):
            result = await update_company_status_period(
                period_id,
                name=name,
                slug=slug,
                current=_coerce_bool(current),
                starts_on=starts_on,
                ends_on=ends_on,
                position=position,
            )
            return _format_result(result)
        result = await get_company_status_period(period_id)
        return _format_result(result)
    if _coerce_bool(current):
        result = await get_current_company_status_period()
        return _format_result(result)
    if slug:
        result = await get_company_status_period_by_slug(slug)
        return _format_result(result)
    if name and not any(field is not None for field in (slug, current, starts_on, ends_on, position)):
        result = await get_company_status_period_by_name(name)
        return _format_result(result)
    if name:
        result = await create_company_status_period(
            name,
            slug=slug,
            current=_coerce_bool(current),
            starts_on=starts_on,
            ends_on=ends_on,
            position=position,
        )
        return _format_result(result)
    result = await list_company_status_periods()
    return _format_result(result)


async def add_company_status_period(
    name: str,
    slug: str | None = None,
    current: Any = None,
    starts_on: str | None = None,
    ends_on: str | None = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    result = await create_company_status_period(
        name,
        slug=slug,
        current=_coerce_bool(current),
        starts_on=starts_on,
        ends_on=ends_on,
        position=position,
    )
    return _format_result(result)


async def edit_company_status_period(
    period_id: Any,
    name: str | None = None,
    slug: str | None = None,
    current: Any = None,
    starts_on: str | None = None,
    ends_on: str | None = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    result = await update_company_status_period(
        period_id,
        name=name,
        slug=slug,
        current=_coerce_bool(current),
        starts_on=starts_on,
        ends_on=ends_on,
        position=position,
    )
    return _format_result(result)


async def _company_status_category_tool(
    category: str,
    item_id: Any = None,
    company_status_period_id: Any = None,
    project_id: Any = None,
    project_name: str | None = None,
    title: str | None = None,
    status: str | None = None,
    health: str | None = None,
    badge: str | None = None,
    summary: str | None = None,
    details: str | None = None,
    owner_name: str | None = None,
    position: int | None = None,
    delete: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = None
    if project_id is not None or project_name:
        resolved_project_id = await _resolve_project_id(project_id, project_name)

    delete = _coerce_bool(delete)
    if delete and item_id is not None:
        await delete_company_status_item(item_id)
        return _format_result(None)
    if item_id is not None:
        if any(field is not None for field in (
            title, status, health, badge, summary, details, owner_name, position, company_status_period_id
        )):
            result = await update_company_status_item(
                item_id,
                company_status_period_id=company_status_period_id,
                title=title,
                category=category,
                status=status,
                health=health,
                badge=badge,
                summary=summary,
                details=details,
                owner_name=owner_name,
                position=position,
                project_id=resolved_project_id,
            )
            return _format_result(result)
        result = await get_company_status_item(item_id)
        return _format_result(result)
    if title is not None:
        if company_status_period_id is None:
            raise ValueError("company_status_period_id is required to create a company status item.")
        result = await create_company_status_item(
            company_status_period_id,
            title,
            category,
            status=status,
            health=health,
            badge=badge,
            summary=summary,
            details=details,
            owner_name=owner_name,
            position=position,
            project_id=resolved_project_id,
        )
        return _format_result(result)
    result = await list_company_status_items(
        company_status_period_id=company_status_period_id,
        project_id=resolved_project_id,
        category=category,
        status=status,
        health=health,
        badge=badge,
        owner_name=owner_name,
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def priorities(**kwargs: Any) -> str:
    return await _company_status_category_tool("priorities", **kwargs)


async def progress(**kwargs: Any) -> str:
    return await _company_status_category_tool("progress", **kwargs)


async def risks(**kwargs: Any) -> str:
    return await _company_status_category_tool("risks", **kwargs)


async def dependencies(**kwargs: Any) -> str:
    return await _company_status_category_tool("dependencies", **kwargs)


async def changes(**kwargs: Any) -> str:
    return await _company_status_category_tool("changes", **kwargs)


async def decisions(**kwargs: Any) -> str:
    return await _company_status_category_tool("decisions", **kwargs)


async def learnings(**kwargs: Any) -> str:
    return await _company_status_category_tool("learnings", **kwargs)


# ============================================================================
# 3. Project Overview
# ============================================================================

async def project_milestones(
    project_id: Any = None,
    project_name: str | None = None,
    milestone_id: Any = None,
    delete: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    delete = _coerce_bool(delete)
    if delete and milestone_id is not None:
        await delete_project_milestone(resolved_project_id, milestone_id)
        return _format_result(None)
    if milestone_id is not None:
        result = await get_project_milestone(resolved_project_id, milestone_id)
        return _format_result(result)
    result = await list_project_milestones(
        resolved_project_id,
        active=_coerce_bool(active),
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def add_project_milestone(
    title: str,
    project_id: Any = None,
    project_name: str | None = None,
    description: str | None = None,
    icon: str | None = None,
    active: Any = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await create_project_milestone(
        resolved_project_id,
        title,
        description=description,
        icon=icon,
        active=_coerce_bool(active),
        position=position,
    )
    return _format_result(result)


async def edit_project_milestone(
    milestone_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    title: str | None = None,
    description: str | None = None,
    icon: str | None = None,
    active: Any = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await update_project_milestone(
        resolved_project_id,
        milestone_id,
        title=title,
        description=description,
        icon=icon,
        active=_coerce_bool(active),
        position=position,
    )
    return _format_result(result)


async def _delete_project_milestone(
    milestone_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    await delete_project_milestone(resolved_project_id, milestone_id)
    return _format_result(None)


# ============================================================================
# 4. Project Status
# ============================================================================

async def project_bottlenecks(
    project_id: Any = None,
    project_name: str | None = None,
    bottleneck_id: Any = None,
    delete: Any = None,
    severity: str | None = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    delete = _coerce_bool(delete)
    if delete and bottleneck_id is not None:
        await delete_project_bottleneck(resolved_project_id, bottleneck_id)
        return _format_result(None)
    if bottleneck_id is not None:
        result = await get_project_bottleneck(resolved_project_id, bottleneck_id)
        return _format_result(result)
    result = await list_project_bottlenecks(
        resolved_project_id,
        severity=severity,
        active=_coerce_bool(active),
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def add_project_bottleneck(
    title: str,
    project_id: Any = None,
    project_name: str | None = None,
    description: str | None = None,
    severity: str | None = None,
    position: int | None = None,
    resolved_at: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await create_project_bottleneck(
        resolved_project_id,
        title,
        description=description,
        severity=severity,
        position=position,
        resolved_at=resolved_at,
    )
    return _format_result(result)


async def edit_project_bottleneck(
    bottleneck_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    title: str | None = None,
    description: str | None = None,
    severity: str | None = None,
    position: int | None = None,
    resolved_at: str | None = None,
    resolved: Any = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await update_project_bottleneck(
        resolved_project_id,
        bottleneck_id,
        title=title,
        description=description,
        severity=severity,
        position=position,
        resolved_at=resolved_at,
        resolved=_coerce_bool(resolved),
    )
    return _format_result(result)


async def _delete_project_bottleneck(
    bottleneck_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    await delete_project_bottleneck(resolved_project_id, bottleneck_id)
    return _format_result(None)


async def project_todos(
    project_id: Any = None,
    project_name: str | None = None,
    todo_id: Any = None,
    delete: Any = None,
    completed: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    delete = _coerce_bool(delete)
    if delete and todo_id is not None:
        await delete_project_todo(resolved_project_id, todo_id)
        return _format_result(None)
    if todo_id is not None:
        result = await get_project_todo(resolved_project_id, todo_id)
        return _format_result(result)
    result = await list_project_todos(
        resolved_project_id,
        completed=_coerce_bool(completed),
        active=_coerce_bool(active),
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def add_project_todo(
    title: str,
    project_id: Any = None,
    project_name: str | None = None,
    meta_text: str | None = None,
    completed: Any = None,
    completed_at: str | None = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await create_project_todo(
        resolved_project_id,
        title,
        meta_text=meta_text,
        completed=_coerce_bool(completed),
        completed_at=completed_at,
        position=position,
    )
    return _format_result(result)


async def edit_project_todo(
    todo_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    title: str | None = None,
    meta_text: str | None = None,
    completed: Any = None,
    completed_at: str | None = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await update_project_todo(
        resolved_project_id,
        todo_id,
        title=title,
        meta_text=meta_text,
        completed=_coerce_bool(completed),
        completed_at=completed_at,
        position=position,
    )
    return _format_result(result)


async def _delete_project_todo(
    todo_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    await delete_project_todo(resolved_project_id, todo_id)
    return _format_result(None)


async def project_knowledge_items(
    project_id: Any = None,
    project_name: str | None = None,
    item_id: Any = None,
    delete: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    delete = _coerce_bool(delete)
    if delete and item_id is not None:
        await delete_knowledge_item(resolved_project_id, item_id)
        return _format_result(None)
    if item_id is not None:
        result = await get_knowledge_item(resolved_project_id, item_id)
        return _format_result(result)
    result = await list_knowledge_items(
        resolved_project_id,
        active=_coerce_bool(active),
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def add_project_knowledge_item(
    title: str,
    description: str,
    project_id: Any = None,
    project_name: str | None = None,
    badge: str | None = None,
    active: Any = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await create_knowledge_item(
        resolved_project_id,
        title,
        description,
        badge=badge,
        active=_coerce_bool(active),
        position=position,
    )
    return _format_result(result)


async def edit_project_knowledge_item(
    item_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    title: str | None = None,
    description: str | None = None,
    badge: str | None = None,
    active: Any = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await update_knowledge_item(
        resolved_project_id,
        item_id,
        title=title,
        description=description,
        badge=badge,
        active=_coerce_bool(active),
        position=position,
    )
    return _format_result(result)


async def _delete_project_knowledge_item(
    item_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    await delete_knowledge_item(resolved_project_id, item_id)
    return _format_result(None)


# ============================================================================
# 5. Project All Hands
# ============================================================================

# ============================================================================
# 5.1 Project Decision Records (ADRs)
# ============================================================================

async def project_decision_records(
    project_id: Any = None,
    project_name: str | None = None,
    decision_record_id: Any = None,
    delete: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    delete = _coerce_bool(delete)
    if delete and decision_record_id is not None:
        await delete_adr(resolved_project_id, decision_record_id)
        return _format_result(None)
    if decision_record_id is not None:
        result = await get_adr(resolved_project_id, decision_record_id)
        return _format_result(result)
    result = await list_adrs(
        resolved_project_id,
        active=_coerce_bool(active),
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def add_project_decision_record(
    identifier: str,
    title: str,
    project_id: Any = None,
    project_name: str | None = None,
    decision_date: str | None = None,
    status: str | None = None,
    file_path: str | None = None,
    active: Any = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await create_adr(
        resolved_project_id,
        identifier,
        title,
        decision_date=decision_date,
        status=status,
        file_path=file_path,
        active=_coerce_bool(active),
        position=position,
    )
    return _format_result(result)


async def edit_project_decision_record(
    decision_record_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    identifier: str | None = None,
    title: str | None = None,
    decision_date: str | None = None,
    status: str | None = None,
    file_path: str | None = None,
    active: Any = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await update_adr(
        resolved_project_id,
        decision_record_id,
        identifier=identifier,
        title=title,
        decision_date=decision_date,
        status=status,
        file_path=file_path,
        active=_coerce_bool(active),
        position=position,
    )
    return _format_result(result)


async def _delete_project_decision_record(
    decision_record_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    await delete_adr(resolved_project_id, decision_record_id)
    return _format_result(None)


# ============================================================================
# 5. Project All Hands
# ============================================================================

async def project_all_hands_takeaway(
    project_id: Any = None,
    project_name: str | None = None,
    takeaway_id: Any = None,
    delete: Any = None,
    category: str | None = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    delete = _coerce_bool(delete)
    if delete and takeaway_id is not None:
        await delete_all_hands_takeaway(resolved_project_id, takeaway_id)
        return _format_result(None)
    if takeaway_id is not None:
        result = await get_all_hands_takeaway(resolved_project_id, takeaway_id)
        return _format_result(result)
    result = await list_all_hands_takeaways(
        resolved_project_id,
        active=_coerce_bool(active),
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def add_project_all_hands_takeaway(
    category: str,
    content: str,
    project_id: Any = None,
    project_name: str | None = None,
    active: Any = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await create_all_hands_takeaway(
        resolved_project_id,
        category,
        content,
        active=_coerce_bool(active),
        position=position,
    )
    return _format_result(result)


async def edit_project_all_hands_takeaway(
    takeaway_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    category: str | None = None,
    content: str | None = None,
    active: Any = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await update_all_hands_takeaway(
        resolved_project_id,
        takeaway_id,
        category=category,
        content=content,
        active=_coerce_bool(active),
        position=position,
    )
    return _format_result(result)


async def _delete_project_all_hands_takeaway(
    takeaway_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    await delete_all_hands_takeaway(resolved_project_id, takeaway_id)
    return _format_result(None)


async def project_all_hands_action_item(
    project_id: Any = None,
    project_name: str | None = None,
    action_item_id: Any = None,
    delete: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    delete = _coerce_bool(delete)
    if delete and action_item_id is not None:
        await delete_all_hands_action_item(resolved_project_id, action_item_id)
        return _format_result(None)
    if action_item_id is not None:
        result = await get_all_hands_action_item(resolved_project_id, action_item_id)
        return _format_result(result)
    result = await list_all_hands_action_items(
        resolved_project_id,
        active=_coerce_bool(active),
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def add_project_all_hands_action_item(
    title: str,
    project_id: Any = None,
    project_name: str | None = None,
    assignee_name: str | None = None,
    due_date: str | None = None,
    completed: Any = None,
    completed_at: str | None = None,
    active: Any = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await create_all_hands_action_item(
        resolved_project_id,
        title,
        assignee_name=assignee_name,
        due_date=due_date,
        completed=_coerce_bool(completed),
        completed_at=completed_at,
        active=_coerce_bool(active),
        position=position,
    )
    return _format_result(result)


async def edit_project_all_hands_action_item(
    action_item_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    title: str | None = None,
    assignee_name: str | None = None,
    due_date: str | None = None,
    completed: Any = None,
    completed_at: str | None = None,
    active: Any = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await update_all_hands_action_item(
        resolved_project_id,
        action_item_id,
        title=title,
        assignee_name=assignee_name,
        due_date=due_date,
        completed=_coerce_bool(completed),
        completed_at=completed_at,
        active=_coerce_bool(active),
        position=position,
    )
    return _format_result(result)


async def _delete_project_all_hands_action_item(
    action_item_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    await delete_all_hands_action_item(resolved_project_id, action_item_id)
    return _format_result(None)


async def project_all_hands_decision(
    project_id: Any = None,
    project_name: str | None = None,
    decision_id: Any = None,
    delete: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    delete = _coerce_bool(delete)
    if delete and decision_id is not None:
        await delete_all_hands_decision(resolved_project_id, decision_id)
        return _format_result(None)
    if decision_id is not None:
        result = await get_all_hands_decision(resolved_project_id, decision_id)
        return _format_result(result)
    result = await list_all_hands_decisions(
        resolved_project_id,
        active=_coerce_bool(active),
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def add_project_all_hands_decision(
    title: str,
    project_id: Any = None,
    project_name: str | None = None,
    basis: str | None = None,
    impact: str | None = None,
    badge: str | None = None,
    active: Any = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await create_all_hands_decision(
        resolved_project_id,
        title,
        basis=basis,
        impact=impact,
        badge=badge,
        active=_coerce_bool(active),
        position=position,
    )
    return _format_result(result)


async def edit_project_all_hands_decision(
    decision_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    title: str | None = None,
    basis: str | None = None,
    impact: str | None = None,
    badge: str | None = None,
    active: Any = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await update_all_hands_decision(
        resolved_project_id,
        decision_id,
        title=title,
        basis=basis,
        impact=impact,
        badge=badge,
        active=_coerce_bool(active),
        position=position,
    )
    return _format_result(result)


async def _delete_project_all_hands_decision(
    decision_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    await delete_all_hands_decision(resolved_project_id, decision_id)
    return _format_result(None)


# ============================================================================
# 6. Project Knowledge
# ============================================================================

async def external_knowledge_assets(
    project_id: Any = None,
    project_name: str | None = None,
    asset_id: Any = None,
    delete: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    delete = _coerce_bool(delete)
    if delete and asset_id is not None:
        await delete_external_asset(resolved_project_id, asset_id)
        return _format_result(None)
    if asset_id is not None:
        result = await get_external_asset(resolved_project_id, asset_id)
        return _format_result(result)
    result = await list_external_assets(
        resolved_project_id,
        active=_coerce_bool(active),
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def add_external_knowledge_asset(
    title: str,
    url: str,
    project_id: Any = None,
    project_name: str | None = None,
    doc_type: str | None = None,
    icon: str | None = None,
    source_type: str | None = None,
    meta_text: str | None = None,
    active: Any = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await create_external_asset(
        resolved_project_id,
        title,
        url,
        doc_type=doc_type,
        icon=icon,
        source_type=source_type,
        meta_text=meta_text,
        active=_coerce_bool(active),
        position=position,
    )
    return _format_result(result)


async def edit_external_knowledge_asset(
    asset_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    title: str | None = None,
    url: str | None = None,
    doc_type: str | None = None,
    icon: str | None = None,
    source_type: str | None = None,
    meta_text: str | None = None,
    active: Any = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await update_external_asset(
        resolved_project_id,
        asset_id,
        title=title,
        url=url,
        doc_type=doc_type,
        icon=icon,
        source_type=source_type,
        meta_text=meta_text,
        active=_coerce_bool(active),
        position=position,
    )
    return _format_result(result)


async def _delete_external_knowledge_asset(
    asset_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    await delete_external_asset(resolved_project_id, asset_id)
    return _format_result(None)


async def knowledge_activity_log(
    project_id: Any = None,
    project_name: str | None = None,
    activity_id: Any = None,
    delete: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    delete = _coerce_bool(delete)
    if delete and activity_id is not None:
        await delete_knowledge_activity(resolved_project_id, activity_id)
        return _format_result(None)
    if activity_id is not None:
        result = await get_knowledge_activity(resolved_project_id, activity_id)
        return _format_result(result)
    result = await list_knowledge_activities(
        resolved_project_id,
        active=_coerce_bool(active),
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def add_knowledge_activity_log(
    actor_name: str,
    action_text: str,
    project_id: Any = None,
    project_name: str | None = None,
    actor_color: str | None = None,
    target_path: str | None = None,
    target_url: str | None = None,
    active: Any = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await create_knowledge_activity(
        resolved_project_id,
        actor_name,
        action_text,
        actor_color=actor_color,
        target_path=target_path,
        target_url=target_url,
        active=_coerce_bool(active),
        position=position,
    )
    return _format_result(result)


async def edit_knowledge_activity_log(
    activity_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    actor_name: str | None = None,
    action_text: str | None = None,
    actor_color: str | None = None,
    target_path: str | None = None,
    target_url: str | None = None,
    active: Any = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await update_knowledge_activity(
        resolved_project_id,
        activity_id,
        actor_name=actor_name,
        action_text=action_text,
        actor_color=actor_color,
        target_path=target_path,
        target_url=target_url,
        active=_coerce_bool(active),
        position=position,
    )
    return _format_result(result)


async def _delete_knowledge_activity_log(
    activity_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    await delete_knowledge_activity(resolved_project_id, activity_id)
    return _format_result(None)


async def tree_based_project_directory_data(
    project_id: Any = None,
    project_name: str | None = None,
    item_id: Any = None,
    delete: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    delete = _coerce_bool(delete)
    if delete and item_id is not None:
        await delete_directory_item(resolved_project_id, item_id)
        return _format_result(None)
    if item_id is not None:
        result = await get_directory_item(resolved_project_id, item_id)
        return _format_result(result)
    result = await list_directory_items(
        resolved_project_id,
        active=_coerce_bool(active),
        page=page,
        per_page=per_page,
    )
    items = _paginated_list(result)
    tree = _build_directory_tree(items)
    return _format_result(tree)


async def add_tree_based_project_directory_item(
    project_id: Any = None,
    project_name: str | None = None,
    name: str | None = None,
    item_type: str | None = None,
    file_path: str | None = None,
    parent_id: Any = None,
    content: str | None = None,
    active: Any = None,
    position: int | None = None,
    attachment_path: str | None = None,
    attachment_url: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    file = await _resolve_attachment(attachment_path, attachment_url)
    result = await create_directory_item(
        resolved_project_id,
        name=name,
        item_type=item_type,
        file_path=file_path,
        parent_id=parent_id,
        content=content,
        active=_coerce_bool(active),
        position=position,
        file=file,
    )
    return _format_result(result)


async def edit_tree_based_project_directory_item(
    item_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    name: str | None = None,
    item_type: str | None = None,
    file_path: str | None = None,
    parent_id: Any = None,
    content: str | None = None,
    active: Any = None,
    position: int | None = None,
    attachment_path: str | None = None,
    attachment_url: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    file = await _resolve_attachment(attachment_path, attachment_url)
    result = await update_directory_item(
        resolved_project_id,
        item_id,
        name=name,
        item_type=item_type,
        file_path=file_path,
        parent_id=parent_id,
        content=content,
        active=_coerce_bool(active),
        position=position,
        file=file,
    )
    return _format_result(result)


async def _delete_tree_based_project_directory_item(
    item_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    await delete_directory_item(resolved_project_id, item_id)
    return _format_result(None)


async def knowledge_summary_items(
    project_id: Any = None,
    project_name: str | None = None,
    item_id: Any = None,
    delete: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    delete = _coerce_bool(delete)
    if delete and item_id is not None:
        await delete_knowledge_item(resolved_project_id, item_id)
        return _format_result(None)
    if item_id is not None:
        result = await get_knowledge_item(resolved_project_id, item_id)
        return _format_result(result)
    result = await list_knowledge_items(
        resolved_project_id,
        active=_coerce_bool(active),
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def add_knowledge_summary_item(
    title: str,
    description: str,
    project_id: Any = None,
    project_name: str | None = None,
    badge: str | None = None,
    active: Any = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await create_knowledge_item(
        resolved_project_id,
        title,
        description,
        badge=badge,
        active=_coerce_bool(active),
        position=position,
    )
    return _format_result(result)


async def edit_knowledge_summary_item(
    item_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    title: str | None = None,
    description: str | None = None,
    badge: str | None = None,
    active: Any = None,
    position: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await update_knowledge_item(
        resolved_project_id,
        item_id,
        title=title,
        description=description,
        badge=badge,
        active=_coerce_bool(active),
        position=position,
    )
    return _format_result(result)


async def _delete_knowledge_summary_item(
    item_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    await delete_knowledge_item(resolved_project_id, item_id)
    return _format_result(None)


async def project_obsidian_note(
    project_id: Any = None,
    project_name: str | None = None,
    note_id: Any = None,
    delete: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    delete = _coerce_bool(delete)
    if delete and note_id is not None:
        await delete_obsidian_note(resolved_project_id, note_id)
        return _format_result(None)
    if note_id is not None:
        result = await get_obsidian_note(resolved_project_id, note_id)
        return _format_result(result)
    result = await list_obsidian_notes(
        resolved_project_id,
        active=_coerce_bool(active),
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def add_project_obsidian_note(
    project_id: Any = None,
    project_name: str | None = None,
    title: str | None = None,
    tags: str | None = None,
    content: str | None = None,
    html_source_type: str | None = None,
    html_source_path: str | None = None,
    active: Any = None,
    position: int | None = None,
    attachment_path: str | None = None,
    attachment_url: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    file = await _resolve_attachment(attachment_path, attachment_url)
    result = await create_obsidian_note(
        resolved_project_id,
        title=title,
        tags=tags,
        content=content,
        html_source_type=html_source_type,
        html_source_path=html_source_path,
        active=_coerce_bool(active),
        position=position,
        file=file,
    )
    return _format_result(result)


async def edit_project_obsidian_note(
    note_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    title: str | None = None,
    tags: str | None = None,
    content: str | None = None,
    html_source_type: str | None = None,
    html_source_path: str | None = None,
    active: Any = None,
    position: int | None = None,
    attachment_path: str | None = None,
    attachment_url: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    file = await _resolve_attachment(attachment_path, attachment_url)
    result = await update_obsidian_note(
        resolved_project_id,
        note_id,
        title=title,
        tags=tags,
        content=content,
        html_source_type=html_source_type,
        html_source_path=html_source_path,
        active=_coerce_bool(active),
        position=position,
        file=file,
    )
    return _format_result(result)


async def _delete_project_obsidian_note(
    note_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    await delete_obsidian_note(resolved_project_id, note_id)
    return _format_result(None)


# ============================================================================
# 7. Room Tools
# ============================================================================

async def add_message(
    project_id: Any = None,
    project_name: str | None = None,
    room_id: Any = None,
    room_name: str | None = None,
    user_id: Any = None,
    user_name: str | None = None,
    bot_id: Any = None,
    bot_name: str | None = None,
    body: str | None = None,
    attachment_path: str | None = None,
    attachment_url: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    resolved_room_id = await _resolve_room_id(resolved_project_id, room_id, room_name)
    sender_id = await _resolve_sender_id(
        resolved_project_id, user_id, user_name, bot_id, bot_name
    )
    attachment = await _resolve_attachment(attachment_path, attachment_url)
    if body is None and attachment is None:
        raise ValueError("Either body or an attachment is required.")
    result = await create_message(
        resolved_project_id,
        resolved_room_id,
        sender_id,
        body=body,
        attachment=attachment,
    )
    return _format_result(result)


async def add_loading_message(
    project_id: Any = None,
    project_name: str | None = None,
    room_id: Any = None,
    room_name: str | None = None,
    user_id: Any = None,
    user_name: str | None = None,
    bot_id: Any = None,
    bot_name: str | None = None,
    body: str = "",
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    resolved_room_id = await _resolve_room_id(resolved_project_id, room_id, room_name)
    sender_id = await _resolve_sender_id(
        resolved_project_id, user_id, user_name, bot_id, bot_name
    )
    prefixed_body = f"{_LOADING_PREFIX} {body}".strip()
    result = await create_message(
        resolved_project_id, resolved_room_id, sender_id, body=prefixed_body
    )
    return _format_result(result)


async def edit_loading_message(
    message_id: Any,
    body: str = "",
    **kwargs: Any,
) -> str:
    prefixed_body = f"{_LOADING_PREFIX} {body}".strip()
    result = await update_message_by_id(message_id, body=prefixed_body)
    return _format_result(result)


async def delete_loading_message(
    message_id: Any,
    **kwargs: Any,
) -> str:
    await delete_message_by_id(message_id)
    return _format_result(None)


async def add_action_message(
    project_id: Any = None,
    project_name: str | None = None,
    room_id: Any = None,
    room_name: str | None = None,
    user_id: Any = None,
    user_name: str | None = None,
    bot_id: Any = None,
    bot_name: str | None = None,
    action_type: str = "typing_start",
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    resolved_room_id = await _resolve_room_id(resolved_project_id, room_id, room_name)
    sender_id = await _resolve_sender_id(
        resolved_project_id, user_id, user_name, bot_id, bot_name
    )
    result = await send_action(
        resolved_project_id, resolved_room_id, sender_id, action_type
    )
    return _format_result(result)


async def add_decision_message(
    approval_request_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    room_id: Any = None,
    room_name: str | None = None,
    user_id: Any = None,
    user_name: str | None = None,
    bot_id: Any = None,
    bot_name: str | None = None,
    decision: str = "approve",
    note: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    resolved_room_id = await _resolve_room_id(resolved_project_id, room_id, room_name)
    sender_id = await _resolve_sender_id(
        resolved_project_id, user_id, user_name, bot_id, bot_name
    )
    result = await create_decision(
        resolved_project_id,
        resolved_room_id,
        sender_id,
        approval_request_id,
        decision,
        note=note,
    )
    return _format_result(result)


# ============================================================================
# Tool Registry and Definitions
# ============================================================================

# ------------------------------------------------------------------------------
# Schema fragments
# ------------------------------------------------------------------------------

_PROJECT_ID_PROPS: dict[str, Any] = {
    "project_id": {"type": ["string", "integer"], "description": "Project ID or slug"},
    "project_name": {"type": "string", "description": "Project name (fuzzy matched to ID)"},
}

_ROOM_ID_PROPS: dict[str, Any] = {
    "room_id": {"type": ["string", "integer"], "description": "Room ID"},
    "room_name": {"type": "string", "description": "Room name (fuzzy matched to ID)"},
}

_SENDER_PROPS: dict[str, Any] = {
    "user_id": {"type": ["string", "integer"], "description": "User ID to send as"},
    "user_name": {"type": "string", "description": "User name to send as (fuzzy matched)"},
    "bot_id": {"type": ["string", "integer"], "description": "Bot ID to send as"},
    "bot_name": {"type": "string", "description": "Bot name to send as (fuzzy matched)"},
}

_PAGINATION_PROPS: dict[str, Any] = {
    "page": {"type": "integer", "description": "Page number"},
    "per_page": {"type": "integer", "description": "Items per page"},
}

_ATTENTION_ITEM_COMMON_PROPS: dict[str, Any] = {
    **_PROJECT_ID_PROPS,
    **_ROOM_ID_PROPS,
    "user_id": {"type": ["string", "integer"], "description": "User ID (fuzzy matched by user_name if omitted)"},
    "user_name": {"type": "string", "description": "User name (fuzzy matched to ID)"},
    "meta_text": {"type": "string", "description": "Additional metadata text"},
    "due_at": {"type": "string", "description": "Due date (ISO 8601)"},
    "status": {"type": "string", "description": "Item status"},
    "overdue": {"type": "boolean", "description": "Overdue flag"},
    "source_id": {"type": ["string", "integer"], "description": "Source record ID"},
    "source_type": {"type": "string", "description": "Source record type"},
    "target_id": {"type": ["string", "integer"], "description": "Target record ID"},
    "target_type": {"type": "string", "description": "Target record type"},
    "action_label": {"type": "string", "description": "Action label"},
    "ai_confirm": {"type": "boolean", "description": "AI confirmation flag"},
}

_DELETE_PROP: dict[str, Any] = {
    "delete": {"type": "boolean", "description": "Set to true to delete the item"}
}

_ACTIVE_PROP: dict[str, Any] = {
    "active": {"type": "boolean", "description": "Filter by active status"}
}


# ------------------------------------------------------------------------------
# Tool registry
# ------------------------------------------------------------------------------

TOOL_HANDLERS: dict[str, Callable[..., Any]] = {
    "hello": hello,
    # Company Home
    "decisions_waiting": decisions_waiting,
    "blockers": blockers,
    "outcomes_review": outcomes_review,
    "mentions": mentions,
    "material_changes": material_changes,
    "ai_confirm": ai_confirm,
    "knowledge_proposals": knowledge_proposals,
    "add_decisions_waiting": add_decisions_waiting,
    "AddDecisionsWaiting": add_decisions_waiting,
    "edit_decisions_waiting": edit_decisions_waiting,
    "EditDecisionsWaiting": edit_decisions_waiting,
    "add_blockers": add_blockers,
    "AddBlockers": add_blockers,
    "edit_blockers": edit_blockers,
    "EditBlockers": edit_blockers,
    "add_outcomes_review": add_outcomes_review,
    "AddOutcomesReview": add_outcomes_review,
    "edit_outcomes_review": edit_outcomes_review,
    "EditOutcomesReview": edit_outcomes_review,
    "add_mentions": add_mentions,
    "AddMentions": add_mentions,
    "edit_mentions": edit_mentions,
    "EditMentions": edit_mentions,
    "add_material_changes": add_material_changes,
    "AddMaterialChanges": add_material_changes,
    "edit_material_changes": edit_material_changes,
    "EditMaterialChanges": edit_material_changes,
    "add_ai_confirm": add_ai_confirm,
    "AddAiConfirm": add_ai_confirm,
    "edit_ai_confirm": edit_ai_confirm,
    "EditAiConfirm": edit_ai_confirm,
    "add_knowledge_proposals": add_knowledge_proposals,
    "AddKnowledgeProposals": add_knowledge_proposals,
    "edit_knowledge_proposals": edit_knowledge_proposals,
    "EditKnowledgeProposals": edit_knowledge_proposals,
    # Company Status
    "company_status_period": company_status_period,
    "add_company_status_period": add_company_status_period,
    "AddCompanyStatusPeriod": add_company_status_period,
    "edit_company_status_period": edit_company_status_period,
    "EditCompanyStatusPeriod": edit_company_status_period,
    "priorities": priorities,
    "progress": progress,
    "risks": risks,
    "dependencies": dependencies,
    "changes": changes,
    "decisions": decisions,
    "learnings": learnings,
    # Project Overview
    "project_milestones": project_milestones,
    "add_project_milestone": add_project_milestone,
    "AddProjectMilestone": add_project_milestone,
    "edit_project_milestone": edit_project_milestone,
    "EditProjectMilestone": edit_project_milestone,
    "delete_project_milestone": _delete_project_milestone,
    "DeleteProjectMilestone": _delete_project_milestone,
    # Project Status
    "project_bottlenecks": project_bottlenecks,
    "add_project_bottleneck": add_project_bottleneck,
    "AddProjectBottleneck": add_project_bottleneck,
    "edit_project_bottleneck": edit_project_bottleneck,
    "EditProjectBottleneck": edit_project_bottleneck,
    "delete_project_bottleneck": _delete_project_bottleneck,
    "DeleteProjectBottleneck": _delete_project_bottleneck,
    "project_todos": project_todos,
    "add_project_todo": add_project_todo,
    "AddProjectTodo": add_project_todo,
    "edit_project_todo": edit_project_todo,
    "EditProjectTodo": edit_project_todo,
    "delete_project_todo": _delete_project_todo,
    "DeleteProjectTodo": _delete_project_todo,
    "project_knowledge_items": project_knowledge_items,
    "add_project_knowledge_item": add_project_knowledge_item,
    "AddProjectKnowledgeItem": add_project_knowledge_item,
    "edit_project_knowledge_item": edit_project_knowledge_item,
    "EditProjectKnowledgeItem": edit_project_knowledge_item,
    "delete_project_knowledge_item": _delete_project_knowledge_item,
    "DeleteProjectKnowledgeItem": _delete_project_knowledge_item,
    # Project All Hands
    "ProjectAllHandsTakeaway": project_all_hands_takeaway,
    "project_all_hands_takeaway": project_all_hands_takeaway,
    "add_project_all_hands_takeaway": add_project_all_hands_takeaway,
    "AddProjectAllHandsTakeaway": add_project_all_hands_takeaway,
    "edit_project_all_hands_takeaway": edit_project_all_hands_takeaway,
    "EditProjectAllHandsTakeaway": edit_project_all_hands_takeaway,
    "delete_project_all_hands_takeaway": _delete_project_all_hands_takeaway,
    "DeleteProjectAllHandsTakeaway": _delete_project_all_hands_takeaway,
    "ProjectAllHandsActionItem": project_all_hands_action_item,
    "project_all_hands_action_item": project_all_hands_action_item,
    "add_project_all_hands_action_item": add_project_all_hands_action_item,
    "AddProjectAllHandsActionItem": add_project_all_hands_action_item,
    "edit_project_all_hands_action_item": edit_project_all_hands_action_item,
    "EditProjectAllHandsActionItem": edit_project_all_hands_action_item,
    "delete_project_all_hands_action_item": _delete_project_all_hands_action_item,
    "DeleteProjectAllHandsActionItem": _delete_project_all_hands_action_item,
    "ProjectAllHandsDecision": project_all_hands_decision,
    "project_all_hands_decision": project_all_hands_decision,
    "add_project_all_hands_decision": add_project_all_hands_decision,
    "AddProjectAllHandsDecision": add_project_all_hands_decision,
    "edit_project_all_hands_decision": edit_project_all_hands_decision,
    "EditProjectAllHandsDecision": edit_project_all_hands_decision,
    "delete_project_all_hands_decision": _delete_project_all_hands_decision,
    "DeleteProjectAllHandsDecision": _delete_project_all_hands_decision,
    # Project Decision Records (ADRs)
    "ProjectDecisionRecord": project_decision_records,
    "project_decision_records": project_decision_records,
    "add_project_decision_record": add_project_decision_record,
    "AddProjectDecisionRecord": add_project_decision_record,
    "edit_project_decision_record": edit_project_decision_record,
    "EditProjectDecisionRecord": edit_project_decision_record,
    "delete_project_decision_record": _delete_project_decision_record,
    "DeleteProjectDecisionRecord": _delete_project_decision_record,
    # Project Knowledge
    "external_knowledge_assets": external_knowledge_assets,
    "external_assets": external_knowledge_assets,
    "add_external_knowledge_asset": add_external_knowledge_asset,
    "AddExternalKnowledgeAsset": add_external_knowledge_asset,
    "edit_external_knowledge_asset": edit_external_knowledge_asset,
    "EditExternalKnowledgeAsset": edit_external_knowledge_asset,
    "delete_external_knowledge_asset": _delete_external_knowledge_asset,
    "DeleteExternalKnowledgeAsset": _delete_external_knowledge_asset,
    "knowledge_activity_log": knowledge_activity_log,
    "add_knowledge_activity_log": add_knowledge_activity_log,
    "AddKnowledgeActivityLog": add_knowledge_activity_log,
    "edit_knowledge_activity_log": edit_knowledge_activity_log,
    "EditKnowledgeActivityLog": edit_knowledge_activity_log,
    "delete_knowledge_activity_log": _delete_knowledge_activity_log,
    "DeleteKnowledgeActivityLog": _delete_knowledge_activity_log,
    "tree_based_project_directory_data": tree_based_project_directory_data,
    "add_tree_based_project_directory_item": add_tree_based_project_directory_item,
    "AddTreeBasedProjectDirectoryItem": add_tree_based_project_directory_item,
    "edit_tree_based_project_directory_item": edit_tree_based_project_directory_item,
    "EditTreeBasedProjectDirectoryItem": edit_tree_based_project_directory_item,
    "delete_tree_based_project_directory_item": _delete_tree_based_project_directory_item,
    "DeleteTreeBasedProjectDirectoryItem": _delete_tree_based_project_directory_item,
    "knowledge_summary_items": knowledge_summary_items,
    "add_knowledge_summary_item": add_knowledge_summary_item,
    "AddKnowledgeSummaryItem": add_knowledge_summary_item,
    "edit_knowledge_summary_item": edit_knowledge_summary_item,
    "EditKnowledgeSummaryItem": edit_knowledge_summary_item,
    "delete_knowledge_summary_item": _delete_knowledge_summary_item,
    "DeleteKnowledgeSummaryItem": _delete_knowledge_summary_item,
    "ProjectObsidianNote": project_obsidian_note,
    "project_obsidian_note": project_obsidian_note,
    "add_project_obsidian_note": add_project_obsidian_note,
    "AddProjectObsidianNote": add_project_obsidian_note,
    "edit_project_obsidian_note": edit_project_obsidian_note,
    "EditProjectObsidianNote": edit_project_obsidian_note,
    "delete_project_obsidian_note": _delete_project_obsidian_note,
    "DeleteProjectObsidianNote": _delete_project_obsidian_note,
    # Room Tools
    "add_message": add_message,
    "AddMessage": add_message,
    "add_loading_message": add_loading_message,
    "AddLoadingMessage": add_loading_message,
    "edit_loading_message": edit_loading_message,
    "EditLoadingMessage": edit_loading_message,
    "delete_loading_message": delete_loading_message,
    "DeleteLoadingMessage": delete_loading_message,
    "add_action_message": add_action_message,
    "AddActionMessage": add_action_message,
    "add_decision_message": add_decision_message,
    "AddDecisionMessage": add_decision_message,
}

_TOOL_METADATA = [
    (
        "hello",
        "Say hello to a given name or the world",
        {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name to greet", "default": "World"}
            },
        },
    ),
    # Company Home
    (
        "decisions_waiting",
        "List company-home decisions-waiting attention items",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                **_ROOM_ID_PROPS,
                "user_id": {"type": ["string", "integer"], "description": "User ID filter"},
                "user_name": {"type": "string", "description": "User name filter (fuzzy matched)"},
                "status": {"type": "string", "description": "Status filter"},
                "overdue": {"type": "boolean", "description": "Filter by overdue flag"},
                "ai_confirm": {"type": "boolean", "description": "Filter by ai_confirm flag"},
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "blockers",
        "List company-home blocker attention items",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                **_ROOM_ID_PROPS,
                "user_id": {"type": ["string", "integer"], "description": "User ID filter"},
                "user_name": {"type": "string", "description": "User name filter (fuzzy matched)"},
                "status": {"type": "string", "description": "Status filter"},
                "overdue": {"type": "boolean", "description": "Filter by overdue flag"},
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "outcomes_review",
        "List company-home outcomes-review attention items",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                **_ROOM_ID_PROPS,
                "user_id": {"type": ["string", "integer"], "description": "User ID filter"},
                "user_name": {"type": "string", "description": "User name filter (fuzzy matched)"},
                "status": {"type": "string", "description": "Status filter"},
                "overdue": {"type": "boolean", "description": "Filter by overdue flag"},
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "mentions",
        "List company-home mention attention items",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                **_ROOM_ID_PROPS,
                "user_id": {"type": ["string", "integer"], "description": "User ID filter"},
                "user_name": {"type": "string", "description": "User name filter (fuzzy matched)"},
                "status": {"type": "string", "description": "Status filter"},
                "overdue": {"type": "boolean", "description": "Filter by overdue flag"},
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "material_changes",
        "List company-home material-change attention items",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                **_ROOM_ID_PROPS,
                "user_id": {"type": ["string", "integer"], "description": "User ID filter"},
                "user_name": {"type": "string", "description": "User name filter (fuzzy matched)"},
                "status": {"type": "string", "description": "Status filter"},
                "overdue": {"type": "boolean", "description": "Filter by overdue flag"},
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "ai_confirm",
        "List company-home AI-confirm attention items",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                **_ROOM_ID_PROPS,
                "user_id": {"type": ["string", "integer"], "description": "User ID filter"},
                "user_name": {"type": "string", "description": "User name filter (fuzzy matched)"},
                "status": {"type": "string", "description": "Status filter"},
                "overdue": {"type": "boolean", "description": "Filter by overdue flag"},
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "knowledge_proposals",
        "List company-home knowledge-proposal attention items",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                **_ROOM_ID_PROPS,
                "user_id": {"type": ["string", "integer"], "description": "User ID filter"},
                "user_name": {"type": "string", "description": "User name filter (fuzzy matched)"},
                "status": {"type": "string", "description": "Status filter"},
                "overdue": {"type": "boolean", "description": "Filter by overdue flag"},
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "add_decisions_waiting",
        "Create a company-home decisions-waiting attention item",
        {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Item title"},
                **_ATTENTION_ITEM_COMMON_PROPS,
            },
            "required": ["title"],
        },
    ),
    (
        "edit_decisions_waiting",
        "Update a company-home decisions-waiting attention item",
        {
            "type": "object",
            "properties": {
                "attention_item_id": {"type": ["string", "integer"], "description": "Attention item ID"},
                **_ATTENTION_ITEM_COMMON_PROPS,
            },
            "required": ["attention_item_id"],
        },
    ),
    (
        "add_blockers",
        "Create a company-home blocker attention item",
        {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Item title"},
                **_ATTENTION_ITEM_COMMON_PROPS,
            },
            "required": ["title"],
        },
    ),
    (
        "edit_blockers",
        "Update a company-home blocker attention item",
        {
            "type": "object",
            "properties": {
                "attention_item_id": {"type": ["string", "integer"], "description": "Attention item ID"},
                **_ATTENTION_ITEM_COMMON_PROPS,
            },
            "required": ["attention_item_id"],
        },
    ),
    (
        "add_outcomes_review",
        "Create a company-home outcomes-review attention item",
        {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Item title"},
                **_ATTENTION_ITEM_COMMON_PROPS,
            },
            "required": ["title"],
        },
    ),
    (
        "edit_outcomes_review",
        "Update a company-home outcomes-review attention item",
        {
            "type": "object",
            "properties": {
                "attention_item_id": {"type": ["string", "integer"], "description": "Attention item ID"},
                **_ATTENTION_ITEM_COMMON_PROPS,
            },
            "required": ["attention_item_id"],
        },
    ),
    (
        "add_mentions",
        "Create a company-home mention attention item",
        {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Item title"},
                **_ATTENTION_ITEM_COMMON_PROPS,
            },
            "required": ["title"],
        },
    ),
    (
        "edit_mentions",
        "Update a company-home mention attention item",
        {
            "type": "object",
            "properties": {
                "attention_item_id": {"type": ["string", "integer"], "description": "Attention item ID"},
                **_ATTENTION_ITEM_COMMON_PROPS,
            },
            "required": ["attention_item_id"],
        },
    ),
    (
        "add_material_changes",
        "Create a company-home material-change attention item",
        {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Item title"},
                **_ATTENTION_ITEM_COMMON_PROPS,
            },
            "required": ["title"],
        },
    ),
    (
        "edit_material_changes",
        "Update a company-home material-change attention item",
        {
            "type": "object",
            "properties": {
                "attention_item_id": {"type": ["string", "integer"], "description": "Attention item ID"},
                **_ATTENTION_ITEM_COMMON_PROPS,
            },
            "required": ["attention_item_id"],
        },
    ),
    (
        "add_ai_confirm",
        "Create a company-home AI-confirm attention item",
        {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Item title"},
                **_ATTENTION_ITEM_COMMON_PROPS,
            },
            "required": ["title"],
        },
    ),
    (
        "edit_ai_confirm",
        "Update a company-home AI-confirm attention item",
        {
            "type": "object",
            "properties": {
                "attention_item_id": {"type": ["string", "integer"], "description": "Attention item ID"},
                **_ATTENTION_ITEM_COMMON_PROPS,
            },
            "required": ["attention_item_id"],
        },
    ),
    (
        "add_knowledge_proposals",
        "Create a company-home knowledge-proposal attention item",
        {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Item title"},
                **_ATTENTION_ITEM_COMMON_PROPS,
            },
            "required": ["title"],
        },
    ),
    (
        "edit_knowledge_proposals",
        "Update a company-home knowledge-proposal attention item",
        {
            "type": "object",
            "properties": {
                "attention_item_id": {"type": ["string", "integer"], "description": "Attention item ID"},
                **_ATTENTION_ITEM_COMMON_PROPS,
            },
            "required": ["attention_item_id"],
        },
    ),
    # Company Status
    (
        "company_status_period",
        "List, get, create, update, or delete company status periods",
        {
            "type": "object",
            "properties": {
                "period_id": {"type": ["string", "integer"], "description": "Period ID for get/update/delete"},
                "name": {"type": "string", "description": "Period name (for get-by-name or create)"},
                "slug": {"type": "string", "description": "Period slug (for get-by-slug)"},
                "current": {"type": "boolean", "description": "Set true to get the current period"},
                "starts_on": {"type": "string", "description": "Start date (ISO 8601)"},
                "ends_on": {"type": "string", "description": "End date (ISO 8601)"},
                "position": {"type": "integer", "description": "Display position"},
                **_DELETE_PROP,
            },
        },
    ),
    (
        "add_company_status_period",
        "Create a company status period",
        {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Period name"},
                "slug": {"type": "string", "description": "Period slug"},
                "current": {"type": "boolean", "description": "Whether this is the current period"},
                "starts_on": {"type": "string", "description": "Start date (ISO 8601)"},
                "ends_on": {"type": "string", "description": "End date (ISO 8601)"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["name"],
        },
    ),
    (
        "edit_company_status_period",
        "Update a company status period",
        {
            "type": "object",
            "properties": {
                "period_id": {"type": ["string", "integer"], "description": "Period ID"},
                "name": {"type": "string", "description": "Period name"},
                "slug": {"type": "string", "description": "Period slug"},
                "current": {"type": "boolean", "description": "Whether this is the current period"},
                "starts_on": {"type": "string", "description": "Start date (ISO 8601)"},
                "ends_on": {"type": "string", "description": "End date (ISO 8601)"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["period_id"],
        },
    ),
    (
        "priorities",
        "List or manage company status priority items",
        {
            "type": "object",
            "properties": {
                "item_id": {"type": ["string", "integer"], "description": "Item ID for get/update/delete"},
                "company_status_period_id": {"type": ["string", "integer"], "description": "Period ID"},
                **_PROJECT_ID_PROPS,
                "title": {"type": "string", "description": "Item title (for create/update)"},
                "status": {"type": "string", "description": "Status"},
                "health": {"type": "string", "description": "Health indicator"},
                "badge": {"type": "string", "description": "Badge"},
                "summary": {"type": "string", "description": "Short summary"},
                "details": {"type": "string", "description": "Detailed description"},
                "owner_name": {"type": "string", "description": "Owner name"},
                "position": {"type": "integer", "description": "Display position"},
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "progress",
        "List or manage company status progress items",
        {
            "type": "object",
            "properties": {
                "item_id": {"type": ["string", "integer"], "description": "Item ID for get/update/delete"},
                "company_status_period_id": {"type": ["string", "integer"], "description": "Period ID"},
                **_PROJECT_ID_PROPS,
                "title": {"type": "string", "description": "Item title (for create/update)"},
                "status": {"type": "string", "description": "Status"},
                "health": {"type": "string", "description": "Health indicator"},
                "badge": {"type": "string", "description": "Badge"},
                "summary": {"type": "string", "description": "Short summary"},
                "details": {"type": "string", "description": "Detailed description"},
                "owner_name": {"type": "string", "description": "Owner name"},
                "position": {"type": "integer", "description": "Display position"},
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "risks",
        "List or manage company status risk items",
        {
            "type": "object",
            "properties": {
                "item_id": {"type": ["string", "integer"], "description": "Item ID for get/update/delete"},
                "company_status_period_id": {"type": ["string", "integer"], "description": "Period ID"},
                **_PROJECT_ID_PROPS,
                "title": {"type": "string", "description": "Item title (for create/update)"},
                "status": {"type": "string", "description": "Status"},
                "health": {"type": "string", "description": "Health indicator"},
                "badge": {"type": "string", "description": "Badge"},
                "summary": {"type": "string", "description": "Short summary"},
                "details": {"type": "string", "description": "Detailed description"},
                "owner_name": {"type": "string", "description": "Owner name"},
                "position": {"type": "integer", "description": "Display position"},
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "dependencies",
        "List or manage company status dependency items",
        {
            "type": "object",
            "properties": {
                "item_id": {"type": ["string", "integer"], "description": "Item ID for get/update/delete"},
                "company_status_period_id": {"type": ["string", "integer"], "description": "Period ID"},
                **_PROJECT_ID_PROPS,
                "title": {"type": "string", "description": "Item title (for create/update)"},
                "status": {"type": "string", "description": "Status"},
                "health": {"type": "string", "description": "Health indicator"},
                "badge": {"type": "string", "description": "Badge"},
                "summary": {"type": "string", "description": "Short summary"},
                "details": {"type": "string", "description": "Detailed description"},
                "owner_name": {"type": "string", "description": "Owner name"},
                "position": {"type": "integer", "description": "Display position"},
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "changes",
        "List or manage company status change items",
        {
            "type": "object",
            "properties": {
                "item_id": {"type": ["string", "integer"], "description": "Item ID for get/update/delete"},
                "company_status_period_id": {"type": ["string", "integer"], "description": "Period ID"},
                **_PROJECT_ID_PROPS,
                "title": {"type": "string", "description": "Item title (for create/update)"},
                "status": {"type": "string", "description": "Status"},
                "health": {"type": "string", "description": "Health indicator"},
                "badge": {"type": "string", "description": "Badge"},
                "summary": {"type": "string", "description": "Short summary"},
                "details": {"type": "string", "description": "Detailed description"},
                "owner_name": {"type": "string", "description": "Owner name"},
                "position": {"type": "integer", "description": "Display position"},
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "decisions",
        "List or manage company status decision items",
        {
            "type": "object",
            "properties": {
                "item_id": {"type": ["string", "integer"], "description": "Item ID for get/update/delete"},
                "company_status_period_id": {"type": ["string", "integer"], "description": "Period ID"},
                **_PROJECT_ID_PROPS,
                "title": {"type": "string", "description": "Item title (for create/update)"},
                "status": {"type": "string", "description": "Status"},
                "health": {"type": "string", "description": "Health indicator"},
                "badge": {"type": "string", "description": "Badge"},
                "summary": {"type": "string", "description": "Short summary"},
                "details": {"type": "string", "description": "Detailed description"},
                "owner_name": {"type": "string", "description": "Owner name"},
                "position": {"type": "integer", "description": "Display position"},
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "learnings",
        "List or manage company status learning items",
        {
            "type": "object",
            "properties": {
                "item_id": {"type": ["string", "integer"], "description": "Item ID for get/update/delete"},
                "company_status_period_id": {"type": ["string", "integer"], "description": "Period ID"},
                **_PROJECT_ID_PROPS,
                "title": {"type": "string", "description": "Item title (for create/update)"},
                "status": {"type": "string", "description": "Status"},
                "health": {"type": "string", "description": "Health indicator"},
                "badge": {"type": "string", "description": "Badge"},
                "summary": {"type": "string", "description": "Short summary"},
                "details": {"type": "string", "description": "Detailed description"},
                "owner_name": {"type": "string", "description": "Owner name"},
                "position": {"type": "integer", "description": "Display position"},
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    # Project Overview
    (
        "project_milestones",
        "List, get, or delete project milestones",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "milestone_id": {"type": ["string", "integer"], "description": "Milestone ID for get/delete"},
                **_ACTIVE_PROP,
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "add_project_milestone",
        "Create a project milestone",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "title": {"type": "string", "description": "Milestone title"},
                "description": {"type": "string", "description": "Milestone description"},
                "icon": {"type": "string", "description": "Icon identifier"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["title"],
        },
    ),
    (
        "edit_project_milestone",
        "Update a project milestone",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "milestone_id": {"type": ["string", "integer"], "description": "Milestone ID"},
                "title": {"type": "string", "description": "Milestone title"},
                "description": {"type": "string", "description": "Milestone description"},
                "icon": {"type": "string", "description": "Icon identifier"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["milestone_id"],
        },
    ),
    (
        "delete_project_milestone",
        "Delete a project milestone",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "milestone_id": {"type": ["string", "integer"], "description": "Milestone ID"},
            },
            "required": ["milestone_id"],
        },
    ),
    # Project Status
    (
        "project_bottlenecks",
        "List, get, or delete project bottlenecks",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "bottleneck_id": {"type": ["string", "integer"], "description": "Bottleneck ID for get/delete"},
                "severity": {"type": "string", "description": "Severity filter"},
                **_ACTIVE_PROP,
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "add_project_bottleneck",
        "Create a project bottleneck",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "title": {"type": "string", "description": "Bottleneck title"},
                "description": {"type": "string", "description": "Bottleneck description"},
                "severity": {"type": "string", "description": "Severity"},
                "position": {"type": "integer", "description": "Display position"},
                "resolved_at": {"type": "string", "description": "Resolution timestamp (ISO 8601)"},
            },
            "required": ["title"],
        },
    ),
    (
        "edit_project_bottleneck",
        "Update a project bottleneck",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "bottleneck_id": {"type": ["string", "integer"], "description": "Bottleneck ID"},
                "title": {"type": "string", "description": "Bottleneck title"},
                "description": {"type": "string", "description": "Bottleneck description"},
                "severity": {"type": "string", "description": "Severity"},
                "position": {"type": "integer", "description": "Display position"},
                "resolved_at": {"type": "string", "description": "Resolution timestamp (ISO 8601)"},
                "resolved": {"type": "boolean", "description": "Resolved flag"},
            },
            "required": ["bottleneck_id"],
        },
    ),
    (
        "delete_project_bottleneck",
        "Delete a project bottleneck",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "bottleneck_id": {"type": ["string", "integer"], "description": "Bottleneck ID"},
            },
            "required": ["bottleneck_id"],
        },
    ),
    (
        "project_todos",
        "List, get, or delete project todos",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "todo_id": {"type": ["string", "integer"], "description": "Todo ID for get/delete"},
                "completed": {"type": "boolean", "description": "Filter by completed status"},
                **_ACTIVE_PROP,
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "add_project_todo",
        "Create a project todo",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "title": {"type": "string", "description": "Todo title"},
                "meta_text": {"type": "string", "description": "Additional metadata text"},
                "completed": {"type": "boolean", "description": "Completed flag"},
                "completed_at": {"type": "string", "description": "Completion timestamp (ISO 8601)"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["title"],
        },
    ),
    (
        "edit_project_todo",
        "Update a project todo",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "todo_id": {"type": ["string", "integer"], "description": "Todo ID"},
                "title": {"type": "string", "description": "Todo title"},
                "meta_text": {"type": "string", "description": "Additional metadata text"},
                "completed": {"type": "boolean", "description": "Completed flag"},
                "completed_at": {"type": "string", "description": "Completion timestamp (ISO 8601)"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["todo_id"],
        },
    ),
    (
        "delete_project_todo",
        "Delete a project todo",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "todo_id": {"type": ["string", "integer"], "description": "Todo ID"},
            },
            "required": ["todo_id"],
        },
    ),
    (
        "project_knowledge_items",
        "List, get, or delete project knowledge items",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "item_id": {"type": ["string", "integer"], "description": "Item ID for get/delete"},
                **_ACTIVE_PROP,
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "add_project_knowledge_item",
        "Create a project knowledge item",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "title": {"type": "string", "description": "Item title"},
                "description": {"type": "string", "description": "Item description"},
                "badge": {"type": "string", "description": "Badge"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["title", "description"],
        },
    ),
    (
        "edit_project_knowledge_item",
        "Update a project knowledge item",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "item_id": {"type": ["string", "integer"], "description": "Item ID"},
                "title": {"type": "string", "description": "Item title"},
                "description": {"type": "string", "description": "Item description"},
                "badge": {"type": "string", "description": "Badge"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["item_id"],
        },
    ),
    (
        "delete_project_knowledge_item",
        "Delete a project knowledge item",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "item_id": {"type": ["string", "integer"], "description": "Item ID"},
            },
            "required": ["item_id"],
        },
    ),
    # Project All Hands
    (
        "project_all_hands_takeaway",
        "List, get, or delete project all-hands takeaways",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "takeaway_id": {"type": ["string", "integer"], "description": "Takeaway ID for get/delete"},
                "category": {"type": "string", "description": "Category filter"},
                **_ACTIVE_PROP,
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "add_project_all_hands_takeaway",
        "Create a project all-hands takeaway",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "category": {"type": "string", "description": "Takeaway category"},
                "content": {"type": "string", "description": "Takeaway content"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["category", "content"],
        },
    ),
    (
        "edit_project_all_hands_takeaway",
        "Update a project all-hands takeaway",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "takeaway_id": {"type": ["string", "integer"], "description": "Takeaway ID"},
                "category": {"type": "string", "description": "Takeaway category"},
                "content": {"type": "string", "description": "Takeaway content"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["takeaway_id"],
        },
    ),
    (
        "delete_project_all_hands_takeaway",
        "Delete a project all-hands takeaway",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "takeaway_id": {"type": ["string", "integer"], "description": "Takeaway ID"},
            },
            "required": ["takeaway_id"],
        },
    ),
    (
        "project_all_hands_action_item",
        "List, get, or delete project all-hands action items",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "action_item_id": {"type": ["string", "integer"], "description": "Action item ID for get/delete"},
                **_ACTIVE_PROP,
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "add_project_all_hands_action_item",
        "Create a project all-hands action item",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "title": {"type": "string", "description": "Action item title"},
                "assignee_name": {"type": "string", "description": "Assignee name"},
                "due_date": {"type": "string", "description": "Due date (ISO 8601)"},
                "completed": {"type": "boolean", "description": "Completed flag"},
                "completed_at": {"type": "string", "description": "Completion timestamp (ISO 8601)"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["title"],
        },
    ),
    (
        "edit_project_all_hands_action_item",
        "Update a project all-hands action item",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "action_item_id": {"type": ["string", "integer"], "description": "Action item ID"},
                "title": {"type": "string", "description": "Action item title"},
                "assignee_name": {"type": "string", "description": "Assignee name"},
                "due_date": {"type": "string", "description": "Due date (ISO 8601)"},
                "completed": {"type": "boolean", "description": "Completed flag"},
                "completed_at": {"type": "string", "description": "Completion timestamp (ISO 8601)"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["action_item_id"],
        },
    ),
    (
        "delete_project_all_hands_action_item",
        "Delete a project all-hands action item",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "action_item_id": {"type": ["string", "integer"], "description": "Action item ID"},
            },
            "required": ["action_item_id"],
        },
    ),
    (
        "project_all_hands_decision",
        "List, get, or delete project all-hands decisions",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "decision_id": {"type": ["string", "integer"], "description": "Decision ID for get/delete"},
                **_ACTIVE_PROP,
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "add_project_all_hands_decision",
        "Create a project all-hands decision",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "title": {"type": "string", "description": "Decision title"},
                "basis": {"type": "string", "description": "Decision basis"},
                "impact": {"type": "string", "description": "Decision impact"},
                "badge": {"type": "string", "description": "Badge"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["title"],
        },
    ),
    (
        "edit_project_all_hands_decision",
        "Update a project all-hands decision",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "decision_id": {"type": ["string", "integer"], "description": "Decision ID"},
                "title": {"type": "string", "description": "Decision title"},
                "basis": {"type": "string", "description": "Decision basis"},
                "impact": {"type": "string", "description": "Decision impact"},
                "badge": {"type": "string", "description": "Badge"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["decision_id"],
        },
    ),
    (
        "delete_project_all_hands_decision",
        "Delete a project all-hands decision",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "decision_id": {"type": ["string", "integer"], "description": "Decision ID"},
            },
            "required": ["decision_id"],
        },
    ),
    # Project Decision Records (ADRs)
    (
        "project_decision_records",
        "List, get, or delete project decision records (ADRs)",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "decision_record_id": {"type": ["string", "integer"], "description": "Decision record (ADR) ID for get/delete"},
                **_ACTIVE_PROP,
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "add_project_decision_record",
        "Create a project decision record (ADR)",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "identifier": {"type": "string", "description": "ADR identifier (e.g. ADR-001)"},
                "title": {"type": "string", "description": "ADR title"},
                "decision_date": {"type": "string", "description": "Decision date (ISO 8601)"},
                "status": {"type": "string", "description": "Status: proposed, accepted, deprecated, or superseded"},
                "file_path": {"type": "string", "description": "File path to the ADR document"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["identifier", "title"],
        },
    ),
    (
        "edit_project_decision_record",
        "Update a project decision record (ADR)",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "decision_record_id": {"type": ["string", "integer"], "description": "Decision record (ADR) ID"},
                "identifier": {"type": "string", "description": "ADR identifier (e.g. ADR-001)"},
                "title": {"type": "string", "description": "ADR title"},
                "decision_date": {"type": "string", "description": "Decision date (ISO 8601)"},
                "status": {"type": "string", "description": "Status: proposed, accepted, deprecated, or superseded"},
                "file_path": {"type": "string", "description": "File path to the ADR document"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["decision_record_id"],
        },
    ),
    (
        "delete_project_decision_record",
        "Delete a project decision record (ADR)",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "decision_record_id": {"type": ["string", "integer"], "description": "Decision record (ADR) ID"},
            },
            "required": ["decision_record_id"],
        },
    ),
    # Project Knowledge
    (
        "external_knowledge_assets",
        "List, get, or delete external knowledge assets",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "asset_id": {"type": ["string", "integer"], "description": "Asset ID for get/delete"},
                **_ACTIVE_PROP,
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "add_external_knowledge_asset",
        "Create an external knowledge asset",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "title": {"type": "string", "description": "Asset title"},
                "url": {"type": "string", "description": "Asset URL"},
                "doc_type": {"type": "string", "description": "Document type"},
                "icon": {"type": "string", "description": "Icon identifier"},
                "source_type": {"type": "string", "description": "Source type: internal_file or external_url"},
                "meta_text": {"type": "string", "description": "Metadata text"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["title", "url"],
        },
    ),
    (
        "edit_external_knowledge_asset",
        "Update an external knowledge asset",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "asset_id": {"type": ["string", "integer"], "description": "Asset ID"},
                "title": {"type": "string", "description": "Asset title"},
                "url": {"type": "string", "description": "Asset URL"},
                "doc_type": {"type": "string", "description": "Document type"},
                "icon": {"type": "string", "description": "Icon identifier"},
                "source_type": {"type": "string", "description": "Source type: internal_file or external_url"},
                "meta_text": {"type": "string", "description": "Metadata text"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["asset_id"],
        },
    ),
    (
        "delete_external_knowledge_asset",
        "Delete an external knowledge asset",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "asset_id": {"type": ["string", "integer"], "description": "Asset ID"},
            },
            "required": ["asset_id"],
        },
    ),
    (
        "knowledge_activity_log",
        "List, get, or delete knowledge activity log entries",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "activity_id": {"type": ["string", "integer"], "description": "Activity ID for get/delete"},
                **_ACTIVE_PROP,
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "add_knowledge_activity_log",
        "Create a knowledge activity log entry",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "actor_name": {"type": "string", "description": "Actor name"},
                "action_text": {"type": "string", "description": "Action description"},
                "actor_color": {"type": "string", "description": "Actor color"},
                "target_path": {"type": "string", "description": "Target path"},
                "target_url": {"type": "string", "description": "Target URL"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["actor_name", "action_text"],
        },
    ),
    (
        "edit_knowledge_activity_log",
        "Update a knowledge activity log entry",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "activity_id": {"type": ["string", "integer"], "description": "Activity ID"},
                "actor_name": {"type": "string", "description": "Actor name"},
                "action_text": {"type": "string", "description": "Action description"},
                "actor_color": {"type": "string", "description": "Actor color"},
                "target_path": {"type": "string", "description": "Target path"},
                "target_url": {"type": "string", "description": "Target URL"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["activity_id"],
        },
    ),
    (
        "delete_knowledge_activity_log",
        "Delete a knowledge activity log entry",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "activity_id": {"type": ["string", "integer"], "description": "Activity ID"},
            },
            "required": ["activity_id"],
        },
    ),
    (
        "tree_based_project_directory_data",
        "List, get, or delete tree-based project directory items",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "item_id": {"type": ["string", "integer"], "description": "Directory item ID for get/delete"},
                **_ACTIVE_PROP,
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "add_tree_based_project_directory_item",
        "Create a tree-based project directory item",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "name": {"type": "string", "description": "Item name"},
                "item_type": {"type": "string", "description": "Item type: file or directory"},
                "file_path": {"type": "string", "description": "File path"},
                "parent_id": {"type": ["string", "integer"], "description": "Parent directory item ID"},
                "content": {"type": "string", "description": "Content for directory items"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
                "attachment_path": {"type": "string", "description": "Local file path to upload"},
                "attachment_url": {"type": "string", "description": "URL of file to upload"},
            },
        },
    ),
    (
        "edit_tree_based_project_directory_item",
        "Update a tree-based project directory item",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "item_id": {"type": ["string", "integer"], "description": "Directory item ID"},
                "name": {"type": "string", "description": "Item name"},
                "item_type": {"type": "string", "description": "Item type: file or directory"},
                "file_path": {"type": "string", "description": "File path"},
                "parent_id": {"type": ["string", "integer"], "description": "Parent directory item ID"},
                "content": {"type": "string", "description": "Content for directory items"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
                "attachment_path": {"type": "string", "description": "Local file path to upload"},
                "attachment_url": {"type": "string", "description": "URL of file to upload"},
            },
            "required": ["item_id"],
        },
    ),
    (
        "delete_tree_based_project_directory_item",
        "Delete a tree-based project directory item",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "item_id": {"type": ["string", "integer"], "description": "Directory item ID"},
            },
            "required": ["item_id"],
        },
    ),
    (
        "knowledge_summary_items",
        "List, get, or delete knowledge summary items",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "item_id": {"type": ["string", "integer"], "description": "Item ID for get/delete"},
                **_ACTIVE_PROP,
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "add_knowledge_summary_item",
        "Create a knowledge summary item",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "title": {"type": "string", "description": "Item title"},
                "description": {"type": "string", "description": "Item description"},
                "badge": {"type": "string", "description": "Badge"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["title", "description"],
        },
    ),
    (
        "edit_knowledge_summary_item",
        "Update a knowledge summary item",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "item_id": {"type": ["string", "integer"], "description": "Item ID"},
                "title": {"type": "string", "description": "Item title"},
                "description": {"type": "string", "description": "Item description"},
                "badge": {"type": "string", "description": "Badge"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
            },
            "required": ["item_id"],
        },
    ),
    (
        "delete_knowledge_summary_item",
        "Delete a knowledge summary item",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "item_id": {"type": ["string", "integer"], "description": "Item ID"},
            },
            "required": ["item_id"],
        },
    ),
    (
        "project_obsidian_note",
        "List, get, or delete project obsidian notes",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "note_id": {"type": ["string", "integer"], "description": "Note ID for get/delete"},
                **_ACTIVE_PROP,
                **_DELETE_PROP,
                **_PAGINATION_PROPS,
            },
        },
    ),
    (
        "add_project_obsidian_note",
        "Create a project obsidian note",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "title": {"type": "string", "description": "Note title"},
                "tags": {"type": "string", "description": "Comma-separated tags"},
                "content": {"type": "string", "description": "Note content"},
                "html_source_type": {"type": "string", "description": "HTML source type: internal_file or external_url"},
                "html_source_path": {"type": "string", "description": "HTML source path"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
                "attachment_path": {"type": "string", "description": "Local file path to upload"},
                "attachment_url": {"type": "string", "description": "URL of file to upload"},
            },
        },
    ),
    (
        "edit_project_obsidian_note",
        "Update a project obsidian note",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "note_id": {"type": ["string", "integer"], "description": "Note ID"},
                "title": {"type": "string", "description": "Note title"},
                "tags": {"type": "string", "description": "Comma-separated tags"},
                "content": {"type": "string", "description": "Note content"},
                "html_source_type": {"type": "string", "description": "HTML source type: internal_file or external_url"},
                "html_source_path": {"type": "string", "description": "HTML source path"},
                "active": {"type": "boolean", "description": "Active flag"},
                "position": {"type": "integer", "description": "Display position"},
                "attachment_path": {"type": "string", "description": "Local file path to upload"},
                "attachment_url": {"type": "string", "description": "URL of file to upload"},
            },
            "required": ["note_id"],
        },
    ),
    (
        "delete_project_obsidian_note",
        "Delete a project obsidian note",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                "note_id": {"type": ["string", "integer"], "description": "Note ID"},
            },
            "required": ["note_id"],
        },
    ),
    # Room Tools
    (
        "add_message",
        "Add a message to a room",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                **_ROOM_ID_PROPS,
                **_SENDER_PROPS,
                "body": {"type": "string", "description": "Message body"},
                "attachment_path": {"type": "string", "description": "Local file path to attach"},
                "attachment_url": {"type": "string", "description": "URL of file to attach"},
            },
            "required": ["room_id"],
        },
    ),
    (
        "add_loading_message",
        "Add a loading message to a room (prefixed with :spin:)",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                **_ROOM_ID_PROPS,
                **_SENDER_PROPS,
                "body": {"type": "string", "description": "Loading message body"},
            },
            "required": ["room_id"],
        },
    ),
    (
        "edit_loading_message",
        "Edit a loading message in a room (prefixed with :spin:)",
        {
            "type": "object",
            "properties": {
                "message_id": {"type": ["string", "integer"], "description": "Message ID"},
                "body": {"type": "string", "description": "Updated loading message body"},
            },
            "required": ["message_id"],
        },
    ),
    (
        "delete_loading_message",
        "Delete a loading message from a room",
        {
            "type": "object",
            "properties": {
                "message_id": {"type": ["string", "integer"], "description": "Message ID"},
            },
            "required": ["message_id"],
        },
    ),
    (
        "add_action_message",
        "Send a real-time action (e.g. typing indicator) to a room",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                **_ROOM_ID_PROPS,
                **_SENDER_PROPS,
                "action_type": {"type": "string", "description": "Action type: typing_start or typing_stop", "default": "typing_start"},
            },
            "required": ["room_id"],
        },
    ),
    (
        "add_decision_message",
        "Respond to an approval request (decision) in a room",
        {
            "type": "object",
            "properties": {
                **_PROJECT_ID_PROPS,
                **_ROOM_ID_PROPS,
                **_SENDER_PROPS,
                "approval_request_id": {"type": ["string", "integer"], "description": "Approval request ID"},
                "decision": {"type": "string", "description": "Decision: approve, confirm, deny, or cancel", "default": "approve"},
                "note": {"type": "string", "description": "Optional note"},
            },
            "required": ["approval_request_id"],
        },
    ),
]

# Register PascalCase aliases with the same schemas as their snake_case counterparts.
_ALIASES = [
    ("ProjectAllHandsTakeaway", "project_all_hands_takeaway"),
    ("ProjectAllHandsActionItem", "project_all_hands_action_item"),
    ("ProjectAllHandsDecision", "project_all_hands_decision"),
    ("ProjectObsidianNote", "project_obsidian_note"),
    ("external_assets", "external_knowledge_assets"),
    ("AddProjectMilestone", "add_project_milestone"),
    ("EditProjectMilestone", "edit_project_milestone"),
    ("DeleteProjectMilestone", "delete_project_milestone"),
    ("AddProjectBottleneck", "add_project_bottleneck"),
    ("EditProjectBottleneck", "edit_project_bottleneck"),
    ("DeleteProjectBottleneck", "delete_project_bottleneck"),
    ("AddProjectTodo", "add_project_todo"),
    ("EditProjectTodo", "edit_project_todo"),
    ("DeleteProjectTodo", "delete_project_todo"),
    ("AddProjectKnowledgeItem", "add_project_knowledge_item"),
    ("EditProjectKnowledgeItem", "edit_project_knowledge_item"),
    ("DeleteProjectKnowledgeItem", "delete_project_knowledge_item"),
    ("AddCompanyStatusPeriod", "add_company_status_period"),
    ("EditCompanyStatusPeriod", "edit_company_status_period"),
    ("AddProjectAllHandsTakeaway", "add_project_all_hands_takeaway"),
    ("EditProjectAllHandsTakeaway", "edit_project_all_hands_takeaway"),
    ("DeleteProjectAllHandsTakeaway", "delete_project_all_hands_takeaway"),
    ("AddProjectAllHandsActionItem", "add_project_all_hands_action_item"),
    ("EditProjectAllHandsActionItem", "edit_project_all_hands_action_item"),
    ("DeleteProjectAllHandsActionItem", "delete_project_all_hands_action_item"),
    ("AddProjectAllHandsDecision", "add_project_all_hands_decision"),
    ("EditProjectAllHandsDecision", "edit_project_all_hands_decision"),
    ("DeleteProjectAllHandsDecision", "delete_project_all_hands_decision"),
    ("ProjectDecisionRecord", "project_decision_records"),
    ("AddProjectDecisionRecord", "add_project_decision_record"),
    ("EditProjectDecisionRecord", "edit_project_decision_record"),
    ("DeleteProjectDecisionRecord", "delete_project_decision_record"),
    ("AddExternalKnowledgeAsset", "add_external_knowledge_asset"),
    ("EditExternalKnowledgeAsset", "edit_external_knowledge_asset"),
    ("DeleteExternalKnowledgeAsset", "delete_external_knowledge_asset"),
    ("AddKnowledgeActivityLog", "add_knowledge_activity_log"),
    ("EditKnowledgeActivityLog", "edit_knowledge_activity_log"),
    ("DeleteKnowledgeActivityLog", "delete_knowledge_activity_log"),
    ("AddTreeBasedProjectDirectoryItem", "add_tree_based_project_directory_item"),
    ("EditTreeBasedProjectDirectoryItem", "edit_tree_based_project_directory_item"),
    ("DeleteTreeBasedProjectDirectoryItem", "delete_tree_based_project_directory_item"),
    ("AddKnowledgeSummaryItem", "add_knowledge_summary_item"),
    ("EditKnowledgeSummaryItem", "edit_knowledge_summary_item"),
    ("DeleteKnowledgeSummaryItem", "delete_knowledge_summary_item"),
    ("AddProjectObsidianNote", "add_project_obsidian_note"),
    ("EditProjectObsidianNote", "edit_project_obsidian_note"),
    ("DeleteProjectObsidianNote", "delete_project_obsidian_note"),
    ("AddMessage", "add_message"),
    ("AddLoadingMessage", "add_loading_message"),
    ("EditLoadingMessage", "edit_loading_message"),
    ("DeleteLoadingMessage", "delete_loading_message"),
    ("AddActionMessage", "add_action_message"),
    ("AddDecisionMessage", "add_decision_message"),
]

_SCHEMAS_BY_NAME = {name: schema for name, _, schema in _TOOL_METADATA}
for alias_name, base_name in _ALIASES:
    _TOOL_METADATA.append((alias_name, f"Alias for {base_name}", _SCHEMAS_BY_NAME[base_name]))

TOOL_DEFINITIONS = [
    {
        "name": name,
        "description": desc,
        "inputSchema": schema,
    }
    for name, desc, schema in _TOOL_METADATA
]
