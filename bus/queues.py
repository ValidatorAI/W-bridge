import asyncio
from dataclasses import dataclass
from typing import Any


@dataclass
class ChatCompletionQueueItem:
    """Item queued for agent.hermes.chat_completions."""

    payload: dict[str, Any]
    session_id: str | None = None
    session_key: str | None = None
    profile: str | None = "default"


@dataclass
class SendChatHistoryQueueItem:
    """Item queued for agent.hermes_logic.send_chat_history."""

    history: list[dict[str, Any]]
    session_id: str | None = None
    profile: str | None = "default"


@dataclass
class SpaceEventQueueItem:
    """Item queued for processing a Space event through Hermes."""

    space_event_id: str | None
    event_type: str | None
    event_data: dict[str, Any] | None
    profile: str = "default"


# Queue for requests targeting agent.hermes.chat_completions
chat_completions_queue: asyncio.Queue[ChatCompletionQueueItem] = asyncio.Queue()

# Queue for requests targeting agent.hermes_logic.send_chat_history
send_chat_history_queue: asyncio.Queue[SendChatHistoryQueueItem] = asyncio.Queue()

# Queue for incoming Space events to be forwarded to Hermes
space_events_queue: asyncio.Queue[SpaceEventQueueItem] = asyncio.Queue()

