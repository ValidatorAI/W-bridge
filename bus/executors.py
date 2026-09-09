import json
import logging
from typing import Any

from agent.hermes import chat_completions
from agent.hermes_logic import build_space_event_message
from bus.queues import (
    ChatCompletionQueueItem,
    SendChatHistoryQueueItem,
    SpaceEventQueueItem,
    chat_completions_queue,
    send_chat_history_queue,
    space_events_queue,
)
from db.database import SessionLocal
from db.models import SpaceEvent

logger = logging.getLogger(__name__)


async def run_chat_completation(input_data: ChatCompletionQueueItem) -> dict[str, Any]:
    return await chat_completions(
        input_data.payload,
        session_id=input_data.session_id,
        session_key=input_data.session_key,
        profile=input_data.profile,
    )


async def run_send_chat_history(input_data: SendChatHistoryQueueItem) -> tuple[str, dict[str, Any]]:
    from agent.hermes_logic import send_chat_history

    return await send_chat_history(
        input_data.history,
        session_id=input_data.session_id,
        profile=input_data.profile,
    )


async def _run_chat_completation_and_update_space_event(
    item: SpaceEventQueueItem,
    space_event: SpaceEvent,
) -> dict[str, Any]:
    """Build a chat payload from the Space event, run it, and update the DB row."""
    message_content = build_space_event_message(
        event_type=item.event_type,
        event_data=item.event_data,
    )

    payload = {
        "messages": [
            {
                "role": "user",
                "content": message_content,
            }
        ]
    }

    response = await run_chat_completation(
        ChatCompletionQueueItem(
            payload=payload,
            profile=item.profile,
        )
    )

    from datetime import datetime, timezone

    space_event.sent_date = datetime.now(timezone.utc)
    space_event.result = json.dumps(response)

    db = SessionLocal()
    try:
        db.add(space_event)
        db.commit()
    except Exception:
        logger.exception("Failed to update space_event id=%s after Hermes call", space_event.id)
        db.rollback()
    finally:
        db.close()

    return response


async def run_space_event(input_data: SpaceEventQueueItem) -> dict[str, Any] | None:
    """Load a Space event from the DB and forward it to Hermes chat completions."""
    db = SessionLocal()
    try:
        space_event: SpaceEvent | None = db.query(SpaceEvent).filter(
            SpaceEvent.space_event_id == input_data.space_event_id
        ).first()

        if space_event is None:
            logger.error("SpaceEvent not found for space_event_id=%s", input_data.space_event_id)
            return None

        return await _run_chat_completation_and_update_space_event(input_data, space_event)
    finally:
        db.close()


async def enqueue_chat_completation(input_data: ChatCompletionQueueItem) -> None:
    await chat_completions_queue.put(input_data)


async def enqueue_send_chat_history(input_data: SendChatHistoryQueueItem) -> None:
    await send_chat_history_queue.put(input_data)


async def submit_chat_completation(input_data: ChatCompletionQueueItem) -> None:
    await chat_completions_queue.put(input_data)


async def submit_send_chat_history(input_data: SendChatHistoryQueueItem) -> None:
    await send_chat_history_queue.put(input_data)


async def submit_space_event(input_data: SpaceEventQueueItem) -> None:
    await space_events_queue.put(input_data)