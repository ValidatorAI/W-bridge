import asyncio
from typing import Any

from schemas import ChatCompletionsInput, SendChatHistoryInput


# Queue for requests targeting agent.hermes.chat_completions
chat_completions_queue: asyncio.Queue[ChatCompletionsInput] = asyncio.Queue()

# Queue for requests targeting agent.hermes_logic.send_chat_history
send_chat_history_queue: asyncio.Queue[SendChatHistoryInput] = asyncio.Queue()


def prepare_chat_completions_input(
    payload: dict[str, Any],
    *,
    session_id: str | None = None,
    session_key: str | None = None,
    profile: str | None = None,
) -> ChatCompletionsInput:
    return ChatCompletionsInput(
        payload=payload,
        session_id=session_id,
        session_key=session_key,
        profile=profile,
    )


def prepare_send_chat_history_input(
    history: list[dict[str, Any]],
    *,
    session_id: str | None = None,
    profile: str | None = None,
) -> SendChatHistoryInput:
    return SendChatHistoryInput(
        history=history,
        session_id=session_id,
        profile=profile,
    )