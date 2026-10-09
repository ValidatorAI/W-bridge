import json
from typing import Any, Callable

from space.api import (
    create_task,
    delete_task,
    get_task,
    list_tasks,
    update_task,
)


def hello(name: str = "World", **kwargs: Any) -> str:
    return f"Hello, {name}!"


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


async def tasks(
    room_id: Any = None,
    project_id: Any = None,
    grand_parent_id: Any = None,
    added_to_kanban: Any = None,
    runned: Any = None,
    **kwargs: Any,
) -> str:
    result = await list_tasks(
        room_id=room_id,
        project_id=project_id,
        grand_parent_id=grand_parent_id,
        added_to_kanban=_coerce_bool(added_to_kanban),
        runned=_coerce_bool(runned),
    )
    return _format_result(result)


async def get_task_tool(task_id: Any, **kwargs: Any) -> str:
    return _format_result(await get_task(task_id))


async def create_task_tool(description: str, **kwargs: Any) -> str:
    result = await create_task(
        description=description,
        adder_profile=kwargs.get("adder_profile"),
        token_used=kwargs.get("token_used"),
        token_budget=kwargs.get("token_budget"),
        usd_usage=kwargs.get("usd_usage"),
        usd_budget=kwargs.get("usd_budget"),
        room_id=kwargs.get("room_id"),
        project_id=kwargs.get("project_id"),
        assigneee_profile=kwargs.get("assigneee_profile"),
        added_to_kanban=_coerce_bool(kwargs.get("added_to_kanban")),
        runned=_coerce_bool(kwargs.get("runned")),
        parent_task_id=kwargs.get("parent_task_id"),
        grand_parent_id=kwargs.get("grand_parent_id"),
        importance=kwargs.get("importance"),
        level=kwargs.get("level"),
    )
    return _format_result(result)


async def update_task_tool(task_id: Any, **kwargs: Any) -> str:
    result = await update_task(
        task_id,
        adder_profile=kwargs.get("adder_profile"),
        token_used=kwargs.get("token_used"),
        token_budget=kwargs.get("token_budget"),
        usd_usage=kwargs.get("usd_usage"),
        usd_budget=kwargs.get("usd_budget"),
        room_id=kwargs.get("room_id"),
        project_id=kwargs.get("project_id"),
        description=kwargs.get("description"),
        assigneee_profile=kwargs.get("assigneee_profile"),
        added_to_kanban=_coerce_bool(kwargs.get("added_to_kanban")),
        runned=_coerce_bool(kwargs.get("runned")),
        parent_task_id=kwargs.get("parent_task_id"),
        grand_parent_id=kwargs.get("grand_parent_id"),
        importance=kwargs.get("importance"),
        level=kwargs.get("level"),
    )
    return _format_result(result)


async def delete_task_tool(task_id: Any, **kwargs: Any) -> str:
    return _format_result(await delete_task(task_id))


TOOL_HANDLERS: dict[str, Callable[..., Any]] = {
    "hello": hello,
    "tasks": tasks,
    "list_tasks": tasks,
    "get_task": get_task_tool,
    "create_task": create_task_tool,
    "update_task": update_task_tool,
    "delete_task": delete_task_tool,
}


TOOL_DEFINITIONS = [
    {
        "name": "hello",
        "description": "Say hello to a given name or the world",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name to greet",
                    "default": "World",
                }
            },
        },
    },
    {
        "name": "tasks",
        "description": "List Bonfire tasks with optional room, project, kanban, and run-state filters",
        "inputSchema": {
            "type": "object",
            "properties": {
                "room_id": {"type": ["string", "integer"]},
                "project_id": {"type": ["string", "integer"]},
                "grand_parent_id": {"type": ["string", "integer"]},
                "added_to_kanban": {"type": "boolean"},
                "runned": {"type": "boolean"},
            },
        },
    },
    {
        "name": "list_tasks",
        "description": "Alias for tasks",
        "inputSchema": {
            "type": "object",
            "properties": {
                "room_id": {"type": ["string", "integer"]},
                "project_id": {"type": ["string", "integer"]},
                "grand_parent_id": {"type": ["string", "integer"]},
                "added_to_kanban": {"type": "boolean"},
                "runned": {"type": "boolean"},
            },
        },
    },
    {
        "name": "get_task",
        "description": "Fetch a single Bonfire task by ID",
        "inputSchema": {
            "type": "object",
            "properties": {"task_id": {"type": ["string", "integer"]}},
            "required": ["task_id"],
        },
    },
    {
        "name": "create_task",
        "description": "Create a Bonfire task",
        "inputSchema": {
            "type": "object",
            "properties": {
                "description": {"type": "string"},
                "adder_profile": {"type": "string"},
                "token_used": {"type": "integer"},
                "token_budget": {"type": "integer"},
                "usd_usage": {"type": "number"},
                "usd_budget": {"type": "number"},
                "room_id": {"type": ["string", "integer"]},
                "project_id": {"type": ["string", "integer"]},
                "assigneee_profile": {"type": "string"},
                "added_to_kanban": {"type": "boolean"},
                "runned": {"type": "boolean"},
                "parent_task_id": {"type": ["string", "integer"]},
                "grand_parent_id": {"type": ["string", "integer"]},
                "importance": {"type": "integer"},
                "level": {"type": "integer"},
            },
            "required": ["description"],
        },
    },
    {
        "name": "update_task",
        "description": "Update a Bonfire task by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {"type": ["string", "integer"]},
                "description": {"type": "string"},
                "adder_profile": {"type": "string"},
                "token_used": {"type": "integer"},
                "token_budget": {"type": "integer"},
                "usd_usage": {"type": "number"},
                "usd_budget": {"type": "number"},
                "room_id": {"type": ["string", "integer"]},
                "project_id": {"type": ["string", "integer"]},
                "assigneee_profile": {"type": "string"},
                "added_to_kanban": {"type": "boolean"},
                "runned": {"type": "boolean"},
                "parent_task_id": {"type": ["string", "integer"]},
                "grand_parent_id": {"type": ["string", "integer"]},
                "importance": {"type": "integer"},
                "level": {"type": "integer"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "delete_task",
        "description": "Delete a Bonfire task by ID",
        "inputSchema": {
            "type": "object",
            "properties": {"task_id": {"type": ["string", "integer"]}},
            "required": ["task_id"],
        },
    },
]


__all__ = [
    "TOOL_DEFINITIONS",
    "TOOL_HANDLERS",
    "hello",
    "tasks",
    "get_task_tool",
    "create_task_tool",
    "update_task_tool",
    "delete_task_tool",
]
