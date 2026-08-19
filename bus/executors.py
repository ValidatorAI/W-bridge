from typing import Any

from agent.hermes import chat_completions
from agent.hermes_logic import send_chat_history
from schemas import ChatCompletionsInput, SendChatHistoryInput


async def run_chat_completation(input_data: ChatCompletionsInput) -> dict[str, Any]:
    return await chat_completions(
        input_data.payload,
        session_id=input_data.session_id,
        session_key=input_data.session_key,
        profile=input_data.profile,
    )


async def run_send_chat_history(input_data: SendChatHistoryInput) -> tuple[str, dict[str, Any]]:
    return await send_chat_history(
        input_data.history,
        session_id=input_data.session_id,
        profile=input_data.profile,
    )