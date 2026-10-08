import json
from typing import Any, Callable

from model_context_protocol.read.tools import (
    TOOL_DEFINITIONS as READ_TOOL_DEFINITIONS,
    TOOL_HANDLERS as READ_TOOL_HANDLERS,
)
from space.api import (
    create_message_analysis,
    create_message_topic,
    create_room_history_topic,
    create_topic,
    delete_message_analysis,
    delete_message_topic,
    delete_room_history_topic,
    delete_topic,
    get_message_analysis,
    get_message_topic,
    get_room_history_topic,
    get_topic,
    list_message_analysis,
    list_message_topics,
    list_room_history_topics,
    list_topics,
    update_message_analysis,
    update_message_topic,
    update_room_history_topic,
    update_topic,
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


async def topics(
    project_id: Any = None,
    active: Any = None,
    need_an_action: Any = None,
    room_id: Any = None,
    parent_topic_id: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    result = await list_topics(
        project_id=project_id,
        active=_coerce_bool(active),
        need_an_action=_coerce_bool(need_an_action),
        room_id=room_id,
        parent_topic_id=parent_topic_id,
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def get_topic_tool(topic_id: Any, **kwargs: Any) -> str:
    return _format_result(await get_topic(topic_id))


async def create_topic_tool(project_id: Any, name: str, **kwargs: Any) -> str:
    result = await create_topic(
        project_id=project_id,
        name=name,
        parent_topic_id=kwargs.get("parent_topic_id"),
        related_topics=kwargs.get("related_topics"),
        active=_coerce_bool(kwargs.get("active")),
        importance_level=kwargs.get("importance_level"),
        memory=kwargs.get("memory"),
        state=kwargs.get("state"),
        need_an_action=_coerce_bool(kwargs.get("need_an_action")),
        required_actions=kwargs.get("required_actions"),
    )
    return _format_result(result)


async def update_topic_tool(topic_id: Any, **kwargs: Any) -> str:
    result = await update_topic(
        topic_id,
        project_id=kwargs.get("project_id"),
        parent_topic_id=kwargs.get("parent_topic_id"),
        name=kwargs.get("name"),
        related_topics=kwargs.get("related_topics"),
        active=_coerce_bool(kwargs.get("active")),
        importance_level=kwargs.get("importance_level"),
        memory=kwargs.get("memory"),
        state=kwargs.get("state"),
        need_an_action=_coerce_bool(kwargs.get("need_an_action")),
        required_actions=kwargs.get("required_actions"),
    )
    return _format_result(result)


async def delete_topic_tool(topic_id: Any, **kwargs: Any) -> str:
    return _format_result(await delete_topic(topic_id))


async def message_analysis(
    message_id: Any = None,
    importance_level: Any = None,
    is_a_response: Any = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    result = await list_message_analysis(
        message_id=message_id,
        importance_level=importance_level,
        is_a_response=_coerce_bool(is_a_response),
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def get_message_analysis_tool(message_analysis_id: Any, **kwargs: Any) -> str:
    return _format_result(await get_message_analysis(message_analysis_id))


async def create_message_analysis_tool(
    message_id: Any,
    importance_level: int,
    message_content_summary: str,
    message_type: str,
    **kwargs: Any,
) -> str:
    result = await create_message_analysis(
        message_id=message_id,
        importance_level=importance_level,
        message_content_summary=message_content_summary,
        message_type=message_type,
        tags=kwargs.get("tags"),
        is_a_response=_coerce_bool(kwargs.get("is_a_response")),
    )
    return _format_result(result)


async def update_message_analysis_tool(message_analysis_id: Any, **kwargs: Any) -> str:
    result = await update_message_analysis(
        message_analysis_id,
        message_id=kwargs.get("message_id"),
        importance_level=kwargs.get("importance_level"),
        message_content_summary=kwargs.get("message_content_summary"),
        message_type=kwargs.get("message_type"),
        tags=kwargs.get("tags"),
        is_a_response=_coerce_bool(kwargs.get("is_a_response")),
    )
    return _format_result(result)


async def delete_message_analysis_tool(message_analysis_id: Any, **kwargs: Any) -> str:
    return _format_result(await delete_message_analysis(message_analysis_id))


async def message_topics(
    topic_id: Any = None,
    message_id: Any = None,
    created_date: str | None = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    result = await list_message_topics(
        topic_id=topic_id,
        message_id=message_id,
        created_date=created_date,
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def get_message_topic_tool(message_topic_id: Any, **kwargs: Any) -> str:
    return _format_result(await get_message_topic(message_topic_id))


async def create_message_topic_tool(topic_id: Any, message_id: Any, **kwargs: Any) -> str:
    result = await create_message_topic(
        topic_id=topic_id,
        message_id=message_id,
        created_date=kwargs.get("created_date"),
    )
    return _format_result(result)


async def update_message_topic_tool(message_topic_id: Any, **kwargs: Any) -> str:
    result = await update_message_topic(
        message_topic_id,
        topic_id=kwargs.get("topic_id"),
        message_id=kwargs.get("message_id"),
        created_date=kwargs.get("created_date"),
    )
    return _format_result(result)


async def delete_message_topic_tool(message_topic_id: Any, **kwargs: Any) -> str:
    return _format_result(await delete_message_topic(message_topic_id))


async def room_history_topics(
    room_id: Any = None,
    created_date: str | None = None,
    page: int | None = None,
    per_page: int | None = None,
    **kwargs: Any,
) -> str:
    result = await list_room_history_topics(
        room_id=room_id,
        created_date=created_date,
        page=page,
        per_page=per_page,
    )
    return _format_result(result)


async def get_room_history_topic_tool(room_history_topic_id: Any, **kwargs: Any) -> str:
    return _format_result(await get_room_history_topic(room_history_topic_id))


async def create_room_history_topic_tool(room_id: Any, **kwargs: Any) -> str:
    result = await create_room_history_topic(
        room_id=room_id,
        created_date=kwargs.get("created_date"),
        last_state=kwargs.get("last_state"),
    )
    return _format_result(result)


async def update_room_history_topic_tool(room_history_topic_id: Any, **kwargs: Any) -> str:
    result = await update_room_history_topic(
        room_history_topic_id,
        room_id=kwargs.get("room_id"),
        created_date=kwargs.get("created_date"),
        last_state=kwargs.get("last_state"),
    )
    return _format_result(result)


async def delete_room_history_topic_tool(room_history_topic_id: Any, **kwargs: Any) -> str:
    return _format_result(await delete_room_history_topic(room_history_topic_id))


TOOL_HANDLERS: dict[str, Callable[..., Any]] = {
    **READ_TOOL_HANDLERS,
    "hello": hello,
    "topics": topics,
    "list_topics": topics,
    "get_topic": get_topic_tool,
    "create_topic": create_topic_tool,
    "update_topic": update_topic_tool,
    "delete_topic": delete_topic_tool,
    "message_analysis": message_analysis,
    "list_message_analysis": message_analysis,
    "get_message_analysis": get_message_analysis_tool,
    "create_message_analysis": create_message_analysis_tool,
    "update_message_analysis": update_message_analysis_tool,
    "delete_message_analysis": delete_message_analysis_tool,
    "message_topics": message_topics,
    "list_message_topics": message_topics,
    "get_message_topic": get_message_topic_tool,
    "create_message_topic": create_message_topic_tool,
    "update_message_topic": update_message_topic_tool,
    "delete_message_topic": delete_message_topic_tool,
    "room_history_topics": room_history_topics,
    "list_room_history_topics": room_history_topics,
    "get_room_history_topic": get_room_history_topic_tool,
    "create_room_history_topic": create_room_history_topic_tool,
    "update_room_history_topic": update_room_history_topic_tool,
    "delete_room_history_topic": delete_room_history_topic_tool,
}


TOOL_DEFINITIONS = [
    *READ_TOOL_DEFINITIONS,
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
        "name": "topics",
        "description": "List Bonfire topics with optional project, room, parent, active, and action filters",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": ["string", "integer"]},
                "active": {"type": "boolean"},
                "need_an_action": {"type": "boolean"},
                "room_id": {"type": ["string", "integer"]},
                "parent_topic_id": {"type": ["string", "integer"]},
                "page": {"type": "integer"},
                "per_page": {"type": "integer"},
            },
        },
    },
    {
        "name": "list_topics",
        "description": "Alias for topics",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": ["string", "integer"]},
                "active": {"type": "boolean"},
                "need_an_action": {"type": "boolean"},
                "room_id": {"type": ["string", "integer"]},
                "parent_topic_id": {"type": ["string", "integer"]},
                "page": {"type": "integer"},
                "per_page": {"type": "integer"},
            },
        },
    },
    {
        "name": "get_topic",
        "description": "Fetch a single Bonfire topic by ID",
        "inputSchema": {
            "type": "object",
            "properties": {"topic_id": {"type": ["string", "integer"]}},
            "required": ["topic_id"],
        },
    },
    {
        "name": "create_topic",
        "description": "Create a Bonfire topic",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": ["string", "integer"]},
                "name": {"type": "string"},
                "parent_topic_id": {"type": ["string", "integer"]},
                "related_topics": {"type": "string"},
                "active": {"type": "boolean"},
                "importance_level": {"type": "integer"},
                "memory": {"type": "string"},
                "state": {"type": "string"},
                "need_an_action": {"type": "boolean"},
                "required_actions": {"type": "string"},
            },
            "required": ["project_id", "name"],
        },
    },
    {
        "name": "update_topic",
        "description": "Update a Bonfire topic by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic_id": {"type": ["string", "integer"]},
                "project_id": {"type": ["string", "integer"]},
                "name": {"type": "string"},
                "parent_topic_id": {"type": ["string", "integer"]},
                "related_topics": {"type": "string"},
                "active": {"type": "boolean"},
                "importance_level": {"type": "integer"},
                "memory": {"type": "string"},
                "state": {"type": "string"},
                "need_an_action": {"type": "boolean"},
                "required_actions": {"type": "string"},
            },
            "required": ["topic_id"],
        },
    },
    {
        "name": "delete_topic",
        "description": "Delete a Bonfire topic by ID",
        "inputSchema": {
            "type": "object",
            "properties": {"topic_id": {"type": ["string", "integer"]}},
            "required": ["topic_id"],
        },
    },
    {
        "name": "message_analysis",
        "description": "List Bonfire message analysis rows with optional message and importance filters",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message_id": {"type": ["string", "integer"]},
                "importance_level": {"type": "integer"},
                "is_a_response": {"type": "boolean"},
                "page": {"type": "integer"},
                "per_page": {"type": "integer"},
            },
        },
    },
    {
        "name": "list_message_analysis",
        "description": "Alias for message_analysis",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message_id": {"type": ["string", "integer"]},
                "importance_level": {"type": "integer"},
                "is_a_response": {"type": "boolean"},
                "page": {"type": "integer"},
                "per_page": {"type": "integer"},
            },
        },
    },
    {
        "name": "get_message_analysis",
        "description": "Fetch a single Bonfire message analysis row by ID",
        "inputSchema": {
            "type": "object",
            "properties": {"message_analysis_id": {"type": ["string", "integer"]}},
            "required": ["message_analysis_id"],
        },
    },
    {
        "name": "create_message_analysis",
        "description": "Create a Bonfire message analysis record",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message_id": {"type": ["string", "integer"]},
                "importance_level": {"type": "integer"},
                "message_content_summary": {"type": "string"},
                "message_type": {"type": "string"},
                "tags": {"type": "string"},
                "is_a_response": {"type": "boolean"},
            },
            "required": ["message_id", "importance_level", "message_content_summary", "message_type"],
        },
    },
    {
        "name": "update_message_analysis",
        "description": "Update a Bonfire message analysis record by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message_analysis_id": {"type": ["string", "integer"]},
                "message_id": {"type": ["string", "integer"]},
                "importance_level": {"type": "integer"},
                "message_content_summary": {"type": "string"},
                "message_type": {"type": "string"},
                "tags": {"type": "string"},
                "is_a_response": {"type": "boolean"},
            },
            "required": ["message_analysis_id"],
        },
    },
    {
        "name": "delete_message_analysis",
        "description": "Delete a Bonfire message analysis record by ID",
        "inputSchema": {
            "type": "object",
            "properties": {"message_analysis_id": {"type": ["string", "integer"]}},
            "required": ["message_analysis_id"],
        },
    },
    {
        "name": "message_topics",
        "description": "List Bonfire message-topic links with optional topic/message filters",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic_id": {"type": ["string", "integer"]},
                "message_id": {"type": ["string", "integer"]},
                "created_date": {"type": "string"},
                "page": {"type": "integer"},
                "per_page": {"type": "integer"},
            },
        },
    },
    {
        "name": "list_message_topics",
        "description": "Alias for message_topics",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic_id": {"type": ["string", "integer"]},
                "message_id": {"type": ["string", "integer"]},
                "created_date": {"type": "string"},
                "page": {"type": "integer"},
                "per_page": {"type": "integer"},
            },
        },
    },
    {
        "name": "get_message_topic",
        "description": "Fetch a single Bonfire message-topic link by ID",
        "inputSchema": {
            "type": "object",
            "properties": {"message_topic_id": {"type": ["string", "integer"]}},
            "required": ["message_topic_id"],
        },
    },
    {
        "name": "create_message_topic",
        "description": "Create a Bonfire message-topic link",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic_id": {"type": ["string", "integer"]},
                "message_id": {"type": ["string", "integer"]},
                "created_date": {"type": "string"},
            },
            "required": ["topic_id", "message_id"],
        },
    },
    {
        "name": "update_message_topic",
        "description": "Update a Bonfire message-topic link by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message_topic_id": {"type": ["string", "integer"]},
                "topic_id": {"type": ["string", "integer"]},
                "message_id": {"type": ["string", "integer"]},
                "created_date": {"type": "string"},
            },
            "required": ["message_topic_id"],
        },
    },
    {
        "name": "delete_message_topic",
        "description": "Delete a Bonfire message-topic link by ID",
        "inputSchema": {
            "type": "object",
            "properties": {"message_topic_id": {"type": ["string", "integer"]}},
            "required": ["message_topic_id"],
        },
    },
    {
        "name": "room_history_topics",
        "description": "List Bonfire room history topic snapshots with optional room/date filters",
        "inputSchema": {
            "type": "object",
            "properties": {
                "room_id": {"type": ["string", "integer"]},
                "created_date": {"type": "string"},
                "page": {"type": "integer"},
                "per_page": {"type": "integer"},
            },
        },
    },
    {
        "name": "list_room_history_topics",
        "description": "Alias for room_history_topics",
        "inputSchema": {
            "type": "object",
            "properties": {
                "room_id": {"type": ["string", "integer"]},
                "created_date": {"type": "string"},
                "page": {"type": "integer"},
                "per_page": {"type": "integer"},
            },
        },
    },
    {
        "name": "get_room_history_topic",
        "description": "Fetch a single Bonfire room history topic snapshot by ID",
        "inputSchema": {
            "type": "object",
            "properties": {"room_history_topic_id": {"type": ["string", "integer"]}},
            "required": ["room_history_topic_id"],
        },
    },
    {
        "name": "create_room_history_topic",
        "description": "Create a Bonfire room history topic snapshot",
        "inputSchema": {
            "type": "object",
            "properties": {
                "room_id": {"type": ["string", "integer"]},
                "created_date": {"type": "string"},
                "last_state": {"type": "string"},
            },
            "required": ["room_id"],
        },
    },
    {
        "name": "update_room_history_topic",
        "description": "Update a Bonfire room history topic snapshot by ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "room_history_topic_id": {"type": ["string", "integer"]},
                "room_id": {"type": ["string", "integer"]},
                "created_date": {"type": "string"},
                "last_state": {"type": "string"},
            },
            "required": ["room_history_topic_id"],
        },
    },
    {
        "name": "delete_room_history_topic",
        "description": "Delete a Bonfire room history topic snapshot by ID",
        "inputSchema": {
            "type": "object",
            "properties": {"room_history_topic_id": {"type": ["string", "integer"]}},
            "required": ["room_history_topic_id"],
        },
    },
]


__all__ = [
    "TOOL_DEFINITIONS",
    "TOOL_HANDLERS",
    "hello",
    "topics",
    "get_topic_tool",
    "create_topic_tool",
    "update_topic_tool",
    "delete_topic_tool",
    "message_analysis",
    "get_message_analysis_tool",
    "create_message_analysis_tool",
    "update_message_analysis_tool",
    "delete_message_analysis_tool",
    "message_topics",
    "get_message_topic_tool",
    "create_message_topic_tool",
    "update_message_topic_tool",
    "delete_message_topic_tool",
    "room_history_topics",
    "get_room_history_topic_tool",
    "create_room_history_topic_tool",
    "update_room_history_topic_tool",
    "delete_room_history_topic_tool",
]
