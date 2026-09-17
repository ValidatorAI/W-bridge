import asyncio
from dataclasses import dataclass
from typing import Any

from helpers.environment import BASE_HERMES_PROFILE


@dataclass
class SpaceEventQueueItem:
    """Item queued for processing a Space event through Hermes."""

    space_event_id: str | None
    event_type: str | None
    event_data: dict[str, Any] | None
    profile: str = BASE_HERMES_PROFILE
    # Routing unit of the event (see bus/dedupe.py). None = not deduplicated, dispatch
    # straight away; a "message:..." key also marks the item for the merge settle window.
    dedupe_key: str | None = None
    # Internal row id of the stored event. The Rails event id (space_event_id) is not
    # unique in the bridge table (a replayed webhook keeps its id), so the row id is the
    # authoritative reference and is resolved first.
    space_event_row_id: int | None = None



# Queue for incoming Space events to be forwarded to Hermes
space_events_queue: asyncio.Queue[SpaceEventQueueItem] = asyncio.Queue()

