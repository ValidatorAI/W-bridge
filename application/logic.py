import asyncio
import logging
import random
import re
import uuid
from typing import Any

from agent.hermes import create_new_hermes_session
from agent.hermes import sessions_fork
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

HermesMessage = dict[str, Any]
HermesHistory = list[HermesMessage]


_SESSION_ADJECTIVES: tuple[str, ...] = (
    "amber",
    "ancient",
    "ardent",
    "autumn",
    "azure",
    "balanced",
    "beaming",
    "bold",
    "bright",
    "brisk",
    "calm",
    "charmed",
    "cheerful",
    "classic",
    "cloudy",
    "coastal",
    "clever",
    "crisp",
    "daring",
    "dawn",
    "deep",
    "delightful",
    "direct",
    "dreamy",
    "dusty",
    "eager",
    "early",
    "electric",
    "emerald",
    "faithful",
    "fancy",
    "fearless",
    "fierce",
    "fluent",
    "focused",
    "fresh",
    "gentle",
    "glad",
    "golden",
    "grand",
    "grateful",
    "green",
    "happy",
    "hidden",
    "honest",
    "humble",
    "icy",
    "indigo",
    "jolly",
    "keen",
    "kind",
    "lucky",
    "lunar",
    "lively",
    "lofty",
    "mellow",
    "midnight",
    "misty",
    "modern",
    "morning",
    "native",
    "neat",
    "nimble",
    "noble",
    "northern",
    "open",
    "patient",
    "peaceful",
    "pearl",
    "playful",
    "polished",
    "primal",
    "quiet",
    "quick",
    "radiant",
    "rainy",
    "rapid",
    "ready",
    "red",
    "resolute",
    "restless",
    "rich",
    "robust",
    "royal",
    "rustic",
    "sandy",
    "scarlet",
    "serene",
    "sharp",
    "silver",
    "simple",
    "skilled",
    "smart",
    "snowy",
    "solar",
    "solid",
    "sparkling",
    "spirited",
    "spring",
    "starlit",
    "steady",
    "still",
    "stormy",
    "strong",
    "sunny",
    "swift",
    "tidy",
    "timeless",
    "tranquil",
    "trusty",
    "upbeat",
    "urban",
    "vast",
    "velvet",
    "vivid",
    "warm",
    "wild",
    "winter",
    "wise",
    "wooden",
    "young",
)

_SESSION_NOUNS: tuple[str, ...] = (
    "anchor",
    "apollo",
    "arc",
    "aurora",
    "bay",
    "beacon",
    "bison",
    "blossom",
    "brook",
    "butterfly",
    "canyon",
    "cedar",
    "channel",
    "circle",
    "cliff",
    "cloud",
    "compass",
    "coral",
    "cove",
    "creek",
    "crescent",
    "crystal",
    "dawn",
    "delta",
    "dolphin",
    "drift",
    "echo",
    "ember",
    "field",
    "falcon",
    "feather",
    "firefly",
    "flame",
    "forest",
    "fox",
    "garden",
    "glacier",
    "glade",
    "grove",
    "harbor",
    "hawk",
    "horizon",
    "island",
    "jade",
    "journey",
    "lake",
    "lantern",
    "leaf",
    "legend",
    "lighthouse",
    "lotus",
    "meadow",
    "meteor",
    "moon",
    "mountain",
    "nebula",
    "oasis",
    "ocean",
    "otter",
    "owl",
    "path",
    "peak",
    "pioneer",
    "planet",
    "prairie",
    "quartz",
    "reef",
    "river",
    "robin",
    "rock",
    "rose",
    "sail",
    "sage",
    "sand",
    "sea",
    "shadow",
    "shore",
    "sky",
    "snow",
    "songbird",
    "spruce",
    "star",
    "sparrow",
    "stone",
    "stream",
    "sun",
    "summit",
    "surf",
    "thunder",
    "tiger",
    "timber",
    "tower",
    "trail",
    "valley",
    "vista",
    "voyager",
    "wave",
    "whale",
    "willow",
    "wind",
    "wing",
    "wolf",
    "zephyr",
)


def _build_readable_session_name() -> str:
    adjective = random.choice(_SESSION_ADJECTIVES)
    noun = random.choice(_SESSION_NOUNS)
    suffix = uuid.uuid4().hex[:3]
    return f"{adjective}-{noun}-{suffix}"


def _generate_session_name(room_path: str) -> str:
    for _ in range(8):
        candidate = _build_readable_session_name()
        if _get_session_id_by_key_and_room_sync(candidate, room_path) is None:
            return candidate
    return f"{_build_readable_session_name()}-{uuid.uuid4().hex[:2]}"


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


async def _ensure_hermes_session_id(local_session_id: int, profile_name: str) -> str | None:
    existing_hermes_session = await asyncio.to_thread(
        _get_hermes_session_by_session_id_sync,
        local_session_id,
    )
    if existing_hermes_session is not None:
        return existing_hermes_session.id

    hermes_create_response = await create_new_hermes_session({}, profile=profile_name)
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


def _fork_parent_session_id(room_path: str) -> int | None:
    return _get_active_session_id_by_room_sync(room_path)


def _compose_user_content(raw_text: str, attachment_parts: list[dict[str, Any]]) -> str | list[dict[str, Any]]:
    text = raw_text.strip()
    if not attachment_parts:
        return text

    content_parts: list[dict[str, Any]] = []
    if text:
        content_parts.append({"type": "text", "text": text})
    content_parts.extend(attachment_parts)
    return content_parts


def _message_for_storage(raw_text: str, attachment_log: str | None) -> str:
    text = raw_text.strip()
    if attachment_log and text:
        return f"{text}\n\n[attachments: {attachment_log}]"
    if attachment_log:
        return f"[attachments: {attachment_log}]"
    return text


def _normalize_sender_bot(sender_bot: str | None) -> str:
    value = (sender_bot or "").strip()
    return value or "default"


def _inject_webhook_context_message(
    message_payload: HermesHistory,
    room_path: str,
    sender_bot: str | None,
) -> HermesHistory:
    if not message_payload:
        return message_payload

    system_message: HermesMessage = {
        "role": "system",
        "content": (
            f"This message is sent from room {room_path} "
            f"using sender bot {_normalize_sender_bot(sender_bot)}."
        ),
    }

    if len(message_payload) == 1:
        return [system_message, message_payload[0]]

    return [system_message] + message_payload[-1:]


def prepare_new_message(
    message_id: int | None,
    user_name: str,
    room_path: str,
    raw_content: str,
    attachment_parts: list[dict[str, Any]],
) -> tuple[HermesHistory, int | None, str | None]:
    match = re.search(r"/new(?::([^\s]+))?", raw_content)
    if match is None:
        session_name = _generate_session_name(room_path)
        content = raw_content.strip()
    else:
        session_name = (match.group(1) or "").strip() or _generate_session_name(room_path)
        content = (raw_content[: match.start()] + raw_content[match.end() :]).strip() or raw_content.strip()

    session_id = _create_session_sync(session_name, room_path)
    if message_id is not None and session_id is not None:
        _create_message_session_sync(message_id, session_id)

    user_content = _compose_user_content(content, attachment_parts)

    return (
        [
            {
                "role": "system",
                "content": (
                    f"message_id={message_id}; user={user_name}; room={room_path}. "
                    f"Start a fresh session named '{session_name}' and ignore earlier context."
                ),
            },
            {"role": "user", "content": user_content},
        ],
        session_id,
        session_name,
    )


def prepare_single_message(
    message_id: int | None,
    user_name: str,
    room_path: str,
    raw_content: str,
    attachment_parts: list[dict[str, Any]],
) -> tuple[HermesHistory, int | None, str | None]:
    del message_id, user_name, room_path
    content = _strip_command_occurrence(raw_content, "/single")
    return ([{"role": "user", "content": _compose_user_content(content, attachment_parts)}], None, None)


def prepare_named_session_message(
    message_id: int | None,
    user_name: str,
    room_path: str,
    raw_content: str,
    attachment_parts: list[dict[str, Any]],
) -> tuple[HermesHistory, int | None, str | None]:
    match = re.search(r"/session:([^\s]+)", raw_content)
    if match is None:
        return prepare_normal_message(message_id, user_name, room_path, raw_content, attachment_parts)

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

    user_content = _compose_user_content(content, attachment_parts)

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
            {"role": "user", "content": user_content},
        ],
        session_id,
        session_name,
    )


def prepare_fork_message(
    message_id: int | None,
    user_name: str,
    room_path: str,
    raw_content: str,
    attachment_parts: list[dict[str, Any]],
) -> tuple[HermesHistory, int | None, str | None, int | None]:
    match = re.search(r"/fork:([^\s]+)", raw_content)
    if match is None:
        message_payload, session_id, session_key = prepare_normal_message(
            message_id,
            user_name,
            room_path,
            raw_content,
            attachment_parts,
        )
        return (message_payload, session_id, session_key, None)

    fork_name = match.group(1).strip()
    content = (raw_content[: match.start()] + raw_content[match.end() :]).strip() or raw_content.strip()

    parent_session_id = _fork_parent_session_id(room_path)
    parent_history = _get_session_history_sync(parent_session_id) if parent_session_id is not None else []

    session_id = _create_session_sync(fork_name, room_path)
    if message_id is not None and session_id is not None:
        _create_message_session_sync(message_id, session_id)

    user_content = _compose_user_content(content, attachment_parts)

    return (
        [
            {
                "role": "system",
                "content": (
                    f"message_id={message_id}; user={user_name}; room={room_path}. "
                    f"Fork active context into session named '{fork_name}' and continue from there."
                ),
            },
            *parent_history,
            {"role": "user", "content": user_content},
        ],
        session_id,
        fork_name,
        parent_session_id,
    )


def prepare_normal_message(
    message_id: int | None,
    user_name: str,
    room_path: str,
    raw_content: str,
    attachment_parts: list[dict[str, Any]],
) -> tuple[HermesHistory, int | None, str | None]:
    del user_name
    session_id = _get_active_session_id_by_room_sync(room_path)
    session_key: str | None = None
    if session_id is None:
        session_key = _generate_session_name(room_path)
        session_id = _create_session_sync(session_key, room_path)
    else:
        session_key = _get_session_key_by_id_sync(session_id)

    session_history = _get_session_history_sync(session_id) if session_id is not None else []

    if message_id is not None and session_id is not None:
        _create_message_session_sync(message_id, session_id)

    user_content = _compose_user_content(raw_content, attachment_parts)

    return (
        [
            *session_history,
            {"role": "user", "content": user_content},
        ],
        session_id,
        session_key,
    )


def prepare_base_message(
    message_id: int | None,
    user_name: str,
    room_path: str,
    raw_content: str,
    attachment_parts: list[dict[str, Any]],
) -> tuple[HermesHistory, int | None, str | None, int | None, bool]:
    normalized = raw_content.strip()

    if "/new" in normalized:
        message_payload, session_id, session_key = prepare_new_message(message_id, user_name, room_path, raw_content, attachment_parts)
        return (message_payload, session_id, session_key, None, False)
    if "/single" in normalized:
        message_payload, session_id, session_key = prepare_single_message(message_id, user_name, room_path, raw_content, attachment_parts)
        return (message_payload, session_id, session_key, None, False)
    if "/session:" in normalized:
        message_payload, session_id, session_key = prepare_named_session_message(message_id, user_name, room_path, raw_content, attachment_parts)
        return (message_payload, session_id, session_key, None, False)
    if "/fork:" in normalized:
        message_payload, session_id, session_key, parent_session_id = prepare_fork_message(
            message_id,
            user_name,
            room_path,
            raw_content,
            attachment_parts,
        )
        return (message_payload, session_id, session_key, parent_session_id, True)
    if "/h" in normalized or "/help" in normalized:
        return ([], None, None, None, False)
    message_payload, session_id, session_key = prepare_normal_message(message_id, user_name, room_path, raw_content, attachment_parts)
    return (message_payload, session_id, session_key, None, False)


async def generate_and_persist_bot_reply(
    user_name: str,
    room_path: str,
    raw_content: str,
    attachment_parts: list[dict[str, Any]] | None = None,
    attachment_log: str | None = None,
    profile_name: str = "default",
    sender_bot: str = "default",
) -> tuple[str, str | None]:
    resolved_attachment_parts = attachment_parts or []
    message_text_for_storage = _message_for_storage(raw_content, attachment_log)

    message_id = await asyncio.to_thread(
        _save_message_log_sync,
        user_name,
        room_path,
        message_text_for_storage,
    )

    message_payload, local_session_id, local_session_key, fork_parent_local_session_id, should_fork_hermes = prepare_base_message(
        message_id,
        user_name,
        room_path,
        raw_content,
        resolved_attachment_parts,
    )

    if not message_payload:
        logger.info("Ask help.")
        return ("Help", local_session_key)

    message_payload = _inject_webhook_context_message(message_payload, room_path, sender_bot)

    hermes_session_id: str | None = None
    if local_session_id is not None:
        if should_fork_hermes and fork_parent_local_session_id is not None:
            parent_hermes_session = await asyncio.to_thread(
                _get_hermes_session_by_session_id_sync,
                fork_parent_local_session_id,
            )
            if parent_hermes_session is not None:
                try:
                    fork_payload: dict[str, Any] = {}
                    if local_session_key is not None:
                        fork_payload["title"] = local_session_key
                    hermes_fork_response = await sessions_fork(
                        parent_hermes_session.id,
                        fork_payload,
                        profile=profile_name,
                    )
                    forked_hermes_session_id = _extract_hermes_session_id(hermes_fork_response)
                    if forked_hermes_session_id is not None:
                        created_fork = await asyncio.to_thread(
                            _create_hermes_session_sync,
                            forked_hermes_session_id,
                            local_session_id,
                            True,
                            parent_hermes_session.id,
                        )
                        if created_fork is not None:
                            hermes_session_id = created_fork
                except Exception:
                    logger.exception("Failed to fork Hermes session; falling back to regular session creation")

        if hermes_session_id is None:
            hermes_session_id = await _ensure_hermes_session_id(local_session_id, profile_name)

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
        profile=profile_name,
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
