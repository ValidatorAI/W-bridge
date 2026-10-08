import json
from typing import Any, Callable

from space.api import (
    filter_company_status_items,
    get_ai_profile,
    get_ai_profile_mcp,
    get_ai_profile_skill,
    get_ai_profile_tool as get_ai_profile_tool_record,
    get_ai_setting,
    get_all_hands_action_item,
    get_all_hands_decision,
    get_all_hands_takeaway,
    get_approval_request,
    get_adr,
    get_company_status_item,
    get_company_status_period,
    get_company_status_period_by_name,
    get_company_status_period_by_slug,
    get_current_company_status_period,
    get_directory_item,
    get_external_asset,
    get_knowledge_activity,
    get_knowledge_item,
    get_mcp,
    get_obsidian_note,
    get_project_bottleneck,
    get_project_milestone,
    get_project_todo,
    get_skill,
    get_tool,
    list_adrs,
    list_ai_profile_mcps,
    list_ai_profile_skills,
    list_ai_profile_tools,
    list_ai_profiles,
    list_ai_settings,
    list_all_hands_action_items,
    list_all_hands_decisions,
    list_all_hands_takeaways,
    list_approval_requests,
    list_attention_items,
    list_company_status_items,
    list_company_status_periods,
    list_directory_items,
    list_external_assets,
    list_knowledge_activities,
    list_knowledge_items,
    list_mcps,
    list_obsidian_notes,
    list_project_bottlenecks,
    list_project_milestones,
    list_project_todos,
    list_skills,
    list_tools,
)
from model_context_protocol.shared.helpers import (
    bot_name_fuzzy_match,
    project_name_fuzzy_match,
    room_name_fuzzy,
    username_fuzzy_match,
)


def _format_result(result: Any) -> str:
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


async def _resolve_project_id(project_id: Any = None, project_name: str | None = None) -> Any:
    if project_id is not None:
        return project_id
    if project_name:
        project = await project_name_fuzzy_match(project_name)
        if project is None:
            raise ValueError(f"Project not found: {project_name}")
        return project.get("id") or project.get("slug")
    return None


async def _resolve_room_id(project_id: Any, room_id: Any = None, room_name: str | None = None) -> Any:
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


async def _resolve_user_id(project_id: Any, user_id: Any = None, user_name: str | None = None) -> Any:
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


async def _resolve_bot_id(project_id: Any, bot_id: Any = None, bot_name: str | None = None) -> Any:
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


def _paginated_list(result: Any) -> list[dict[str, Any]]:
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


def hello(name: str = "World", **kwargs: Any) -> str:
    return f"Hello, {name}!"


async def decisions_waiting(**kwargs: Any) -> str:
    category = kwargs.get("category", "decisions_waiting")
    project_id = kwargs.get("project_id")
    project_name = kwargs.get("project_name")
    room_id = kwargs.get("room_id")
    room_name = kwargs.get("room_name")
    user_id = kwargs.get("user_id")
    user_name = kwargs.get("user_name")
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
        status=kwargs.get("status"),
        overdue=_coerce_bool(kwargs.get("overdue")),
        ai_confirm=_coerce_bool(kwargs.get("ai_confirm")),
        page=kwargs.get("page"),
        per_page=kwargs.get("per_page"),
    )
    return _format_result(result)


async def blockers(**kwargs: Any) -> str:
    kwargs["category"] = "blockers"
    return await decisions_waiting(**kwargs)


async def outcomes_review(**kwargs: Any) -> str:
    kwargs["category"] = "outcomes_review"
    return await decisions_waiting(**kwargs)


async def mentions(**kwargs: Any) -> str:
    kwargs["category"] = "mentions"
    return await decisions_waiting(**kwargs)


async def material_changes(**kwargs: Any) -> str:
    kwargs["category"] = "material_changes"
    return await decisions_waiting(**kwargs)


async def ai_confirm(**kwargs: Any) -> str:
    kwargs["category"] = "ai_confirm"
    return await decisions_waiting(**kwargs)


async def knowledge_proposals(**kwargs: Any) -> str:
    kwargs["category"] = "knowledge_proposals"
    return await decisions_waiting(**kwargs)


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
        return _format_result(None)
    if period_id is not None:
        result = await get_company_status_period(period_id)
        return _format_result(result)
    if _coerce_bool(current):
        result = await get_current_company_status_period()
        return _format_result(result)
    if slug:
        result = await get_company_status_period_by_slug(slug)
        return _format_result(result)
    if name:
        result = await get_company_status_period_by_name(name)
        return _format_result(result)
    result = await list_company_status_periods()
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


async def _company_status_category_tool(category: str, **kwargs: Any) -> str:
    project_id = kwargs.get("project_id")
    project_name = kwargs.get("project_name")
    resolved_project_id = None
    if project_id is not None or project_name:
        resolved_project_id = await _resolve_project_id(project_id, project_name)
    result = await list_company_status_items(
        company_status_period_id=kwargs.get("company_status_period_id"),
        project_id=resolved_project_id,
        category=category,
        status=kwargs.get("status"),
        health=kwargs.get("health"),
        badge=kwargs.get("badge"),
        owner_name=kwargs.get("owner_name"),
        page=kwargs.get("page"),
        per_page=kwargs.get("per_page"),
    )
    return _format_result(result)


async def project_milestones(
    project_id: Any = None,
    project_name: str | None = None,
    milestone_id: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
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


async def project_bottlenecks(
    project_id: Any = None,
    project_name: str | None = None,
    bottleneck_id: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    if bottleneck_id is not None:
        result = await get_project_bottleneck(resolved_project_id, bottleneck_id)
        return _format_result(result)
    result = await list_project_bottlenecks(
        resolved_project_id,
        active=_coerce_bool(active),
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def project_todos(
    project_id: Any = None,
    project_name: str | None = None,
    todo_id: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    if todo_id is not None:
        result = await get_project_todo(resolved_project_id, todo_id)
        return _format_result(result)
    result = await list_project_todos(
        resolved_project_id,
        active=_coerce_bool(active),
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def project_knowledge_items(
    project_id: Any = None,
    project_name: str | None = None,
    item_id: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
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


async def project_decision_records(
    project_id: Any = None,
    project_name: str | None = None,
    decision_record_id: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
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


async def project_all_hands_takeaway(
    project_id: Any = None,
    project_name: str | None = None,
    takeaway_id: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
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


async def project_all_hands_action_item(
    project_id: Any = None,
    project_name: str | None = None,
    action_item_id: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
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


async def project_all_hands_decision(
    project_id: Any = None,
    project_name: str | None = None,
    decision_id: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
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


async def external_knowledge_assets(
    project_id: Any = None,
    project_name: str | None = None,
    asset_id: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
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


async def knowledge_activity_log(
    project_id: Any = None,
    project_name: str | None = None,
    activity_id: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
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


async def tree_based_project_directory_data(
    project_id: Any = None,
    project_name: str | None = None,
    item_id: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
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


async def knowledge_summary_items(
    project_id: Any = None,
    project_name: str | None = None,
    item_id: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
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


async def project_obsidian_note(
    project_id: Any = None,
    project_name: str | None = None,
    note_id: Any = None,
    active: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
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


async def approval_requests(
    project_id: Any = None,
    project_name: str | None = None,
    room_id: Any = None,
    room_name: str | None = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    resolved_room_id = await _resolve_room_id(resolved_project_id, room_id, room_name)
    result = await list_approval_requests(
        resolved_project_id,
        resolved_room_id,
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def get_approval_request_tool(
    approval_request_id: Any,
    project_id: Any = None,
    project_name: str | None = None,
    room_id: Any = None,
    room_name: str | None = None,
    **kwargs: Any,
) -> str:
    resolved_project_id = await _resolve_project_id(project_id, project_name)
    resolved_room_id = await _resolve_room_id(resolved_project_id, room_id, room_name)
    result = await get_approval_request(
        resolved_project_id, resolved_room_id, approval_request_id
    )
    return _format_result(result)


async def list_ai_profiles_tool(**kwargs: Any) -> str:
    return _format_result(await list_ai_profiles())


async def get_ai_profile_tool(ai_profile_id: Any, **kwargs: Any) -> str:
    return _format_result(await get_ai_profile(ai_profile_id))


async def list_ai_settings_tool(**kwargs: Any) -> str:
    return _format_result(await list_ai_settings())


async def get_ai_setting_tool(ai_setting_id: Any, **kwargs: Any) -> str:
    return _format_result(await get_ai_setting(ai_setting_id))


async def list_mcps_tool(**kwargs: Any) -> str:
    return _format_result(await list_mcps())


async def get_mcp_tool(mcp_id: Any, **kwargs: Any) -> str:
    return _format_result(await get_mcp(mcp_id))


async def list_tools_tool(**kwargs: Any) -> str:
    return _format_result(await list_tools())


async def get_tool_tool(tool_id: Any, **kwargs: Any) -> str:
    return _format_result(await get_tool(tool_id))


async def list_skills_tool(**kwargs: Any) -> str:
    return _format_result(await list_skills())


async def get_skill_tool(skill_id: Any, **kwargs: Any) -> str:
    return _format_result(await get_skill(skill_id))


async def list_ai_profile_tools_tool(ai_profile_id: Any = None, tool_id: Any = None, **kwargs: Any) -> str:
    return _format_result(await list_ai_profile_tools(ai_profile_id=ai_profile_id, tool_id=tool_id))


async def get_ai_profile_tool_link(ai_profile_tool_id: Any, **kwargs: Any) -> str:
    return _format_result(await get_ai_profile_tool_record(ai_profile_tool_id))


async def list_ai_profile_skills_tool(ai_profile_id: Any = None, skill_id: Any = None, **kwargs: Any) -> str:
    return _format_result(await list_ai_profile_skills(ai_profile_id=ai_profile_id, skill_id=skill_id))


async def get_ai_profile_skill_tool(ai_profile_skill_id: Any, **kwargs: Any) -> str:
    return _format_result(await get_ai_profile_skill(ai_profile_skill_id))


async def list_ai_profile_mcps_tool(ai_profile_id: Any = None, mcp_id: Any = None, **kwargs: Any) -> str:
    return _format_result(await list_ai_profile_mcps(ai_profile_id=ai_profile_id, mcp_id=mcp_id))


async def get_ai_profile_mcp_tool(ai_profile_mcp_id: Any, **kwargs: Any) -> str:
    return _format_result(await get_ai_profile_mcp(ai_profile_mcp_id))


TOOL_HANDLERS: dict[str, Callable[..., Any]] = {
    "hello": hello,
    "decisions_waiting": decisions_waiting,
    "blockers": blockers,
    "outcomes_review": outcomes_review,
    "mentions": mentions,
    "material_changes": material_changes,
    "ai_confirm": ai_confirm,
    "knowledge_proposals": knowledge_proposals,
    "company_status_period": company_status_period,
    "priorities": priorities,
    "progress": progress,
    "risks": risks,
    "dependencies": dependencies,
    "changes": changes,
    "decisions": decisions,
    "learnings": learnings,
    "project_milestones": project_milestones,
    "project_bottlenecks": project_bottlenecks,
    "project_todos": project_todos,
    "project_knowledge_items": project_knowledge_items,
    "ProjectAllHandsTakeaway": project_all_hands_takeaway,
    "project_all_hands_takeaway": project_all_hands_takeaway,
    "ProjectAllHandsActionItem": project_all_hands_action_item,
    "project_all_hands_action_item": project_all_hands_action_item,
    "ProjectAllHandsDecision": project_all_hands_decision,
    "project_all_hands_decision": project_all_hands_decision,
    "ProjectDecisionRecord": project_decision_records,
    "project_decision_records": project_decision_records,
    "external_knowledge_assets": external_knowledge_assets,
    "external_assets": external_knowledge_assets,
    "knowledge_activity_log": knowledge_activity_log,
    "tree_based_project_directory_data": tree_based_project_directory_data,
    "knowledge_summary_items": knowledge_summary_items,
    "ProjectObsidianNote": project_obsidian_note,
    "project_obsidian_note": project_obsidian_note,
    "approval_requests": approval_requests,
    "ApprovalRequests": approval_requests,
    "get_approval_request": get_approval_request_tool,
    "GetApprovalRequest": get_approval_request_tool,
    "list_ai_profiles": list_ai_profiles_tool,
    "get_ai_profile": get_ai_profile_tool,
    "list_ai_settings": list_ai_settings_tool,
    "get_ai_setting": get_ai_setting_tool,
    "list_mcps": list_mcps_tool,
    "get_mcp": get_mcp_tool,
    "list_tools": list_tools_tool,
    "get_tool": get_tool_tool,
    "list_skills": list_skills_tool,
    "get_skill": get_skill_tool,
    "list_ai_profile_tools": list_ai_profile_tools_tool,
    "get_ai_profile_tool": get_ai_profile_tool_link,
    "list_ai_profile_skills": list_ai_profile_skills_tool,
    "get_ai_profile_skill": get_ai_profile_skill_tool,
    "list_ai_profile_mcps": list_ai_profile_mcps_tool,
    "get_ai_profile_mcp": get_ai_profile_mcp_tool,
}


_READ_ONLY_TOOL_DEFINITIONS = [
    (
        "hello",
        "Say hello to a given name or the world",
        {"type": "object", "properties": {"name": {"type": "string", "description": "The name to greet", "default": "World"}}},
    ),
    ("decisions_waiting", "List company-home decisions-waiting attention items", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "room_id": {"type": ["string", "integer"]}, "room_name": {"type": "string"}, "user_id": {"type": ["string", "integer"]}, "user_name": {"type": "string"}, "status": {"type": "string"}, "overdue": {"type": "boolean"}, "ai_confirm": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("blockers", "List company-home blocker attention items", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "room_id": {"type": ["string", "integer"]}, "room_name": {"type": "string"}, "user_id": {"type": ["string", "integer"]}, "user_name": {"type": "string"}, "status": {"type": "string"}, "overdue": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("outcomes_review", "List company-home outcomes-review attention items", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "room_id": {"type": ["string", "integer"]}, "room_name": {"type": "string"}, "user_id": {"type": ["string", "integer"]}, "user_name": {"type": "string"}, "status": {"type": "string"}, "overdue": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("mentions", "List company-home mention attention items", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "room_id": {"type": ["string", "integer"]}, "room_name": {"type": "string"}, "user_id": {"type": ["string", "integer"]}, "user_name": {"type": "string"}, "status": {"type": "string"}, "overdue": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("material_changes", "List company-home material-change attention items", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "room_id": {"type": ["string", "integer"]}, "room_name": {"type": "string"}, "user_id": {"type": ["string", "integer"]}, "user_name": {"type": "string"}, "status": {"type": "string"}, "overdue": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("ai_confirm", "List company-home AI-confirm attention items", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "room_id": {"type": ["string", "integer"]}, "room_name": {"type": "string"}, "user_id": {"type": ["string", "integer"]}, "user_name": {"type": "string"}, "status": {"type": "string"}, "overdue": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("knowledge_proposals", "List company-home knowledge-proposal attention items", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "room_id": {"type": ["string", "integer"]}, "room_name": {"type": "string"}, "user_id": {"type": ["string", "integer"]}, "user_name": {"type": "string"}, "status": {"type": "string"}, "overdue": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("company_status_period", "List or fetch company status periods", {"type": "object", "properties": {"period_id": {"type": ["string", "integer"]}, "name": {"type": "string"}, "slug": {"type": "string"}, "current": {"type": "boolean"}, "starts_on": {"type": "string"}, "ends_on": {"type": "string"}, "position": {"type": "integer"}}}),
    ("priorities", "List priorities company-status items", {"type": "object", "properties": {"company_status_period_id": {"type": ["string", "integer"]}, "project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "status": {"type": "string"}, "health": {"type": "string"}, "badge": {"type": "string"}, "owner_name": {"type": "string"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("progress", "List progress company-status items", {"type": "object", "properties": {"company_status_period_id": {"type": ["string", "integer"]}, "project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "status": {"type": "string"}, "health": {"type": "string"}, "badge": {"type": "string"}, "owner_name": {"type": "string"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("risks", "List risk company-status items", {"type": "object", "properties": {"company_status_period_id": {"type": ["string", "integer"]}, "project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "status": {"type": "string"}, "health": {"type": "string"}, "badge": {"type": "string"}, "owner_name": {"type": "string"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("dependencies", "List dependency company-status items", {"type": "object", "properties": {"company_status_period_id": {"type": ["string", "integer"]}, "project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "status": {"type": "string"}, "health": {"type": "string"}, "badge": {"type": "string"}, "owner_name": {"type": "string"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("changes", "List change company-status items", {"type": "object", "properties": {"company_status_period_id": {"type": ["string", "integer"]}, "project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "status": {"type": "string"}, "health": {"type": "string"}, "badge": {"type": "string"}, "owner_name": {"type": "string"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("decisions", "List decision company-status items", {"type": "object", "properties": {"company_status_period_id": {"type": ["string", "integer"]}, "project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "status": {"type": "string"}, "health": {"type": "string"}, "badge": {"type": "string"}, "owner_name": {"type": "string"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("learnings", "List learning company-status items", {"type": "object", "properties": {"company_status_period_id": {"type": ["string", "integer"]}, "project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "status": {"type": "string"}, "health": {"type": "string"}, "badge": {"type": "string"}, "owner_name": {"type": "string"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("project_milestones", "List project milestones", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "milestone_id": {"type": ["string", "integer"]}, "active": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("project_bottlenecks", "List project bottlenecks", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "bottleneck_id": {"type": ["string", "integer"]}, "active": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("project_todos", "List project todos", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "todo_id": {"type": ["string", "integer"]}, "active": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("project_knowledge_items", "List project knowledge items", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "item_id": {"type": ["string", "integer"]}, "active": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("project_decision_records", "List project decision records", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "decision_record_id": {"type": ["string", "integer"]}, "active": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("project_all_hands_takeaway", "List project all-hands takeaways", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "takeaway_id": {"type": ["string", "integer"]}, "active": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("project_all_hands_action_item", "List project all-hands action items", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "action_item_id": {"type": ["string", "integer"]}, "active": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("project_all_hands_decision", "List project all-hands decisions", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "decision_id": {"type": ["string", "integer"]}, "active": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("external_knowledge_assets", "List project external knowledge assets", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "asset_id": {"type": ["string", "integer"]}, "active": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("knowledge_activity_log", "List project knowledge activity log", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "activity_id": {"type": ["string", "integer"]}, "active": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("tree_based_project_directory_data", "List project directory tree data", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "item_id": {"type": ["string", "integer"]}, "active": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("knowledge_summary_items", "List project summary knowledge items", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "item_id": {"type": ["string", "integer"]}, "active": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("project_obsidian_note", "List project Obsidian notes", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "note_id": {"type": ["string", "integer"]}, "active": {"type": "boolean"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("approval_requests", "List approval requests for a project and room", {"type": "object", "properties": {"project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "room_id": {"type": ["string", "integer"]}, "room_name": {"type": "string"}, "page": {"type": "integer"}, "per_page": {"type": "integer"}}}),
    ("get_approval_request", "Fetch a single approval request", {"type": "object", "properties": {"approval_request_id": {"type": ["string", "integer"]}, "project_id": {"type": ["string", "integer"]}, "project_name": {"type": "string"}, "room_id": {"type": ["string", "integer"]}, "room_name": {"type": "string"}}}),
    ("list_ai_profiles", "List AI profiles", {"type": "object", "properties": {}}),
    ("get_ai_profile", "Fetch one AI profile", {"type": "object", "properties": {"ai_profile_id": {"type": ["string", "integer"]}}}),
    ("list_ai_settings", "List AI settings", {"type": "object", "properties": {}}),
    ("get_ai_setting", "Fetch one AI setting", {"type": "object", "properties": {"ai_setting_id": {"type": ["string", "integer"]}}}),
    ("list_mcps", "List MCP registrations", {"type": "object", "properties": {}}),
    ("get_mcp", "Fetch one MCP registration", {"type": "object", "properties": {"mcp_id": {"type": ["string", "integer"]}}}),
    ("list_tools", "List tool definitions", {"type": "object", "properties": {}}),
    ("get_tool", "Fetch one tool definition", {"type": "object", "properties": {"tool_id": {"type": ["string", "integer"]}}}),
    ("list_skills", "List skills", {"type": "object", "properties": {}}),
    ("get_skill", "Fetch one skill", {"type": "object", "properties": {"skill_id": {"type": ["string", "integer"]}}}),
    ("list_ai_profile_tools", "List AI profile tool mappings", {"type": "object", "properties": {"ai_profile_id": {"type": ["string", "integer"]}, "tool_id": {"type": ["string", "integer"]}}}),
    ("get_ai_profile_tool", "Fetch one AI profile tool mapping", {"type": "object", "properties": {"ai_profile_tool_id": {"type": ["string", "integer"]}}}),
    ("list_ai_profile_skills", "List AI profile skill mappings", {"type": "object", "properties": {"ai_profile_id": {"type": ["string", "integer"]}, "skill_id": {"type": ["string", "integer"]}}}),
    ("get_ai_profile_skill", "Fetch one AI profile skill mapping", {"type": "object", "properties": {"ai_profile_skill_id": {"type": ["string", "integer"]}}}),
    ("list_ai_profile_mcps", "List AI profile MCP mappings", {"type": "object", "properties": {"ai_profile_id": {"type": ["string", "integer"]}, "mcp_id": {"type": ["string", "integer"]}}}),
    ("get_ai_profile_mcp", "Fetch one AI profile MCP mapping", {"type": "object", "properties": {"ai_profile_mcp_id": {"type": ["string", "integer"]}}}),
]


TOOL_DEFINITIONS = [
    {"name": name, "description": description, "inputSchema": schema}
    for name, description, schema in _READ_ONLY_TOOL_DEFINITIONS
]


__all__ = [
    "TOOL_DEFINITIONS",
    "TOOL_HANDLERS",
    "hello",
    "decisions_waiting",
    "blockers",
    "outcomes_review",
    "mentions",
    "material_changes",
    "ai_confirm",
    "knowledge_proposals",
    "company_status_period",
    "priorities",
    "progress",
    "risks",
    "dependencies",
    "changes",
    "decisions",
    "learnings",
    "project_milestones",
    "project_bottlenecks",
    "project_todos",
    "project_knowledge_items",
    "project_decision_records",
    "project_all_hands_takeaway",
    "project_all_hands_action_item",
    "project_all_hands_decision",
    "external_knowledge_assets",
    "knowledge_activity_log",
    "tree_based_project_directory_data",
    "knowledge_summary_items",
    "project_obsidian_note",
    "approval_requests",
    "get_approval_request_tool",
    "list_ai_profiles_tool",
    "get_ai_profile_tool",
    "list_ai_settings_tool",
    "get_ai_setting_tool",
    "list_mcps_tool",
    "get_mcp_tool",
    "list_tools_tool",
    "get_tool_tool",
    "list_skills_tool",
    "get_skill_tool",
    "list_ai_profile_tools_tool",
    "get_ai_profile_tool_link",
    "list_ai_profile_skills_tool",
    "get_ai_profile_skill_tool",
    "list_ai_profile_mcps_tool",
    "get_ai_profile_mcp_tool",
]
