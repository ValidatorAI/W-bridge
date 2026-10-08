from ..schema import Topic, TopicList
from ._client import prune, request


async def list_topics(
    *,
    project_id: int | str | None = None,
    active: bool | None = None,
    need_an_action: bool | None = None,
    room_id: int | str | None = None,
    parent_topic_id: int | str | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> TopicList:
    return await request(
        "GET",
        "/topics",
        params=prune(
            {
                "project_id": project_id,
                "active": active,
                "need_an_action": need_an_action,
                "room_id": room_id,
                "parent_topic_id": parent_topic_id,
                "page": page,
                "per_page": per_page,
            }
        ),
    )


async def get_topic(topic_id: int | str) -> Topic:
    return await request("GET", f"/topics/{topic_id}")


async def create_topic(
    project_id: int | str,
    name: str,
    *,
    parent_topic_id: int | str | None = None,
    related_topics: str | None = None,
    active: bool | None = None,
    importance_level: int | None = None,
    memory: str | None = None,
    state: str | None = None,
    need_an_action: bool | None = None,
    required_actions: str | None = None,
) -> Topic:
    return await request(
        "POST",
        "/topics",
        json=prune(
            {
                "project_id": project_id,
                "parent_topic_id": parent_topic_id,
                "name": name,
                "related_topics": related_topics,
                "active": active,
                "importance_level": importance_level,
                "memory": memory,
                "state": state,
                "need_an_action": need_an_action,
                "required_actions": required_actions,
            }
        ),
    )


async def update_topic(
    topic_id: int | str,
    *,
    project_id: int | str | None = None,
    parent_topic_id: int | str | None = None,
    name: str | None = None,
    related_topics: str | None = None,
    active: bool | None = None,
    importance_level: int | None = None,
    memory: str | None = None,
    state: str | None = None,
    need_an_action: bool | None = None,
    required_actions: str | None = None,
) -> Topic:
    return await request(
        "PATCH",
        f"/topics/{topic_id}",
        json=prune(
            {
                "project_id": project_id,
                "parent_topic_id": parent_topic_id,
                "name": name,
                "related_topics": related_topics,
                "active": active,
                "importance_level": importance_level,
                "memory": memory,
                "state": state,
                "need_an_action": need_an_action,
                "required_actions": required_actions,
            }
        ),
    )


async def delete_topic(topic_id: int | str) -> None:
    return await request("DELETE", f"/topics/{topic_id}")
