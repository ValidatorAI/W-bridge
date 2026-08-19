from typing import Any

from agent.hermes import chat_completions
from bus.queues import chat_completions_queue, send_chat_history_queue
from schemas import ChatCompletionsInput, SendChatHistoryInput


async def run_chat_completation(input_data: ChatCompletionsInput) -> dict[str, Any]:
    return await chat_completions(
        input_data.payload,
        session_id=input_data.session_id,
        session_key=input_data.session_key,
        profile=input_data.profile,
    )


async def run_send_chat_history(input_data: SendChatHistoryInput) -> tuple[str, dict[str, Any]]:
    from agent.hermes_logic import send_chat_history

    return await send_chat_history(
        input_data.history,
        session_id=input_data.session_id,
        profile=input_data.profile,
    )


async def enqueue_chat_completation(input_data: ChatCompletionsInput) -> dict[str, Any]:
    await chat_completions_queue.put(input_data)
    queued_input = await chat_completions_queue.get()
    try:
        return await run_chat_completation(queued_input)
    finally:
        chat_completions_queue.task_done()


async def enqueue_send_chat_history(input_data: SendChatHistoryInput) -> tuple[str, dict[str, Any]]:
    await send_chat_history_queue.put(input_data)
    queued_input = await send_chat_history_queue.get()
    try:
        return await run_send_chat_history(queued_input)
    finally:
        send_chat_history_queue.task_done()