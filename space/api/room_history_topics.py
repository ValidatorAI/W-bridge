from ..schema import RoomHistoryTopic, RoomHistoryTopicList
from ._client import prune, request


async def list_room_history_topics(
    *,
    room_id: int | str | None = None,
    created_date: str | None = None,
    page: int | None = None,
    per_page: int | None = None,
) -> RoomHistoryTopicList:
    return await request(
        "GET",
        "/room_history_topics",
        params=prune(
            {
                "room_id": room_id,
                "created_date": created_date,
                "page": page,
                "per_page": per_page,
            }
        ),
    )


async def get_room_history_topic(room_history_topic_id: int | str) -> RoomHistoryTopic:
    return await request("GET", f"/room_history_topics/{room_history_topic_id}")


async def create_room_history_topic(
    room_id: int | str,
    *,
    created_date: str | None = None,
    last_state: str | None = None,
) -> RoomHistoryTopic:
    return await request(
        "POST",
        "/room_history_topics",
        json=prune(
            {
                "room_id": room_id,
                "created_date": created_date,
                "last_state": last_state,
            }
        ),
    )


async def update_room_history_topic(
    room_history_topic_id: int | str,
    *,
    room_id: int | str | None = None,
    created_date: str | None = None,
    last_state: str | None = None,
) -> RoomHistoryTopic:
    return await request(
        "PATCH",
        f"/room_history_topics/{room_history_topic_id}",
        json=prune(
            {
                "room_id": room_id,
                "created_date": created_date,
                "last_state": last_state,
            }
        ),
    )


async def delete_room_history_topic(room_history_topic_id: int | str) -> None:
    return await request("DELETE", f"/room_history_topics/{room_history_topic_id}")
