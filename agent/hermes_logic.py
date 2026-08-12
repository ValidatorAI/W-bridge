import os
from typing import Any

from agent.hermes import chat_completions

MODEL = os.environ.get("MODEL", "deepseek-v4-flash")

base_system_prompt = "Answer using only this chat history. Do not use context from other sessions. For formatting do not use markup, you must use HTML tags like <ul>,<li>,<a>,<b>,<pre>, specially for codes use <pre> tag"


# ----------------------------- Hermes-version -----------------------------

def _extract_reply_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first_choice = choices[0]
        if isinstance(first_choice, dict):
            message = first_choice.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str):
                    return content
    return ""

async def send_chat(message: str, history: list | None = None) -> str:
    """Send a single message to Hermes and return the reply text."""
    messages = (history or []) + [{"role": "user", "content": message}]

    response = await chat_completions(
        {
            "model": MODEL,
            "messages": messages,
        }
    )

    return _extract_reply_text(response)


async def send_chat_history(history: list[dict[str, str]], *, session_id: str | None = None) -> tuple[str, dict[str, Any]]:
    """Send one full chat history to Hermes and return the assistant reply."""
    # Restrict the model to this provided history only.
    system_message: dict[str, str] = {
        "role": "system",
        "content": base_system_prompt,
    }
    messages: list[dict[str, str]] = [system_message, *history]

    response = await chat_completions(
        {
            "model": MODEL,
            "messages": messages,
        },
        session_id=session_id,
    )

    return _extract_reply_text(response), response