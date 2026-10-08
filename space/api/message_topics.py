from ..schema import MessageTopic, MessageTopicList
from ._client import prune, request


async def list_message_topics(
    *,
    topic_id: int | str | None = None,
    message_id: int | str | None = None,
    created_date: str | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> MessageTopicList:
    return await request(
        "GET",
        "/message_topics",
        params=prune(
            {
                "topic_id": topic_id,
                "message_id": message_id,
                "created_date": created_date,
                "page": page,
                "per_page": per_page,
            }
        ),
    )


async def get_message_topic(message_topic_id: int | str) -> MessageTopic:
    return await request("GET", f"/message_topics/{message_topic_id}")


async def create_message_topic(
    topic_id: int | str,
    message_id: int | str,
    *,
    created_date: str | None = None,
) -> MessageTopic:
    return await request(
        "POST",
        "/message_topics",
        json=prune(
            {
                "topic_id": topic_id,
                "message_id": message_id,
                "created_date": created_date,
            }
        ),
    )


async def update_message_topic(
    message_topic_id: int | str,
    *,
    topic_id: int | str | None = None,
    message_id: int | str | None = None,
    created_date: str | None = None,
) -> MessageTopic:
    return await request(
        "PATCH",
        f"/message_topics/{message_topic_id}",
        json=prune(
            {
                "topic_id": topic_id,
                "message_id": message_id,
                "created_date": created_date,
            }
        ),
    )


async def delete_message_topic(message_topic_id: int | str) -> None:
    return await request("DELETE", f"/message_topics/{message_topic_id}")
