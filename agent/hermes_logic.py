import json
from typing import Any

from agent.hermes import chat_completions
from helpers.environment import MODEL

base_format_hint = "For formatting do not use markup, you must use HTML tags like <ul>,<li>,<a>,<b>,<pre>, specially for codes use <pre> tag"
base_kanban_bord = "use anban board per room, if room is not created yesm create one, this would be used for collaboration"
base_response = "This message is sent from specific room send response to that room use agent with the same name of bot for sending message. "
base_system_prompt = f"{base_response} \n {base_format_hint} \n {base_kanban_bord}"


# ----------------------------- Space event message builder -----------------------------

def build_space_event_message(
    event_type: str | None,
    event_data: dict[str, Any] | None,
) -> str:
    """Convert a Space event into a user message for Hermes chat completions."""
    event_data = event_data or {}
    serialized = json.dumps(event_data, ensure_ascii=False, default=str)
    if event_type:
        return f"Space event ({event_type}): {serialized}"
    return f"Space event: {serialized}"


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
    messages = [{"role": "user", "content": message}]

    response = await chat_completions(
        {"model": MODEL, "messages": messages},
        profile="default",
    )

    return _extract_reply_text(response)


async def send_chat_history(
    history: list[dict[str, Any]],
    *,
    session_id: str | None = None,
    profile: str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Send one full chat history to Hermes and return the assistant reply."""
    # Restrict the model to this provided history only.
    system_message: dict[str, str] = {
        "role": "system",
        "content": base_system_prompt,
    }
    messages: list[dict[str, Any]] = [system_message, *history]

    response = await chat_completions(
        {"model": MODEL, "messages": messages},
        session_id=session_id,
        profile=profile,
    )

    return _extract_reply_text(response), response