import asyncio
import logging
import re
import uuid
from typing import Any

from agent.hermes import create_new_hermes_session
from agent.hermes_logic import send_chat_history
from application.command import (
    _create_hermes_session_sync,
    _create_hermess_message_sync,
    _create_message_session_sync,
    _create_reply_session_sync,
    _create_session_sync,
    _get_active_session_id_by_room_sync,
    _get_hermes_session_by_session_id_sync,
    _get_session_key_by_id_sync,
    _get_session_history_sync,
    _get_session_id_by_key_and_room_sync,
    _save_bot_reply_sync,
    _save_message_log_sync,
    _set_active_session_for_room_sync,
)
from helpers.helpers import _strip_command_occurrence


logger = logging.getLogger(__name__)


def _extract_hermes_session_id(payload: dict[str, Any] | None) -> str | None:
    if not isinstance(payload, dict):
        return None

    for key in ("id", "session_id"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    nested = payload.get("session")
    if isinstance(nested, dict):
        value = nested.get("id") or nested.get("session_id")
        if isinstance(value, str) and value.strip():
            return value.strip()

    data = payload.get("data")
    if isinstance(data, dict):
        value = data.get("id") or data.get("session_id")
        if isinstance(value, str) and value.strip():
            return value.strip()

    return None


def _extract_hermes_message_id(payload: dict[str, Any] | None) -> str | None:
    if not isinstance(payload, dict):
        return None

    value = payload.get("id")
    if isinstance(value, str) and value.strip():
        return value.strip()

    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first_choice = choices[0]
        if isinstance(first_choice, dict):
            message = first_choice.get("message")
            if isinstance(message, dict):
                message_id = message.get("id")
                if isinstance(message_id, str) and message_id.strip():
                    return message_id.strip()

    return None


async def _ensure_hermes_session_id(local_session_id: int) -> str | None:
    existing_hermes_session = await asyncio.to_thread(
        _get_hermes_session_by_session_id_sync,
        local_session_id,
    )
    if existing_hermes_session is not None:
        return existing_hermes_session.id

    hermes_create_response = await create_new_hermes_session({})
    hermes_session_id = _extract_hermes_session_id(hermes_create_response)
    if hermes_session_id is None:
        logger.error("Hermes session creation succeeded but session id was not found in response")
        return None

    created = await asyncio.to_thread(
        _create_hermes_session_sync,
        hermes_session_id,
        local_session_id,
    )
    if created is None:
        return None

    return created


def _build_user_hermes_message_id(hermes_session_id: str, message_id: int) -> str:
    return f"{hermes_session_id}:user:{message_id}"


def prepare_new_message(
    message_id: int | None,
    user_name: str,
    room_path: str,
    raw_content: str,
) -> tuple[list[dict[str, str]], int | None, str | None]:
    match = re.search(r"/new(?::([^\s]+))?", raw_content)
    if match is None:
        session_name = f"session-{uuid.uuid4().hex[:4]}"
        content = raw_content.strip()
    else:
        session_name = (match.group(1) or "").strip() or f"session-{uuid.uuid4().hex[:4]}"
        content = (raw_content[: match.start()] + raw_content[match.end() :]).strip() or raw_content.strip()

    session_id = _create_session_sync(session_name, room_path)
    if message_id is not None and session_id is not None:
        _create_message_session_sync(message_id, session_id)

    return (
        [
            {
                "role": "system",
                "content": (
                    f"message_id={message_id}; user={user_name}; room={room_path}. "
                    f"Start a fresh session named '{session_name}' and ignore earlier context."
                ),
            },
            {"role": "user", "content": content},
        ],
        session_id,
        session_name,
    )


def prepare_single_message(
    message_id: int | None,
    user_name: str,
    room_path: str,
    raw_content: str,
) -> tuple[list[dict[str, str]], int | None, str | None]:
    del message_id, user_name, room_path
    content = _strip_command_occurrence(raw_content, "/single")
    return ([{"role": "user", "content": content}], None, None)


def prepare_named_session_message(
    message_id: int | None,
    user_name: str,
    room_path: str,
    raw_content: str,
) -> tuple[list[dict[str, str]], int | None, str | None]:
    match = re.search(r"/session:([^\s]+)", raw_content)
    if match is None:
        return prepare_normal_message(message_id, user_name, room_path, raw_content)

    session_name = match.group(1).strip()
    content = (raw_content[: match.start()] + raw_content[match.end() :]).strip() or raw_content.strip()

    session_id = _get_session_id_by_key_and_room_sync(session_name, room_path)
    if session_id is None:
        session_id = _create_session_sync(session_name, room_path)
    else:
        _set_active_session_for_room_sync(room_path, session_id)

    session_history = _get_session_history_sync(session_id) if session_id is not None else []

    if message_id is not None and session_id is not None:
        _create_message_session_sync(message_id, session_id)

    return (
        [
            {
                "role": "system",
                "content": (
                    f"message_id={message_id}; user={user_name}; room={room_path}. "
                    f"Use session named '{session_name}' as context key."
                ),
            },
            *session_history,
            {"role": "user", "content": content},
        ],
        session_id,
        session_name,
    )


def prepare_normal_message(
    message_id: int | None,
    user_name: str,
    room_path: str,
    raw_content: str,
) -> tuple[list[dict[str, str]], int | None, str | None]:
    del user_name
    session_id = _get_active_session_id_by_room_sync(room_path)
    session_key: str | None = None
    if session_id is None:
        session_key = f"session-{uuid.uuid4().hex[:4]}"
        session_id = _create_session_sync(session_key, room_path)
    else:
        session_key = _get_session_key_by_id_sync(session_id)

    session_history = _get_session_history_sync(session_id) if session_id is not None else []

    if message_id is not None and session_id is not None:
        _create_message_session_sync(message_id, session_id)

    return (
        [
            *session_history,
            {"role": "user", "content": raw_content.strip()},
        ],
        session_id,
        session_key,
    )


def prepare_base_message(
    message_id: int | None,
    user_name: str,
    room_path: str,
    raw_content: str,
) -> tuple[list[dict[str, str]], int | None, str | None]:
    normalized = raw_content.strip()

    if "/new" in normalized:
        return prepare_new_message(message_id, user_name, room_path, raw_content)
    if "/single" in normalized:
        return prepare_single_message(message_id, user_name, room_path, raw_content)
    if "/session:" in normalized:
        return prepare_named_session_message(message_id, user_name, room_path, raw_content)
    if "/h" in normalized or "/help" in normalized:
        return ([], None, None)
    return prepare_normal_message(message_id, user_name, room_path, raw_content)


async def generate_and_persist_bot_reply(
    user_name: str,
    room_path: str,
    raw_content: str,
) -> tuple[str, str | None]:
    message_id = await asyncio.to_thread(
        _save_message_log_sync,
        user_name,
        room_path,
        raw_content,
    )

    message_payload, local_session_id, local_session_key = prepare_base_message(
        message_id,
        user_name,
        room_path,
        raw_content,
    )

    if not message_payload:
        logger.info("Ask help.")
        return ("Help", local_session_key)

    hermes_session_id: str | None = None
    if local_session_id is not None:
        hermes_session_id = await _ensure_hermes_session_id(local_session_id)
        if message_id is not None and hermes_session_id is not None:
            await asyncio.to_thread(
                _create_hermess_message_sync,
                _build_user_hermes_message_id(hermes_session_id, message_id),
                message_id,
                False,
            )

    bot_reply, bot_payload = await send_chat_history(
        message_payload,
        session_id=hermes_session_id,
    )

    if message_id is not None:
        bot_reply_id = await asyncio.to_thread(_save_bot_reply_sync, message_id, bot_reply)
        if bot_reply_id is not None:
            if local_session_id is not None:
                await asyncio.to_thread(_create_reply_session_sync, bot_reply_id, local_session_id)

            hermes_bot_message_id = _extract_hermes_message_id(bot_payload) or f"bot-reply:{bot_reply_id}"
            await asyncio.to_thread(
                _create_hermess_message_sync,
                hermes_bot_message_id,
                bot_reply_id,
                True,
            )
        else:
            logger.warning("Skipping reply-session persistence because bot reply id is unavailable")
    else:
        logger.warning("Skipping bot reply persistence because message log id is unavailable")

    return (bot_reply, local_session_key)
