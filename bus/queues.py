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


# Queue for incoming Space events to be forwarded to Hermes
space_events_queue: asyncio.Queue[SpaceEventQueueItem] = asyncio.Queue()

