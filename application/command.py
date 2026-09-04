from datetime import datetime, timezone
import logging

from sqlalchemy.orm import Session

from db.database import SessionLocal

logger = logging.getLogger(__name__)


def _create_session_sync(session_key: str, room_id: str) -> int | None:
    logger.warning("Session tracking tables were removed; session persistence is disabled.")
    return None


def _create_message_session_sync(message_id: int, session_id: int) -> None:
    return None


def _create_reply_session_sync(reply_id: int, session_id: int) -> None:
    return None


def _set_active_session_for_room_sync(room_id: str, session_id: int) -> None:
    return None


def _get_session_id_by_key_and_room_sync(session_key: str, room_id: str) -> int | None:
    return None


def _get_active_session_id_by_room_sync(room_id: str) -> int | None:
    return None


def _get_session_key_by_id_sync(session_id: int) -> str | None:
    return None


def _get_session_history_sync(session_id: int) -> list[dict[str, str]]:
    return []


def _create_hermes_session_sync(
    hermes_id: str,
    session_id: int,
    is_forked: bool = False,
    parent: str | None = None,
) -> str | None:
    return hermes_id


def _create_hermess_message_sync(
    hermes_message_id: str,
    message_id: int,
    is_bot_reply: bool,
) -> str | None:
    return hermes_message_id


def _get_hermes_session_by_id_sync(hermes_id: str):
    return None


def _get_hermes_session_by_session_id_sync(session_id: int):
    return None


def _get_hermess_message_by_id_sync(hermes_message_id: str):
    return None


def _get_hermess_message_by_message_id_sync(message_id: int):
    return None