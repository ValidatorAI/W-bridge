import json
import logging
from typing import Any

from agent.hermes import chat_completions
from agent.hermes_logic import build_space_event_message
from bus.queues import SpaceEventQueueItem, space_events_queue
from db.database import SessionLocal
from db.models import SpaceEvent
from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


async def _send_to_hermes(
    payload: dict[str, Any],
    *,
    profile: str,
    session_id: str | None = None,
    session_key: str | None = None,
) -> dict[str, Any]:
    """Low-level wrapper around agent.hermes.chat_completions."""
    return await chat_completions(
        payload,
        session_id=session_id,
        session_key=session_key,
        profile=profile,
    )


async def _run_space_event_and_update(
    item: SpaceEventQueueItem,
    space_event: SpaceEvent,
    db: Session,
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

    response = await _send_to_hermes(payload, profile=item.profile)

    space_event.sent_date = func.now()
    space_event.result = json.dumps(response)

    try:
        # space_event is already attached to this session in run_space_event.
        db.commit()
    except Exception:
        logger.exception("Failed to update space_event id=%s after Hermes call", space_event.id)
        db.rollback()

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

        return await _run_space_event_and_update(input_data, space_event, db)
    finally:
        db.close()


async def submit_space_event(input_data: SpaceEventQueueItem) -> None:
    await space_events_queue.put(input_data)